from flask import flash, redirect, render_template, url_for, request, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from forms import LoginForm
from models import User, db, Project, Task, Submission, Feedback
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timezone
import werkzeug.exceptions
from urllib.parse import urlparse

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
        projects = Project.query.order_by(Project.created_at.desc()).all()
        return render_template('projects.html', projects=projects)

    @app.route('/projects/create', methods=['GET', 'POST'])
    @login_required
    def create_project():
        if not current_user.is_administrator():
            flash('Only administrators can create new projects.', 'error')
            return redirect(url_for('projects'))

        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            status = request.form.get('status', 'active')
            
            if not title:
                return jsonify({'error': 'Title is required'}), 400
            
            if status not in Project.VALID_STATUSES:
                return jsonify({'error': f'Invalid status. Must be one of: {", ".join(Project.VALID_STATUSES)}'}), 400
            
            try:
                due_date = None
                if due_date_str := request.form.get('due_date'):
                    try:
                        due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                    except ValueError:
                        return jsonify({'error': 'Invalid date format'}), 400
                    
                project = Project(
                    title=title,
                    description=description,
                    status=status,
                    priority=request.form.get('priority', 'medium'),
                    project_url=request.form.get('project_url'),
                    github_url=request.form.get('github_url'),
                    document_url=request.form.get('document_url'),
                    features=request.form.getlist('features[]'),
                    due_date=due_date,
                    owner_id=current_user.id
                )
                
                db.session.add(project)
                db.session.commit()
                
                flash('Project created successfully!', 'success')
                return redirect(url_for('projects'))
            
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': str(e)}), 500
        
        # Get all users for member selection
        users = User.query.filter(User.id != current_user.id).all()
        return render_template('create_project.html', users=users) 

    @app.route('/projects/<int:project_id>')
    @login_required
    def view_project(project_id):
        project = Project.query.get_or_404(project_id)
        return render_template('view_project.html', project=project, project_id=project_id)

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
            project.github_url = request.form.get('github_url')
            project.document_url = request.form.get('document_url')
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

    @app.route('/project/<int:project_id>/add_task', methods=['POST'])
    @login_required
    def add_task(project_id):
        try:
            project = Project.query.get_or_404(project_id)
            
            # Check if user has permission
            if project.owner_id != current_user.id and current_user not in project.members:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 403
            
            # Get form data
            title = request.form.get('title')
            description = request.form.get('description')
            status = request.form.get('status', 'open')
            parent_id = request.form.get('parent_id')
            
            # Validate required fields
            if not title:
                return jsonify({'success': False, 'error': 'Title is required'}), 400
            
            # Create new task (removed assigned_to_id and due_date)
            new_task = Task(
                title=title,
                description=description,
                status=status,
                project_id=project_id,
                parent_id=parent_id if parent_id else None,
                created_by_id=current_user.id
            )
            
            db.session.add(new_task)
            db.session.commit()
            
            return jsonify({'success': True})
            
        except werkzeug.exceptions.NotFound:
            return jsonify({'error': 'Project not found'}), 404
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/tasks/<int:task_id>/toggle', methods=['POST'])
    @login_required
    def toggle_task(task_id):
        try:
            task = Task.query.get_or_404(task_id)
            
            # Check if user has access to this task's project
            if task.project.owner_id != current_user.id and current_user not in task.project.members:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 403
            
            # Toggle the completion state
            task.is_completed = not task.is_completed
            task.status = 'completed' if task.is_completed else 'open'
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'is_completed': task.is_completed,
                'status': task.status
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/users/lookup/<username>')
    @login_required
    def lookup_user(username):
        user = User.query.filter_by(username=username).first()
        if user:
            return jsonify({'user_id': user.id})
        return jsonify({'error': 'User not found'}), 404

    @app.route('/api/tasks/<int:task_id>/assign', methods=['POST'])
    @login_required
    def assign_task(task_id):
        try:
            task = Task.query.get_or_404(task_id)
            project = task.project
            
            # Check permissions
            if project.owner_id != current_user.id and current_user not in project.members:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 403
            
            data = request.get_json()
            username = data.get('username')
            
            if not username:
                return jsonify({'success': False, 'error': 'Username is required'}), 400
            
            user = User.query.filter_by(username=username).first()
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            task.assigned_to_id = user.id
            db.session.commit()
            
            return jsonify({'success': True})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/profile/<username>')
    @login_required
    def user_profile(username):
        user = User.query.filter_by(username=username).first_or_404()
        
        # Update this line to get tasks assigned to this user
        assigned_tasks = Task.query.filter_by(assigned_to_id=user.id)\
            .join(Project)\
            .order_by(Task.due_date.asc())\
            .all()
        
        # If user is admin or viewing their own profile
        if current_user.is_administrator() or current_user.username == username:
            return render_template('profile.html', 
                                 user=user, 
                                 assigned_tasks=assigned_tasks,
                                 is_admin=current_user.is_administrator())
        
        flash('You do not have permission to view this profile.', 'error')
        return redirect(url_for('index'))

    @app.route('/admin/users')
    @login_required
    def admin_users():
        if not current_user.is_administrator():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('index'))
        
        users = User.query.all()
        return render_template('admin/users.html', users=users)

    @app.route('/admin/users/quick-add', methods=['POST'])
    @login_required
    def quick_add_user():
        if not current_user.is_administrator():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('index'))
        
        email = request.form.get('email')
        password = request.form.get('password') or 'prepkc123'  # Use provided password or default
        
        if not email:
            flash('Email is required.', 'error')
            return redirect(url_for('admin_users'))
        
        # Use email as username
        username = email
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('User with this email already exists.', 'error')
            return redirect(url_for('admin_users'))
        
        if User.query.filter_by(username=username).first():
            flash('User with this username already exists.', 'error')
            return redirect(url_for('admin_users'))
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role='user',
            is_admin=False
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash(f'User {email} created successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error creating user.', 'error')
            
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<username>/delete', methods=['DELETE'])
    @login_required
    def delete_user(username):
        if not current_user.is_administrator():
            return jsonify({'success': False, 'error': 'Access denied. Admin privileges required.'}), 403
        
        # Prevent self-deletion
        if username == current_user.username:
            return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
        
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        try:
            # Remove user from all projects
            for project in user.member_of_projects:
                project.members.remove(user)
            
            # Reassign or delete tasks
            Task.query.filter_by(assigned_to_id=user.id).update({'assigned_to_id': None})
            Task.query.filter_by(created_by_id=user.id).update({'created_by_id': current_user.id})
            
            # Delete the user
            db.session.delete(user)
            db.session.commit()
            
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/users/<username>/info', methods=['GET'])
    @login_required
    def get_user_info(username):
        if not current_user.is_administrator():
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_admin': user.is_admin,
                'is_active': user.is_active
            }
        })

    @app.route('/admin/users/<username>/edit', methods=['POST'])
    @login_required
    def edit_user(username):
        if not current_user.is_administrator():
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        if username == current_user.username:
            return jsonify({'success': False, 'error': 'Cannot edit your own account this way'}), 400
        
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        try:
            data = request.get_json()
            
            # Validate email format
            if not data.get('email') or '@' not in data['email']:
                return jsonify({'success': False, 'error': 'Invalid email format'}), 400
            
            # Check if new username is taken by another user
            if data.get('username') != username:
                existing_user = User.query.filter_by(username=data['username']).first()
                if existing_user:
                    return jsonify({'success': False, 'error': 'Username already in use'}), 400
            
            # Check if email is taken by another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.username != username:
                return jsonify({'success': False, 'error': 'Email already in use'}), 400
            
            # Update all user fields
            user.username = data['username']
            user.email = data['email']
            user.first_name = data.get('first_name')
            user.last_name = data.get('last_name')
            user.role = data['role']
            user.is_admin = data['is_admin']
            user.is_active = data['is_active']
            
            db.session.commit()
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/profile/<username>/change-password', methods=['POST'])
    @login_required
    def change_password(username):
        if current_user.username != username:
            flash('You can only change your own password.', 'error')
            return redirect(url_for('user_profile', username=username))
        
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Verify current password
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('user_profile', username=username))
        
        # Verify new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return redirect(url_for('user_profile', username=username))
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('Password updated successfully.', 'success')
        return redirect(url_for('user_profile', username=username))

    @app.route('/api/tasks/<int:task_id>/delete', methods=['DELETE'])
    @login_required
    def delete_task(task_id):
        if not current_user.is_administrator():
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        task = Task.query.get_or_404(task_id)
        
        try:
            # Delete all subtasks first
            Task.query.filter_by(parent_id=task_id).delete()
            
            # Delete the task
            db.session.delete(task)
            db.session.commit()
            
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/tasks/<int:task_id>/edit', methods=['POST'])
    @login_required
    def edit_task(task_id):
        if not current_user.is_administrator():
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        try:
            task = Task.query.get_or_404(task_id)
            
            # Validate required fields
            title = request.form.get('title')
            if not title:
                return jsonify({'success': False, 'error': 'Title is required'}), 400
            
            task.title = title
            task.description = request.form.get('description')
            
            db.session.commit()
            return jsonify({'success': True})
        except werkzeug.exceptions.NotFound:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/profile/<username>/edit', methods=['POST'])
    @login_required
    def edit_profile(username):
        if current_user.username != username:
            return jsonify({'success': False, 'error': 'You can only edit your own profile'}), 403
        
        try:
            data = request.get_json()
            
            # Validate email format
            if not data.get('email') or '@' not in data['email']:
                return jsonify({'success': False, 'error': 'Invalid email format'}), 400
            
            # Check if email is taken by another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.username != username:
                return jsonify({'success': False, 'error': 'Email already in use'}), 400
            
            current_user.email = data['email']
            current_user.first_name = data.get('first_name')
            current_user.last_name = data.get('last_name')
            
            db.session.commit()
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/admin/users/<username>/change-password', methods=['POST'])
    @login_required
    def admin_change_password(username):
        if not current_user.is_administrator():
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        if username == current_user.username:
            return jsonify({'success': False, 'error': 'Use profile settings to change your own password'}), 400
        
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        try:
            data = request.get_json()
            new_password = data.get('new_password')
            
            if not new_password or len(new_password) < 6:
                return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
            
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/tasks/<int:task_id>', methods=['GET', 'POST'])
    @login_required
    def task_detail(task_id):
        task = Task.query.get_or_404(task_id)
        project = task.project
        
        # Check if user has access to this task
        if not (current_user.is_administrator() or 
                project.owner_id == current_user.id or 
                current_user in project.members or 
                task.assigned_to_id == current_user.id):
            flash('You do not have permission to view this task.', 'error')
            return redirect(url_for('view_project', project_id=project.id))
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'submit':
                submission_url = request.form.get('submission_url')
                # Validate URL if provided
                if submission_url:
                    try:
                        result = urlparse(submission_url)
                        if not all([result.scheme, result.netloc]):
                            flash('Invalid URL format. Please include http:// or https://', 'error')
                            return redirect(url_for('task_detail', task_id=task_id))
                    except ValueError:
                        flash('Invalid URL format', 'error')
                        return redirect(url_for('task_detail', task_id=task_id))
                
                # Create new submission
                new_submission = Submission(
                    task_id=task_id,
                    submission_text=request.form.get('submission_text'),
                    submission_url=submission_url,
                    submitted_by_id=current_user.id
                )
                db.session.add(new_submission)
                flash('Submission saved successfully!', 'success')
                
            elif action == 'feedback' and (current_user.is_administrator() or project.owner_id == current_user.id):
                # Create new feedback
                new_feedback = Feedback(
                    task_id=task_id,
                    feedback_text=request.form.get('feedback'),
                    feedback_by_id=current_user.id
                )
                db.session.add(new_feedback)
                flash('Feedback provided successfully!', 'success')
                
            elif action == 'notes':
                task.notes = request.form.get('notes')
                flash('Notes updated successfully!', 'success')
                
            db.session.commit()
            return redirect(url_for('task_detail', task_id=task_id))
        
        # Get submissions and feedback ordered by date
        submissions = Submission.query.filter_by(task_id=task_id).order_by(Submission.submission_date.desc()).all()
        feedback_entries = Feedback.query.filter_by(task_id=task_id).order_by(Feedback.feedback_date.desc()).all()
        
        return render_template('task_detail.html', 
                             task=task, 
                             submissions=submissions,
                             feedback_entries=feedback_entries)