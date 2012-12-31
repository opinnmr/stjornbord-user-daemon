#!/usr/bin/python
# coding: utf-8

import logging
import hashlib
import random

import settings
import backends
import apis.google

log = logging.getLogger("user_daemon.google")

class GoogleBackend(backends.UserBackend):
    def __init__(self):
        self.g_api = apis.google.get_api(settings.GOOGLE_API_USER, settings.GOOGLE_API_PASS,
            settings.GOOGLE_TMP_DIR, debug=settings.DEBUG)


    def tick(self):
        # Clear the Google apps session, just to make sure we
        # eventually flush Google apps token.
        self.g_api.disconnect()


    def fetch_backend_user(self, username):
        log.info("Querying for user %s", username)
        return self.g_api.user_get(username)


    def user_add(self, user):
        log.info("Creating user %s", user["username"])

        tmppass = user["tmppass"]
        if not tmppass:
            log.error("Creating user, but tmppass empty! Setting rubbish temporary password.")
            tmppass = "".join([random.choice(string.letters) for x in range(32)])
    
    
        return self.g_api.user_add(
            user["username"],
            user["first_name"],
            user["last_name"],
            self._gapps_sha1_password(tmppass),
            suspended=self._is_suspended_str(user),
        )
    
    
    def user_mod(self, gapps_user, user):
        log.info("Updating user %s", user["username"])
        
        gapps_user.name.family_name = user["last_name"]
        gapps_user.name.given_name  = user["first_name"]
        gapps_user.login.suspended  = self._is_suspended_str(user)
    
        if user["tmppass"]:
            log.info("Updating password for %s", user["username"])
            gapps_user.login.password = self._gapps_sha1_password(user["tmppass"])
            gapps_user.login.hash_function_name = 'SHA-1'
    
        return self.g_api.user_mod(user["username"], gapps_user)
    
    
    def user_del(self, backend_user, user):
        log.error("Don't know how to delete users yet!")
        raise NotImplemented()


    def _gapps_sha1_password(self, password):
        return hashlib.sha1(password.encode("utf8")).hexdigest()


    def _is_suspended_str(self, user):
        if user["status"] in (settings.ACTIVE_USER, settings.WCLOSURE_USER):
            return "false"
        return "true"

