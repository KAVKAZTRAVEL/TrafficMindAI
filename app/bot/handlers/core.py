from pathlib import Path
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from app.bot.keyboards import main_menu, subscription_keyboard
from app.bot.states import AddSiteState, AskAIState
from app.config import get_settings
from app.database import SessionLocal
from app.models import Report, TrafficSource, Website
from app.services.ai_service import explain_sources, recommendations_from_audit
from app.services.audit_service import audit_domain
from app.services.infographic_service import render_traffic_map_html
from app.services.pdf_service import generate_pdf_report
from app.services.subscription_service import PLANS, get_or_create_user, trial_status_text
from app.services.traffic_service import aggregate_sources
from app.services.website_service import add_website

router = Router()


async def current_user(message_or_query):
    tg_user = message_or_query.from_user
    settings = get_settings()
    async with SessionLocal() as session:
        return await get_or_create_user(session, tg_user, settings.admin_ids)


@router.message(Command("start"))
async def start(message: Message) -> None:
    user = await current_user(message)
    await message.answer(
        "TrafficMind AI уже готов следить за трафиком простым языком.\n"
        f"{trial_status_text(user)}\n\nВыберите действие:",
        reply_markup=main_menu(),
    )


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
        "AI Tracking Script для установки на сайт:\n"
        f"<code>{script}</code>\n\n"
        "Теперь можно запустить бесплатный аудит.",
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
        "Что сделать дальше:\n" + "\n".join(f"• {item}" for item in recs),
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
        "Можно подключить GA4 OAuth позже или сразу поставить AI Tracking Script.\n\n"
        f"<code>{script}</code>",
        parse_mode="HTML",
        reply_markup=main_menu(),
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
        "Traffic Map построена по реальным источникам.\n"
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
    await message.answer(
        f"Отчет готов.\n\n{summary}\n\nPDF: {Path(pdf_path).resolve()}",
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
    await message.answer("/add_site, /audit, /connect, /traffic_map, /report, /recommendations, /subscription", reply_markup=main_menu())
