
from flask_migrate import Migrate

from flaskr import create_app
from flaskr.constants import PORT
from flaskr.models.models import db

app = create_app()
db.init_app(app)

migrate = Migrate(app, db)


if __name__ == "__main__":
    app.run(debug=True, port=PORT)
