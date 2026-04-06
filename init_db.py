from app import create_app
from models import db, Admin, Company, Student, PlacementDrive, Application, Placement, Notification
from werkzeug.security import generate_password_hash
from datetime import date, timedelta
import os

app = create_app()

with app.app_context():

    # ── Create uploads folder if not exists ─────────────────────────────────
    os.makedirs('static/uploads/resumes', exist_ok=True)

    # ── Drop and recreate all tables (clean slate) ───────────────────────────
    db.drop_all()
    db.create_all()
    print("All tables created.")

    # ── Seed: Admin ───────────────────
    admin = Admin(
        username      = 'admin',
        email         = 'admin@placementportal.com',
        password_hash = generate_password_hash('admin123')
    )
    db.session.add(admin)
    print("Admin created → email: admin@placementportal.com | password: admin123")

    company = Company(
    company_name='Test Corp',
    email='company@test.com',
    password_hash=generate_password_hash('test123'),
    approval_status='Approved'
    )

    student = Student(
    full_name='Test Student',
    email='student@test.com',
    password_hash=generate_password_hash('test123'),
    )
    db.session.add_all([company, student])
    

    db.session.commit()
