import os
from datetime import datetime
from pathlib import Path
import tempfile

import pytest
from werkzeug.security import generate_password_hash

import app.app as app_module


@pytest.fixture()
def app():
    temp_dir = tempfile.TemporaryDirectory()
    db_path = Path(temp_dir.name) / "test.db"

    app = app_module.app
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAIL_SUPPRESS_SEND=True,
    )

    # Prevent real email sends by replacing route-level imported mail functions.
    app_module.send_booking_submitted_email = lambda *a, **k: True
    app_module.send_booking_approved_email = lambda *a, **k: True
    app_module.send_booking_denied_email = lambda *a, **k: True
    app_module.send_new_booking_notification_email = lambda *a, **k: True
    app_module.send_signup_approved_email = lambda *a, **k: True
    app_module.send_signup_denied_email = lambda *a, **k: True
    app_module.send_new_signup_request_notification_email = lambda *a, **k: True
    app_module.send_new_admin_signup_request_notification_email = lambda *a, **k: True

    with app.app_context():
        app_module.db.drop_all()
        app_module.db.create_all()

    yield app

    with app.app_context():
        app_module.db.session.remove()
        app_module.db.drop_all()

    temp_dir.cleanup()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app):
    with app.app_context():
        yield app_module.db.session


@pytest.fixture()
def create_user(app):
    def _create_user(
        email,
        username,
        password,
        role="student",
        status="approved",
        first_name="Test",
        last_name="User",
    ):
        with app.app_context():
            user = app_module.User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password_hash=generate_password_hash(password),
                role=role,
                status=status,
            )
            app_module.db.session.add(user)
            app_module.db.session.commit()
            return user
    return _create_user


@pytest.fixture()
def login(client):
    def _login(identifier, password):
        # login form uses field name "email" even for username login flow
        return client.post(
            "/login",
            data={"email": identifier, "password": password},
            follow_redirects=False,
        )
    return _login