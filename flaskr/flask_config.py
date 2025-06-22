from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

TESTING = True
SECRET_KEY = "fghj23342wf0u0:Da0s"
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
