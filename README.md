# ContractCommand

**Defense Contract & Procurement Management System**

## Overview

ContractCommand is a Django-based application for managing procurement planning, vendor qualification, vendor evaluation, contract lifecycles, invoices, payments, and executive reporting.

## Key Features

- Role-based access control
- Procurement plan creation and tracking
- Vendor qualification and management
- Vendor evaluation with weighted scoring
- Contract lifecycle management
- Invoice review and payment tracking
- Executive dashboard and financial summaries
- CSV exports for contracts and invoices

## Technology Stack

- Python
- Django
- PostgreSQL (if configured for the project)
- HTML, CSS, and Django templates
- Git for version control

## Local Setup

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies from `requirements.txt`.
4. Configure environment variables and database credentials.
5. Apply migrations with `python manage.py migrate`.
6. Create an administrator using `python manage.py createsuperuser`.
7. Start the development server with `python manage.py runserver`.

## Testing

Run the Django configuration check:

`python manage.py check`

Run automated tests:

`python manage.py test`

## Security Notes

Keep secrets and database credentials out of version control. Use production-appropriate security settings before deployment.

## Project Status

Deployment status and CI/CD configuration should be documented after they have been verified.
