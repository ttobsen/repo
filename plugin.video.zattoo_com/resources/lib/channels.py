# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import xbmcplugin
import xbmcgui
import json
import time

from .api import get_json_data

try:
    from urllib.error import URLError, HTTPError
except:
    from urllib2 import URLError, HTTPError

URI = sys.argv[0]
ADDON_HANDLE = int(sys.argv[1])


def round_seconds(seconds_to_round, round_to_nearest_seconds=300):
    if seconds_to_round <= 60:
        return 60
    if seconds_to_round < 500:
        return seconds_to_round - (seconds_to_round % 60)
    important_range = seconds_to_round % round_to_nearest_seconds
    half_round_range = round_to_nearest_seconds >> 1
    if important_range < half_round_range:
        seconds_to_round -= important_range
    else:
        seconds_to_round = seconds_to_round + (round_to_nearest_seconds - important_range)
    return seconds_to_round


def list_channels(session, pg_hash, USE_FANARTS=False):
    if not pg_hash or not session:
        from .api import login
        login()
        import xbmcaddon
        addon = xbmcaddon.Addon(id='plugin.video.zattoo_com')
        pg_hash = addon.getSetting('pg_hash')
        session = addon.getSetting('session')
    try:
        json_data = json.loads(get_json_data('https://zattoo.com/zapi/v2/cached/channels/%s?details=True' % pg_hash, session))
    except HTTPError:
        from .api import login
        login()
        import xbmcaddon
        addon = xbmcaddon.Addon(id='plugin.video.zattoo_com')
        pg_hash = addon.getSetting('pg_hash')
        session = addon.getSetting('session')
        json_data = json.loads(get_json_data('https://zattoo.com/zapi/v2/cached/channels/%s?details=True' % pg_hash, session))
    except URLError:
        from .functions import warning
        warning('Keine Netzwerkverbindung!')
        return
    except:
        from .functions import warning
        warning('TV Daten konnten nicht geladen werden!')
        return

    channel_groups = json_data['channel_groups']  # [:3]
    current_timestamp = int(time.time())

    for group in channel_groups:
        for channel in group['channels']:
            for quality in channel['qualities']:
                if quality['availability'] == 'available':
                    channel_name = quality['title']
                    id = channel['cid']
                    thumb = 'http://thumb.zattic.com/%s/500x288.jpg?r=%i' % (id, current_timestamp)
                    try:
                        title = channel['now']['t']
                        subtitle = channel['now']['et']
                        if subtitle:
                            title = '%s: %s' % (title, subtitle)
                    except:
                        title = ''
                    item = xbmcgui.ListItem('[B][COLOR blue]%s[/COLOR][/B] %s' % (channel_name, title))
                    item.setArt({'thumb': thumb})
                    try:
                        duration_in_seconds = round_seconds(channel['now']['e'] - current_timestamp)
                    except:
                        duration_in_seconds = 0
                    try:
                        next = '[B][COLOR blue]Danach:[/COLOR][/B] %s (%i Min.)' % (
                                channel['next']['t'], (channel['next']['e'] - channel['next']['s']) / 60)
                        item.addContextMenuItems(
                            [('EPG Daten laden', 'xbmc.RunPlugin(plugin://plugin.video.zattoo_com/?mode=epg&id=%s)' % channel['now']['id'])]
                        )
                    except:
                        next = ''
                    if USE_FANARTS:
                        try:
                            fanart = channel['now']['i'].replace('format_480x360.jpg', 'format_1280x720.jpg')
                        except:
                            fanart = 'http://thumb.zattic.com/%s/1280x720.jpg' % id
                        item.setProperty('fanart_image', fanart)
                    item.setInfo(type='Video', infoLabels={
                        'Title': title or channel_name,
                        'Plot': next,
                        }
                    )
                    item.addStreamInfo('video', {'duration': duration_in_seconds})
                    item.setProperty('IsPlayable', 'true')
                    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url='%s?mode=watch&id=%s' % (URI, id), listitem=item)
                    break
    xbmcplugin.endOfDirectory(ADDON_HANDLE)