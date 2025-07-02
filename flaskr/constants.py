import datetime

FIELDS_FOR_MEAL_PLACE = (
    "items.schedule,items.external_content,"
    "items.reviews,items.description,"
    "items.attribute_groups"
)
START_BREAKFAST_TIME = datetime.time(7)
START_LUNCH_TIME = datetime.time(12)
START_DINNER_TIME = datetime.time(16)

MAX_PARTICIPANT_COUNT = 5

SESSION_NOT_FOUND = "Сессия указанная в ссылке не найдена"
INVALID_INVITE = "Срок приглашения истек или им уже воспользовались"
TRANSPORTS_NOT_FOUND = "Проблема с получением рейсов"
INVITE_NOT_FOUND = "Приглашение не найдено"
PARTIAL_VOTES = "Выбранных вариантов меньше, чем дней в поездке"
SESSION_UUID_REQUIRED = "Session uuid обязателен"

PORT = 3000
ENDPOINTS = {
    "swwager": "/api/docs",
}
