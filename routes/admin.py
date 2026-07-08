from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_
from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField
from wtforms.validators import EqualTo, Length, Optional
from models.user import User
from models.work_request import WorkRequest
from models.manpower_request import ManpowerRequest
from models.supply_request import SupplyRequest
from models.approval_log import ApprovalLog
from models.tracking_event import TrackingEvent
from models import db
from forms.auth_forms import ROLE_CHOICES
from routes.supply import TRACKING_STATUSES, create_supply_tracking, geocode_location

admin = Blueprint('admin', __name__, url_prefix='/admin')


REQUEST_MODELS = (WorkRequest, ManpowerRequest, SupplyRequest)


class AdminUserForm(FlaskForm):
    full_name = StringField('Full Name', validators=[Length(max=100)])
    username = StringField('Username', validators=[Length(max=80)])
    email = StringField('Email', validators=[Length(max=120)])
    store_branch = StringField('Assigned Store', validators=[Length(max=100)])
    role = SelectField('Role', choices=ROLE_CHOICES)
    password = PasswordField('Password', validators=[Optional(), Length(min=6, max=128)])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[Optional(), EqualTo('password', message='Passwords must match.')],
    )


def admin_required():
    return current_user.role == 'admin'


@admin.route('')
@admin.route('/dashboard')
@login_required
def dashboard():
    if not admin_required():
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


@admin.route('/users')
@login_required
def users():
    if not admin_required():
        return render_template('admin/restricted.html')

    q = request.args.get('q', '').strip()
    store = request.args.get('store', '').strip()
    cluster = request.args.get('cluster', '').strip()
    query = User.query
    if q:
        like = f'%{q}%'
        query = query.filter(or_(
            User.full_name.ilike(like),
            User.username.ilike(like),
            User.email.ilike(like),
            User.role.ilike(like),
            User.store_branch.ilike(like),
        ))
    if store:
        query = query.filter(User.store_branch.ilike(store))
    if cluster:
        query = query.filter(User.full_name.ilike(cluster))

    users = query.order_by(User.id.desc()).all()
    role_labels = {
        'admin': 'Administrator',
        'manager': 'Store Manager',
        'cluster_manager': 'Cluster Manager',
        'requester': 'Store Manager',
    }
    return render_template(
        'admin/users.html',
        users=users,
        q=q,
        store=store,
        cluster=cluster,
        role_labels=role_labels,
        new_user_form=AdminUserForm(),
    )


