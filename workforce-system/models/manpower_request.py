from models import db
from datetime import datetime, timezone


class ManpowerRequest(db.Model):
    __tablename__ = 'manpower_requests'

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    store_branch = db.Column(db.String(100), nullable=False)
    question_type = db.Column(db.String(100))
    manager_name = db.Column(db.String(100), nullable=False)
    cluster_manager_name = db.Column(db.String(100), nullable=False)
    name_type = db.Column(db.String(20))  # Promotion / Replacement / Transfer
    reason = db.Column(db.Text, nullable=False)
    reason_detail = db.Column(db.Text)
    additional = db.Column(db.Text)  # comma-separated tags

    position_title = db.Column(db.String(100), nullable=False)
    department_store = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    date_required = db.Column(db.Date, nullable=False)
    employees_needed = db.Column(db.Integer, nullable=False)
    existing_headcount = db.Column(db.Integer, nullable=False)

    manager_signature = db.Column(db.String(200))
    cm_signature = db.Column(db.String(200))

    status = db.Column(db.String(30), nullable=False, default='draft')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    requester = db.relationship('User', backref='manpower_requests', lazy=True)

    def status_display(self):
        display = {
            'draft': 'Draft',
            'pending_manager': 'Pending Manager Approval',
            'pending_cm': 'Pending Cluster Manager Approval',
            'approved': 'Approved',
            'rejected': 'Rejected',
        }
        return display.get(self.status, self.status)

    def __repr__(self):
        return f'<ManpowerRequest {self.id} - {self.position_title}>'
