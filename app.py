import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask
from flask_login import current_user
from sqlalchemy import text
from config import Config, basedir
from models import db, login_manager, mail


def ensure_tracking_schema():
    if not db.engine.url.drivername.startswith('sqlite'):
        return

    with db.engine.begin() as conn:
        columns = {
            row[1] for row in conn.execute(text('PRAGMA table_info(supply_requests)'))
        }
        if 'tracking_id' not in columns:
            conn.execute(text('ALTER TABLE supply_requests ADD COLUMN tracking_id VARCHAR(30)'))
        if 'tracking_status' not in columns:
            conn.execute(text('ALTER TABLE supply_requests ADD COLUMN tracking_status VARCHAR(50)'))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'signatures'), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from routes.auth import auth
    from routes.dashboard import dashboard
    from routes.work import work
    from routes.manpower import manpower
    from routes.supply import supply
    from routes.approval import approval
    from routes.reports import reports
    from routes.notifications import notifications_bp
    from routes.admin import admin
    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(work)
    app.register_blueprint(manpower)
    app.register_blueprint(supply)
    app.register_blueprint(approval)
    app.register_blueprint(reports)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(admin)

    @app.context_processor
    def inject_globals():
        if current_user.is_authenticated:
            from models.notification import Notification
            unread_count = Notification.query.filter_by(
                user_id=current_user.id, is_read=False).count()
            can_see_approvals = current_user.role in ('manager', 'cluster_manager', 'admin')
            return dict(unread_count=unread_count, can_see_approvals=can_see_approvals)
        return dict(unread_count=0, can_see_approvals=False)

    with app.app_context():
        db.create_all()
        ensure_tracking_schema()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
