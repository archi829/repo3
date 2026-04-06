from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()

# ─────────────────────────────────────────────
# ADMIN
# ─────────────────────────────────────────────
class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def get_id(self):
        return f"admin-{self.id}"


# ─────────────────────────────────────────────
# COMPANY
# ─────────────────────────────────────────────
class Company(UserMixin, db.Model):
    __tablename__ = 'company'

    id              = db.Column(db.Integer, primary_key=True)
    company_name    = db.Column(db.String(150), nullable=False)
    email           = db.Column(db.String(120), unique=True, nullable=False)
    password_hash   = db.Column(db.String(256), nullable=False)
    hr_contact      = db.Column(db.String(100))
    website         = db.Column(db.String(200))
    industry        = db.Column(db.String(100))
    description     = db.Column(db.Text)

    # Admin controls
    approval_status = db.Column(db.String(20), default='Pending')   # Pending / Approved / Rejected
    is_blacklisted  = db.Column(db.Boolean, default=False)
    created_at      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    drives = db.relationship('PlacementDrive', backref='company', lazy=True,cascade='all, delete-orphan')
    placements = db.relationship('Placement', backref='company', lazy=True)

    def get_id(self):
        return f"company-{self.id}"


# ─────────────────────────────────────────────
# STUDENT
# ─────────────────────────────────────────────
class Student(UserMixin, db.Model):
    __tablename__ = 'student'

    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(150), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone         = db.Column(db.String(20))
    cgpa          = db.Column(db.Float)
    skills        = db.Column(db.Text)  # comma-separated 
    education     = db.Column(db.Text)          
    resume_path   = db.Column(db.String(300))   # path to uploaded resume file

    # Admin controls
    is_blacklisted = db.Column(db.Boolean, default=False)
    is_active      = db.Column(db.Boolean, default=True)
    created_at     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    applications = db.relationship('Application', backref='student', lazy=True, cascade='all, delete-orphan')
    placements = db.relationship('Placement', backref='student', lazy=True)

    def get_id(self):
        return f"student-{self.id}"

# ─────────────────────────────────────────────
# Notification 
# ─────────────────────────────────────────────
class Notification(db.Model):
    __tablename__ = 'notification'

    id          = db.Column(db.Integer, primary_key=True)

    user_type   = db.Column(db.String(20), nullable=False)  
    user_id     = db.Column(db.Integer, nullable=False)

    message     = db.Column(db.Text, nullable=False)
    is_read     = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.Index('idx_user_lookup', 'user_type', 'user_id'),)

# ─────────────────────────────────────────────
# PLACEMENT DRIVE
# ─────────────────────────────────────────────
class PlacementDrive(db.Model):
    __tablename__ = 'placement_drive'

    id                  = db.Column(db.Integer, primary_key=True)
    company_id          = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    job_title           = db.Column(db.String(150), nullable=False)
    job_description     = db.Column(db.Text, nullable=False)
    eligibility_criteria= db.Column(db.Text)
    required_skills     = db.Column(db.Text)     
    salary_range        = db.Column(db.String(100))
    application_deadline= db.Column(db.Date, nullable=False)
    location            = db.Column(db.String(150))

    # Status flow: Pending → Approved → Closed
    status      = db.Column(db.String(20), default='Pending')  # Pending / Approved / Closed
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    applications = db.relationship('Application', backref='drive', lazy=True, cascade='all, delete-orphan')
    placements = db.relationship('Placement', backref='drive', lazy=True)

# ─────────────────────────────────────────────
# PLACEMENT (Finalized Hires)
# ─────────────────────────────────────────────
class Placement(db.Model):
    __tablename__ = 'placement'

    id           = db.Column(db.Integer, primary_key=True)
    student_id   = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    drive_id     = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    company_id   = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    package_offered = db.Column(db.String(100)) # e.g., "12 LPA"
    placed_at       = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Optional: Remarks from HR or Admin
    remarks         = db.Column(db.Text)

# ─────────────────────────────────────────────
# APPLICATION
# ─────────────────────────────────────────────
class Application(db.Model):
    __tablename__ = 'application'

    id           = db.Column(db.Integer, primary_key=True)
    student_id   = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    drive_id     = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)

    applied_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Status flow: Applied → Shortlisted → Selected / Rejected
    status       = db.Column(db.String(20), default='Applied')

    cover_letter = db.Column(db.Text)

    # Prevent duplicate applications: one student can apply once per drive
    __table_args__ = (
        db.UniqueConstraint('student_id', 'drive_id', name='unique_student_drive'),
    )