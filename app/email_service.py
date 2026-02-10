from flask import current_app
from flask_mail import Message
from app import mail

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
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_booking_submitted_email(student_email, student_name, booking_time, duration):
    """Send email when student submits a booking request."""
    subject = "Booking Request Submitted"
    template = f"""
Hello {student_name},

Your booking request has been submitted successfully!

Details:
- Time: {booking_time}
- Duration: {duration} hours

Your request is now pending admin approval. You will receive another email once your booking is approved or denied.

Thank you for using Tutomatics!
"""
    return send_email(student_email, subject, template)

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
    template = f"""
Hello Admin,

A new booking request has been submitted:

- Student: {student_name}
- Time: {booking_time}

Please log in to review and approve/deny this request.

Tutomatics Admin Panel
"""
    return send_email(admin_email, subject, template)

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