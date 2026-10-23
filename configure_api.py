"""Run locally: the key is entered without echo and saved only as encrypted bytes."""
import getpass
import warnings
from reroute.config import save_api


def main():
    print('ReRoute API setup — saved for this Windows user using Windows encryption.')
    print('Use a provider endpoint and model that support Chat Completions tool calling.')
    url = input('HTTPS endpoint [https://api.openai.com/v1/chat/completions]: ').strip() or 'https://api.openai.com/v1/chat/completions'
    model = input('Model ID: ').strip()
    # Refuse getpass fallback to visible stdin when no secure terminal is available.
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        key = getpass.getpass('API key (hidden): ')
    save_api(key, model, url)
    print('Encrypted API configuration saved. Restart ReRoute and select LLM · configured API.')


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt):
        print('Setup did not complete. Use a local terminal, a valid HTTPS endpoint, and a non-empty key and model.')
        raise SystemExit(1)
