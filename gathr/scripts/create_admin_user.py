import argparse
import getpass
import os
import sys
import transaction

from pyramid.paster import bootstrap

from ..security import MANAGERS
from ..users import User
from ..users import UsersFolder


def main(argv=sys.argv[1:]):
    # Parse arguments and find a config file
    parser = argparse.ArgumentParser(
        description="Create an administrative user.")
    parser.add_argument('--config', '-C', metavar='INI_FILE',
        help="Path to ini configuration file.  Default: etc/gathr.ini")
    parser.add_argument('userid', help="New user id")
    args = parser.parse_args(argv)
    config = args.config
    if not config:
        envdir = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
        config = os.path.join(envdir, 'etc', 'gathr.ini')
    appenv = bootstrap(config)

    root = appenv['root']
    if 'users' not in root:
        root['users'] = UsersFolder()
    users = root['users']

    if args.userid in users:
        parser.error("User exists.")

    fullname = ''
    while not fullname:
        fullname = raw_input("Full name: ")
    email = raw_input("Email: ")
    while True:
        pass1 = ''
        while not pass1:
            pass1 = getpass.getpass("Password: ")
        pass2 = ''
        while not pass2:
            pass2 = getpass.getpass("Again to confirm: ")
        if pass1 != pass2:
            print "Passwords don't match, try again."
            continue
        break

    user = User(fullname, email)
    users[args.userid] = user
    user.add_to_group(root, MANAGERS)

    transaction.commit()
