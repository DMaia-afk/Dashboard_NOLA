#!/usr/bin/env python3
"""Small HTTP helper used by card API test scripts.

Usage: import and call `fetch_json(url)` which returns (status_code, parsed_json_or_text)
It prefers `requests` if available, otherwise falls back to urllib.
"""
import json
import sys
import logging
from urllib import request as _request
from urllib.error import URLError, HTTPError

try:
    import requests
    _HAS_REQUESTS = True
except Exception:
    _HAS_REQUESTS = False


def fetch_raw(url, timeout=10):
    """Return (status_code, raw_bytes, content_type_or_none)"""
    if _HAS_REQUESTS:
        r = requests.get(url, timeout=timeout)
        return r.status_code, r.content, r.headers.get('Content-Type')
    try:
        with _request.urlopen(url, timeout=timeout) as resp:
            status = resp.getcode()
            ct = resp.headers.get('Content-Type')
            body = resp.read()
            return status, body, ct
    except HTTPError as e:
        body = None
        try:
            body = e.read()
        except Exception:
            body = None
        return e.code or 500, body or b'', getattr(e, 'headers', {}).get('Content-Type') if getattr(e, 'headers', None) else None
    except URLError as e:
        raise


def fetch_json(url, timeout=10):
    """Fetch URL and attempt to parse JSON. Returns (status_code, parsed_json_or_text).

    If JSON parse succeeds, the second element is the parsed object. Otherwise it's the raw text.
    """
    status, raw, ct = fetch_raw(url, timeout=timeout)
    if raw is None:
        return status, None
    try:
        text = raw.decode('utf-8')
    except Exception:
        try:
            text = raw.decode('latin-1')
        except Exception:
            text = str(raw)
    try:
        parsed = json.loads(text)
        return status, parsed
    except Exception:
        return status, text


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        logging.error('Usage: api_test_client.py <url>')
        sys.exit(2)
    url = sys.argv[1]
    try:
        status, data = fetch_json(url)
    except Exception:
        logging.exception('ERROR while fetching URL %s', url)
        sys.exit(3)
    logging.info('Status: %s', status)
    if isinstance(data, (dict, list)):
        logging.info('JSON: %s', json.dumps(data)[:1000])
    else:
        logging.info('Body preview: %s', str(data)[:1000])
