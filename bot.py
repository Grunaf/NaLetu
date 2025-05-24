from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import asyncio
import os
import uuid
from dotenv import load_dotenv

# 🧭 Импорт логики маршрута
from planner.user_context import user_sessions, save_user_sessions
from planner.loader import load_geojson
from planner.route_builder import build_routes_for_all_days
from planner.user_context import update_filters

load_dotenv()

router = Router()

# === States ===
class PlanningStates(StatesGroup):
    waiting_for_city = State()
    waiting_for_dates = State()
    waiting_for_accommodation = State()
    choosing_travel_mode = State()     
    waiting_for_constraints = State()
    waiting_for_event_link = State()
    confirmation = State()

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# === Handlers ===
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    # kb = types.ReplyKeyboardMarkup(
    # keyboard=[
    #     [types.KeyboardButton(text="Санкт-Петербург")],
    #     [types.KeyboardButton(text="Москва")],
    #     [types.KeyboardButton(text="Другой город")]
    # ],
    # resize_keyboard=True
    # )
    # await message.answer("Привет! Давай спланируем твоё путешествие. В какой город ты едешь?", reply_markup=kb)
    # await state.set_state(PlanningStates.waiting_for_city)
    await state.update_data({
        "city": "Санкт-Петербург",
        "dates": "20–26 июня",
        "accommodation": "Балтийский вокзал",
        "constraints": "без музеев",
        "travel_mode": "solo"
    })

    await message.answer("Тест: данные подставлены по умолчанию.")
    await message.answer(
        "Вот что я понял:\n"
        "Город: Санкт-Петербург\n"
        "Даты: 20–26 июня\n"
        "Район: Балтийский вокзал\n"
        "Ограничения: без музеев\n\n"
        "Всё верно? (да/нет)"
    )
    await state.set_state(PlanningStates.confirmation)

@router.message(PlanningStates.waiting_for_city)
async def city_chosen(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Отлично! А какие даты поездки? (например, 5–8 мая)", reply_markup=ReplyKeyboardRemove())
    await state.set_state(PlanningStates.waiting_for_dates)

@router.message(PlanningStates.waiting_for_dates)
async def dates_chosen(message: Message, state: FSMContext):
    await state.update_data(dates=message.text)
    
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Центр")],
            [types.KeyboardButton(text="Петроградка")],
            [types.KeyboardButton(text="Васильевский остров")],
            [types.KeyboardButton(text="Другой район")]
        ],
        resize_keyboard=True
    )
    await message.answer("Где ты будешь жить? Можно просто район или метро — чтобы не предлагать завтрак в другой конец города 😄", reply_markup=kb)
    await state.set_state(PlanningStates.waiting_for_accommodation)


@router.message(PlanningStates.waiting_for_accommodation)
async def accommodation_chosen(message: Message, state: FSMContext):
    await state.update_data(accommodation=message.text)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Один")],
            [KeyboardButton(text="С кем-то")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "Ты путешествуешь один или с кем-то?",
        reply_markup=kb
    )
    await state.set_state(PlanningStates.choosing_travel_mode)

@router.message(PlanningStates.choosing_travel_mode)
async def travel_mode_chosen(message: Message, state: FSMContext):
    choice = message.text.lower()
    if "один" in choice:
        await state.update_data(travel_mode="solo")
        await message.answer("Окей, планируем только для тебя.")
    else:
        trip_id = str(uuid.uuid4())[:8]
        await state.update_data(trip_id=trip_id, travel_mode="group")
        link = f"https://t.me/MeetThere?start=join_{trip_id}"
        await message.answer(f"Создана группа поездки!\nОтправь другу эту ссылку:\n{link}")

    await message.answer("Есть ли у тебя ограничения или пожелания по маршруту? (например, 'без музеев', 'не больше 3 часов в день')", reply_markup=ReplyKeyboardRemove())
    await state.set_state(PlanningStates.waiting_for_constraints)


@router.message(PlanningStates.waiting_for_constraints)
async def constraints_chosen(message: Message, state: FSMContext):
    await state.update_data(constraints=message.text)

    # Предлагаем вставить ссылку на мероприятие или пропустить
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Пропустить")]],
        resize_keyboard=True
    )

    await message.answer(
        "Если у тебя есть ссылка на мероприятие (например, с Яндекс.Афиши), просто вставь её — я добавлю в маршрут.\n"
        "Если пока ничего нет — нажми 'Пропустить'.",
        reply_markup=kb
    )
    await state.set_state(PlanningStates.waiting_for_event_link)

@router.message(PlanningStates.waiting_for_event_link, F.text.lower() == "пропустить")
async def skip_event_link(message: Message, state: FSMContext):
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
    await state.set_state(PlanningStates.confirmation)

