from models import db
from datetime import datetime, timezone


class WorkRequest(db.Model):
    __tablename__ = 'work_requests'

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    store_branch = db.Column(db.String(100), nullable=False)
    question_type = db.Column(db.String(100))
    manager_name = db.Column(db.String(100), nullable=False)
    cluster_manager_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    particular_job = db.Column(db.String(20), nullable=False)
    warranty = db.Column(db.String(20), nullable=False)
    warranty_other = db.Column(db.String(200))
    department = db.Column(db.String(30), nullable=False)
    asset_type = db.Column(db.String(30), nullable=False)
    asset_detail_type = db.Column(db.String(30), nullable=False)
    urgency = db.Column(db.String(10), nullable=False)

    pictures = db.Column(db.Text)  # comma-separated filenames
    manager_signature = db.Column(db.String(200))
    cm_signature = db.Column(db.String(200))

    status = db.Column(db.String(30), nullable=False, default='draft')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    requester = db.relationship('User', backref='work_requests', lazy=True)

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
        return f'<WorkRequest {self.id} - {self.store_branch}>'
