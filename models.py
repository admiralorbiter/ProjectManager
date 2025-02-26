# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from flask_login import UserMixin

db = SQLAlchemy()

# Association table for Project-User many-to-many relationship
project_users = db.Table('project_users',
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role', db.String(50), default='member')  # e.g., 'owner', 'member', 'viewer'
)

# User model
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='user')  # 'admin', 'user'
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    owned_projects = db.relationship('Project', backref='owner', lazy=True)
    member_of_projects = db.relationship('Project', 
                                       secondary=project_users,
                                       backref=db.backref('members', lazy='dynamic'),
                                       lazy='dynamic')
    
    # Helper methods for role checking
    def is_administrator(self):
        return self.is_admin
    
    def has_role(self, role):
        return self.role == role

class Project(db.Model):
    __tablename__ = 'projects'
    
    VALID_STATUSES = ['active', 'completed', 'on_hold', 'archived']
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # Changed back to status
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    due_date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # New fields
    github_url = db.Column(db.String(500))
    document_url = db.Column(db.String(500))
    features = db.Column(db.JSON, default=list)
    project_url = db.Column(db.String(500))
    
    # Relationships
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')

    def __setattr__(self, name, value):
        """Validate status before setting it"""
        if name == 'status' and value not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.VALID_STATUSES)}")
        super().__setattr__(name, value)

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')  # open, in_progress, completed, blocked
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    is_completed = db.Column(db.Boolean, default=False)  
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Foreign Keys
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    subtasks = db.relationship('Task', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    # New fields for enhanced features
    notes = db.Column(db.Text)
    
    # Add new relationships for feedback and submissions
    feedback = db.relationship('Feedback', back_populates='task', cascade='all, delete-orphan')
    submissions = db.relationship('Submission', back_populates='task', cascade='all, delete-orphan')

class Feedback(db.Model):
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    feedback_text = db.Column(db.Text, nullable=False)
    feedback_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    feedback_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    task = db.relationship('Task', back_populates='feedback')
    feedback_by = db.relationship('User')

class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    submission_text = db.Column(db.Text)
    submission_url = db.Column(db.String(500))
    submission_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    task = db.relationship('Task', back_populates='submissions')
    submitted_by = db.relationship('User')