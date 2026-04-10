from datetime import datetime, time

import pytest

import app.app as app_module
from app.helpers import (
    parse_email_input,
    calculate_price,
    slots_overlap,
    is_within_availability,
)


def test_parse_email_input_valid_email():
    username, email = parse_email_input("Student.One@Example.com")
    assert username == "Student.One"
    assert email == "student.one@example.com"


def test_parse_email_input_blank_rejected():
    with pytest.raises(ValueError, match="email is required"):
        parse_email_input("   ")


def test_parse_email_input_invalid_at_format_rejected():
    with pytest.raises(ValueError, match="Invalid email format"):
        parse_email_input("bad@@example.com")


def test_parse_email_input_username_only_converted():
    username, email = parse_email_input("biglez")
    assert username == "biglez"
    assert email == "biglez@tutomatics.com"


def test_calculate_price_values():
    assert calculate_price(120) == 100
    assert calculate_price(180) == 150
    assert calculate_price(240) == 200


def test_calculate_price_below_minimum_raises():
    with pytest.raises(ValueError, match="Minimum lesson duration is 2 hours"):
        calculate_price(60)


def test_slots_overlap_true_case():
    a_start = datetime(2026, 3, 20, 10, 0)
    a_end = datetime(2026, 3, 20, 12, 0)
    b_start = datetime(2026, 3, 20, 11, 0)
    b_end = datetime(2026, 3, 20, 13, 0)
    assert slots_overlap(a_start, a_end, b_start, b_end) is True


def test_slots_overlap_touching_boundary_false():
    a_start = datetime(2026, 3, 20, 10, 0)
    a_end = datetime(2026, 3, 20, 12, 0)
    b_start = datetime(2026, 3, 20, 12, 0)
    b_end = datetime(2026, 3, 20, 14, 0)
    assert slots_overlap(a_start, a_end, b_start, b_end) is False


def test_slots_overlap_non_overlap_false():
    a_start = datetime(2026, 3, 20, 8, 0)
    a_end = datetime(2026, 3, 20, 9, 0)
    b_start = datetime(2026, 3, 20, 10, 0)
    b_end = datetime(2026, 3, 20, 11, 0)
    assert slots_overlap(a_start, a_end, b_start, b_end) is False


def test_is_within_availability_overlap_rejected(app, db_session, create_user):
    tutor = create_user(
        email="admin@tutomatics.com",
        username="admin",
        password="A12345",
        role="admin",
        status="approved",
    )

    with app.app_context():
        block = app_module.Availability(
            user_id=tutor.id,
            start_time=time(10, 0),
            end_time=time(12, 0),
            repeat_rule="none",
        )
        db_session.add(block)
        db_session.commit()

        allowed = is_within_availability(
            tutor_id=tutor.id,
            start=datetime(2026, 3, 20, 11, 0),
            end=datetime(2026, 3, 20, 12, 0),
            db_session=db_session,
        )
        assert allowed is False


def test_is_within_availability_non_overlap_allowed(app, db_session, create_user):
    tutor = create_user(
        email="admin2@tutomatics.com",
        username="admin2",
        password="A12345",
        role="admin",
        status="approved",
    )

    with app.app_context():
        block = app_module.Availability(
            user_id=tutor.id,
            start_time=time(10, 0),
            end_time=time(12, 0),
            repeat_rule="none",
        )
        db_session.add(block)
        db_session.commit()

        allowed = is_within_availability(
            tutor_id=tutor.id,
            start=datetime(2026, 3, 20, 12, 0),
            end=datetime(2026, 3, 20, 13, 0),
            db_session=db_session,
        )
        assert allowed is True