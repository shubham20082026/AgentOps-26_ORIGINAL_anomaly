"""Print only a password hash for environment variables or hosted Secrets."""
from getpass import getpass
from reroute.auth import password_hash
if __name__ == '__main__':
    password = getpass('Choose a dispatcher password (12+ characters): ')
    if password != getpass('Confirm password: '):
        raise SystemExit('Passwords did not match.')
    print('REROUTE_LOGIN_HASH = "'+password_hash(password)+'"')
