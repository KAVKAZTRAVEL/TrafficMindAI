from pathlib import Path
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from app.bot.keyboards import main_menu, subscription_keyboard
from app.bot.keyboards.integrations import (
    integration_categories_keyboard,
    integration_setup_keyboard,
    integrations_list_keyboard,
)
from app.bot.states import AddSiteState
from app.config import get_settings
from app.database import SessionLocal
from app.models import Report, TrafficSource, Website
from app.integrations.registry import CATEGORY_TITLES, get_integration
from app.services.ai_service import explain_sources, recommendations_from_audit
from app.services.audit_service import audit_domain
from app.services.growth_intelligence_service import (
    build_profit_map,
    demo_metrics,
    detect_insights,
    forecast_revenue,
    generate_today_actions,
)
from app.services.infographic_service import render_traffic_map_html
from app.services.integration_connection_service import (
    category_summary,
    prepare_integration_setup,
)
from app.services.link_only_report_service import link_only_report_payload
from app.services.pdf_service import generate_pdf_report
from app.services.subscription_service import PLANS, get_or_create_user, trial_status_text
from app.services.traffic_service import aggregate_sources
from app.services.website_service import add_website

router = Router()


async def current_user(message_or_query):
    telegram_user = message_or_query.from_user
    settings = get_settings()
    async with SessionLocal() as session:
        return await get_or_create_user(session, telegram_user, settings.admin_ids)


@router.message(Command("start"))
async def start(message: Message) -> None:
    user = await current_user(message)
    await message.answer(
        "TrafficMind AI - AI-платформа роста для бизнеса.\n\n"
        "Я отвечаю не только на вопрос «сколько было трафика», а на главное:\n"
        "- откуда приходят деньги;\n"
        "- где теряются лиды и бюджет;\n"
        "- что сделать сегодня;\n"
        "- какой эффект ожидается дальше.\n\n"
        f"{trial_status_text(user)}\n\nВыберите раздел:",
        reply_markup=main_menu(),
    )


@router.callback_query(F.data == "dashboard")
async def dashboard_handler(query: CallbackQuery) -> None:
    metrics = demo_metrics()
    forecast = forecast_revenue(metrics)
    insights = detect_insights(metrics)
    await query.message.answer(
        "Dashboard\n\n"
        f"Доход сейчас: {forecast.current:,.0f} ₽\n"
        f"Прогноз на {forecast.horizon_days} дней: {forecast.lower_bound:,.0f}-{forecast.upper_bound:,.0f} ₽\n"
        f"Главный вывод: {insights[0].title}\n\n"
        "Следующий шаг: откройте «Что делать сегодня», чтобы увидеть приоритетные действия.",
        reply_markup=main_menu(),
    )
    await query.answer()


@router.callback_query(F.data == "profit_map")
async def profit_map_handler(query: CallbackQuery) -> None:
    profit_map = build_profit_map(demo_metrics())
    rows = "\n".join(
        f"- {item['source']}: {item['size']:,.0f} ₽, ROI {item['roi']}, статус: {item['status']}"
        for item in profit_map["nodes"][:4]
    )
    await query.message.answer(
        "Карта прибыли\n\n"
        "Показывает не посетителей, а источники денег: доход, лиды, продажи, ROI и ROAS.\n\n"
        f"{rows}",
        reply_markup=main_menu(),
    )
    await query.answer()


@router.callback_query(F.data == "today_actions")
async def today_actions_handler(query: CallbackQuery) -> None:
    actions = generate_today_actions(demo_metrics())[:3]
    text = "\n\n".join(
        f"{index}. {item.title}\n"
        f"Почему: {item.why}\n"
        f"Эффект: {item.expected_effect}\n"
        f"Влияние: ~{item.revenue_impact:,.0f} ₽\n"
        f"Сложность: {item.complexity}, время: {item.time_to_execute}"
        for index, item in enumerate(actions, start=1)
    )
    await query.message.answer(f"Что делать сегодня\n\n{text}", reply_markup=main_menu())
    await query.answer()


