from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Company, PlacementDrive, Application, Student
from functools import wraps

company_bp = Blueprint('company', __name__, url_prefix='/company')

def company_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not isinstance(current_user, Company):
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        if current_user.is_blacklisted:
            flash('Your account has been blacklisted.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@company_bp.route('/dashboard')
@login_required
@company_required
def dashboard():
    drives = PlacementDrive.query.filter_by(
        company_id=current_user.id
    ).order_by(PlacementDrive.created_at.desc()).all()

    return render_template('company/dashboard.html',
        company=current_user,
        drives=drives
    )

@company_bp.route('/drive/create', methods=['GET', 'POST'])
@login_required
@company_required
def create_drive():
    if request.method == 'POST':
        job_title    = request.form.get('job_title', '').strip()
        job_desc     = request.form.get('job_description', '').strip()
        eligibility  = request.form.get('eligibility_criteria', '').strip()
        skills       = request.form.get('required_skills', '').strip()
        salary       = request.form.get('salary_range', '').strip()
        deadline_str = request.form.get('application_deadline', '')
        location     = request.form.get('location', '').strip()

        if not job_title or not job_desc or not deadline_str:
            flash('Job title, description and deadline are required.', 'danger')
            return render_template('company/create_drive.html')

        from datetime import date
        try:
            deadline = date.fromisoformat(deadline_str)
            if deadline <= date.today():
                flash('Deadline must be a future date.', 'danger')
                return render_template('company/create_drive.html')
        except ValueError:
            flash('Invalid date format.', 'danger')
            return render_template('company/create_drive.html')

        drive = PlacementDrive(
            company_id           = current_user.id,
            job_title            = job_title,
            job_description      = job_desc,
            eligibility_criteria = eligibility,
            required_skills      = skills,
            salary_range         = salary,
            application_deadline = deadline,
            location             = location,
            status               = 'Pending'
        )
        db.session.add(drive)
        db.session.commit()
        flash('Drive posted! Waiting for admin approval.', 'success')
        return redirect(url_for('company.dashboard'))

    return render_template('company/create_drive.html')

@company_bp.route('/drive/<int:drive_id>/edit', methods=['GET', 'POST'])
@login_required
@company_required
def edit_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))

    if request.method == 'POST':
        drive.job_title             = request.form.get('job_title', '').strip()
        drive.job_description       = request.form.get('job_description', '').strip()
        drive.eligibility_criteria  = request.form.get('eligibility_criteria', '').strip()
        drive.required_skills       = request.form.get('required_skills', '').strip()
        drive.salary_range          = request.form.get('salary_range', '').strip()
        drive.location              = request.form.get('location', '').strip()

        from datetime import date
        deadline_str = request.form.get('application_deadline', '')
        try:
            drive.application_deadline = date.fromisoformat(deadline_str)
        except ValueError:
            flash('Invalid date.', 'danger')
            return render_template('company/edit_drive.html', drive=drive)

        db.session.commit()
        flash('Drive updated.', 'success')
        return redirect(url_for('company.dashboard'))

    return render_template('company/edit_drive.html', drive=drive)


@company_bp.route('/drive/<int:drive_id>/close', methods=['POST'])
@login_required
@company_required
def close_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))
    drive.status = 'Closed'
    db.session.commit()
    flash('Drive closed.', 'warning')
    return redirect(url_for('company.dashboard'))


@company_bp.route('/drive/<int:drive_id>/delete', methods=['POST'])
@login_required
@company_required
def delete_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))
    db.session.delete(drive)
    db.session.commit()
    flash('Drive deleted.', 'danger')
    return redirect(url_for('company.dashboard'))

@company_bp.route('/drive/<int:drive_id>/applications')
@login_required
@company_required
def drive_applications(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))
    apps = Application.query.filter_by(
        drive_id=drive_id
    ).join(Student).order_by(Application.applied_at.desc()).all()
    return render_template('company/applications.html', drive=drive, apps=apps)


@company_bp.route('/application/<int:app_id>/status', methods=['POST'])
@login_required
@company_required
def update_status(app_id):
    app = Application.query.get_or_404(app_id)
    if app.drive.company_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))

    new_status = request.form.get('status')
    if new_status not in ['Applied', 'Shortlisted', 'Selected', 'Rejected']:
        flash('Invalid status.', 'danger')
        return redirect(request.referrer or url_for('company.dashboard'))

    app.status = new_status
    db.session.commit()
    flash(f'Status updated to {new_status}.', 'success')
    return redirect(url_for('company.drive_applications', drive_id=app.drive_id))