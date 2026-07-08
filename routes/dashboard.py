from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.work_request import WorkRequest
from models.manpower_request import ManpowerRequest
from models.supply_request import SupplyRequest

dashboard = Blueprint('dashboard', __name__)


@dashboard.route('/')
@dashboard.route('/dashboard')
@login_required
def index():
    work_count = WorkRequest.query.filter_by(requester_id=current_user.id).count()
    manpower_count = ManpowerRequest.query.filter_by(requester_id=current_user.id).count()
    supply_count = SupplyRequest.query.filter_by(requester_id=current_user.id).count()

    my_pending_count = WorkRequest.query.filter(
        WorkRequest.requester_id == current_user.id,
        WorkRequest.status.in_(['pending_manager', 'pending_cm'])
    ).count()
    my_pending_count += ManpowerRequest.query.filter(
        ManpowerRequest.requester_id == current_user.id,
        ManpowerRequest.status.in_(['pending_manager', 'pending_cm'])
    ).count()
    my_pending_count += SupplyRequest.query.filter(
        SupplyRequest.requester_id == current_user.id,
        SupplyRequest.status.in_(['pending_manager', 'pending_cm'])
    ).count()

    approval_pending_count = 0
    if current_user.role in ('manager', 'admin'):
        approval_pending_count += WorkRequest.query.filter(
            WorkRequest.status == 'pending_manager',
            WorkRequest.requester_id != current_user.id,
        ).count()
        approval_pending_count += ManpowerRequest.query.filter(
            ManpowerRequest.status == 'pending_manager',
            ManpowerRequest.requester_id != current_user.id,
        ).count()
        approval_pending_count += SupplyRequest.query.filter(
            SupplyRequest.status == 'pending_manager',
            SupplyRequest.requester_id != current_user.id,
        ).count()
    if current_user.role in ('cluster_manager', 'admin'):
        approval_pending_count += WorkRequest.query.filter(
            WorkRequest.status == 'pending_cm',
            WorkRequest.requester_id != current_user.id,
        ).count()
        approval_pending_count += ManpowerRequest.query.filter(
            ManpowerRequest.status == 'pending_cm',
            ManpowerRequest.requester_id != current_user.id,
        ).count()
        approval_pending_count += SupplyRequest.query.filter(
            SupplyRequest.status == 'pending_cm',
            SupplyRequest.requester_id != current_user.id,
        ).count()

    recent_work = WorkRequest.query.filter_by(requester_id=current_user.id)\
        .order_by(WorkRequest.created_at.desc()).limit(4).all()
    recent_manpower = ManpowerRequest.query.filter_by(requester_id=current_user.id)\
        .order_by(ManpowerRequest.created_at.desc()).limit(4).all()
    recent_supply = SupplyRequest.query.filter_by(requester_id=current_user.id)\
        .order_by(SupplyRequest.created_at.desc()).limit(4).all()

    combined = [('Work', r) for r in recent_work] + [('Manpower', r) for r in recent_manpower] + [('Supply', r) for r in recent_supply]
    combined.sort(key=lambda x: x[1].created_at or x[1].created_at, reverse=True)
    combined = combined[:10]

    return render_template('dashboard.html',
                           work_count=work_count,
                           manpower_count=manpower_count,
                           supply_count=supply_count,
                           my_pending_count=my_pending_count,
                           approval_pending_count=approval_pending_count,
                           recent_requests=combined)
