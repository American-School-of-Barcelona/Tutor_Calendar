import app.app as app_module


def test_signup_creates_pending_student(client, app):
    response = client.post(
        "/signup",
        data={
            "name": "Big",
            "lastname": "Lez",
            "username": "biglez",
            "email": "big.lez@example.com",
            "password": "S12345",
            "repeat_password": "S12345",
            "admin_code": "",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)

    with app.app_context():
        user = app_module.User.query.filter_by(email="big.lez@example.com").first()
        assert user is not None
        assert user.status == "pending"
        assert user.role == "student"


def test_login_approved_student_email_success(client, create_user, login):
    create_user(
        email="student1@tutomatics.com",
        username="student1",
        password="S12345",
        role="student",
        status="approved",
    )
    response = login("student1@tutomatics.com", "S12345")
    assert response.status_code in (302, 303)
    assert "/student/dashboard" in response.headers["Location"]


def test_login_approved_student_username_success(client, create_user, login):
    create_user(
        email="student2@tutomatics.com",
        username="student2",
        password="S12345",
        role="student",
        status="approved",
    )
    response = login("student2", "S12345")
    assert response.status_code in (302, 303)
    assert "/student/dashboard" in response.headers["Location"]


def test_login_invalid_password_rejected(client, create_user, login):
    create_user(
        email="student3@tutomatics.com",
        username="student3",
        password="S12345",
        role="student",
        status="approved",
    )
    response = login("student3@tutomatics.com", "wrongpass")
    assert response.status_code == 403
    assert b"Invalid email/username or password" in response.data


def test_login_pending_student_blocked(client, create_user, login):
    create_user(
        email="pending@tutomatics.com",
        username="pendinguser",
        password="S12345",
        role="student",
        status="pending",
    )
    response = login("pending@tutomatics.com", "S12345")
    assert response.status_code == 200
    assert b"pending approval" in response.data


def test_login_denied_student_blocked(client, create_user, login):
    create_user(
        email="denied@tutomatics.com",
        username="denieduser",
        password="S12345",
        role="student",
        status="denied",
    )
    response = login("denied@tutomatics.com", "S12345")
    assert response.status_code == 200
    assert b"signup request was denied" in response.data


def test_login_admin_redirects_to_admin_dashboard(client, create_user, login):
    create_user(
        email="admin@tutomatics.com",
        username="admin",
        password="A12345",
        role="admin",
        status="approved",
    )
    response = login("admin@tutomatics.com", "A12345")
    assert response.status_code in (302, 303)
    assert "/admin/dashboard" in response.headers["Location"]