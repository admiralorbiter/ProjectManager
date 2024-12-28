import pytest
from datetime import datetime, timezone
from models import User, Project, Task, db

@pytest.fixture
def test_user():
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash='fakehash123',
        first_name='Test',
        last_name='User',
        is_admin=False,
        role='user'
    )
    return user

def test_new_user(test_user):
    """Test creating a new user"""
    assert test_user.username == 'testuser'
    assert test_user.email == 'test@example.com'
    assert test_user.password_hash == 'fakehash123'
    assert test_user.first_name == 'Test'
    assert test_user.last_name == 'User'

def test_user_unique_constraints(test_user, app):
    """Test that unique constraints are enforced"""
    with app.app_context():
        db.session.add(test_user)
        db.session.commit()

        # Try to create another user with the same username
        duplicate_username = User(
            username='testuser',  # Same username
            email='different@example.com',
            password_hash='fakehash456'
        )

        with pytest.raises(Exception):  # SQLAlchemy will raise an error
            db.session.add(duplicate_username)
            db.session.commit()

        db.session.rollback()

        # Try to create another user with the same email
        duplicate_email = User(
            username='different',
            email='test@example.com',  # Same email
            password_hash='fakehash789'
        )

        with pytest.raises(Exception):
            db.session.add(duplicate_email)
            db.session.commit()

@pytest.fixture
def test_project(test_user):
    project = Project(
        title='Test Project',
        description='Test Description',
        owner=test_user,
        status='active',
        priority='medium',
        created_at=datetime.now(timezone.utc)
    )
    return project

def test_new_project(test_project, test_user):
    """Test creating a new project"""
    assert test_project.title == 'Test Project'
    assert test_project.description == 'Test Description'
    assert test_project.owner == test_user
    assert test_project.status == 'active'
    assert test_project.priority == 'medium'
    assert test_project.created_at is not None

@pytest.fixture
def test_task(test_project, test_user):
    task = Task(
        title='Test Task',
        description='Test Description',
        project=test_project,
        created_by=test_user,
        status='open',
        priority='medium',
        is_completed=False
    )
    return task

def test_new_task(test_task, test_project, test_user):
    """Test creating a new task"""
    assert test_task.title == 'Test Task'
    assert test_task.project == test_project
    assert test_task.created_by == test_user
    assert test_task.status == 'open'
    assert test_task.is_completed == False

def test_project_user_relationship(test_project, test_user, app):
    """Test project-user relationships"""
    with app.app_context():
        db.session.add(test_user)
        db.session.add(test_project)
        db.session.commit()
        
        # Test owner relationship
        assert test_project.owner == test_user
        assert test_user.owned_projects[0] == test_project
        
        # Test member relationship
        test_project.members.append(test_user)
        db.session.commit()
        assert test_user in test_project.members.all()
        assert test_project in test_user.member_of_projects.all()

@pytest.mark.parametrize("status", ['active', 'completed', 'on_hold', 'archived'])
def test_project_status_values(test_project, status):
    test_project.status = status
    assert test_project.status == status

def test_invalid_project_status(test_project):
    with pytest.raises(ValueError):
        test_project.status = 'invalid_status'

def test_user_role_methods(test_user):
    """Test user role checking methods"""
    # Test regular user
    assert test_user.is_administrator() == False
    assert test_user.has_role('user') == True
    assert test_user.has_role('admin') == False

    # Test admin user
    test_user.is_admin = True
    test_user.role = 'admin'
    assert test_user.is_administrator() == True
    assert test_user.has_role('admin') == True
