from flask import current_app
from flask_mail import Message
import threading

def send_email(to, subject, template, **kwargs):
    """
    Send an email using Flask-Mail.
    
    Args:
        to: Recipient email address
        subject: Email subject line
        template: Email template name (or plain text)
        **kwargs: Variables to pass to template
    """
    try:
        msg = Message(
            subject=current_app.config['MAIL_SUBJECT_PREFIX'] + subject,
            recipients=[to],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        msg.body = template.format(**kwargs)
        msg.html = f"<html><body>{template.format(**kwargs)}</body></html>"
        
        # Send email with timeout protection
        mail_instance = current_app.extensions['mail']
        mail_instance.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
    
def send_email_safe(to, subject, template, *format_args, **format_kwargs):
    try:
        if format_args or format_kwargs:
            body = template.format(*format_args, **format_kwargs)
        else:
            body = template
        return send_email(to, subject, body)
    except Exception as e:
        print(f"Email error (non-blocking): {e}")
        return False
    
def send_booking_submitted_email(student_email, student_name, booking_time, duration):
    """Send email when student submits a booking request."""
    subject = "Booking Request Submitted"
    template = """Hello {},

Your booking request has been submitted successfully!

Details:
- Time: {}
- Duration: {} hours

Your request is now pending admin approval. You will receive another email once your booking is approved or denied.

Thank you for using Tutomatics!"""
    return send_email_safe(student_email, subject, template, student_name, booking_time, duration)

def send_booking_approved_email(student_email, student_name, booking_time, duration, price):
    """Send email when admin approves a booking."""
    subject = "Booking Approved!"
    template = f"""
Hello {student_name},

Great news! Your booking has been approved.

Details:
- Time: {booking_time}
- Duration: {duration} hours
- Price: {price}€

Please make sure to attend your lesson at the scheduled time.

Thank you for using Tutomatics!
"""
    return send_email(student_email, subject, template)

def send_booking_denied_email(student_email, student_name, booking_time):
    """Send email when admin denies a booking."""
    subject = "Booking Request Denied"
    template = f"""
Hello {student_name},

Unfortunately, your booking request for {booking_time} has been denied.

This may be due to scheduling conflicts or other reasons. Please try booking a different time slot.

Thank you for using Tutomatics!
"""
    return send_email(student_email, subject, template)

def send_new_booking_notification_email(admin_email, student_name, booking_time):
    """Send email to admin when a new booking request is submitted."""
    subject = "New Booking Request"
    template = """Hello Admin,

A new booking request has been submitted:

- Student: {}
- Time: {}

Please log in to review and approve/deny this request.

Tutomatics Admin Panel"""
    return send_email_safe(admin_email, subject, template, student_name, booking_time)

def send_signup_approved_email(user_email, user_name):
    subject = "Signup Approved"
    template = """Hello {},

Your Tutomatics account has been approved.

You can now log in and start booking lessons.

Thank you for registering with Tutomatics!"""
    return send_email_safe(user_email, subject, template, user_name)


def send_signup_denied_email(user_email, user_name):
    subject = "Signup Request Denied"
    template = """Hello {},

Unfortunately, your signup request for Tutomatics has been denied.

If you believe this is a mistake, please contact us for more information.

Thank you for your interest in Tutomatics."""
    return send_email_safe(user_email, subject, template, user_name)

def send_new_signup_request_notification_email(admin_email, user_name, user_email):
    subject = "New Signup Request"
    template = """Hello Admin,

A new student signup request has been submitted:

- Name: {}
- Email: {}

Please log in to review and approve/deny this signup.

Tutomatics Admin Panel"""
    return send_email_safe(admin_email, subject, template, user_name, user_email)

def send_new_admin_signup_request_notification_email(admin_email, user_name, user_email):
    subject = "New Admin Signup Request"
    template = """Hello Admin,

A new admin signup request has been submitted:

- Name: {}
- Email: {}

Please log in to Sign-up Approvals to approve or deny this admin account.

Tutomatics Admin Panel"""
    return send_email_safe(admin_email, subject, template, user_name, user_email)