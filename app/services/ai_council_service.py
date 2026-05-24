from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import httpx

from app.config import get_settings


@dataclass(frozen=True)
class CouncilAgent:
    name: str
    role: str
    provider: str
    fallback: bool = False


@dataclass(frozen=True)
class CouncilMessage:
    agent: str
    role: str
    message: str
    fallback: bool = False


@dataclass(frozen=True)
class CouncilAction:
    step: int
    title: str
    why: str
    how: str
    expected_effect: str
    priority: str


@dataclass(frozen=True)
class CouncilResult:
    summary: str
    main_problem: str
    evidence: list[str]
    debate: list[CouncilMessage]
    action_plan: list[CouncilAction]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "main_problem": self.main_problem,
            "evidence": self.evidence,
            "debate": [asdict(item) for item in self.debate],
            "action_plan": [asdict(item) for item in self.action_plan],
            "confidence": self.confidence,
        }


class AIGrowthCouncil:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.timeout = httpx.Timeout(30.0)
        self.agents = [
            CouncilAgent("GPT Strategist", "ищет стратегию роста и точки масштабирования", "openai"),
            CouncilAgent("DeepSeek Analyst", "проверяет цифры, ROI, CPL и конверсии", "deepseek"),
            CouncilAgent("Grok Challenger", "критикует выводы, ищет риски и слабые места", "grok"),
        ]

    async def run_council(self, context: dict) -> CouncilResult:
        if self._must_use_demo_mode():
            return self._demo_result(context, fallback_agents=[agent.name for agent in self.agents])

        debate: list[CouncilMessage] = []
        for agent in self.agents:
            try:
                message = await self._call_agent(agent, context, debate)
                debate.append(CouncilMessage(agent=agent.name, role=agent.role, message=message, fallback=False))
            except Exception:
                debate.append(self._fallback_message(agent, context))

        return self._synthesize(context, debate)

    def _must_use_demo_mode(self) -> bool:
        if self.settings.ai_council_mode.lower() == "demo":
            return True
        return not any([self.settings.openai_api_key, self.settings.deepseek_api_key, self.settings.grok_api_key])

    async def _call_agent(self, agent: CouncilAgent, context: dict, debate: list[CouncilMessage]) -> str:
        if agent.provider == "openai":
            return await self._call_openai(context, debate)
        if agent.provider == "deepseek":
            return await self._call_deepseek(context, debate)
        if agent.provider == "grok":
            return await self._call_grok(context, debate)
        raise ValueError(f"Unknown AI provider: {agent.provider}")

    async def _call_openai(self, context: dict, debate: list[CouncilMessage]) -> str:
        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is empty")
        return await self._post_chat_completion(
            url="https://api.openai.com/v1/chat/completions",
            api_key=self.settings.openai_api_key,
            model="gpt-4o-mini",
            system="You are GPT Strategist. Find growth strategy and scaling opportunities.",
            context=context,
            debate=debate,
        )

    async def _call_deepseek(self, context: dict, debate: list[CouncilMessage]) -> str:
        if not self.settings.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is empty")
        return await self._post_chat_completion(
            url="https://api.deepseek.com/chat/completions",
            api_key=self.settings.deepseek_api_key,
            model="deepseek-chat",
            system="You are DeepSeek Analyst. Validate numbers, ROI, CPL, ROAS, conversion rates and weak metrics.",
            context=context,
            debate=debate,
        )

    async def _call_grok(self, context: dict, debate: list[CouncilMessage]) -> str:
        if not self.settings.grok_api_key:
            raise ValueError("GROK_API_KEY is empty")
        return await self._post_chat_completion(
            url="https://api.x.ai/v1/chat/completions",
            api_key=self.settings.grok_api_key,
            model="grok-2-latest",
            system="You are Grok Challenger. Challenge assumptions, find risks, and expose weak recommendations.",
            context=context,
            debate=debate,
        )

    async def _post_chat_completion(
        self,
        *,
        url: str,
        api_key: str,
        model: str,
        system: str,
        context: dict,
        debate: list[CouncilMessage],
    ) -> str:
        previous_debate = [asdict(item) for item in debate]
        payload = {
            "model": model,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": (
                        "Analyze this business analytics context. Answer in Russian, concise and practical. "
                        "Mention only evidence-backed conclusions.\n\n"
                        f"Context: {context}\n\nPrevious debate: {previous_debate}"
                    ),
                },
            ],
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers={"Authorization": f"Bearer {api_key}"})
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    def _fallback_message(self, agent: CouncilAgent, context: dict) -> CouncilMessage:
        messages = {
            "openai": self._strategist_demo(context),
            "deepseek": self._analyst_demo(context),
            "grok": self._challenger_demo(context),
        }
        return CouncilMessage(
            agent=agent.name,
            role=f"{agent.role} (fallback)",
            message=messages.get(agent.provider, "Модель недоступна, использован резервный анализ."),
            fallback=True,
        )

    def _demo_result(self, context: dict, fallback_agents: list[str] | None = None) -> CouncilResult:
        debate = [
            CouncilMessage("GPT Strategist", "ищет стратегию роста (demo/fallback)", self._strategist_demo(context), True),
            CouncilMessage("DeepSeek Analyst", "проверяет цифры (demo/fallback)", self._analyst_demo(context), True),
            CouncilMessage("Grok Challenger", "ищет риски (demo/fallback)", self._challenger_demo(context), True),
        ]
        return self._synthesize(context, debate)

    def _synthesize(self, context: dict, debate: list[CouncilMessage]) -> CouncilResult:
        metrics = context.get("metrics", [])
        profit_map = context.get("profit_map", {})
        nodes = profit_map.get("nodes", [])
        losing = [item for item in nodes if item.get("roi", 0) < 0]
        best = max(nodes, key=lambda item: item.get("roi", 0), default={})
        total_revenue = profit_map.get("total_revenue", sum(item.get("revenue", 0) for item in metrics))
        main_problem = (
            f"{losing[0]['source']} тратит бюджет с отрицательным ROI."
            if losing
            else "Главный риск не в трафике, а в недостаточной связке рекламы, заявок и продаж."
        )
        evidence = [
            f"Общий доход в демо-срезе: {total_revenue:,.0f} ₽.",
            f"Лучший канал для масштабирования: {best.get('source', 'не определен')} с ROI {best.get('roi', 0)}.",
        ]
        if losing:
            evidence.append(f"Канал с потерями: {losing[0]['source']}, ROI {losing[0].get('roi')}, ROAS {losing[0].get('roas')}.")

        return CouncilResult(
            summary="AI Growth Council нашел, где бизнес теряет деньги, какой канал можно масштабировать и какие действия дадут самый быстрый эффект.",
            main_problem=main_problem,
            evidence=evidence,
            debate=debate,
            action_plan=[
                CouncilAction(
                    step=1,
                    title="Остановить или ограничить убыточный канал",
                    why="Если канал уходит в отрицательный ROI, он съедает бюджет быстрее, чем бизнес получает продажи.",
                    how="Поставить дневной лимит, проверить аудитории, посадочную страницу, оффер и события конверсий.",
                    expected_effect="Снижение лишних расходов и рост общей окупаемости уже в ближайшие дни.",
                    priority="high",
                ),
                CouncilAction(
                    step=2,
                    title="Усилить канал с лучшим ROI",
                    why="Рост быстрее всего появляется там, где уже есть доказанная экономика.",
                    how=f"Постепенно увеличить бюджет на {best.get('source', 'лучший канал')} на 15-20% и отслеживать CPL/ROAS каждый день.",
                    expected_effect="Больше заявок без резкой смены стратегии.",
                    priority="high",
                ),
                CouncilAction(
                    step=3,
                    title="Связать заявки с CRM и рекламными расходами",
                    why="Без CRM и целей система видит активность, но не видит точную прибыль по каждому источнику.",
                    how="Подключить GA4/Метрику, рекламные кабинеты, CRM и UTM, затем включить отчет по качеству лидов.",
                    expected_effect="Появятся точные CPL, CPA, ROAS, источники денег и точки потерь.",
                    priority="medium",
                ),
            ],
            confidence=0.82 if any(item.fallback for item in debate) else 0.9,
        )

    def _strategist_demo(self, context: dict) -> str:
        best = max(context.get("profit_map", {}).get("nodes", []), key=lambda item: item.get("roi", 0), default={})
        return (
            f"Я бы начал с масштабирования канала {best.get('source', 'с лучшим ROI')}: там уже видна экономика. "
            "Параллельно нужно убрать расходы из каналов, которые не возвращают деньги."
        )

    def _analyst_demo(self, context: dict) -> str:
        nodes = context.get("profit_map", {}).get("nodes", [])
        losing = [item for item in nodes if item.get("roi", 0) < 0]
        if losing:
            item = losing[0]
            return f"По цифрам главный красный флаг: {item['source']} имеет ROI {item.get('roi')} и ROAS {item.get('roas')}. Этот канал нужно проверить первым."
        return "По цифрам критичных отрицательных ROI не видно, но без CRM нельзя подтвердить качество лидов и реальную прибыль."

    def _challenger_demo(self, context: dict) -> str:
        return (
            "Я бы не масштабировал бюджет резко: сначала нужно проверить трекинг, цели и CRM. "
            "Иначе можно увеличить не прибыль, а количество слабых заявок."
        )
