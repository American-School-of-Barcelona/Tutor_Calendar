from datetime import datetime, timedelta

import app.app as app_module


def _login_student(client, email, password):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


def _login_admin(client, email, password):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


def test_book_slot_under_3_hours_rejected(client, create_user):
    create_user("admin@tutomatics.com", "admin", "A12345", role="admin", status="approved")
    create_user("student@tutomatics.com", "student", "S12345", role="student", status="approved")

    _login_student(client, "student@tutomatics.com", "S12345")
    start = (datetime.utcnow() + timedelta(hours=2)).replace(second=0, microsecond=0)

    response = client.post("/api/book-slot", json={
        "start_time": start.isoformat(),
        "lesson_minutes": 120
    })
    data = response.get_json()

    assert response.status_code == 400
    assert "at least 3 hours" in data["error"]


def test_book_slot_at_or_over_3_hours_allowed(client, create_user, app):
    create_user("admin@tutomatics.com", "admin", "A12345", role="admin", status="approved")
    student = create_user("student2@tutomatics.com", "student2", "S12345", role="student", status="approved")

    _login_student(client, "student2@tutomatics.com", "S12345")
    start = (datetime.utcnow() + timedelta(hours=4)).replace(second=0, microsecond=0)

    response = client.post("/api/book-slot", json={
        "start_time": start.isoformat(),
        "lesson_minutes": 120
    })
    data = response.get_json()

    assert response.status_code == 201
    assert data["success"] is True

    with app.app_context():
        b = app_module.Booking.query.filter_by(student_id=student.id).first()
        assert b is not None
        assert b.status == "pending"
        assert b.price_eur == 100


def test_book_slot_invalid_duration_rejected(client, create_user):
    create_user("admin@tutomatics.com", "admin", "A12345", role="admin", status="approved")
    create_user("student3@tutomatics.com", "student3", "S12345", role="student", status="approved")

    _login_student(client, "student3@tutomatics.com", "S12345")
    start = (datetime.utcnow() + timedelta(hours=4)).replace(second=0, microsecond=0)

    response = client.post("/api/book-slot", json={
        "start_time": start.isoformat(),
        "lesson_minutes": 130
    })
    data = response.get_json()

    assert response.status_code == 400
    assert "1-hour increments" in data["error"]


def test_book_slot_past_rejected(client, create_user):
    create_user("admin@tutomatics.com", "admin", "A12345", role="admin", status="approved")
    create_user("student4@tutomatics.com", "student4", "S12345", role="student", status="approved")

    _login_student(client, "student4@tutomatics.com", "S12345")
    start = (datetime.utcnow() - timedelta(hours=1)).replace(second=0, microsecond=0)

    response = client.post("/api/book-slot", json={
        "start_time": start.isoformat(),
        "lesson_minutes": 120
    })
    data = response.get_json()

    assert response.status_code == 400
    assert "past time slots" in data["error"]


def test_approve_booking_denies_overlapping_pending_only(client, create_user, app):
    admin = create_user("admin@tutomatics.com", "admin", "A12345", role="admin", status="approved")
    s1 = create_user("s1@tutomatics.com", "s1", "S12345", role="student", status="approved")
    s2 = create_user("s2@tutomatics.com", "s2", "S12345", role="student", status="approved")
    s3 = create_user("s3@tutomatics.com", "s3", "S12345", role="student", status="approved")

    with app.app_context():
        base = datetime.utcnow().replace(second=0, microsecond=0) + timedelta(days=1)
        b1 = app_module.Booking(
            student_id=s1.id, tutor_id=admin.id,
            start_time=base.replace(hour=10, minute=0),
            end_time=base.replace(hour=12, minute=0),
            lesson_minutes=120, price_eur=100, status="pending"
        )
        b2 = app_module.Booking(
            student_id=s2.id, tutor_id=admin.id,
            start_time=base.replace(hour=11, minute=0),
            end_time=base.replace(hour=13, minute=0),
            lesson_minutes=120, price_eur=100, status="pending"
        )
        b3 = app_module.Booking(
            student_id=s3.id, tutor_id=admin.id,
            start_time=base.replace(hour=12, minute=0),
            end_time=base.replace(hour=14, minute=0),
            lesson_minutes=120, price_eur=100, status="pending"
        )
        app_module.db.session.add_all([b1, b2, b3])
        app_module.db.session.commit()
        b1_id, b2_id, b3_id = b1.id, b2.id, b3.id

    _login_admin(client, "admin@tutomatics.com", "A12345")
    response = client.post(f"/admin/bookings/{b1_id}/approve")
    data = response.get_json()
    assert response.status_code == 200
    assert data["denied_conflicts"] == 1

    with app.app_context():
        rb1 = app_module.Booking.query.get(b1_id)
        rb2 = app_module.Booking.query.get(b2_id)
        rb3 = app_module.Booking.query.get(b3_id)
        assert rb1.status == "accepted"
        assert rb2.status == "denied"
        assert rb3.status == "pending"


