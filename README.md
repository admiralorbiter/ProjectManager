# ProjectManager: Documentation

This document provides an overview of the **ProjectManager** application, outlines its project structure, core technologies, available features, known limitations, and possible future enhancements. It is designed to be easily copied and adapted as needed.

---

## Project Documentation

### 1. Project Overview
**ProjectManager** is a Flask-based web application for managing projects and tasks. It includes a robust user authentication system, role-based user management (including admin privileges), and a hierarchical task management setup. The app is designed to help teams or individuals:

- Create and track projects.
- Organize tasks (including subtasks).
- Assign tasks to users.
- Monitor statuses and due dates.
- Manage user profiles and permissions.

### 2. Project Structure
The repository is organized into a standard Flask project layout:
```
PROJECTMANAGER/
├── __pycache__/
├── instance/
├── your_database.db
├── static/
│   └── css/
│       ├── admin.css
│       ├── create_project.css
│       ├── index.css
│       ├── login.css
│       ├── profile.css
│       ├── projects.css
│       ├── style.css
│       └── view_project.css
├── templates/
│   ├── admin/
│   │   └── users.html
│   ├── base.html
│   ├── create_project.html
│   ├── edit_project.html
│   ├── index.html
│   ├── login.html
│   ├── nav.html
│   ├── profile.html
│   ├── projects.html
│   └── view_project.html
├── tests/
│   └── test_models.py
├── .gitignore
├── app.py
├── config.py
├── conftest.py
├── create_admin.py
├── create_jonlane.py
├── features.md
├── forms.py
├── models.py
├── README.md
├── requirements.txt
└── routes.py
```
- **`PROJECTMANAGER/`**  
  The root folder containing the entire Flask application.  
  - Includes subfolders like `static/`, `templates/`, `tests/`, and the SQLite database file (`your_database.db`).
  - Contains various utility and config files (`config.py`, `conftest.py`, `forms.py`, etc.).

- **`app.py`**  
  The main entry point for the Flask application. This is where the Flask app is initialized and run.

- **`routes.py`**  
  Defines the route logic (endpoints) for the Flask app, handling how users interact with different pages and functionalities.

- **`models.py`**  
  Contains the SQLAlchemy model definitions and database schema logic. Uses **Flask-SQLAlchemy** for ORM functionality, making it easier to work with SQLite (or other databases if configured).

- **`requirements.txt`**  
  Lists the Python dependencies needed to run the project (e.g., Flask, Flask-SQLAlchemy, etc.).

### 3. Project Technologies
- **Language:** Python 3.x  
- **Framework:** Flask  
- **Database:** SQLite (using **Flask-SQLAlchemy** for ORM)  
- **Front-End:** HTML, CSS, JavaScript, and Bootstrap for styling  
- **Other:**  
  - Flask’s built-in development server (or a WSGI server in production)  
  - Config files (`config.py`) and additional scripts (`create_admin.py`) for setup and maintenance  

### 4. Project Features

For a detailed list of current, planned, and completed features, please see [features.md](features.md).

A high-level overview of the main features includes:
- User Authentication System with role-based management
- Comprehensive Project Management
- Hierarchical Task Management
- User Profile Management
- Admin Features
- Technical Features

### 5. Project Limitations
- **Testing Coverage**: Although there is a placeholder for tests (`tests.py`), unit testing is not fully implemented.  
- **Deployment Configuration**: No Docker configuration or production-ready settings are included by default.  
- **Scalability & Performance**: Suitable for smaller teams or single-users as-is. Large enterprise-scale usage would require further optimization and testing.  

### 6. Project Future Development
Here are some potential avenues to grow or improve **ProjectManager**:

1. **Unit Test Implementation**  
   - Add comprehensive tests for models, views, and forms.  
   - Integrate CI/CD pipeline (e.g., GitHub Actions) to automate test runs.

2. **Refined Authorization**  
   - Implement more granular permission systems (e.g., only project owners can edit tasks).

3. **Enhanced UI/UX**  
   - Incorporate a frontend framework like Bootstrap or Tailwind CSS.  
   - Use HTMX for a  single-page app approach for a more dynamic interface.

4. **Notifications & Reminders**  
   - Email or in-app notifications for upcoming due dates or project updates.  
   - Calendar/scheduling integration.

5. **Deployment & Scalability**  
   - Containerize the app with Docker for easier deployment.  
   - Configure a production database (e.g., PostgreSQL) and environment variables for secrets.

---

### How to Use (Quick Start)

1. **Clone the repository**  
   ```bash
   git clone https://github.com/admiralorbiter/ProjectManager.git
   cd ProjectManager
   ```


2. **Install Dependencies**  
```bash
pip install -r requirements.txt
```

3. **Setup Database**  
To set up the database for the first time, run:

```bash
python app.py
```

4. **Setup Admin**  

To create a superuser for accessing the Django admin interface, run:

```bash
python create_admin.py
```
5. ** Access the Application**  

Visit http://127.0.0.1:5000/ in your browser.

Note: For production use, ensure you set the appropriate environment variables, turn off DEBUG in settings.py, and secure your secret keys.

### Testing

The project uses pytest for testing. The test suite includes:
- Unit tests for models
- Integration tests for routes
- Authentication testing
- Database operations testing

#### Running Tests

1. **Setup Test Environment**
```bash
pip install pytest
pip install pytest-cov  # for coverage reports
```

2. **Run All Tests**
```bash
pytest
```

3. **Run Tests with Coverage Report**
```bash
pytest --cov=.
```

4. **Run Specific Test Files**
```bash
pytest tests/test_routes.py  # Run route tests
pytest tests/test_models.py  # Run model tests
```

#### Test Structure
- `conftest.py`: Contains pytest fixtures and test configuration
- `tests/test_routes.py`: Tests for route functionality and API endpoints
- `tests/test_models.py`: Tests for database models and relationships

#### Key Testing Features
- Uses in-memory SQLite database for testing
- Separate test configuration in `config.py`
- Fixtures for common test scenarios:
  - Test users (admin and regular)
  - Test projects
  - Test tasks
- Comprehensive API endpoint testing
- Database operation verification
- Authentication and authorization testing

#### Writing New Tests
When adding new features, ensure to:
1. Create corresponding test cases
2. Use existing fixtures where applicable
3. Follow the established pattern for similar functionality
4. Include both positive and negative test cases
5. Test edge cases and error conditions