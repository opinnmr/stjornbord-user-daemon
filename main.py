#!/usr/bin/python
# coding: utf-8

import logging
import urllib
import urllib2
import time
import os.path
import simplejson
import sys

import settings
import backends
import utils.dictconfig

POST_SYNC_SECRET = SYNC_SECRET = urllib.urlencode((("secret", settings.SYNC_SECRET),)) 

def init_logging():
    """
    Set up logging, see config in the settings module
    """
    utils.dictconfig.dictConfig(settings.LOGGING)

    return logging.getLogger("user_daemon")

def init_backends():
    """
    Import backends, logic borrowed from Django.
    """
    my_backends = []
    # Logic borrowed from django.middleware.base
    for backend_path in settings.BACKENDS:
        module, classname = backend_path.rsplit('.', 1)
        try:
            # Extract, since Python 2.6 doesn't include importlib
            __import__(module)
            mod = sys.modules[module]
        except ImportError, e:
            raise RuntimeError('Error importing backend %s: "%s"' % (module, e))
        try:
            klass = getattr(mod, classname)
        except AttributeError:
            raise RuntimeError('Backend module "%s" does not define a "%s" class' % (module, classname))

        my_backends.append(klass())

    return my_backends

def poll(my_backends):
    """
    Fetch a list of dirty users and pipe them through processing backends.
    """

    # Tick all backends. This gives them a chance to do background work.
    for backend in my_backends:
        backend.tick()

    # Fetch a list of dirty users
    log.debug("Polling dirty users from %s", settings.DIRTY_USERS)
    fp = urllib2.urlopen(settings.DIRTY_USERS, POST_SYNC_SECRET)
    dirty = simplejson.load(fp)
    fp.close()

    # Iterate through users and process
    processed = 0
    for user in dirty:
        log.info("Processing user %s", user["username"])
        try:
            for backend in my_backends:
                backend.process_user(user)
        except Exception, e:
            log.exception("Could not process user %s", user["username"])
            continue
        
        clear_dirtybit(user)
        processed += 1

    return processed


def clear_dirtybit(user):
    """
    Connect to Stjornbord and clear the user's dirty bit. The clearing condition
    is that the dirty timestamp is the same.
    """
    query = urllib2.urlopen(settings.CLEAN_DIRTY % (user["username"], user["dirty"]), POST_SYNC_SECRET)
    http_code = query.getcode()
    if http_code == 200:
        log.info("Successfully cleared dirtybit for %s (%s)", user["username"], user["dirty"])
    else:
        log.warning("Failed to clear dirtybit for %s (%s). Return code: %s", user["username"], user["dirty"], http_code)


def main():
    log.info("Starting up!")
    
    poll_failures = 0
    my_backends = init_backends()

    while True:
        processed = 0
        try:
            processed = poll(my_backends)
            poll_failures = 0

        except urllib2.URLError, e:
            poll_failures += 1
            log.warn("Fetch failure, reason: %s. Will throw an exception after %d failures.",
                e, settings.POLL_ALERT_THRESHOLD)

            if poll_failures % settings.POLL_ALERT_THRESHOLD == 0:
                log.exception("Error fetching data from %s. Failures: %d", settings.DIRTY_USERS, poll_failures)

        except backends.NonRetryableException, e:
            t = settings.NON_RETRYABLE_ERROR_SLEEP_SEC
            log.exception("Non retryable exception raised, going to sleep for %d seconds", t)
            time.sleep(t)

        except Exception, e:
            log.exception("Uncaught exception while processing dirty users")

        if processed == 0:
            log.debug("Didn't process any records, sleeping for %d seconds", settings.POLL_INTERVAL_SEC)
            time.sleep(settings.POLL_INTERVAL_SEC)


if __name__ == "__main__":
    log = init_logging()
    main()