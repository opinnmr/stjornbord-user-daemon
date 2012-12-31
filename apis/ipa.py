import logging
import subprocess
import time
import datetime

try:
    from ipalib import api as ipa_api
    import ipalib.errors
    imported = True
except ImportError:
    imported = False

log = logging.getLogger("ipaapi")


LDAPMOD     = ["ldapmodify", "-x", "-D", "cn=Directory Manager", "-w", ]


class IpaException(Exception): pass
class IpaTicketExpired(IpaException): pass

def get_api(*args, **kwargs):
    """
    API factory, returns mock if `debug` is set.
    """
    if kwargs.pop("debug", True):
        return IpaMock()
    else:
        assert imported, "Failed importing ipa libraries"
        return Ipa(*args, **kwargs)


class Ipa(object):
    def __init__(self, context, ldap_pass):
        ipa_api.bootstrap_with_global_options(context=context)
        ipa_api.finalize()
        ipa_api.Backend.xmlclient.connect()

        self.ldap_pass = ldap_pass
        self.ldapmod = LDAPMOD + [ldap_pass, ]


    def user_get(self, username):
        try:
            return ipa_api.Command.user_show(unicode(username))["result"]
        except ipalib.errors.TicketExpired:
            raise IpaTicketExpired()
        except ipalib.errors.NotFound:
            pass

        return None


    def user_add(self, username, enabled=True, givenname=None, sn=None, cn=None, displayname=None,
            loginshell=u'/bin/bash', uidnumber=None, gidnumber=None):

        # Currently we make the assumption that we only create new users (as
        # per UserBackend.process_user. We could create users and disable them,
        # let's implement that if we ever need to..
        assert enabled, "Creating a disabled user? Enabled must be true!"

        fullname = self._format_fullname(givenname, sn)
        try:
            return ipa_api.Command.user_add(
                unicode(username),
                givenname=unicode(givenname),
                sn=unicode(sn),
                cn=fullname,
                displayname=fullname,
                loginshell=unicode(loginshell),
                uidnumber=uidnumber,
                gidnumber=gidnumber)["result"]
        except ipalib.errors.TicketExpired:
            raise IpaTicketExpired()


    def user_mod(self, username, backend_user, enabled=True,
            givenname=None, sn=None, displayname=None, cn=None):
        fullname = self._format_fullname(givenname, sn)
        try:
            ipa_api.Command.user_mod(unicode(username),
                givenname=unicode(givenname),
                sn=unicode(sn),
                displayname=fullname,
                cn=fullname)["result"]
        except ipalib.errors.TicketExpired:
            raise IpaTicketExpired()
        except ipalib.errors.EmptyModlist:
            pass

        self.update_status(username, backend_user, enabled)


    def _format_fullname(self, first, last):
        return u"%s %s" % (first, last, )


    def update_status(self, username, user, enabled):
        try:
            currently_locked  = user["nsaccountlock"]
            currently_enabled = not currently_locked
        except KeyError:
            log.warning("Got backend_user that can't be used to determine "
                "current status, user=%s", user)
            return

        if currently_enabled == enabled:
            log.debug("User status is correct (currently_enabled == enabled == %s)", currently_enabled)
            return

        if enabled:
            log.info("Enabling user %s", username)
            ipa_api.Command.user_enable(unicode(username))
        else:
            log.info("Disabling user %s", username)
            ipa_api.Command.user_disable(unicode(username))


    def update_password(self, username, password):
        """
        We have to write the password manually into LDAP to avoid
        having the password immediately expire.
    
        Note, the admin user has to be defined in passSyncManagersDNs,
        see http://freeipa.org/page/PasswordSynchronization.
        """

        if not password:
            return

        username = unicode(username)
        password = unicode(password)
    
        def _update_passwd(username, password):
            log.info("Updating password for %s" % username)
            p = subprocess.Popen(self.ldapmod, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.stdin.write("dn: uid=%s,cn=users,cn=accounts,dc=mr,dc=lan\n" % username)
            p.stdin.write("changetype:modify\n")
            p.stdin.write("replace:userpassword\n")
            p.stdin.write("userpassword:%s\n" % password)
            p.stdin.close()
            ret = p.wait()
            log.info("ldapmodify output: %s" % p.stdout.read().strip())
            return (ret == 0)
    
        def _update_exp(username):
            log.info("Updating exp for %s" % username)
            pw_exp = (datetime.datetime.now() + datetime.timedelta(days=365 * 9)).strftime("%Y%m%d")
            p = subprocess.Popen(self.ldapmod, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.stdin.write("dn: uid=%s,cn=users,cn=accounts,dc=mr,dc=lan\n" % username)
            p.stdin.write("changetype:modify\n")
            p.stdin.write("replace:krbpasswordexpiration\n")
            p.stdin.write("krbpasswordexpiration:%s120000Z\n" % pw_exp)
            p.stdin.close()
            ret = p.wait()
            log.info("ldapmodify output: %s" % p.stdout.read().strip())
            return (ret == 0)
    
        # The LDAP server is sometime slow, and there is race here where we can
        # update the expiry before the password change has been processed. So
        # we use an advanced synchronization method called "sleeping".
        SLEEP_TIME_SEC = 5

        _update_passwd(username, password)
        log.info("Sleeping for %d seconds ...", SLEEP_TIME_SEC)
        time.sleep(SLEEP_TIME_SEC)
        _update_exp(username)
        

class IpaMock(object):
    def __init__(self):
        pass

    def user_get(self, username):
        log.info("IpaMock: user_get: username=%s", username)
        return {"username": username}

    def user_add(self, username, **kwargs):
        log.info("IpaMock: user_add: username=%s kwargs=%s", username, kwargs)

    def user_mod(self, username, backend_user, **kwargs):
        log.info("IpaMock: user_mod: username=%s kwargs=%s", username, kwargs)

    def update_password(self, username, password):
        log.info("IpaMock: update_password: backend_user=%s username=%s password-len=%s",
            backend_user, username, len(password))
