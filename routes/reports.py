import csv
import io
from datetime import datetime
from flask import Blueprint, render_template, request as req, Response
from flask_login import login_required, current_user
from models.work_request import WorkRequest
from models.manpower_request import ManpowerRequest
from models.supply_request import SupplyRequest

reports = Blueprint('reports', __name__, url_prefix='/reports')


def get_filtered_data(request_type, status, branch, date_from, date_to):
    results = []

    def filter_query(Model, rtype):
        query = Model.query
        if branch:
            query = query.filter(Model.store_branch.ilike(f'%{branch}%'))
        if status:
            query = query.filter_by(status=status)
        if not current_user.role == 'admin':
            query = query.filter_by(requester_id=current_user.id)
        rows = query.order_by(Model.created_at.desc()).all()
        if date_from:
            try:
                d = datetime.strptime(date_from, '%Y-%m-%d')
                rows = [r for r in rows if r.created_at and r.created_at.date() >= d.date()]
            except ValueError:
                pass
        if date_to:
            try:
                d = datetime.strptime(date_to, '%Y-%m-%d')
                rows = [r for r in rows if r.created_at and r.created_at.date() <= d.date()]
            except ValueError:
                pass
        for r in rows:
            results.append((rtype, r))

    if not request_type or request_type == 'work':
        filter_query(WorkRequest, 'Work')
    if not request_type or request_type == 'manpower':
        filter_query(ManpowerRequest, 'Manpower')
    if not request_type or request_type == 'supply':
        filter_query(SupplyRequest, 'Supply')

    results.sort(key=lambda x: x[1].created_at or x[1].created_at, reverse=True)
    return results


@reports.route('', methods=['GET'])
@login_required
def index():
    request_type = req.args.get('type', '')
    status = req.args.get('status', '')
    branch = req.args.get('branch', '')
    date_from = req.args.get('date_from', '')
    date_to = req.args.get('date_to', '')

    results = get_filtered_data(request_type, status, branch, date_from, date_to)

    return render_template('reports/index.html',
                           results=results,
                           request_type=request_type,
                           status=status,
                           branch=branch,
                           date_from=date_from,
                           date_to=date_to)


@reports.route('/export/csv', methods=['GET'])
@login_required
def export_csv():
    request_type = req.args.get('type', '')
    status = req.args.get('status', '')
    branch = req.args.get('branch', '')
    date_from = req.args.get('date_from', '')
    date_to = req.args.get('date_to', '')

    results = get_filtered_data(request_type, status, branch, date_from, date_to)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['ID', 'Type', 'Store Branch', 'Status', 'Created At'])

    for rtype, r in results:
        if rtype == 'Work':
            row = [r.id, 'Work', r.store_branch, r.manager_name,
                   r.cluster_manager_name, r.particular_job, r.department,
                   r.asset_type, r.asset_detail_type, r.urgency,
                   r.status, r.created_at]
            if len(row) > 12:
                row = row[:12]
            writer.writerow(row)
        elif rtype == 'Manpower':
            writer.writerow([r.id, 'Manpower', r.store_branch, r.manager_name,
                             r.cluster_manager_name, r.position_title,
                             r.employees_needed, r.existing_headcount,
                             r.name_type, r.status, r.created_at])
        elif rtype == 'Supply':
            writer.writerow([r.id, 'Supply', r.store_branch, r.manager_name,
                             r.cluster_manager_name, len(r.get_items()),
                             r.status, r.created_at])

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=requests_export_{timestamp}.csv'}
    )
