import os
import uuid
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db
from models.work_request import WorkRequest
from models.approval_log import ApprovalLog
from forms.work_forms import WorkRequestSection1Form, WorkRequestSection2Form
from routes.approval import can_approve, initial_status_for_user

work = Blueprint('work', __name__, url_prefix='/work')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file):
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f'{uuid.uuid4().hex}.{ext}'
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'pictures')
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))
    return filename


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


@work.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    form = WorkRequestSection1Form()
    if form.validate_on_submit():
        session['work_s1'] = {
            'store_branch': form.store_branch.data.strip(),
            'question_type': form.question_type.data.strip() if form.question_type.data else '',
            'manager_name': form.manager_name.data.strip(),
            'cluster_manager_name': form.cluster_manager_name.data.strip(),
            'description': form.description.data.strip(),
            'particular_job': form.particular_job.data,
            'warranty': form.warranty.data,
            'warranty_other': form.warranty_other.data.strip() if form.warranty_other.data else '',
            'department': form.department.data,
            'asset_type': form.asset_type.data,
            'asset_detail_type': form.asset_detail_type.data,
            'urgency': form.urgency.data,
        }
        return redirect(url_for('work.new_step2'))
    return render_template('work/form_s1.html', form=form)


@work.route('/new/step2', methods=['GET', 'POST'])
@login_required
def new_step2():
    if 'work_s1' not in session:
        flash('Please fill in the first section first.', 'warning')
        return redirect(url_for('work.new'))

    form = WorkRequestSection2Form()
    if form.validate_on_submit():
        s1 = session['work_s1']

        picture_files = []
        uploaded_files = request.files.getlist('pictures')
        for f in uploaded_files:
            if f and f.filename and allowed_file(f.filename):
                picture_files.append(save_upload(f))

        mgr_sig = save_signature(form.manager_signature.data, 'mgr')
        cm_sig = save_signature(form.cm_signature.data, 'cm')

        is_draft = form.save_draft.data

        work_req = WorkRequest(
            requester_id=current_user.id,
            store_branch=s1['store_branch'],
            question_type=s1['question_type'],
            manager_name=s1['manager_name'],
            cluster_manager_name=s1['cluster_manager_name'],
            description=s1['description'],
            particular_job=s1['particular_job'],
            warranty=s1['warranty'],
            warranty_other=s1['warranty_other'],
            department=s1['department'],
            asset_type=s1['asset_type'],
            asset_detail_type=s1['asset_detail_type'],
            urgency=s1['urgency'],
            pictures=','.join(picture_files) if picture_files else '',
            manager_signature=mgr_sig or '',
            cm_signature=cm_sig or '',
            status=initial_status_for_user(current_user, is_draft),
        )
        db.session.add(work_req)
        db.session.commit()
        session.pop('work_s1', None)

        flash('Work request submitted successfully!', 'success')
        return redirect(url_for('work.detail', request_id=work_req.id))

    return render_template('work/form_s2.html', form=form)


@work.route('/<int:request_id>')
@login_required
def detail(request_id):
    req = WorkRequest.query.get_or_404(request_id)
    approval_logs = ApprovalLog.query.filter_by(request_type='work', request_id=req.id)\
        .order_by(ApprovalLog.created_at.desc()).all()
    can_review = can_approve(req, current_user)
    return render_template('work/detail.html', req=req, approval_logs=approval_logs, can_approve=can_review)


@work.route('/my-requests')
@login_required
def my_requests():
    requests = WorkRequest.query.filter_by(requester_id=current_user.id)\
        .order_by(WorkRequest.created_at.desc()).all()
    return render_template('work/list.html', requests=requests, title='My Work Requests')
