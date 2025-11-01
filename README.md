# Study Session Organizer

A Flask-based web application for organizing study sessions with intelligent partner matching, session management, analytics, and notifications.

## Features

- **Authentication**: Simple login/register system
- **Session Management**: Create, browse, join, and manage study sessions
- **Partner Finder**: Find compatible study partners based on compatibility scores
- **Dashboard**: View upcoming sessions, notifications, and quick stats
- **Analytics**: Track your study performance and patterns
- **Notifications**: Stay updated on session invites, cancellations, and reminders

## Technology Stack

- **Backend**: Flask 3.0+, Python 3.10+
- **Database**: MySQL 8.0+ with stored procedures and triggers
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript
- **Visualizations**: Chart.js

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- MySQL 8.0 or higher
- Git

### 1. Clone the Repository

```bash
cd /Users/sanidhyakumar/Downloads/study_session_code
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Database

1. Create MySQL database:
```sql
CREATE DATABASE studysessionorganizer;
```

2. Import your schema file with tables, procedures, triggers, and functions:
```bash
mysql -u root -p studysessionorganizer < database/schema.sql
```

3. Create `.env` file from template:
```bash
cp .env.example .env
```

4. Edit `.env` with your MySQL credentials:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=studysessionorganizer
SECRET_KEY=your_secret_key_here
```

### 5. Run the Application

```bash
python app.py
```

The application will be available at: `http://localhost:5000`

## Project Structure

```
study_session_organizer/
├── app.py                  # Main Flask application
├── config.py               # Configuration
├── requirements.txt        # Python dependencies
├── database/
│   ├── db_manager.py      # Database connection manager
│   └── procedures.py      # Stored procedure wrappers
├── routes/
│   ├── auth.py            # Authentication routes
│   ├── dashboard.py       # Dashboard routes
│   ├── sessions.py        # Session management
│   ├── partners.py        # Partner finder
│   ├── analytics.py       # Analytics
│   └── notifications.py   # Notifications
├── utils/
│   ├── auth_helpers.py    # Authentication decorators
│   ├── validators.py      # Input validation
│   └── formatters.py      # Data formatting
├── templates/             # HTML templates
└── static/
    ├── css/              # Stylesheets
    └── js/               # JavaScript files
```

## Database Schema

The application uses your existing MySQL schema with:
- **11 Tables**: STUDENT, STUDYSESSION, SESSIONPARTICIPANT, SUBJECT, etc.
- **5 Stored Procedures**: FindStudyPartners, CreateStudySession, JoinStudySession, etc.
- **8 Triggers**: Auto-notifications, validation, status updates
- **5 Functions**: CALCULATECOMPATIBILITY, CHECKAVAILABILITY, etc.

## Usage

1. **Register**: Create an account with your student details
2. **Login**: Sign in with email and password
3. **Browse Sessions**: View available study sessions
4. **Create Session**: Organize a new study session
5. **Find Partners**: Discover compatible study partners
6. **Join Sessions**: Participate in study sessions
7. **View Analytics**: Track your study performance

## Development

- Run in debug mode: `FLASK_ENV=development python app.py`
- Database logs are in terminal output
- Check `flask_session/` folder for session data

## Next Steps (Core Features to Add)

1. Dashboard route and UI
2. Session management (browse, create, join, detail pages)
3. Partner finder implementation
4. Notifications system
5. Analytics dashboard

## License

Educational Project - 2025
