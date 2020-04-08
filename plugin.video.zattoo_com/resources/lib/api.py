# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from re import search
import xbmcaddon

try:
    from urllib.parse import urlencode
    from urllib.request import urlopen, Request
    from urllib.error import URLError, HTTPError
except:
    from urllib import urlencode
    from urllib2 import urlopen, Request, URLError, HTTPError

addon = xbmcaddon.Addon(id='plugin.video.zattoo_com')
standard_header = {
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'
}


def get_app_token():
    try:
        html = urlopen('https://zattoo.com/').read().decode('utf-8')
        return search("window\.appToken\s*=\s*'(.*)'", html).group(1)
    except URLError:
        from .functions import warning
        return warning('Keine Netzwerkverbindung!', exit=True)
    except:
        return ''


def extract_session_id(cookie):
    if len(cookie) > 0:
        return search('beaker\.session\.id\s*=\s*([^\s;]*)', cookie[0]).group(1)
    return ''


def get_session_cookie():
    post_data = ('lang=en&client_app_token=%s&uuid=d7512e98-38a0-4f01-b820-5a5cf98141fe&format=json' % get_app_token()).encode('utf-8')
    req = Request('https://zattoo.com/zapi/session/hello', post_data, standard_header)
    response = urlopen(req)
    return extract_session_id([value for key, value in response.headers.items() if key.lower() == 'set-cookie'])


def update_pg_hash(hash):
    addon.setSetting(id='pg_hash', value=hash)


def update_session(session):
    addon.setSetting(id='session', value=session)


def get_json_data(api_url, cookie, post_data=None):
    header = standard_header.copy()
    header.update({'Cookie': 'beaker.session.id=' + cookie})
    if post_data:
        post_data = urlencode(post_data).encode('utf-8')
    req = Request(api_url, post_data, header)
    response = urlopen(req)
    new_cookie = extract_session_id([value for key, value in response.headers.items() if key.lower() == 'set-cookie'])
    if new_cookie:
        update_session(new_cookie)
    return response.read()


def login():
    USER_NAME = addon.getSetting('username')
    PASSWORD = addon.getSetting('password')
    if not USER_NAME or not PASSWORD:
        from .functions import warning
        return warning('Bitte Benutzerdaten eingeben!', exit=True)
    handshake_cookie = get_session_cookie()
    try:
        login_json_data = get_json_data('https://zattoo.com/zapi/v2/account/login', handshake_cookie, {'login': USER_NAME, 'password': PASSWORD})
    except HTTPError:
        from .functions import warning
        return warning('Falsche Logindaten!', exit=True)
    import json
    pg_hash = json.loads(login_json_data)['session']['power_guide_hash']
    update_pg_hash(pg_hash)
