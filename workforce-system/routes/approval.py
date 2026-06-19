from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.approval_log import ApprovalLog
from models.notification import Notification
from models.work_request import WorkRequest
from models.manpower_request import ManpowerRequest
from models.supply_request import SupplyRequest
from services.email_service import notify_status_change

approval = Blueprint('approval', __name__, url_prefix='/approval')

MODEL_MAP = {
    'work': WorkRequest,
    'manpower': ManpowerRequest,
    'supply': SupplyRequest,
}

ROLE_LABEL = {
    'manager': 'Manager',
    'cluster_manager': 'Cluster Manager',
    'admin': 'Administrator',
}

STATUS_FLOW = {
    'pending_manager': 'pending_cm',
    'pending_cm': 'approved',
}


def get_model(request_type):
    return MODEL_MAP.get(request_type)


@approval.route('/pending')
@login_required
def pending():
    if current_user.role == 'requester':
        flash('You do not have approval permissions.', 'warning')
        return redirect(url_for('dashboard.index'))

    pending_work = []
    pending_manpower = []
    pending_supply = []

    if current_user.role in ('manager', 'admin'):
        pending_work = WorkRequest.query.filter_by(status='pending_manager').all()
        pending_manpower = ManpowerRequest.query.filter_by(status='pending_manager').all()
        pending_supply = SupplyRequest.query.filter_by(status='pending_manager').all()

    if current_user.role in ('cluster_manager', 'admin'):
        pending_work += WorkRequest.query.filter_by(status='pending_cm').all()
        pending_manpower += ManpowerRequest.query.filter_by(status='pending_cm').all()
        pending_supply += SupplyRequest.query.filter_by(status='pending_cm').all()

    combined = [('Work', r) for r in pending_work] + \
               [('Manpower', r) for r in pending_manpower] + \
               [('Supply', r) for r in pending_supply]
    combined.sort(key=lambda x: x[1].created_at or x[1].created_at, reverse=True)

    return render_template('approval/pending.html', requests=combined)


@approval.route('/approve', methods=['POST'])
@login_required
def approve():
    return handle_action('approved')


@approval.route('/reject', methods=['POST'])
@login_required
def reject():
    return handle_action('rejected')


def handle_action(action):
    request_type = request.form.get('request_type')
    request_id = request.form.get('request_id')
    comments = request.form.get('comments', '').strip()

    if not request_type or not request_id:
        flash('Invalid request.', 'danger')
        return redirect(url_for('dashboard.index'))

    Model = get_model(request_type)
    if not Model:
        flash('Invalid request type.', 'danger')
        return redirect(url_for('dashboard.index'))

    req = Model.query.get(int(request_id))
    if not req:
        flash('Request not found.', 'danger')
        return redirect(url_for('dashboard.index'))

    if not can_approve(req, current_user):
        flash('You do not have permission to approve this request.', 'danger')
        return redirect(url_for('dashboard.index'))

    if action == 'approved':
        next_status = STATUS_FLOW.get(req.status)
        if next_status:
            req.status = next_status
        else:
            flash('This request cannot be approved in its current state.', 'warning')
            return redirect_detail(request_type, request_id)
    else:
        req.status = 'rejected'

    log = ApprovalLog(
        request_type=request_type,
        request_id=req.id,
        approver_id=current_user.id,
        action=action,
        comments=comments,
    )
    db.session.add(log)

    approver_label = ROLE_LABEL.get(current_user.role, current_user.role)
    notify_msg = f'Your {request_type.title()} Request #{req.id} has been {action} by {approver_label}.'
    if comments:
        notify_msg += f' Comments: {comments}'
    notify = Notification(
        user_id=req.requester_id,
        message=notify_msg,
        request_type=request_type,
        request_id=req.id,
    )
    db.session.add(notify)

    db.session.commit()

    notify_status_change(
        request_type=request_type,
        request_id=req.id,
        requester=req.requester,
        action=action,
        approver_name=f'{current_user.full_name} ({approver_label})',
        comments=comments,
    )

    flash(f'Request #{req.id} {action} successfully!', 'success')
    return redirect_detail(request_type, request_id)


def can_approve(req, user):
    if user.role == 'admin':
        return True
    if user.role == 'manager' and req.status == 'pending_manager':
        return True
    if user.role == 'cluster_manager' and req.status == 'pending_cm':
        return True
    return False


def redirect_detail(request_type, request_id):
    routes = {
        'work': 'work.detail',
        'manpower': 'manpower.detail',
        'supply': 'supply.detail',
    }
    route = routes.get(request_type, 'dashboard.index')
    return redirect(url_for(route, request_id=request_id))
