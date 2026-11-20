# Hotel Management System

A comprehensive hotel management system built with Flask for front desk operations, management, and HR.

## Features

- **Multi-level Access Control**: Front Desk Agent, General Manager, HR Manager
- **Room Management**: Visual floor maps with dynamic pricing
- **Guest Profiles**: Track guest history and notes
- **Staff Scheduling**: Manager-controlled duty assignments
- **Dynamic Pricing**: Competitive rates based on third-party platforms

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Access the application at `http://localhost:5000`

## Project Structure

```
Hotel/
├── app.py              # Main Flask application
├── templates/          # HTML templates
│   └── index.html     # Landing page
├── static/            # Static files
│   ├── css/
│   │   └── style.css  # Styles
│   └── js/            # JavaScript files
└── requirements.txt   # Python dependencies
```

## Next Steps

- Implement authentication system
- Create database models
- Build role-based dashboards
- Implement room management features
