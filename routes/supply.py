import os
import uuid
import json
import secrets
import string
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify
from flask_login import login_required, current_user
from models import db
from models.supply_request import SupplyRequest
from models.approval_log import ApprovalLog
from models.tracking_event import TrackingEvent
from models.supply_catalog import SupplyCatalog
from forms.supply_forms import SupplyRequestForm
from routes.approval import can_approve, initial_status_for_user


TRACKING_STATUSES = [
    'Order Placed',
    'Tracking Number Generated',
    'Package Picked Up',
    'In Transit',
    'Out for Delivery',
    'Delivered',
    'Failed Delivery Attempt',
    'Return to Sender',
]


def gen_tracking_id():
    chars = string.ascii_uppercase + string.digits
    while True:
        tracking_id = 'SPL-' + ''.join(secrets.choice(chars) for _ in range(10))
        if not SupplyRequest.query.filter_by(tracking_id=tracking_id).first():
            return tracking_id


def create_supply_tracking(req, updated_by='System'):
    if req.tracking_id:
        return False

    req.tracking_id = gen_tracking_id()
    req.tracking_status = 'Order Placed'
    now = datetime.now(timezone.utc)
    db.session.add(TrackingEvent(
        request_type='supply',
        request_id=req.id,
        tracking_id=req.tracking_id,
        status='Order Placed',
        location=req.store_branch,
        notes='Request approved. Order created.',
        updated_by=updated_by,
        created_at=now,
    ))
    db.session.add(TrackingEvent(
        request_type='supply',
        request_id=req.id,
        tracking_id=req.tracking_id,
        status='Tracking Number Generated',
        location=req.store_branch,
        notes=f'Tracking ID {req.tracking_id} issued.',
        updated_by=updated_by,
        created_at=datetime.now(timezone.utc),
    ))
    return True


def geocode_location(location_text):
    import requests
    if not location_text:
        return None, None
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": location_text, "format": "json", "limit": 1}
    try:
        resp = requests.get(url, params=params, headers={"User-Agent": "WorkforceSystem/1.0"}, timeout=5)
        if resp.ok and resp.json():
            return float(resp.json()[0]["lat"]), float(resp.json()[0]["lon"])
    except Exception:
        pass
    return None, None

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


def build_items_from_request():
    categories = request.form.getlist('item_category')
    names = request.form.getlist('item_name')
    quantities = request.form.getlist('item_quantity')
    items = []

    for index, category in enumerate(categories):
        item_name = names[index].strip() if index < len(names) else ''
        quantity_text = quantities[index].strip() if index < len(quantities) else ''
        category = category.strip()

        if not category or not item_name or not quantity_text:
            continue

        try:
            quantity = int(quantity_text)
        except ValueError:
            continue

        if quantity < 1:
            continue

        catalog_item = SupplyCatalog.query.filter_by(
            category=category,
            item_name=item_name,
        ).first()

        items.append({
            'category': category,
            'item_name': item_name,
            'quantity': quantity,
            'unit': catalog_item.unit if catalog_item else '',
        })

    return items


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
            items = json.loads(form.items_data.data or '[]')
        except json.JSONDecodeError:
            flash('Invalid items data.', 'danger')
            return render_template('supply/form.html', form=form)

        if not items:
            items = build_items_from_request()

        if not items:
            flash('Please add at least one item.', 'danger')
            return render_template('supply/form.html', form=form)

        mgr_sig = save_signature(form.manager_signature.data, 'mgr')
        cm_sig = save_signature(form.cm_signature.data, 'cm')

        is_draft = form.save_draft.data

        next_status = initial_status_for_user(current_user, is_draft)
        req = SupplyRequest(
            requester_id=current_user.id,
            store_branch=form.store_branch.data.strip(),
            manager_name=form.manager_name.data.strip(),
            cluster_manager_name=form.cluster_manager_name.data.strip(),
            purpose=form.purpose.data.strip(),
            items=json.dumps(items),
            manager_signature=mgr_sig or '',
            cm_signature=cm_sig or '',
            status=next_status,
        )
        db.session.add(req)
        if next_status == 'approved':
            db.session.flush()
            create_supply_tracking(req, updated_by=current_user.full_name)
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
    can_review = can_approve(req, current_user)

    tracking_events = []
    if req.tracking_id:
        tracking_events = TrackingEvent.query.filter_by(
            request_type='supply', request_id=req.id,
        ).order_by(TrackingEvent.created_at.asc()).all()

    return render_template('supply/detail.html', req=req, approval_logs=approval_logs,
                           can_approve=can_review, tracking_events=tracking_events,
                           tracking_statuses=TRACKING_STATUSES)


@supply.route('/<int:request_id>/tracking/update', methods=['POST'])
@login_required
def update_tracking(request_id):
    if current_user.role not in ('admin', 'manager'):
        flash('Only admins and managers can update tracking.', 'danger')
        return redirect(url_for('supply.detail', request_id=request_id))

    req = SupplyRequest.query.get_or_404(request_id)
    if not req.tracking_id:
        flash('No tracking ID found for this request.', 'warning')
        return redirect(url_for('supply.detail', request_id=request_id))

    status = request.form.get('status', '').strip()
    location = request.form.get('location', '').strip()
    notes = request.form.get('notes', '').strip()

    if status not in TRACKING_STATUSES:
        flash('Invalid tracking status.', 'danger')
        return redirect(url_for('supply.detail', request_id=request_id))

    lat, lng = geocode_location(location)

    event = TrackingEvent(
        request_type='supply',
        request_id=req.id,
        tracking_id=req.tracking_id,
        status=status,
        location=location,
        latitude=lat,
        longitude=lng,
        notes=notes,
        updated_by=current_user.full_name,
    )
    db.session.add(event)
    req.tracking_status = status
    db.session.commit()

    flash(f'Tracking updated to "{status}".', 'success')
    return redirect(url_for('supply.detail', request_id=request_id))


@supply.route('/<int:request_id>/tracking/start', methods=['POST'])
@login_required
def start_tracking(request_id):
    if current_user.role not in ('admin', 'manager'):
        flash('Only admins and managers can start tracking.', 'danger')
        return redirect(url_for('supply.detail', request_id=request_id))

    req = SupplyRequest.query.get_or_404(request_id)
    if req.status != 'approved':
        flash('Tracking can only be started after a supply request is approved.', 'warning')
        return redirect(url_for('supply.detail', request_id=request_id))

    if create_supply_tracking(req, updated_by=current_user.full_name):
        db.session.commit()
        flash(f'Tracking started. Tracking ID: {req.tracking_id}', 'success')
    else:
        flash('Tracking has already been started for this request.', 'info')
    return redirect(url_for('supply.detail', request_id=request_id))


@supply.route('/my-requests')
@login_required
def my_requests():
    requests = SupplyRequest.query.filter_by(requester_id=current_user.id)\
        .order_by(SupplyRequest.created_at.desc()).all()
    return render_template('supply/list.html', requests=requests, title='My Supply Requests')
