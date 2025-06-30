import datetime

FIELDS_FOR_MEAL_PLACE = (
    "items.schedule,items.external_content,"
    "items.reviews,items.description,"
    "items.attribute_groups"
)
START_BREAKFAST_TIME = datetime.time(7)
START_LUNCH_TIME = datetime.time(12)
START_DINNER_TIME = datetime.time(16)
PORT = 3000

ENDPOINTS = {
    "swwager": "/api/docs",
}
