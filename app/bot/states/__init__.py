from aiogram.fsm.state import State, StatesGroup


class AddSiteState(StatesGroup):
    waiting_for_domain = State()


class AskAIState(StatesGroup):
    waiting_for_question = State()
