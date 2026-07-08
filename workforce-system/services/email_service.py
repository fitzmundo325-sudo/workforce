from flask import current_app, render_template
from flask_mail import Message
from models import db, mail
from models.notification import Notification


def send_notification_email(user, subject, body):
    if not user.email:
        return
    if not current_app.config['MAIL_USERNAME']:
        return

    try:
        msg = Message(
            subject=subject,
            recipients=[user.email],
            html=body,
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f'Email send failed to {user.email}: {e}')


def notify_status_change(request_type, request_id, requester, action, approver_name, comments=''):
    status_label = 'Approved' if action == 'approved' else 'Rejected'
    subject = f'[{request_type.title()} #{request_id}] Request {status_label}'

    body = render_template('email/status_notification.html',
                           request_type=request_type,
                           request_id=request_id,
                           action=action,
                           status_label=status_label,
                           approver_name=approver_name,
                           comments=comments,
                           requester_name=requester.full_name)

    notify = Notification(
        user_id=requester.id,
        message=f'Your {request_type.title()} Request #{request_id} has been {action} by {approver_name}.',
        request_type=request_type,
        request_id=request_id,
    )
    db.session.add(notify)

    send_notification_email(requester, subject, body)


def notify_submitted(request_type, request_id, requester, approver_role):
    subject = f'[New {request_type.title()} #{request_id}] Pending {approver_role} Approval'

    body = render_template('email/submitted_notification.html',
                           request_type=request_type,
                           request_id=request_id,
                           requester_name=requester.full_name,
                           approver_role=approver_role)

    admins = current_app.config['ADMINS']
    for admin_email in admins:
        try:
            from flask_mail import Message
            msg = Message(subject=subject, recipients=[admin_email], html=body)
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f'Email send failed: {e}')
