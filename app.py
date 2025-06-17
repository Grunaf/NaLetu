from flask_migrate import Migrate, upgrade, downgrade
from sqlalchemy import text
from models.models import db, PriceEntry
from flaskr import create_app
import json
import os

from routes.hotels import hotels_bp

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# app = Flask(__name__, static_folder='static')
# app.jinja_env.filters['loads'] = json.loads
# app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app = create_app()
db.init_app(app)
# app.register_blueprint(hotels_bp)

migrate = Migrate(app, db)
PORT = 3000

# ====================
# UTILS
# ====================

def get_price(object_type, object_id):
    p = PriceEntry.query.filter_by(object_type=object_type, object_id=object_id).first()
    return p.last_known_price if p else None
    
def extract_entry_point_summary(entry_json_str):
    if not entry_json_str:
        return "–"
    try:
        data = json.loads(entry_json_str)
        from_point = data.get("from_point", {}).get("name")
        zones = data.get("recommendations", [])
        if from_point:
            return f"от {from_point} / {len(zones)} зон"
        return f"{len(zones)} зон входа"
    except Exception:
        return "–"


def seed_db(file_seed="initial_data.sql"):
    with app.app_context():
        db.create_all()
        with open(file_seed, encoding="UTF-8") as file:
            db.session.execute(text(file.read()))
        db.session.commit()

@app.cli.command("reset-db")
def reset_db():
    print("Dropping all tables")
    downgrade(revision="base")
    print("Upgrading")
    upgrade()
    print("Seeding")
    seed_db()
        
if __name__ == '__main__':
    app.run(debug=True, port=PORT)