@router.message(PlanningStates.confirmation)
async def build_and_send(message: Message):

    routes = build_routes_for_all_days(
        user_location=[59.908814, 30.310512],
        user_id=str(message.from_user.id) 
    )

    print(routes)
    
    for route in routes:
        if route["points"]:
            day_text = f"🗓 <b>День {route['day']}</b>\n"
            poi_list = "\n".join([f"• {p['name']}" for p in route["points"]])
            await message.answer(
                f"{day_text}{poi_list}\n\n🔗 <a href='{route['yandex_url']}'>Открыть на карте</a>",
                parse_mode="HTML"
            )
        else:
            await message.answer(f"День {route['day']}: нет маршрута\n{route.get('note', '')}")

    # Кнопки управления маршрутом
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Новый маршрут", callback_data="reroll")],
        # [InlineKeyboardButton(text="🚫 Исключить POI", callback_data="excl_poi")],
        # [InlineKeyboardButton(text="🚫 Исключить тег", callback_data="excl_tag")],
        # [InlineKeyboardButton(text="❌ Исключить музей", callback_data="exclude_museum")],
        # [InlineKeyboardButton(text="📍 Изменить район", callback_data="change_location")],
        # [InlineKeyboardButton(text="🧹 Очистить фильтры", callback_data="clear_filters")]
    ])
    await message.answer("🔧 Хочешь изменить маршрут?", reply_markup=kb)

@router.message(PlanningStates.confirmation)
async def confirm_data(message: Message, state: FSMContext):
    if message.text.lower() == "да":
        await build_and_send(message)
    else:
        await message.answer("Окей, давай начнём сначала. В какой город ты едешь?", reply_markup=ReplyKeyboardRemove())
        await state.set_state(PlanningStates.waiting_for_city)

# @dp.callback_query_handler(text="excl_tag")
# async def ask_which_tag_to_exclude(q: CallbackQuery):
#     session = user_sessions[str(q.from_user.id)]
#     # Собираем все теги из последних рассчитанных POI:
#     routes = session.get("cached_routes", [])
#     tags = set()
#     for day in routes:
#         for p in day.get("points", []):
#             for k,v in p.get("properties", {}).get("tags", {}).items():
#                 tags.add(k)
#                 tags.add(v)
#     # Строим кнопки:
#     kb = InlineKeyboardMarkup(row_width=3)
#     for t in sorted(tags):
#         kb.insert(InlineKeyboardButton(t, callback_data=f"tag__{t}"))
#     await q.message.answer("Выберите тег для исключения:", reply_markup=kb)

# @dp.callback_query_handler(lambda c: c.data.startswith("tag__"))
# async def exclude_tag_cb(q: CallbackQuery):
#     tag = q.data.split("__",1)[1]
#     user_id = q.from_user.id
#     session = user_sessions.setdefault(str(user_id), {})
#     filters = session.setdefault("filters", {})
#     excl = filters.get("exclude_tags", [])
#     if tag not in excl:
#         excl.append(tag)
#         update_filters(user_id, exclude_tags=excl)
#     await q.answer(f"Тег «{tag}» добавлен в исключения")
#     # и сразу пересчитаем маршрут:
#     await recalc_and_send(q.message, user_id)


@router.callback_query(lambda c: c.data == "reroll")
async def reroll_route(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    session = user_sessions.setdefault(user_id, {})
    session["last_request_hash"] = None   # 💥 Сбрасываем хэш, чтобы пересчитать маршрут
    user_sessions[user_id] = session
    save_user_sessions()
    await callback.message.answer("🔁 Генерирую другой маршрут...")
    await build_and_send(callback.message)

@router.callback_query(lambda c: c.data == "exclude_museum")
async def exclude_category(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    session = user_sessions.setdefault(user_id, {})
    session.setdefault("exclude_categories", [])
    if "музей" not in session["exclude_categories"]:
        session["exclude_categories"].append("музей")

    session["last_request_hash"] = None
    user_sessions[user_id] = session
    save_user_sessions()

    await callback.message.answer("❌ Убираю музеи из маршрута...")
    await confirm_data(callback.message, state)

@router.callback_query(lambda c: c.data == "change_location")
async def change_location(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📍 Введи новый район или метро:")
    await state.set_state(PlanningStates.waiting_for_accommodation)
    
@router.callback_query(lambda c: c.data == "clear_filters")
async def clear_filters(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    session = user_sessions.setdefault(user_id, {})
    session["exclude_categories"] = []
    session["exclude_names"] = []
    session["last_request_hash"] = None
    user_sessions[user_id] = session
    save_user_sessions()

    await callback.message.answer("🧹 Фильтры очищены. Перестраиваю маршрут...")
    await confirm_data(callback.message, state)

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
