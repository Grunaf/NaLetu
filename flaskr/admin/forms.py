from wtforms import fields
from wtforms import form
from wtforms import validators

from sqlalchemy import select
from models.models import db
from models.trip import Staff


from werkzeug.security import check_password_hash


class LoginForm(form.Form):
    login = fields.StringField(validators=[validators.InputRequired()])
    password = fields.PasswordField(validators=[validators.InputRequired()])

    def validate_login(self, fields):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError("Invaliduser")

        if not check_password_hash(user.password, self.password.data):
            raise validators.ValidationError("Invalid password")

    def get_user(self):
        stmt = select(Staff).where(Staff.login == self.login.data)
        return db.session.execute(stmt).scalars().first()


class RegistrationForm(form.Form):
    first_name = fields.StringField(validators=[validators.InputRequired()])
    last_name = fields.StringField(validators=[validators.InputRequired()])

    login = fields.StringField(validators=[validators.InputRequired()])
    email = fields.StringField(validators=[validators.InputRequired()])
    password = fields.PasswordField(validators=[validators.InputRequired()])
