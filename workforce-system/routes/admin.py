from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.user import User
from models.work_request import WorkRequest
from models.manpower_request import ManpowerRequest
from models.supply_request import SupplyRequest
from models.approval_log import ApprovalLog

admin = Blueprint('admin', __name__, url_prefix='/admin')


@admin.route('')
@admin.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        return render_template('admin/restricted.html')

    total_users = User.query.count()
    total_work = WorkRequest.query.count()
    total_manpower = ManpowerRequest.query.count()
    total_supply = SupplyRequest.query.count()

    work_by_status = {
        'draft': WorkRequest.query.filter_by(status='draft').count(),
        'pending_manager': WorkRequest.query.filter_by(status='pending_manager').count(),
        'pending_cm': WorkRequest.query.filter_by(status='pending_cm').count(),
        'approved': WorkRequest.query.filter_by(status='approved').count(),
        'rejected': WorkRequest.query.filter_by(status='rejected').count(),
    }
    manpower_by_status = {
        'draft': ManpowerRequest.query.filter_by(status='draft').count(),
        'pending_manager': ManpowerRequest.query.filter_by(status='pending_manager').count(),
        'pending_cm': ManpowerRequest.query.filter_by(status='pending_cm').count(),
        'approved': ManpowerRequest.query.filter_by(status='approved').count(),
        'rejected': ManpowerRequest.query.filter_by(status='rejected').count(),
    }
    supply_by_status = {
        'draft': SupplyRequest.query.filter_by(status='draft').count(),
        'pending_manager': SupplyRequest.query.filter_by(status='pending_manager').count(),
        'pending_cm': SupplyRequest.query.filter_by(status='pending_cm').count(),
        'approved': SupplyRequest.query.filter_by(status='approved').count(),
        'rejected': SupplyRequest.query.filter_by(status='rejected').count(),
    }

    recent_approvals = ApprovalLog.query.order_by(ApprovalLog.created_at.desc()).limit(10).all()
    users = User.query.order_by(User.created_at.desc()).all()

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_work=total_work,
                           total_manpower=total_manpower,
                           total_supply=total_supply,
                           work_by_status=work_by_status,
                           manpower_by_status=manpower_by_status,
                           supply_by_status=supply_by_status,
                           recent_approvals=recent_approvals,
                           users=users)
