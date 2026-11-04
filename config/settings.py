from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "change-this-secret-key-before-going-live"
DEBUG = True  # set False in production
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "gas",
    "accounts",
    "shop",
     "carousel",
      "connection",
       "dashboard",
         "notices.apps.NoticesConfig",
         "consumers",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "gas.context.agency",
        "accounts.utils.role_context",
                "notices.context.unread",
        "shop.context.cart_count",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_TZ = True
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- EDIT YOUR AGENCY DETAILS HERE ----
AGENCY = {
    "name": "Kasaragod gas Suppliers",
    "dealer_code": "41002905",
    "phone": "+91 75919 11975",
    "whatsapp": "917591911975",   # country code + number, no + or spaces
    "email": "sales.kgshp@gmail.com",
    "address": "Kasaragod, Kerala, India",
    "hours": "Mon-Sat 9:00 AM - 6:00 PM",
}
# ---- Authentication ----
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "home"


# ---- Shop: product photos ----
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---- Shop: Razorpay online payment (leave empty to allow only cash on delivery) ----
import os
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_Tm9xDGYcXxyeIe")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "XrzD9XU8edoEh8QI9NerUe27")

# ---- New connection: private folder for Aadhaar and photos (not publicly served) ----
PRIVATE_MEDIA_ROOT = BASE_DIR / "private_media"


# ---- Auto logout after 3 minutes without activity ----
SESSION_COOKIE_AGE = 180            # 3 minutes, in seconds
SESSION_SAVE_EVERY_REQUEST = True   # every request restarts the 3 minutes
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# ---- Notifications by email ----
# Prints emails in the terminal while testing. For real emails, see the note at the end.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "Kasaragod gas Suppliers <noreply@example.com>"