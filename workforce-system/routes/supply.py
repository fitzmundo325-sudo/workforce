import os
import uuid
import json
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify
from flask_login import login_required, current_user
from models import db
from models.supply_request import SupplyRequest
from models.approval_log import ApprovalLog
from models.supply_catalog import SupplyCatalog
from forms.supply_forms import SupplyRequestForm

supply = Blueprint('supply', __name__, url_prefix='/supply')


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


@supply.route('/catalog/categories')
@login_required
def get_categories():
    categories = [r[0] for r in SupplyCatalog.query.with_entities(SupplyCatalog.category).distinct().order_by(SupplyCatalog.category).all()]
    return jsonify(categories)


@supply.route('/catalog/items/<category>')
@login_required
def get_items(category):
    items = SupplyCatalog.query.filter_by(category=category).order_by(SupplyCatalog.item_name).all()
    return jsonify([{'id': i.id, 'name': i.item_name, 'unit': i.unit} for i in items])


@supply.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    form = SupplyRequestForm()
    if form.validate_on_submit():
        try:
            items = json.loads(form.items_data.data)
        except json.JSONDecodeError:
            flash('Invalid items data.', 'danger')
            return render_template('supply/form.html', form=form)

        if not items:
            flash('Please add at least one item.', 'danger')
            return render_template('supply/form.html', form=form)

        mgr_sig = save_signature(form.manager_signature.data, 'mgr')
        cm_sig = save_signature(form.cm_signature.data, 'cm')

        is_draft = form.save_draft.data

        req = SupplyRequest(
            requester_id=current_user.id,
            store_branch=form.store_branch.data.strip(),
            manager_name=form.manager_name.data.strip(),
            cluster_manager_name=form.cluster_manager_name.data.strip(),
            purpose=form.purpose.data.strip(),
            items=json.dumps(items),
            manager_signature=mgr_sig or '',
            cm_signature=cm_sig or '',
            status='draft' if is_draft else 'pending_manager',
        )
        db.session.add(req)
        db.session.commit()

        flash('Supply request submitted successfully!', 'success')
        return redirect(url_for('supply.detail', request_id=req.id))

    return render_template('supply/form.html', form=form)


@supply.route('/<int:request_id>')
@login_required
def detail(request_id):
    req = SupplyRequest.query.get_or_404(request_id)
    approval_logs = ApprovalLog.query.filter_by(request_type='supply', request_id=req.id)\
        .order_by(ApprovalLog.created_at.desc()).all()
    can_approve = (
        current_user.role == 'admin' or
        (current_user.role == 'manager' and req.status == 'pending_manager') or
        (current_user.role == 'cluster_manager' and req.status == 'pending_cm')
    )
    return render_template('supply/detail.html', req=req, approval_logs=approval_logs, can_approve=can_approve)


@supply.route('/my-requests')
@login_required
def my_requests():
    requests = SupplyRequest.query.filter_by(requester_id=current_user.id)\
        .order_by(SupplyRequest.created_at.desc()).all()
    return render_template('supply/list.html', requests=requests, title='My Supply Requests')
