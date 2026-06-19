from models import db
from datetime import datetime, timezone


class SupplyRequest(db.Model):
    __tablename__ = 'supply_requests'

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    store_branch = db.Column(db.String(100), nullable=False)
    manager_name = db.Column(db.String(100), nullable=False)
    cluster_manager_name = db.Column(db.String(100), nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    items = db.Column(db.Text, nullable=False)  # JSON array

    manager_signature = db.Column(db.String(200))
    cm_signature = db.Column(db.String(200))

    status = db.Column(db.String(30), nullable=False, default='draft')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    requester = db.relationship('User', backref='supply_requests', lazy=True)

    def status_display(self):
        display = {
            'draft': 'Draft',
            'pending_manager': 'Pending Manager Approval',
            'pending_cm': 'Pending Cluster Manager Approval',
            'approved': 'Approved',
            'rejected': 'Rejected',
        }
        return display.get(self.status, self.status)

    def get_items(self):
        import json
        return json.loads(self.items) if self.items else []

    def __repr__(self):
        return f'<SupplyRequest {self.id} - {self.store_branch}>'
