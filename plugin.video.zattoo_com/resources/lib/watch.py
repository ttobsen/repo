# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

try:
    from urllib.parse import urljoin
    from urllib.request import urlopen
except:
    from urllib2 import urlopen
    from urlparse import urljoin


def get_playlist_url(cid, SESSION):
    from .api import get_json_data
    json_data = get_json_data('https://zattoo.com/zapi/watch', SESSION, {'stream_type':'hls', 'cid':cid})
    return json.loads(json_data)['stream']['url']


def get_stream_url(cid, SESSION, MAX_BITRATE):
    playlist_url = get_playlist_url(cid, SESSION)
    m3u8_data = urlopen(playlist_url).read().decode('utf-8')
    url_parts = [line for line in m3u8_data.split('\n') if '.m3u8' in line]
    prefix_url = urljoin(playlist_url, '/')
    if MAX_BITRATE == '3000000':
        suffix_url = url_parts[0]
    elif MAX_BITRATE == '1500000':
        if len(url_parts) == 4:
            suffix_url = url_parts[1]
        else:
            suffix_url = url_parts[0]
    elif MAX_BITRATE == '900000':
        if len(url_parts) == 4:
            suffix_url = url_parts[2]
        else:
            suffix_url = url_parts[1]
    else:
        suffix_url = url_parts[-1]
    return prefix_url + suffix_url