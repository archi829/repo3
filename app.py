from flask import Flask, redirect, url_for, render_template_string, abort
from models import db, Admin, Company, Student
from flask_login import LoginManager, login_required, current_user

from routes.auth import auth_bp
from routes.admin import admin_bp
 
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'mad1-project'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_portal.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'static/uploads/resumes'

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        if user_id.startswith('admin-'):
            return Admin.query.get(int(user_id.split('-')[1]))
        elif user_id.startswith('company-'):
            return Company.query.get(int(user_id.split('-')[1]))
        elif user_id.startswith('student-'):
            return Student.query.get(int(user_id.split('-')[1]))
        return None
    
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)


    STUB = '''
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"/>
    </head>
    <body class="bg-light">
        <div class="container mt-5 text-center">
            <h3> {{ title }} Dashboard</h3>
            <p class="text-muted">Coming in the next milestone!</p>
            <a href="/auth/logout" class="btn btn-dark mt-3">Logout</a>
        </div>
    </body>
    </html>
    '''
 
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
 
    @app.route('/company/dashboard')
    @login_required
    def company_dashboard():
        if not isinstance(current_user, Company):
            abort(403)
        return render_template_string(STUB, title='Company')

    @app.route('/student/dashboard')
    @login_required
    def student_dashboard():
        if not isinstance(current_user, Student):
            abort(403)
        return render_template_string(STUB, title='Student')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)