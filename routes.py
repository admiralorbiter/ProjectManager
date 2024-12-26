from flask import flash, redirect, render_template, url_for, request, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from forms import LoginForm
from models import User, db, Project
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

def init_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash('Logged in successfully.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'danger')
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
    
    @app.route('/projects')
    @login_required
    def projects():
        # Get both owned projects and projects user is a member of
        owned_projects = Project.query.filter_by(owner_id=current_user.id)
        member_projects = current_user.member_of_projects
        projects = owned_projects.union(member_projects).order_by(Project.created_at.desc()).all()
        return render_template('projects.html', projects=projects)

    @app.route('/projects/create', methods=['GET', 'POST'])
    @login_required
    def create_project():
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            status = request.form.get('status', 'active')
            priority = request.form.get('priority', 'medium')
            project_url = request.form.get('project_url')
            features = request.form.getlist('features[]')  # Get list of features
            due_date_str = request.form.get('due_date')
            
            # Convert date string to datetime if provided
            due_date = None
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                except ValueError:
                    flash('Invalid date format', 'error')
                    return redirect(url_for('create_project'))
            
            project = Project(
                title=title,
                description=description,
                status=status,
                priority=priority,
                project_url=project_url,
                features=features,
                due_date=due_date,
                owner_id=current_user.id
            )
            
            db.session.add(project)
            db.session.commit()
            
            flash('Project created successfully!', 'success')
            return redirect(url_for('projects'))
            
        # Get all users for member selection
        users = User.query.filter(User.id != current_user.id).all()
        return render_template('create_project.html', users=users) 

    @app.route('/projects/<int:project_id>')
    @login_required
    def view_project(project_id):
        project = Project.query.get_or_404(project_id)
        
        # Check if user has access to this project
        if project.owner_id != current_user.id and current_user not in project.members:
            flash('You do not have access to this project.', 'error')
            return redirect(url_for('projects'))
        
        return render_template('view_project.html', project=project) 

    @app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_project(project_id):
        project = Project.query.get_or_404(project_id)
        
        # Check if user is the owner
        if project.owner_id != current_user.id:
            flash('Only the project owner can edit the project.', 'error')
            return redirect(url_for('view_project', project_id=project.id))
        
        if request.method == 'POST':
            project.title = request.form.get('title')
            project.description = request.form.get('description')
            project.status = request.form.get('status', 'active')
            project.priority = request.form.get('priority', 'medium')
            project.project_url = request.form.get('project_url')
            project.features = request.form.getlist('features[]')
            
            due_date_str = request.form.get('due_date')
            if due_date_str:
                try:
                    project.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                except ValueError:
                    flash('Invalid date format', 'error')
                    return redirect(url_for('edit_project', project_id=project.id))
            else:
                project.due_date = None
            
            db.session.commit()
            flash('Project updated successfully!', 'success')
            return redirect(url_for('view_project', project_id=project.id))
        
        # Get all users for member selection
        users = User.query.filter(User.id != current_user.id).all()
        return render_template('edit_project.html', project=project, users=users) 