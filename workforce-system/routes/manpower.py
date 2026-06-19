import os
import uuid
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_required, current_user
from models import db
from models.manpower_request import ManpowerRequest
from models.approval_log import ApprovalLog
from forms.manpower_forms import ManpowerRequestSection1Form, ManpowerRequestSection2Form

manpower = Blueprint('manpower', __name__, url_prefix='/manpower')


def save_signature(data_url, prefix):
    import base64
    import re
    match = re.match(r'data:image/png;base64,(.+)', data_url)
    if not match:
        return None
    img_data = base64.b64decode(match.group(1))
    filename = f'{prefix}_{uuid.uuid4().hex}.png'
    sig_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'signatures')
    os.makedirs(sig_dir, exist_ok=True)
    with open(os.path.join(sig_dir, filename), 'wb') as f:
        f.write(img_data)
    return filename


@manpower.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    form = ManpowerRequestSection1Form()
    if form.validate_on_submit():
        additional = ','.join(form.additional.data) if form.additional.data else ''
        session['manpower_s1'] = {
            'store_branch': form.store_branch.data.strip(),
            'question_type': form.question_type.data.strip() if form.question_type.data else '',
            'manager_name': form.manager_name.data.strip(),
            'cluster_manager_name': form.cluster_manager_name.data.strip(),
            'name_type': form.name_type.data,
            'reason': form.reason.data.strip(),
            'reason_detail': form.reason_detail.data.strip() if form.reason_detail.data else '',
            'additional': additional,
        }
        return redirect(url_for('manpower.new_step2'))
    return render_template('manpower/form_s1.html', form=form)


@manpower.route('/new/step2', methods=['GET', 'POST'])
@login_required
def new_step2():
    if 'manpower_s1' not in session:
        flash('Please fill in the first section first.', 'warning')
        return redirect(url_for('manpower.new'))

    form = ManpowerRequestSection2Form()
    if form.validate_on_submit():
        s1 = session['manpower_s1']

        mgr_sig = save_signature(form.manager_signature.data, 'mgr')
        cm_sig = save_signature(form.cm_signature.data, 'cm')

        is_draft = form.save_draft.data

        req = ManpowerRequest(
            requester_id=current_user.id,
            store_branch=s1['store_branch'],
            question_type=s1['question_type'],
            manager_name=s1['manager_name'],
            cluster_manager_name=s1['cluster_manager_name'],
            name_type=s1['name_type'],
            reason=s1['reason'],
            reason_detail=s1['reason_detail'],
            additional=s1['additional'],
            position_title=form.position_title.data.strip(),
            department_store=form.department_store.data.strip(),
            company=form.company.data.strip(),
            date_required=form.date_required.data,
            employees_needed=form.employees_needed.data,
            existing_headcount=form.existing_headcount.data,
            manager_signature=mgr_sig or '',
            cm_signature=cm_sig or '',
            status='draft' if is_draft else 'pending_manager',
        )
        db.session.add(req)
        db.session.commit()
        session.pop('manpower_s1', None)

        flash('Manpower request submitted successfully!', 'success')
        return redirect(url_for('manpower.detail', request_id=req.id))

    return render_template('manpower/form_s2.html', form=form)


@manpower.route('/<int:request_id>')
@login_required
def detail(request_id):
    req = ManpowerRequest.query.get_or_404(request_id)
    approval_logs = ApprovalLog.query.filter_by(request_type='manpower', request_id=req.id)\
        .order_by(ApprovalLog.created_at.desc()).all()
    can_approve = (
        current_user.role == 'admin' or
        (current_user.role == 'manager' and req.status == 'pending_manager') or
        (current_user.role == 'cluster_manager' and req.status == 'pending_cm')
    )
    return render_template('manpower/detail.html', req=req, approval_logs=approval_logs, can_approve=can_approve)


@manpower.route('/my-requests')
@login_required
def my_requests():
    requests = ManpowerRequest.query.filter_by(requester_id=current_user.id)\
        .order_by(ManpowerRequest.created_at.desc()).all()
    return render_template('manpower/list.html', requests=requests, title='My Manpower Requests')
