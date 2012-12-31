#!/usr/bin/python
# coding: utf-8

import logging
import time
import subprocess
import datetime

import settings
import backends
import apis.ipa

log = logging.getLogger("user_daemon.ipa")

# IPA constants
IPA_DEFAULT_GROUPS = [u"ipausers", ]

RENEW_TICKET_EVERY_SEC    = 60 * 60
SEND_WARN_EMAIL_EVERY_SEC = 3600

class IpaBackend(backends.UserBackend):
    def __init__(self):
        self.last_ticket_renew = None

        self.ipa_api = apis.ipa.get_api("stjornbord", settings.IPA_LDAP_PASS,
            debug=settings.DEBUG)


    def tick(self):
        self._renew_ticket()

    def process_user(self, user):
        # Wrap parent's process_user call to catch a ticket expired exception.
        try:
            backends.UserBackend.process_user(self, user)
        except apis.ipa.IpaTicketExpired, e:
            self.kerberos_warn()


    def fetch_backend_user(self, username):
        # Fetch user_info
        log.info("Querying user %s", username)
        return self.ipa_api.user_get(username)
        
    
    def user_add(self, user):
        log.info("Creating user %s", user["username"])

        backend_user = self.ipa_api.user_add(user["username"], enabled=self._is_enabled(user),
            givenname=user["first_name"], sn=user["last_name"],
            uidnumber=user["posix_uid"], gidnumber=user["posix_uid"])

        if backend_user:
            self.ipa_api.update_password(user["username"], user["tmppass"])

        return backend_user


    def user_mod(self, backend_user, user):
        log.info("Updating user %s", user["username"])


        self.ipa_api.user_mod(user["username"], backend_user,
            enabled=self._is_enabled(user),
            givenname=user["first_name"], sn=user["last_name"])
        self.ipa_api.update_password(user["username"], user["tmppass"])

    def delete_user(self, backend_user, user):
        log.error("Don't know how to delete users yet!")
        raise NotImplemented()
    
    def _is_enabled(self, user):
        if user["status"] in (settings.ACTIVE_USER, settings.WCLOSURE_USER):
            return True
        return False

    def _renew_ticket(self):
        if settings.DEBUG:
            return

        now = datetime.datetime.now()
        if (self.last_ticket_renew is None or
              (now - self.last_ticket_renew).seconds > RENEW_TICKET_EVERY_SEC):
            p = subprocess.Popen(["kinit", "-R"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            ret = p.wait()
            log.debug("   kinit renew ret=%s, output: %s", ret, p.stdout.read().strip())
            if ret == 0:
                self.last_ticket_renew = now
            else:
                self.kerberos_warn()

    def kerberos_warn(self):
        raise backends.NonRetryableException("""Kerberos ticket runninn út!

Kerberos ticket á auth.mr.lan er:
 1) Runninn út eða
 2) Ekki renew-able

Vinsamlegast tengu þig inn á auth.mr.lan sem rót og keyrðu:
  # kinit -l 30d -r 30w admin@MR.LAN

Þangað til virkar ekki sync milli Stjórnborðs, IPA og Google.

Ég held áfram að reyna og sendi annan póst eftir klukkutíma ef
ekkert gengur.

Kveðja,
Stjórnborðið
""")