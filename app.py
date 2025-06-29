
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flaskr import create_app
from flaskr.constants import PORT
from flaskr.models.models import db

app = create_app()
db.init_app(app)

migrate = Migrate(app, db)
limiter = Limiter(get_remote_address, app=app)

if __name__ == "__main__":
    app.run(debug=True, port=PORT)
