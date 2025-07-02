import datetime
from flask import Flask
from flask_babel import format_datetime


def setup_filters(app: Flask):
    @app.template_filter("datetimeformatnative")
    def format_datetime_native_tz(datetime: datetime.datetime, format: str) -> str:
        return format_datetime(datetime, format=format, rebase=False)
