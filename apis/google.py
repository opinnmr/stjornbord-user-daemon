import datetime
import cPickle
import os
import logging

try:
    import stjornbord_google_api
    imported = True
except ImportError:
    imported = False

log = logging.getLogger("googleapi")

class GoogleException(Exception): pass

# This is a really weird way of setting up mocks. I believe the
# intent (way back when) was to do manual integration testing
# between the Stjornbord Django app and this user daemon. In
# any case, this is weird, proper tests should be written.

def get_api(*args, **kwargs):
    """
    API factory, returns mock if `debug` is set.
    """
    if kwargs.pop("debug", True):
        return GoogleMock()
    else:
        assert imported, "Failed importing gdata libraries"
        return stjornbord_google_api.Google(*args, **kwargs)


# Used for mocking user objects
class Bunch(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class GoogleMock(object):
    def __init__(self):
        pass

    def disconnect(self):
        log.info("GoogleMock: disconnect")

    def user_add(self, username, first_name, last_name, password,
            suspended='false', password_hash_function="SHA-1"):
        log.info("GoogleMock: user_add: username=%s, first_name=%s, last_name=%s "
            "password-hash=%d suspended=%s password_hash_function=%s", username, first_name,
            last_name, password, suspended, password_hash_function)
        return self.user_get(username)

    def user_get(self, username):
        log.info("GoogleMock: user_get: username=%s", username)
        return Bunch(
            name=Bunch(given_name="Mock", family_name="Swift"),
            login=Bunch(suspended="false", password="asdf", hash_function_name="SHA-1"),
            )

    def user_mod(self, username, backend_user):
        log.info("GoogleMock: user_mod: username=%s backend_user=%s", username, backend_user)
        pass

    def list_sync(self, name, members):
        log.info("GoogleMock: list_sync: name=%s members=%s", name, members)
        return

    def list_members(self, name):
        log.info("GoogleMock: list_members: name=%s", name)
        return ['fake.google.test.user%d' % i for i in range(3)]
