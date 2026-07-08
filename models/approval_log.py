from models import db
from datetime import datetime, timezone


class ApprovalLog(db.Model):
    __tablename__ = 'approval_logs'

    id = db.Column(db.Integer, primary_key=True)
    request_type = db.Column(db.String(20), nullable=False)
    request_id = db.Column(db.Integer, nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(10), nullable=False)  # approved / rejected
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    approver = db.relationship('User', backref='approvals', lazy=True)

    def __repr__(self):
        return f'<ApprovalLog {self.request_type}#{self.request_id} - {self.action}>'
