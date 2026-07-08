from models import db
from datetime import datetime, timezone


class TrackingEvent(db.Model):
    __tablename__ = 'tracking_events'

    id = db.Column(db.Integer, primary_key=True)
    request_type = db.Column(db.String(20), nullable=False)
    request_id = db.Column(db.Integer, nullable=False)
    tracking_id = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), default='')
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, default='')
    updated_by = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<TrackingEvent {self.id} - {self.tracking_id} - {self.status}>'
