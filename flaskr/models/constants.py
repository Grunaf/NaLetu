MEAL = 0
POI = 1

SEGMENT_TYPE = {MEAL: "meal", POI: "poi"}
REVERSED_SEGMENT_TYPE = {v.lower(): k for k, v in SEGMENT_TYPE.items()}

CANTEEN = 0
CAFE = 1
RESTAURANT = 2

MEAL_PLACE_TYPE = {
    CANTEEN: "столовая",
    CAFE: "кафе",
    RESTAURANT: "ресторан"
    }

ASIAN = 0
RUSSIAN = 1
ITALIAN = 2
MEXICAN = 3
FRENCH = 4
INDIAN = 5
CHINESE = 6
JAPANESE = 7
AMERICAN = 8
MIDDLE_EASTERN = 9
EUROPEAN = 10
TATARIAN = 11

CUISINE = {
    ASIAN: "азиатская",
    RUSSIAN: "русская",
    ITALIAN: "итальянская",
    MEXICAN: "мексиканская",
    FRENCH: "французская",
    INDIAN: "индийская",
    CHINESE: "китайская",
    JAPANESE: "японская",
    AMERICAN: "американская",
    MIDDLE_EASTERN: "средне-восточная",
    EUROPEAN: "европейская",
    TATARIAN: "татарская",
}

ADMIN = 0
MODERATOR = 1
ROLE = {ADMIN: "admin", MODERATOR: "moderator"}

NEW = 0
APPROVED = 1
REJECTED = 2
STATUC_REQUEST = {NEW: "new", APPROVED: "approved", REJECTED: "rejected"}
