# ASHA - Disaster Relief Management System

A web-based Disaster Relief Management System developed using **Django**, **PostgreSQL**, and **MongoDB** to improve emergency response coordination between victims, volunteers, and administrators.

The system provides a centralized platform for managing disaster relief requests, volunteer assignments, real-time status tracking, and emergency alerts.

---

## Features

### Victim Module
- User Registration and Login
- Raise Emergency Requests
- Submit request description and location
- Track request status

### Volunteer Module
- Volunteer Registration
- Admin Approval System
- View Assigned Requests
- Update Request Status
- Manage Disaster Relief Activities

### Administrator Module
- Approve Volunteers
- Manage Users
- Monitor Disaster Requests
- Raise Emergency Alerts
- Coordinate Disaster Response

---

## Technology Stack

### Backend
- Django 5.2.6
- Python 3.12

### Databases
- PostgreSQL
- MongoDB

### Frontend
- HTML
- CSS
- Bootstrap

### Containerization
- Docker
- Docker Compose

---

## Project Structure

```
ASHA-Disaster-Management
│
├── asha_project/
├── core_app/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── manage.py
└── README.md
```

---

# Running the Project using Docker (Recommended)

## Prerequisites

Install:

- Docker Desktop
- Git

---

## Clone the Repository

```bash
git clone https://github.com/gitkoustavgit/ASHA-Disaster-Management.git

cd ASHA-Disaster-Management
```

---

## Create the Environment File

Create a file named

```
.env
```

using the provided

```
.env.example
```

template.

Example:

```env
SECRET_KEY=django-insecure-change-this

DEBUG=True

POSTGRES_DB=asha_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

MONGO_DB_NAME=asha_mongodb
MONGO_HOST=localhost
MONGO_PORT=27017
```

---

## Start the Application

Run

```bash
docker compose up
```

Docker Compose will automatically:

- Pull the Django image from Docker Hub
- Download the official PostgreSQL image
- Download the official MongoDB image
- Create the required containers
- Create Docker volumes
- Apply Django migrations
- Start the application

---

## Open the Application

```
http://localhost:8000
```

---

# Creating an Administrator

To access the Django Admin Panel, create a superuser.

Open another terminal and run:

```bash
docker compose exec django python manage.py createsuperuser
```

Enter the required credentials.

Then visit:

```
http://localhost:8000/admin
```

---

# Running Without Docker (Development)

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure PostgreSQL and MongoDB

Ensure both PostgreSQL and MongoDB are installed and running locally.

Update the `.env` file accordingly.

---

## Apply Migrations

```bash
python manage.py migrate
```

---

## Create Superuser

```bash
python manage.py createsuperuser
```

---

## Run Development Server

```bash
python manage.py runserver
```

Open

```
http://127.0.0.1:8000
```

---

# Docker Images Used

## Django

Docker Hub:

```
koustavmitra18/asha:latest
```

## Official Database Images

- postgres:17
- mongo:8

---

# Project Workflow

```
Victim
    │
    ▼
Raise Request
    │
    ▼
Stored in PostgreSQL
    │
    ▼
Admin Reviews Request
    │
    ▼
Volunteer Assignment
    │
    ▼
Volunteer Updates Status
    │
    ▼
Victim Tracks Progress

Emergency Alerts
        │
        ▼
Stored in MongoDB
```