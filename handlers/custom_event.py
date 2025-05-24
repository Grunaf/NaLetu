from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot import PlanningStates

router = Router()

@router.message(PlanningStates.waiting_for_event_link, F.text.startswith("http"))
async def handle_event_link(message: Message, state: FSMContext):
    url = message.text.strip()

    # Фейковый "парсинг"
    event = {
        "title": "Мероприятие по ссылке",
        "datetime": "2025-04-12 19:00",
        "location": "Уточняется",
        "url": url
    }
    user_data = await state.get_data()
    summary = (
        f"Вот что я понял:\n"
        f"Город: {user_data.get('city', '-')}\n"
        f"Даты: {user_data.get('dates', '-')}\n"
        f"Район: {user_data.get('accommodation', '-')}\n"
        f"Ограничения: {user_data.get('constraints', '-')}\n"
        "\nВсё верно? (да/нет)"
    )
    await message.answer(summary)
    await state.update_data(custom_events=[event])
    await message.answer(
        f"✅ Добавлено в маршрут:\n\n"
        f"🎫 {event['title']}\n"
        f"📅 {event['datetime']}\n"
        f"📍 {event['location']}\n\n"
        f"{summary}",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(PlanningStates.confirmation)
