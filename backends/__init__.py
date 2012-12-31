import logging

import settings

log = logging.getLogger("user_daemon")

class NonRetryableException(Exception): pass


class Backend(object):
    def tick(self):
        """
        Invoked every cycle by the main loop, whether there are any
        dirty users or not.
        """
        pass

    def process_user(self, user):
        """
        Invoked for each dirty user. Implementations should be idempotent and
        raise exceptions on errors. If no exception is raised, the backend is
        assumed to have successfully updated its user store and the next backend
        in the chain is invoked.
        """
        raise NotImplementedError

    def __str__(self):
        return self.__class__.__name__


class UserBackend(Backend):
    def fetch_backend_user(self, username):
        """
        Fetch user object from backend store, None if non-existent. The
        returned backend user object is passed back into user_mod and
        user_del.
        """
        raise NotImplementedError()

    def user_add(self, user):
        raise NotImplementedError()

    def user_mod(self, backend_user, user):
        raise NotImplementedError()

    def user_del(self, backend_user, user):
        raise NotImplementedError()

    def process_user(self, user):
        username = user["username"]

        log.info("Processing user %s in backend %s", username, self.__class__.__name__)

        # Fetch user_info
        backend_user = self.fetch_backend_user(user["username"])
        
        # If the user does not exist
        if backend_user is None:
            log.info("User does not exists")

            if user["status"] in (settings.ACTIVE_USER, settings.WCLOSURE_USER):
                backend_user = self.user_add(user)

            elif user["status"] == settings.INACTIVE_USER:
                log.info("User does not exist in backend, but is marked inactive. Skipping creation.")

            elif user["status"] == settings.DELETED_USER:
                pass

        # User does exist
        else:
            log.info("User exists")

            if user["status"] in (settings.ACTIVE_USER, settings.WCLOSURE_USER, settings.INACTIVE_USER):
                self.user_mod(backend_user, user)

            elif user["status"] == settings.DELETED_USER:
                self.user_del(backend_user)

        log.info("Done processing user %s in backend %s", username, self.__class__.__name__)
