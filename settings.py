import os.path

try:
    from settings_prod import *
except ImportError:
    from settings_dev import *

POLL_INTERVAL_SEC = 60
POLL_ALERT_THRESHOLD = 5

# How long to sleep when we hit a non-retryable error, for example
# if a kerberos ticket has expired
NON_RETRYABLE_ERROR_SLEEP_SEC = 3600

# User statuses. This should eventually be serialized as a string.
ACTIVE_USER   = 1
WCLOSURE_USER = 2
INACTIVE_USER = 3
DELETED_USER  = 4

SMTP_TO = "admin+user_daemon@mr.is"
SMTP_FROM = "admin@mr.is"

# Backends
# Contract: The backend's processing should be idempotent. Backends
# are invoked in the order defined below, and may make the assumption
# that previous backends successfully processed the user entry.
# Backend operations are not atomic, and they make the assumption that
# nothing else is changing state in the underlying storage. For example,
# backends may read a user's status, modify and overwrite, and assume
# that no other process has changed state in the mean time.

BACKENDS = [
    'backends.ipa.IpaBackend',
    'backends.google.GoogleBackend',
    'backends.storage.HomeBackend',
]


LOGGING = {
    'version': 1,
    'filters': {
        'require_debug_false': {
            '()': 'utils.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'utils.RequireDebugTrue',
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)-8.8s %(asctime)s %(name)-20.20s msg:%(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false', ], 
            'class': 'logging.handlers.SMTPHandler',
            'mailhost': SMTP_HOST,
            'fromaddr': SMTP_FROM,
            'toaddrs':  SMTP_TO,
            'subject':  "Stjornbord update daemon error",
        },
        'console': {
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['require_debug_true'],
        },
        'file_handler': {
            'level':'DEBUG',
            'class':'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOGGING_ROOT, 'update_daemon.log'),
            'when': 'w0', # weekly
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'user_daemon': {
            'handlers': ['mail_admins', 'file_handler', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'ipaapi': {
            'handlers': ['mail_admins', 'file_handler', 'console'],
            'propagate': False,
            'level': 'DEBUG',

        },
        'googleapi': {
            'handlers': ['mail_admins', 'file_handler', 'console'],
            'propagate': False,
            'level': 'DEBUG',
        },
    }
}