@admin.route('/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    if not admin_required():
        return render_template('admin/restricted.html')

    if request.method == 'GET':
        return redirect(url_for('admin.users'))

    form = AdminUserForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()
        if not form.full_name.data.strip() or not username or not email or not form.store_branch.data.strip():
            flash('Full name, username, email, and assigned store are required.', 'danger')
            return redirect(url_for('admin.users'))
        if not form.password.data:
            flash('Password is required for new users.', 'danger')
            return redirect(url_for('admin.users'))
        if form.password.data != form.confirm_password.data:
            flash('Passwords must match.', 'danger')
            return redirect(url_for('admin.users'))

        existing = User.query.filter_by(username=username).first()
        if existing:
            flash('An account with this username already exists.', 'danger')
            return redirect(url_for('admin.users'))
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('An account with this email already exists.', 'danger')
            return redirect(url_for('admin.users'))

        user = User(
            full_name=form.full_name.data.strip(),
            username=username,
            email=email,
            role=form.role.data,
            store_branch=form.store_branch.data.strip(),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully.', 'success')
        return redirect(url_for('admin.users'))

    flash('Please check the user form and try again.', 'danger')
    return redirect(url_for('admin.users'))


@admin.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not admin_required():
        return render_template('admin/restricted.html')

    user = User.query.get_or_404(user_id)
    form = AdminUserForm(obj=user)
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()
        if not form.full_name.data.strip() or not username or not email or not form.store_branch.data.strip():
            flash('Full name, username, email, and assigned store are required.', 'danger')
            return render_template('admin/user_form.html', form=form, mode='edit', user=user)
        if form.password.data and form.password.data != form.confirm_password.data:
            flash('Passwords must match.', 'danger')
            return render_template('admin/user_form.html', form=form, mode='edit', user=user)

        username_owner = User.query.filter(User.username == username, User.id != user.id).first()
        if username_owner:
            flash('An account with this username already exists.', 'danger')
            return render_template('admin/user_form.html', form=form, mode='edit', user=user)
        email_owner = User.query.filter(User.email == email, User.id != user.id).first()
        if email_owner:
            flash('An account with this email already exists.', 'danger')
            return render_template('admin/user_form.html', form=form, mode='edit', user=user)

        user.full_name = form.full_name.data.strip()
        user.username = username
        user.email = email
        user.role = form.role.data
        user.store_branch = form.store_branch.data.strip()
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html', form=form, mode='edit', user=user)


@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not admin_required():
        return render_template('admin/restricted.html')

    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'warning')
        return redirect(url_for('admin.users'))

    request_count = (
        WorkRequest.query.filter_by(requester_id=user.id).count()
        + ManpowerRequest.query.filter_by(requester_id=user.id).count()
        + SupplyRequest.query.filter_by(requester_id=user.id).count()
    )
    if request_count:
        flash('This user has request history and cannot be deleted.', 'warning')
        return redirect(url_for('admin.users'))

    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.users'))


def _request_identity_rows():
    rows = []
    for model in REQUEST_MODELS:
        rows.extend(
            db.session.query(
                model.store_branch,
                model.manager_name,
                model.cluster_manager_name,
                model.created_at,
            ).filter(
                model.store_branch.isnot(None),
                model.store_branch != '',
            ).all()
        )
    return rows


def _earliest_date(current, candidate):
    if not candidate:
        return current
    if not current:
        return candidate
    try:
        return candidate if candidate < current else current
    except TypeError:
        return candidate if candidate.replace(tzinfo=None) < current.replace(tzinfo=None) else current


@admin.route('/clusters')
@login_required
def clusters():
    if not admin_required():
        return render_template('admin/restricted.html')

    q = request.args.get('q', '').strip()
    cluster_data = {}
    for store_branch, manager_name, cluster_manager_name, created_at in _request_identity_rows():
        if not cluster_manager_name or not cluster_manager_name.strip():
            continue
        cluster_name = cluster_manager_name.strip()
        cluster = cluster_data.setdefault(cluster_name, {
            'manager': cluster_name,
            'stores': set(),
            'added': created_at,
        })
        if store_branch and store_branch.strip():
            cluster['stores'].add(store_branch.strip())
        cluster['added'] = _earliest_date(cluster['added'], created_at)

    cluster_rows = []
    for index, (name, data) in enumerate(sorted(cluster_data.items(), key=lambda item: item[0].lower()), start=1):
        label = f'Cluster {index}'
        description = f'{label} - {name}'
        if q and q.lower() not in ' '.join([label, description, name]).lower():
            continue
        cluster_rows.append({
            'name': label,
            'description': description,
            'manager': data['manager'],
            'initial': data['manager'][:1].upper(),
            'store_count': len(data['stores']),
            'added': data['added'],
            'filter_value': name,
            'users': User.query.filter(User.full_name.ilike(name)).count(),
            'work': WorkRequest.query.filter(WorkRequest.cluster_manager_name.ilike(name)).count(),
            'manpower': ManpowerRequest.query.filter(ManpowerRequest.cluster_manager_name.ilike(name)).count(),
            'supply': SupplyRequest.query.filter(SupplyRequest.cluster_manager_name.ilike(name)).count(),
        })

    managers = User.query.filter_by(role='cluster_manager').order_by(User.full_name.asc()).all()
    return render_template('admin/clusters.html', clusters=cluster_rows, managers=managers, q=q)


@admin.route('/stores')
@login_required
def stores():
    if not admin_required():
        return render_template('admin/restricted.html')

    q = request.args.get('q', '').strip()
    selected_cluster = request.args.get('cluster', '').strip()

    cluster_names = sorted({
        row[2].strip()
        for row in _request_identity_rows()
        if row[2] and row[2].strip()
    }, key=str.lower)
    cluster_labels = {
        name: f'Cluster {index}'
        for index, name in enumerate(cluster_names, start=1)
    }

    store_data = {}
    for user in User.query.filter(User.store_branch.isnot(None), User.store_branch != '').all():
        name = user.store_branch.strip()
        if not name:
            continue
        store = store_data.setdefault(name, {
            'name': name,
            'address': name,
            'manager': user.full_name or user.username,
            'manager_initial': (user.full_name or user.username or name)[:1].upper(),
            'manager_id': user.id,
            'cluster_manager': '',
            'cluster_label': '',
            'added': user.created_at,
        })
        store['added'] = _earliest_date(store['added'], user.created_at)

    for store_branch, manager_name, cluster_manager_name, created_at in _request_identity_rows():
        name = store_branch.strip()
        store = store_data.setdefault(name, {
            'name': name,
            'address': name,
            'manager': manager_name or name,
            'manager_initial': (manager_name or name)[:1].upper(),
            'manager_id': None,
            'cluster_manager': '',
            'cluster_label': '',
            'added': created_at,
        })
        if manager_name:
            store['manager'] = manager_name.strip()
            store['manager_initial'] = store['manager'][:1].upper()
        if cluster_manager_name:
            cluster_manager = cluster_manager_name.strip()
            store['cluster_manager'] = cluster_manager
            store['cluster_label'] = cluster_labels.get(cluster_manager, cluster_manager)
        store['added'] = _earliest_date(store['added'], created_at)

    store_rows = []
    for index, (name, data) in enumerate(sorted(store_data.items(), key=lambda item: item[0].lower()), start=1):
        if selected_cluster and data['cluster_manager'].lower() != selected_cluster.lower():
            continue
        if q:
            haystack = ' '.join([
                data['name'],
                data['address'],
                data['manager'],
                data['cluster_label'],
                data['cluster_manager'],
            ]).lower()
            if q.lower() not in haystack:
                continue
        store_rows.append({
            **data,
            'id': index,
            'name': name,
            'date_added': data['added'],
            'is_one_year_already': False,
            'users': User.query.filter(User.store_branch.ilike(name)).count(),
            'work': WorkRequest.query.filter(WorkRequest.store_branch.ilike(name)).count(),
            'manpower': ManpowerRequest.query.filter(ManpowerRequest.store_branch.ilike(name)).count(),
            'supply': SupplyRequest.query.filter(SupplyRequest.store_branch.ilike(name)).count(),
        })

    managers = User.query.filter(User.role.in_(['manager', 'requester'])).order_by(User.full_name.asc()).all()
    return render_template(
        'admin/stores.html',
        stores=store_rows,
        managers=managers,
        all_managers=managers,
        q=q,
        selected_cluster=selected_cluster,
    )


@admin.route('/tracking')
@login_required
def tracking():
    if not admin_required():
        return render_template('admin/restricted.html')

    q = request.args.get('q', '').strip()
    tracking_status = request.args.get('status', '').strip()
    queue = request.args.get('queue', '').strip()

    query = SupplyRequest.query.outerjoin(User, SupplyRequest.requester_id == User.id)\
        .filter(SupplyRequest.status == 'approved')

    if q:
        like = f'%{q}%'
        query = query.filter(or_(
            SupplyRequest.store_branch.ilike(like),
            SupplyRequest.tracking_id.ilike(like),
            User.full_name.ilike(like),
        ))

    if tracking_status:
        query = query.filter(SupplyRequest.tracking_status == tracking_status)

    if queue == 'not_started':
        query = query.filter(SupplyRequest.tracking_id.is_(None))
    elif queue == 'active':
        query = query.filter(
            SupplyRequest.tracking_id.isnot(None),
            SupplyRequest.tracking_status.notin_(['Delivered', 'Failed Delivery Attempt', 'Return to Sender']),
        )
    elif queue == 'closed':
        query = query.filter(SupplyRequest.tracking_status.in_(['Delivered', 'Failed Delivery Attempt', 'Return to Sender']))

    requests = query.order_by(SupplyRequest.updated_at.desc()).all()

    tracking_summary = {
        'approved': SupplyRequest.query.filter_by(status='approved').count(),
        'not_started': SupplyRequest.query.filter(
            SupplyRequest.status == 'approved',
            SupplyRequest.tracking_id.is_(None),
        ).count(),
        'active': SupplyRequest.query.filter(
            SupplyRequest.status == 'approved',
            SupplyRequest.tracking_id.isnot(None),
            SupplyRequest.tracking_status.notin_(['Delivered', 'Failed Delivery Attempt', 'Return to Sender']),
        ).count(),
        'delivered': SupplyRequest.query.filter_by(status='approved', tracking_status='Delivered').count(),
    }

    latest_events = TrackingEvent.query.filter_by(request_type='supply')\
        .order_by(TrackingEvent.created_at.desc()).limit(8).all()
    mapped_events = TrackingEvent.query.filter(
        TrackingEvent.request_type == 'supply',
        TrackingEvent.latitude.isnot(None),
        TrackingEvent.longitude.isnot(None),
    ).order_by(TrackingEvent.created_at.asc()).all()
    map_events = [
        {
            'request_id': event.request_id,
            'tracking_id': event.tracking_id,
            'status': event.status,
            'location': event.location,
            'notes': event.notes,
            'updated_by': event.updated_by,
            'lat': event.latitude,
            'lng': event.longitude,
            'time': event.created_at.strftime('%b %d, %Y %I:%M %p') if event.created_at else '',
            'url': url_for('supply.detail', request_id=event.request_id),
        }
        for event in mapped_events
    ]

    return render_template(
        'admin/tracking.html',
        requests=requests,
        tracking_statuses=TRACKING_STATUSES,
        tracking_summary=tracking_summary,
        latest_events=latest_events,
        map_events=map_events,
        selected_status=tracking_status,
        selected_queue=queue,
        q=q,
    )


@admin.route('/tracking/<int:request_id>/start', methods=['POST'])
@login_required
def start_tracking(request_id):
    if not admin_required():
        return render_template('admin/restricted.html')

    req = SupplyRequest.query.get_or_404(request_id)
    if req.status != 'approved':
        flash('Tracking can only be started after a supply request is approved.', 'warning')
        return redirect(url_for('admin.tracking'))

    if create_supply_tracking(req, updated_by=current_user.full_name):
        db.session.commit()
        flash(f'Tracking started for Supply Request #{req.id}: {req.tracking_id}', 'success')
    else:
        flash(f'Supply Request #{req.id} already has tracking.', 'info')
    return redirect(url_for('admin.tracking'))


@admin.route('/tracking/<int:request_id>/update', methods=['POST'])
@login_required
def update_tracking(request_id):
    if not admin_required():
        return render_template('admin/restricted.html')

    req = SupplyRequest.query.get_or_404(request_id)
    if not req.tracking_id:
        flash('Start tracking before posting shipment updates.', 'warning')
        return redirect(url_for('admin.tracking'))

    status = request.form.get('status', '').strip()
    location = request.form.get('location', '').strip()
    notes = request.form.get('notes', '').strip()

    if status not in TRACKING_STATUSES:
        flash('Invalid tracking status.', 'danger')
        return redirect(url_for('admin.tracking'))

    lat, lng = geocode_location(location)
    db.session.add(TrackingEvent(
        request_type='supply',
        request_id=req.id,
        tracking_id=req.tracking_id,
        status=status,
        location=location,
        latitude=lat,
        longitude=lng,
        notes=notes,
        updated_by=current_user.full_name,
    ))
    req.tracking_status = status
    db.session.commit()

    flash(f'Supply Request #{req.id} tracking updated to "{status}".', 'success')
    return redirect(url_for('admin.tracking'))
