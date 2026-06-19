# 🏘️ Community Property Management System

A full-featured Django web application for managing community properties, announcements, fees, parking, and social messaging.

## Features
- Property CRUD (managers only)
- Announcement board with emergency highlighting
- Fee management with payment tracking
- Parking spot allocation
- Resident registration and login
- Friend system (add/accept/reject)
- Private 1-on-1 chat (messenger style)
- User profiles with bio and picture

## Setup Instructions
1. Clone the repo:  
   `git clone https://github.com/shiyam5656/community-management-system.git`
2. Create virtual environment:  
   `python -m venv venv`
3. Activate it:  
   - Windows: `venv\Scripts\activate`  
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies:  
   `pip install -r requirements.txt`
5. Run migrations:  
   `python manage.py makemigrations`  
   `python manage.py migrate`
6. Create a superuser:  
   `python manage.py createsuperuser`
7. Run the server:  
   `python manage.py runserver`
8. Visit `http://127.0.0.1:8000`

## Default Roles
- **Manager** (staff) – full management access.
- **Resident** – view property, fees, announcements, chat.

## Tech Stack
- Django 6.0
- SQLite (default)
- Bootstrap 5
- Font Awesome Icons