@router.callback_query(F.data == "losses")
async def losses_handler(query: CallbackQuery) -> None:
    insights = [item for item in detect_insights(demo_metrics()) if item.severity in {"high", "critical"}]
    text = "\n\n".join(f"- {item.title}\n{item.explanation}\nДанные: {item.evidence}" for item in insights)
    await query.message.answer(f"Потери\n\n{text or 'Критичных потерь сейчас не найдено.'}", reply_markup=main_menu())
    await query.answer()


@router.callback_query(F.data == "content_ai")
async def content_ai_handler(query: CallbackQuery) -> None:
    await query.message.answer(
        "Content AI\n\n"
        "Генерирует контент-планы, Reels идеи, рекламные объявления, email-кампании, CTA и SEO-страницы на основе аналитики.\n\n"
        "Пример: 7 Reels для TikTok Ads, потому что этот канал уже показывает высокий ROI.",
        reply_markup=main_menu(),
    )
    await query.answer()


@router.callback_query(F.data == "competitors")
async def competitors_handler(query: CallbackQuery) -> None:
    await query.message.answer(
        "Конкуренты\n\n"
        "Раздел покажет популярные страницы, ключевые слова, объявления, соцсети и частоту публикаций конкурентов.\n\n"
        "Главная задача: объяснить, почему конкурент растет и что можно применить у себя.",
        reply_markup=main_menu(),
    )
    await query.answer()


@router.callback_query(F.data == "integrations")
async def integrations_handler(query: CallbackQuery) -> None:
    await query.message.answer(
        "Интеграции\n\n"
        "Выберите тип источника. Я покажу самый короткий путь подключения: вход через аккаунт, API-ключ, пиксель, GTM или webhook.\n\n"
        "После подключения данные будут приводиться к единой модели: прибыль, лиды, продажи, ROI, ROAS и потери.",
        reply_markup=integration_categories_keyboard(),
    )
    await query.answer()


@router.callback_query(F.data.startswith("int_cat:"))
async def integration_category_handler(query: CallbackQuery) -> None:
    category = query.data.split(":", 1)[1]
    if category not in CATEGORY_TITLES:
        await query.answer("Категория не найдена", show_alert=True)
        return
    await query.message.answer(category_summary(category), reply_markup=integrations_list_keyboard(category))
    await query.answer()


@router.callback_query(F.data.startswith("int_svc:"))
async def integration_service_handler(query: CallbackQuery) -> None:
    code = query.data.split(":", 1)[1]
    item = get_integration(code)
    if not item:
        await query.answer("Сервис не найден", show_alert=True)
        return
    async with SessionLocal() as session:
        user = await get_or_create_user(session, query.from_user, get_settings().admin_ids)
        setup = await prepare_integration_setup(session, user, code)
    await query.message.answer(
        setup.text,
        reply_markup=integration_setup_keyboard(code, setup.connect_url, setup.docs_url),
        disable_web_page_preview=True,
    )
    await query.answer()


@router.callback_query(F.data.startswith("int_check:"))
async def integration_check_handler(query: CallbackQuery) -> None:
    code = query.data.split(":", 1)[1]
    item = get_integration(code)
    if not item:
        await query.answer("Сервис не найден", show_alert=True)
        return
    await query.message.answer(
        f"{item.title}\n\n"
        "Проверка подключения добавлена в сценарий. Для OAuth сервисов она начнет работать после настройки callback endpoint и client secret в .env. "
        "Для API-ключей и пикселей бот проверит наличие ключа/событий после первого sync.",
        reply_markup=integration_setup_keyboard(code, None, item.docs_url),
    )
    await query.answer()


@router.message(Command("add_site"))
async def add_site_command(message: Message, state: FSMContext) -> None:
    await state.set_state(AddSiteState.waiting_for_domain)
    await message.answer("Пришлите домен сайта, например example.com.")


@router.callback_query(F.data == "add_site")
async def add_site_callback(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddSiteState.waiting_for_domain)
    await query.message.answer("Пришлите домен сайта, например example.com.")
    await query.answer()


