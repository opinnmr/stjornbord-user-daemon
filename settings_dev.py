import os.path

# Tells backends to use mock APIs
DEBUG = True

# URLs 
DIRTY_USERS = "http://127.0.0.1:8000/dirty/users/"
CLEAN_DIRTY = "http://127.0.0.1:8000/clean/user/%s/%s/"

# Same as in Stjornbord's settings
SYNC_SECRET = "devsecret123"

LOGGING_ROOT = "/tmp/"
# sudo python -m smtpd -n -c DebuggingServer localhost:25
SMTP_HOST    = "localhost"


# Google specific settings
GOOGLE_TOKEN   = "/tmp/tokens.dat"
GOOGLE_SECRETS = os.path.join(os.path.dirname(__file__), "client_secrets.json")

# IPA
IPA_LDAP_PASS = "secret"