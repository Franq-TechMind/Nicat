# NICAT School Management System

Flask-based starter MVP for the Nanyuki Institute of Communication and Advanced Technology (NICAT).

## Included modules

- Authentication
- Dashboard
- Admissions
- Students
- Academics
- Finance
- Results

## Project structure

- `app/` - application package
- `app/models/` - database models
- `app/templates/` - HTML templates
- `app/static/` - CSS, JS, images
- `instance/` - SQLite database storage
- `run.py` - start the app

## Quick start

### 1. Create virtual environment

Ubuntu may require:

```bash
sudo apt install python3.12-venv
```

Then:

```bash
cd ~/Desktop/NICAT
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open:

- http://127.0.0.1:5000

## Next build steps

- Add real forms and CRUD operations
- Add authentication with password hashing
- Add role-based permissions
- Add reports and printable receipts
- Add seed data for NICAT departments and programs
