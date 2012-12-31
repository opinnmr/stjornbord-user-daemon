# Tells backends to use mock APIs
DEBUG = True

# URLs 
DIRTY_USERS = "http://127.0.0.1:8000/dirty/users/"
CLEAN_DIRTY = "http://127.0.0.1:8000/clean/user/%s/%s/"

# Same as in Stjornbord's settings
SYNC_SECRET = "devsecret123"

LOGGING_ROOT = "/tmp/"
SMTP_HOST    = "ASPMX.L.GOOGLE.COM"


# Google specific settings
GOOGLE_TMP_DIR  = "/tmp"
GOOGLE_API_USER = "adminuser@example.com"
GOOGLE_API_PASS = "secret"

# IPA
IPA_LDAP_PASS = "secret"