"""Stable local configuration; Windows protects saved credentials with DPAPI."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
_hosted_secrets = {}

def set_hosted_secrets(values):
    """Accept hosted secrets in memory only; environment values take priority."""
    global _hosted_secrets
    _hosted_secrets = {k: str(v) for k,v in values.items() if k.startswith('REROUTE_') or k == 'OPENAI_API_KEY'}



def database_path():
    value = os.environ.get('REROUTE_DB', _hosted_secrets.get('REROUTE_DB', 'data/reroute.db')).strip()
    if not value or value == ':memory:':
        raise ValueError('REROUTE_DB must name a persistent database file')
    path = Path(value).expanduser()
    return (path if path.is_absolute() else ROOT / path).resolve()


def protect(data, decrypt=False):
    if os.name != 'nt':
        raise RuntimeError('Saved credentials require Windows; use environment variables on other systems')

    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_char))]

    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    output = Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    function = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                         ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output)):
        raise RuntimeError('Windows could not unlock or save the API configuration for this user')
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        kernel.LocalFree(ctypes.cast(output.data, ctypes.c_void_p))


def validate_endpoint(url):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError('The API endpoint must be an HTTPS URL without embedded credentials or a fragment')
    return url


def save_api(key, model, url):
    if not key.strip() or not model.strip():
        raise ValueError('Both an API key and a tool-capable model ID are required')
    settings = {'key': key.strip(), 'model': model.strip(), 'url': validate_endpoint(url.strip())}
    encrypted = protect(json.dumps(settings).encode('utf-8'))
    folder = ROOT / '.private'
    folder.mkdir(exist_ok=True)
    temporary = folder / 'api.dpapi.tmp'
    temporary.write_bytes(encrypted)
    temporary.replace(folder / 'api.dpapi')


def api_settings():
    values = dict(_hosted_secrets)
    values.update({k:v for k,v in os.environ.items() if k.startswith('REROUTE_') or k=='OPENAI_API_KEY'})
    key = values.get('REROUTE_API_KEY') or values.get('OPENAI_API_KEY')
    # A complete environment configuration does not depend on a local Windows account.
    saved = {}
    path = ROOT / '.private' / 'api.dpapi'
    if not key and path.exists():
        saved = json.loads(protect(path.read_bytes(), decrypt=True))
    return {
        'key': key or saved.get('key'),
        'model': values.get('REROUTE_MODEL') or saved.get('model'),
        'url': validate_endpoint(values.get('REROUTE_API_URL') or saved.get('url') or 'https://api.openai.com/v1/chat/completions'),
    }

