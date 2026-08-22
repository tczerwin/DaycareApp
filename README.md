# Daycare Management App

A Flask web application for managing daycare attendance, check-ins/check-outs, and child information.

## Features

- **Check-in/Check-out Tracking** — Record arrival and departure times for children
- **Child Profiles** — Store child names, photos, parent contact info, and special notes
- **Photo Management** — Upload and display child photos with automatic image display
- **Allergy Alerts** — Visual badge (!) on photos for children with allergies or special needs
- **Search & Autocomplete** — Quick search for children or parents
- **Daily Statistics** — View total children, current attendance, average time spent
- **Attendance Export** — Generate PDF reports with daily attendance summary
- **Parent Contacts** — View all unique children with parent contact information
- **Responsive Design** — Works on desktop and mobile devices
- **Dark Mode** — Toggle between light and dark themes

## Tech Stack

- **Backend:** Flask 2.3.0, SQLAlchemy ORM
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript
- **PDF Generation:** ReportLab
- **Deployment:** PythonAnywhere (free tier compatible)

## Installation

### Requirements
- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/tczerwin/DaycareApp.git
cd DaycareApp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create the database:
```bash
python create_db.py
```

4. Run the application:
```bash
python main.py
```

5. Open your browser and go to `http://localhost:8000`

## Usage

### Adding a Child
1. Click **"+ New Child"** button
2. Enter child's name, parent info, upload photo (optional), add notes (allergies, medications)
3. Click **"Add Child"** — child is now registered in the system

### Checking In
1. On the main page, type the child's name in the search box
2. Click **"Check In Child"** — records arrival time
3. Child appears in the main table with their photo and check-in time

### Checking Out
1. Click **"Check Out"** button next to the child's name
2. Departure time is recorded automatically
3. Child is removed from the active list

### Viewing Details
- Click on a child's row in the table to see full details
- View parent contact info, check-in/out times, notes, and allergies
- Edit or check out from the detail page

### Exporting Attendance
- Click **"📥 Export Day to PDF"** to generate daily attendance report
- Includes all children checked in that day with times and status
- Displays notes/allergies section

### Parent Contacts
- Click **"📞 Parent Contacts"** to view all registered parents
- Clickable phone numbers for quick calling


## Database Schema

**Child Model:**
- `id` — Primary key
- `name` — Child's name (required)
- `image` — Photo filename (optional)
- `parent_name` — Parent/guardian name
- `parent_phone` — Contact phone number
- `notes` — Allergies, medications, special instructions
- `arrived` — Check-in timestamp (nullable)
- `departed` — Check-out timestamp (nullable)

## Routes

- `GET /` — Main dashboard with checked-in children
- `POST /` — Check in a child
- `/add-child` — Add new child form
- `/child/<id>` — View child details
- `/update/<id>` — Edit child information
- `/delete/<id>` — Check out a child
- `/parents` — List all parent contacts
- `/export-pdf` — Generate attendance PDF
- `/api/child-info/<name>` — Get child info (for autocomplete)

## Deployment

### PythonAnywhere

1. Create account at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Upload project files via Git or web upload
3. Create virtual environment and install dependencies
4. Configure Web app settings:
   - Python version: 3.8+
   - WSGI config: Point to Flask app
   - Static files: Map `/static/` to `/home/username/DaycareApp/static/`
5. Reload web app

**Note:** Database and images persist in the `instance/` and `static/img/` folders.

## Features in Progress

- [ ] File upload debug (images not saving on PythonAnywhere)
- [ ] Dynamic image display (currently hardcoded for specific children)
- [ ] Export to CSV
- [ ] Email notifications for parents
- [ ] Mobile app

## Author

Taylor Czerwinski
