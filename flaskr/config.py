import os
TESTING = True
SQLALCHEMY_DATABASE_URI = \
    f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASS")}@{os.getenv("DB_HOST", "localhost")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}'