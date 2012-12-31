import datetime
import cPickle
import os
import logging

try:
    from gdata.apps.service import AppsForYourDomainException, AppsService
    imported = True
except ImportError:
    imported = False

log = logging.getLogger("googleapi")

class GoogleException(Exception): pass

def get_api(*args, **kwargs):
    """
    API factory, returns mock if `debug` is set.
    """
    if kwargs.pop("debug", True):
        return GoogleMock()
    else:
        assert imported, "Failed importing gdata libraries"
        return Google(*args, **kwargs)


class Google(object):
    def __init__(self, api_user, api_pass, tmp_dir, token_lifetime_days=3):
        self._service = None

        self.api_user = api_user
        self.api_pass = api_pass
        self.tmp_dir  = tmp_dir
        self.token_fn = os.path.join(tmp_dir, "google.auth.mr")
        self.token_lifetime = datetime.timedelta(days=token_lifetime_days)


    @property
    def service(self):
        if not self._service:
            self._service = AppsService(domain='mr.is')
            
            # Try to authenticate with a cached auth token
            token = self._load_token()
            if token:
                self._service.SetClientLoginToken(token)

            # Fail back to user/pass auth, and cache token
            else:
                log.info("Reauthenticating")
                self._service.ClientLogin(username=self.api_user, password=self.api_pass,
                    account_type='HOSTED', service='apps')
                self._save_token(self._service.GetClientLoginToken())

        return self._service


    def disconnect(self):
        """
        Clears the cached service connection.
        """
        self._service = None


    def _load_token(self):
        try:
            with open(self.token_fn) as fp:
                token = cPickle.load(fp)
        except:
            token = None
        
        # Return token, if still valid
        if token and token["timestamp"] + self.token_lifetime > datetime.datetime.now():
            return token["token"]


    def _save_token(self, token):
        token = {
            'timestamp': datetime.datetime.now(),
            'token': token,     
        }
        
        prev = os.umask(077)
        with open(self.token_fn, "wb") as fp:
            cPickle.dump(token, fp)
        os.umask(prev)


    def user_add(self, username, first_name, last_name, password,
            suspended='false', password_hash_function="SHA-1"):
        """
        Create new user, returns a Google User object.
        """
        log.info("Adding user %s (%s %s), suspeded=%s", username, first_name, last_name, suspended)
        user = self.service.CreateUser(
            user_name              = username,
            family_name            = last_name,
            given_name             = first_name,
            password               = password,
            suspended              = suspended,
            password_hash_function = password_hash_function
            )
        
        return user


    def user_get(self, username):
        """
        Fetch user, returns a Google User object or None if not found.
        """
        log.info("Fetching user %s", username)
        try:
            return self.service.RetrieveUser(username)
        except AppsForYourDomainException, e:
            if e.error_code == 1301: #EntityDoesNotExist
                log.debug("User doesn't exist %s", username)
                pass
            else:
                raise GoogleException(e.reason)

        return None


    def user_mod(self, username, backend_user):
        """
        Update user, takes username (str) and Google User object.
        """
        log.info("Modifying user %s", username)
        self.service.UpdateUser(username, backend_user)


    def list_sync(self, name, members):
        """
        Synchronizes email list to include `members`. If the list doesn't
        exist it's created.
        """
        log.info("Synchronizing email list %s", name)
        try:
            self.service.RetrieveEmailList(name)
        except AppsForYourDomainException, e:
            if e.error_code == 1301: #EntityDoesNotExist
                log.debug("List didn't exist, creating %s", name)
                self.service.CreateEmailList(name)
            else:
                raise e

        # Get list recipients, store in a set.
        google_recipients = set( self.list_members(name) )
        local_recipients  = set( members )

        # See which entries we need to add and which should be deleted
        add_recipients = local_recipients - google_recipients
        del_recipients = google_recipients - local_recipients

        log.debug("Adding: %s", add_recipients)
        log.debug("Removing: %s", del_recipients)

        for recipient in add_recipients:
            try:
                self.service.AddRecipientToEmailList(recipient, name)
            except AppsForYourDomainException, e:
                raise GoogleException(e.reason)

        for recipient in del_recipients:
            try:
                self.service.RemoveRecipientFromEmailList(recipient, name)
            except AppsForYourDomainException, e:
                raise GoogleException(e.reason)


    def list_members(self, name):
        """
        Return list member iterable
        """
        log.debug("Listing members of %s", name)
        try:
            self.service.RetrieveEmailList(name)
        except AppsForYourDomainException, e:
            if e.error_code == 1301: #EntityDoesNotExist
                return
            else:
                raise GoogleException(e.reason)

        try:
            members = (e.title.text for e in self.service.RetrieveAllRecipients(name).entry)
        except AppsForYourDomainException, e:
            raise GoogleException(e.reason)

        return members


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
