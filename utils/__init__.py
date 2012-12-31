import logging
import settings

# Filters to aid with logging, borrowed from django.util.log
class RequireDebugFalse(logging.Filter):
    def filter(self, record):
        return not settings.DEBUG

class RequireDebugTrue(logging.Filter):
    def filter(self, record):
        return settings.DEBUG