@router.message(AddSiteState.waiting_for_domain)
async def receive_domain(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user, get_settings().admin_ids)
        try:
            website = await add_website(session, user, message.text or "")
        except (ValueError, PermissionError) as exc:
            await message.answer(str(exc), reply_markup=subscription_keyboard())
            return
    await state.clear()
    script = (
        f'<script async src="{get_settings().public_base_url}/static/tracker.js" '
        f'data-token="{website.tracking_token}" data-endpoint="{get_settings().public_base_url}/tracker/event"></script>'
    )
    await message.answer(
        f"Сайт {website.domain} добавлен.\n\n"
        "Скрипт отслеживания для установки на сайт:\n"
        f"<code>{script}</code>\n\n"
        "Теперь можно запустить бесплатный аудит и начать строить карту прибыли.",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


@router.message(Command("audit"))
@router.callback_query(F.data == "audit")
async def audit_handler(event) -> None:
    message = event.message if isinstance(event, CallbackQuery) else event
    async with SessionLocal() as session:
        user = await get_or_create_user(session, event.from_user, get_settings().admin_ids)
        website = await session.scalar(select(Website).where(Website.user_id == user.id).order_by(Website.id.desc()))
        if not website:
            await message.answer("Сначала добавьте сайт.", reply_markup=main_menu())
            return
    await message.answer("Проверяю сайт: доступность, CMS, формы, аналитику, SEO и кнопки связи.")
    audit = await audit_domain(website.domain)
    recs = recommendations_from_audit(audit)
    await message.answer(
        f"Аудит {website.domain}\n\n"
        f"{audit['summary']}\n\n"
        "Что сделать дальше:\n" + "\n".join(f"- {item}" for item in recs),
        reply_markup=main_menu(),
    )
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(Command("connect"))
async def connect_handler(message: Message) -> None:
    async with SessionLocal() as session:
        user = await get_or_create_user(session, message.from_user, get_settings().admin_ids)
        website = await session.scalar(select(Website).where(Website.user_id == user.id).order_by(Website.id.desc()))
        if not website:
            await message.answer("Сначала добавьте сайт.", reply_markup=main_menu())
            return
    script = (
        f'<script async src="{get_settings().public_base_url}/static/tracker.js" '
        f'data-token="{website.tracking_token}" data-endpoint="{get_settings().public_base_url}/tracker/event"></script>'
    )
    await message.answer(
        "Самый простой старт:\n"
        "1. Поставьте скрипт TrafficMind на сайт.\n"
        "2. Подключите GA4 или Яндекс Метрику.\n"
        "3. Подключите CRM, чтобы считать деньги, а не только заявки.\n\n"
        "Скрипт TrafficMind:\n"
        f"<code>{script}</code>\n\n"
        "Ниже можно выбрать сервис и получить короткую инструкцию подключения.",
        parse_mode="HTML",
        reply_markup=integration_categories_keyboard(),
    )


@router.message(Command("traffic_map"))
@router.callback_query(F.data == "traffic_map")
async def traffic_map_handler(event) -> None:
    message = event.message if isinstance(event, CallbackQuery) else event
    async with SessionLocal() as session:
        user = await get_or_create_user(session, event.from_user, get_settings().admin_ids)
        website = await session.scalar(select(Website).where(Website.user_id == user.id).order_by(Website.id.desc()))
        if not website:
            await message.answer("Сначала добавьте сайт.", reply_markup=main_menu())
            return
        sources = await aggregate_sources(session, website.id)
        html_path = f"storage/maps/traffic_map_{website.id}.html"
        render_traffic_map_html(website, sources, html_path)
    await message.answer(
        "Карта прибыли построена по реальным источникам.\n"
        f"HTML-файл карты: {Path(html_path).resolve()}\n\n"
        f"{explain_sources(sources)}",
        reply_markup=main_menu(),
    )
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(Command("recommendations"))
@router.callback_query(F.data.in_({"ask_ai", "find_problem"}))
async def ai_handler(event, state: FSMContext | None = None) -> None:
    message = event.message if isinstance(event, CallbackQuery) else event
    async with SessionLocal() as session:
        user = await get_or_create_user(session, event.from_user, get_settings().admin_ids)
        website = await session.scalar(select(Website).where(Website.user_id == user.id).order_by(Website.id.desc()))
        if not website:
            await message.answer("Сначала добавьте сайт.", reply_markup=main_menu())
            return
        sources = (await session.execute(select(TrafficSource).where(TrafficSource.website_id == website.id))).scalars().all()
    await message.answer(explain_sources(sources), reply_markup=main_menu())
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(Command("report"))
@router.callback_query(F.data == "report")
async def report_handler(event) -> None:
    message = event.message if isinstance(event, CallbackQuery) else event
    async with SessionLocal() as session:
        user = await get_or_create_user(session, event.from_user, get_settings().admin_ids)
        website = await session.scalar(select(Website).where(Website.user_id == user.id).order_by(Website.id.desc()))
        if not website:
            await message.answer("Сначала добавьте сайт.", reply_markup=main_menu())
            return
        sources = await aggregate_sources(session, website.id)
        summary = explain_sources(sources)
        pdf_path = f"storage/reports/report_{website.id}.pdf"
        generate_pdf_report(pdf_path, f"TrafficMind AI: {website.domain}", summary, [summary])
        report = Report(website_id=website.id, period="daily", status="created", pdf_path=pdf_path, ai_summary=summary)
        session.add(report)
        await session.commit()
    await message.answer(f"Отчет готов.\n\n{summary}\n\nPDF: {Path(pdf_path).resolve()}", reply_markup=main_menu())
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(Command("link_report"))
@router.callback_query(F.data == "link_only_report")
async def link_only_report_handler(event) -> None:
    message = event.message if isinstance(event, CallbackQuery) else event
    async with SessionLocal() as session:
        user = await get_or_create_user(session, event.from_user, get_settings().admin_ids)
        website = await session.scalar(select(Website).where(Website.user_id == user.id).order_by(Website.id.desc()))
    report = link_only_report_payload(website.domain if website else "example.com")
    top_findings = "\n\n".join(
        f"- {item['title']}\n"
        f"Почему важно: {item['why']}\n"
        f"Что сделать: {item['recommendation']}"
        for item in report["findings"][:3]
    )
    actions = "\n".join(
        f"{item['priority']}. {item['title']} - {item['effect']} ({item['time']})"
        for item in report["today_actions"]
    )
    visible = "\n".join(f"- {item['label']}: {item['value']}" for item in report["observability"]["visible"][:3])
    not_visible = "\n".join(f"- {item['label']} (нужно: {item['needed']})" for item in report["observability"]["not_visible"][:3])
    leaks = "\n".join(
        f"- {item['title']}: {item['estimated_loss']}. {item['fix']}"
        for item in report["money_leaks"][:3]
    )
    missing = ", ".join(report["missing_data"][:4])
    await message.answer(
        f"Полный отчет по ссылке: {report['domain']}\n\n"
        f"{report['executive_summary']['headline']}\n\n"
        f"Уверенность: {report['confidence']['score']}/100 - {report['confidence']['label']}\n"
        f"Оценочные потери: {report['executive_summary']['estimated_revenue_leak']}\n"
        f"Первое действие: {report['executive_summary']['next_best_action']}\n\n"
        "Что найдено:\n"
        f"{top_findings}\n\n"
        "Что делать сегодня:\n"
        f"{actions}\n\n"
        "Что я вижу:\n"
        f"{visible}\n\n"
        "Что я не вижу без подключений:\n"
        f"{not_visible}\n\n"
        "Потери денег:\n"
        f"{leaks}\n\n"
        "Важно: без подключений я не вижу реальные продажи и рекламные расходы. "
        f"Для точной карты прибыли нужны: {missing}.",
        reply_markup=main_menu(),
    )
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(Command("subscription"))
@router.callback_query(F.data == "subscription")
async def subscription_handler(event) -> None:
    message = event.message if isinstance(event, CallbackQuery) else event
    text = "\n".join(f"{plan.title}: {plan.price} ₽/мес, сайтов: {plan.max_websites}" for plan in PLANS.values())
    await message.answer(text, reply_markup=subscription_keyboard())
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.callback_query(F.data == "check_all")
async def check_all_handler(query: CallbackQuery) -> None:
    await audit_handler(query)
    await traffic_map_handler(query)


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "/add_site, /audit, /connect, /traffic_map, /report, /link_report, /recommendations, /subscription",
        reply_markup=main_menu(),
    )
