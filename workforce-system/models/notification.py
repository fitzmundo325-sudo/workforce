from models import db
from datetime import datetime, timezone


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    request_type = db.Column(db.String(20))
    request_id = db.Column(db.Integer)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='notifications', lazy=True)

    def __repr__(self):
        return f'<Notification #{self.id} - user#{self.user_id}>'
