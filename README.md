# Kasaragod AGS Suppliers - Django gas agency website (Dealer code 41002905)

## Run
    python -m venv venv
    venv\Scripts\activate          (Windows)    or    source venv/bin/activate  (Mac/Linux)
    pip install -r requirements.txt
    python manage.py makemigrations gas
    python manage.py migrate
    python manage.py loaddata cylinders      # sample cylinders; edit prices in admin
    python manage.py createsuperuser
    python manage.py runserver
Site: http://127.0.0.1:8000/   Admin (bookings, prices): http://127.0.0.1:8000/admin/

## Customise
- Phone, WhatsApp, email, address, hours: AGENCY dict in config/settings.py
- Colours/fonts: static/css/style.css (variables at top)
- Logo: static/img/logo.svg
- Before going live: DEBUG=False, new SECRET_KEY, your domain in ALLOWED_HOSTS, run collectstatic.
