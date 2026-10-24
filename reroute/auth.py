"""Optional dispatcher access gate with two configured accounts. No default credentials."""
import hashlib
import hmac
import os
import secrets
import time
import threading

_lock = threading.Lock()
_attempts = []

def password_hash(password):
    if not 12 <= len(password) <= 256:
        raise ValueError('Use a password of 12 to 256 characters.')
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 600000)
    return 'pbkdf2_sha256$600000$'+salt.hex()+'$'+digest.hex()

def valid_hash(encoded):
    try:
        algorithm, count, salt, digest = encoded.split('$')
        return (algorithm == 'pbkdf2_sha256' and 600000 <= int(count) <= 2000000
                and len(bytes.fromhex(salt)) == 16 and len(bytes.fromhex(digest)) == 32)
    except (ValueError, TypeError, AttributeError):
        return False

def verify(password, encoded):
    if not valid_hash(encoded) or not isinstance(password, str) or len(password) > 256:
        return False
    _, count, salt, digest = encoded.split('$')
    actual = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(count))
    return hmac.compare_digest(actual, bytes.fromhex(digest))

def settings(hosted):
    user = str(os.environ.get('REROUTE_LOGIN_USER', hosted.get('REROUTE_LOGIN_USER', ''))).strip()
    encoded = str(os.environ.get('REROUTE_LOGIN_HASH', hosted.get('REROUTE_LOGIN_HASH', '')))
    required = str(os.environ.get('REROUTE_REQUIRE_LOGIN', hosted.get('REROUTE_REQUIRE_LOGIN', 'false'))).lower() in ('true','1','yes')
    enabled = bool(user or encoded or required)
    ready = bool(user and valid_hash(encoded))
    fingerprint = hashlib.sha256((user+'\0'+encoded).encode()).hexdigest()
    return user, encoded, enabled, ready, fingerprint


def accounts(hosted):
    user, encoded, enabled, ready, fingerprint = settings(hosted)
    second_user = str(os.environ.get('REROUTE_LOGIN_USER_2', hosted.get('REROUTE_LOGIN_USER_2', ''))).strip()
    second_hash = str(os.environ.get('REROUTE_LOGIN_HASH_2', hosted.get('REROUTE_LOGIN_HASH_2', '')))
    values = {user: encoded} if ready else {}
    if second_user or second_hash:
        enabled = True
        ready = bool(ready and second_user and valid_hash(second_hash) and second_user != user)
        if ready:
            values[second_user] = second_hash
        fingerprint = hashlib.sha256((fingerprint+'\0'+second_user+'\0'+second_hash).encode()).hexdigest()
    return values, enabled, ready, fingerprint

def login_allowed():
    """Process-wide throttle survives browser session resets, but not server restarts."""
    now = time.monotonic()
    with _lock:
        _attempts[:] = [t for t in _attempts if now-t < 60]
        if len(_attempts) >= 5:
            return False
        _attempts.append(now)
        return True

def gate(st, hosted):
    users, enabled, ready, fingerprint = accounts(hosted)
    session = st.session_state
    user = session.get('_login_user', '')
    authenticated = (session.get('_login_fingerprint') == fingerprint
                     and time.time() < session.get('_login_until', 0) and ready and user in users)
    if authenticated:
        with st.sidebar:
            st.caption('Signed in as '+user)
            if st.button('Sign out'):
                session.clear()
                st.rerun()
        return user
    if enabled or session.get('_show_login'):
        st.markdown('<div class="login-banner"><span>REROUTE / DISPATCHER ACCESS</span><h1>Welcome back.</h1><p>A careful recovery starts with you.</p><p style="margin-top:20px;font-size:13px">Created by Shubham Parmar · ORIGINAL_anomaly</p></div>', unsafe_allow_html=True)
        _, middle, _ = st.columns([1, 1.4, 1])
        with middle:
            st.subheader('Sign in to the rescue desk')
            if not ready:
                st.info('Dispatcher login is not configured. Add the login settings in Streamlit Secrets. See LOGIN_SETUP.md.')
                if not enabled and st.button('Return to public sandbox'):
                    session.pop('_show_login', None)
                    st.rerun()
            else:
                with st.form('dispatcher_login', clear_on_submit=True):
                    entered_user = st.text_input('Username', max_chars=128)
                    password = st.text_input('Password', type='password', max_chars=256)
                    submitted = st.form_submit_button('Sign in', type='primary', width='stretch')
                if submitted:
                    if not login_allowed():
                        st.error('Too many sign-in attempts. Wait one minute and try again.')
                    else:
                        encoded = users.get(entered_user, next(iter(users.values())))
                        password_ok = verify(password, encoded)
                        if entered_user in users and password_ok:
                            session.clear()
                            session['_login_user'] = entered_user
                            session['_login_fingerprint'] = fingerprint
                            session['_login_until'] = time.time()+3600
                            st.rerun()
                        st.error('Username or password is incorrect.')
                st.caption('Sessions expire after one hour. Configured accounts share the dispatcher workspace.')
        st.stop()
    with st.sidebar:
        st.caption('Public synthetic sandbox')
        if st.button('Dispatcher sign in'):
            session['_show_login'] = True
            st.rerun()
    return None
