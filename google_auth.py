"""
This script authenticates the client id and stores a refresh token,
later used for the web site and cron jobs.

Based on apiclient.sample_tools and oauth2client.tools.

This sample was also helpful:
https://code.google.com/r/jeremye-admin-directory-sample/source/browse/samples/admin_directory/admin_directory.py
"""

import logging
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())

import uuid

import settings
import apis.google
import stjornbord_google_api

# https://developers.google.com/admin-sdk/directory/v1/guides/authorizing
SCOPE = [
    "https://www.googleapis.com/auth/admin.directory.user",
    "https://www.googleapis.com/auth/admin.directory.group",
    ]

g = apis.google.get_api(settings.GOOGLE_TOKEN, settings.DOMAIN, debug=False)

def fetch_nonexistent_list():
    try:
        return g.list_members(str(uuid.uuid4())) is None
    except stjornbord_google_api.GoogleAPICredentialException, e:
        return False

def main():
    # See if we're already authenticated
    if not fetch_nonexistent_list():
        g.authenticate(settings.GOOGLE_SECRETS, SCOPE)

    if fetch_nonexistent_list():
        print "Authentication tokens are valid, test query was successful."
    else:
        print "Authentication failed."


if __name__ == '__main__':
    main()