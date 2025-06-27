import flask_admin as admin
import flask_login as login

from flask import abort, redirect, request, url_for
from flask_admin import BaseView, expose, helpers
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash

from flaskr.admin.forms import LoginForm, RegistrationForm
from models.models import db
from models.trip import ADMIN, MODERATOR, AdditionRequest, Staff


def is_authenticated_and_have_permission(role: int):
    return login.current_user.is_authenticated and login.current_user.role == role


class AdminModelView(ModelView):
    def is_accessible(self):
        return is_authenticated_and_have_permission(ADMIN)


class ModeratorView(BaseView):
    def is_accessible(self):
        return is_authenticated_and_have_permission(MODERATOR)


class TravelerView(AdminModelView):
    form_columns = ["uuid", "name"]


class AssembleRouteView(ModeratorView):
    @expose("/", methods=["GET"])
    def index(self):
        # Города загружаются для каждой страницы
        return self.render("admin/assemble_route.html")


class AuthIndexView(admin.AdminIndexView):
    @expose("/login/", methods=("GET", "POST"))
    def login_view(self, link=None):
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            staff = form.get_user()
            login.login_user(staff)

        if login.current_user.is_authenticated:
            return redirect(url_for(".index"))
        if link is None:
            link = (
                'Вы гид? <a href="'
                + url_for("moderator.login_view")
                + '">Click here</a>'
            )
        self._template_args["form"] = form
        self._template_args["link"] = link
        return super().index()

    @expose("logout")
    def logout_view(self):
        login.logout_user()
        return redirect(url_for(".index"))


class MyModeratorIndexView(AuthIndexView):
    @expose("/")
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for(".login_view"))
        return super().index()

    @expose("/login/", methods=("GET", "POST"))
    def login_view(self):
        link = 'Вы админ? <a href="' + url_for("admin.login_view") + '">Click here</a>'
        return super().login_view(link)

    @expose("/register/", methods=["GET", "POST"])
    def register_view(self):
        form = RegistrationForm(request.form)

        if helpers.validate_form_on_submit(form):
            staff = Staff()

            form.populate_obj(staff)
            staff.password = generate_password_hash(form.password.data)

            addition_request = AdditionRequest(staff=staff)
            db.session.add(staff)
            db.session.add(addition_request)
            db.session.commit()

            print("Пользователь отправил заявку на регистрацию")
            import traceback

            try:
                return redirect(url_for(".index"))
            except Exception as e:
                traceback.print_exc()
                raise

        link = (
            'Уже есть акканут? <a href="' + url_for(".login_view") + '">Click here</a>'
        )

        self._template_args["form"] = form
        self._template_args["link"] = link

        return super().index()


class MyAdminIndexView(AuthIndexView):
    @expose("/")
    def index(self):
        if login.current_user.role == MODERATOR and request.path.startswith("/admin"):
            abort(403)

        if not login.current_user.is_authenticated:
            return redirect(url_for("admin.login_view"))

        return super().index()
