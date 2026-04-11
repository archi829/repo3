from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
from flask_login import login_required, current_user
from models import db, Admin, Company, Student, PlacementDrive, Application
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not isinstance(current_user, Admin):
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_students  = Student.query.count()
    total_companies = Company.query.count()
    total_drives    = PlacementDrive.query.count()
    total_apps      = Application.query.count()
    pending_companies = Company.query.filter_by(approval_status='Pending').all()
    pending_drives    = PlacementDrive.query.filter_by(status='Pending').all()

    return render_template('admin/dashboard.html',
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        total_apps=total_apps,
        pending_companies=pending_companies,
        pending_drives=pending_drives
    )


# ── Approve/Reject Companies ──────────────────────────────────────────────────
@admin_bp.route('/company/<int:company_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = 'Approved'
    db.session.commit()
    flash(f'{company.company_name} has been approved.', 'success')
    return redirect(request.referrer or url_for('admin.dashboard'))


@admin_bp.route('/company/<int:company_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = 'Rejected'
    db.session.commit()
    flash(f'{company.company_name} has been rejected.', 'warning')
    return redirect(request.referrer or url_for('admin.dashboard'))


# ── Approve/Reject Drives ─────────────────────────────────────────────────────
@admin_bp.route('/drive/<int:drive_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'Approved'
    db.session.commit()
    flash(f'Drive "{drive.job_title}" approved.', 'success')
    return redirect(request.referrer or url_for('admin.dashboard'))


@admin_bp.route('/drive/<int:drive_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'Rejected'
    db.session.commit()
    flash(f'Drive "{drive.job_title}" rejected.', 'warning')
    return redirect(request.referrer or url_for('admin.dashboard'))


# ── Students ──────────────────────────────────────────────────────────────────
@admin_bp.route('/students')
@login_required
@admin_required
def students():
    q = request.args.get('q', '').strip()
    query = Student.query
    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(
                Student.full_name.ilike(like),
                Student.email.ilike(like),
                Student.phone.ilike(like),
                db.cast(Student.id, db.String).ilike(like),
            )
        )
    students = query.order_by(Student.created_at.desc()).all()
    return render_template('admin/students.html', students=students, q=q)


@admin_bp.route('/student/<int:student_id>')
@login_required
@admin_required
def student_detail(student_id):
    student = Student.query.get_or_404(student_id)
    applications = Application.query.filter_by(
        student_id=student_id
    ).order_by(Application.applied_at.desc()).all()
    return render_template('admin/student_detail.html',
                           student=student, applications=applications)


@admin_bp.route('/student/<int:student_id>/blacklist', methods=['POST'])
@login_required
@admin_required
def blacklist_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.is_blacklisted = not student.is_blacklisted
    db.session.commit()
    state = 'blacklisted' if student.is_blacklisted else 'unblacklisted'
    flash(f'{student.full_name} has been {state}.', 'warning')
    return redirect(request.referrer or url_for('admin.students'))


@admin_bp.route('/student/<int:student_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted.', 'danger')
    return redirect(url_for('admin.students'))


# ── Companies ─────────────────────────────────────────────────────────────────
@admin_bp.route('/companies')
@login_required
@admin_required
def companies():
    q = request.args.get('q', '').strip()
    query = Company.query
    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(
                Company.company_name.ilike(like),
                Company.industry.ilike(like),
                db.cast(Company.id, db.String).ilike(like),
            )
        )
    companies = query.order_by(Company.created_at.desc()).all()
    return render_template('admin/companies.html', companies=companies, q=q)


@admin_bp.route('/company/<int:company_id>/blacklist', methods=['POST'])
@login_required
@admin_required
def blacklist_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.is_blacklisted = not company.is_blacklisted
    db.session.commit()
    state = 'blacklisted' if company.is_blacklisted else 'unblacklisted'
    flash(f'{company.company_name} has been {state}.', 'warning')
    return redirect(request.referrer or url_for('admin.companies'))


@admin_bp.route('/company/<int:company_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    flash('Company deleted.', 'danger')
    return redirect(url_for('admin.companies'))


# ── All Drives (admin view) ───────────────────────────────────────────────────
@admin_bp.route('/drives')
@login_required
@admin_required
def drives():
    drives = PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).all()
    return render_template('admin/drives.html', drives=drives)


# ── All Applications (admin view) ─────────────────────────────────────────────
@admin_bp.route('/applications')
@login_required
@admin_required
def applications():
    apps = Application.query.order_by(Application.applied_at.desc()).all()
    return render_template('admin/applications.html', apps=apps)


# ── Admin resume download ──────────────────────────────────────────────────────
@admin_bp.route('/student/<int:student_id>/resume')
@login_required
@admin_required
def download_student_resume(student_id):
    student = Student.query.get_or_404(student_id)
    if not student.resume_path:
        flash('This student has not uploaded a resume.', 'warning')
        return redirect(request.referrer or url_for('admin.students'))
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        student.resume_path,
        as_attachment=True
    )