def test_create_unavailability_invalid_interval_rejected(client, create_user):
    create_user("admin@tutomatics.com", "admin", "A12345", role="admin", status="approved")
    _login_admin(client, "admin@tutomatics.com", "A12345")

    response = client.post("/api/admin/unavailability", json={
        "start_time": "15:00",
        "end_time": "15:00",
        "repeat_rule": "none"
    })
    data = response.get_json()

    assert response.status_code == 400
    assert "End time must be after start time" in data["error"]


def test_create_unavailability_valid_block_accepted(client, create_user):
    create_user("admin@tutomatics.com", "admin", "A12345", role="admin", status="approved")
    _login_admin(client, "admin@tutomatics.com", "A12345")

    response = client.post("/api/admin/unavailability", json={
        "start_time": "15:00",
        "end_time": "16:00",
        "repeat_rule": "none"
    })
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert "block_id" in data


def test_booking_respects_unavailability_block(client, create_user):
    create_user("admin@tutomatics.com", "admin", "A12345", role="admin", status="approved")
    create_user("student5@tutomatics.com", "student5", "S12345", role="student", status="approved")

    _login_admin(client, "admin@tutomatics.com", "A12345")
    client.post("/api/admin/unavailability", json={
        "start_time": "15:00",
        "end_time": "17:00",
        "repeat_rule": "none"
    })

    _login_student(client, "student5@tutomatics.com", "S12345")
    start = (datetime.utcnow() + timedelta(days=1)).replace(hour=16, minute=0, second=0, microsecond=0)

    response = client.post("/api/book-slot", json={
        "start_time": start.isoformat(),
        "lesson_minutes": 120
    })
    data = response.get_json()

    assert response.status_code == 400
    assert "Tutor is unavailable" in data["error"]


def test_student_can_cancel_own_pending_booking(client, create_user, app):
    admin = create_user("admin@tutomatics.com", "admin", "A12345", role="admin", status="approved")
    student = create_user("student6@tutomatics.com", "student6", "S12345", role="student", status="approved")

    with app.app_context():
        start = datetime.utcnow() + timedelta(days=1)
        booking = app_module.Booking(
            student_id=student.id,
            tutor_id=admin.id,
            start_time=start,
            end_time=start + timedelta(hours=2),
            lesson_minutes=120,
            price_eur=100,
            status="pending",
        )
        app_module.db.session.add(booking)
        app_module.db.session.commit()
        booking_id = booking.id

    _login_student(client, "student6@tutomatics.com", "S12345")
    response = client.post(f"/student/bookings/{booking_id}/cancel")
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True

    with app.app_context():
        updated = app_module.Booking.query.get(booking_id)
        assert updated.status == "cancelled"


def test_student_cannot_cancel_accepted_booking(client, create_user, app):
    admin = create_user("admin@tutomatics.com", "admin", "A12345", role="admin", status="approved")
    student = create_user("student7@tutomatics.com", "student7", "S12345", role="student", status="approved")

    with app.app_context():
        start = datetime.utcnow() + timedelta(days=1)
        booking = app_module.Booking(
            student_id=student.id,
            tutor_id=admin.id,
            start_time=start,
            end_time=start + timedelta(hours=2),
            lesson_minutes=120,
            price_eur=100,
            status="accepted",
        )
        app_module.db.session.add(booking)
        app_module.db.session.commit()
        booking_id = booking.id

    _login_student(client, "student7@tutomatics.com", "S12345")
    response = client.post(f"/student/bookings/{booking_id}/cancel")
    data = response.get_json()

    assert response.status_code == 400
    assert "Cannot cancel booking with status: accepted" in data["error"]


def test_student_cannot_cancel_other_students_booking(client, create_user, app):
    admin = create_user("admin@tutomatics.com", "admin", "A12345", role="admin", status="approved")
    owner = create_user("owner@tutomatics.com", "owner", "S12345", role="student", status="approved")
    other = create_user("other@tutomatics.com", "other", "S12345", role="student", status="approved")

    with app.app_context():
        start = datetime.utcnow() + timedelta(days=1)
        booking = app_module.Booking(
            student_id=owner.id,
            tutor_id=admin.id,
            start_time=start,
            end_time=start + timedelta(hours=2),
            lesson_minutes=120,
            price_eur=100,
            status="pending",
        )
        app_module.db.session.add(booking)
        app_module.db.session.commit()
        booking_id = booking.id

    _login_student(client, "other@tutomatics.com", "S12345")
    response = client.post(f"/student/bookings/{booking_id}/cancel")
    data = response.get_json()

    assert response.status_code == 403
    assert data["error"] == "Unauthorized"