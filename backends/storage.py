import logging
import subprocess

import settings
import backends

log = logging.getLogger("user_daemon.storage")


class StorageBackend(backends.Backend):
    def process_user(self, user):
        status = user["status"]
        if status in (settings.ACTIVE_USER, settings.WCLOSURE_USER):
            self.create(user)
        elif status in (settings.INACTIVE_USER, ):
            pass
        elif status in (settings.DELETED_USER, ):
            self.archive(user)

    def create(self, user):
        """
        Idempotent create.
        """
        raise NotImplementedError()

    def archive(self, user):
        """
        Idempotent archive.
        """
        raise NotImplementedError()


class HomeBackend(StorageBackend):
    def create(self, user):
        """
        Creates user's home directory on storage server.
        """
        if settings.DEBUG:
            log.warn("Running in debug mode, skipping homedir creation")
            return

        username = user["username"]
        log.info("Creating homedir for %s" % username)
        p = subprocess.Popen(
            ["ssh", "storage.mr.lan", "/var/opinn/scripts/create_user_dir.sh", username],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ret = p.wait()
        log.info("   ssh output: %s" % p.stdout.read().strip())
        return (ret == 0)
    
