# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from kodi_six.utils import py2_encode
import os
import re
import sys
import xbmc, xbmcplugin, xbmcaddon, xbmcgui
from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime
import time

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

try:
    from urllib.parse import urlencode, urljoin, parse_qsl
    from html.parser import HTMLParser
except ImportError:
    from urllib import urlencode
    from urlparse import urljoin, parse_qsl
    from HTMLParser import HTMLParser

HOST = 'https://www.skysportaustria.at'
VIDEO_URL_HSL = 'https://player.ooyala.com/player/all/{0}.m3u8'
LIVE_URL_HSL = 'https://eventhlshttps-i.akamaihd.net/hls/live/263645/ssn-hd-https/index.m3u8'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'

addon = xbmcaddon.Addon()
addon_base_url = 'plugin://{0}'.format(addon.getAddonInfo('id'))
addon_handle = int(sys.argv[1])
cache = StorageServer.StorageServer(py2_encode('{0}.videoid').format(addon.getAddonInfo('name')), 24 * 30)
sky_sport_news_icon = xbmc.translatePath('{0}/resources/skysport_news.jpg'.format(addon.getAddonInfo('path')))
nav_json = json.load(open(xbmc.translatePath('{0}/resources/navigation.json'.format(addon.getAddonInfo('path')))))
html_parser = HTMLParser()


def rootDir():
    url = build_url({'action': 'playLive'})
    addVideo('Sky Sport News HD', url, sky_sport_news_icon)

    for item in nav_json:
        url = build_url({'action': 'showVideos', 'category': item.get('category'), 'page': 1})
        addDir(item.get('label'), url)

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)


def addDir(label, url, icon=None):
    addVideo(label, url, icon, isFolder=True)


def addVideo(label, url, icon, infoLabels={}, isFolder=False):
    li = xbmcgui.ListItem(label)
    li.setArt({'icon': icon, 'thumb': icon})
    li.setInfo('video', infoLabels)
    li.setProperty('IsPlayable', str(isFolder))

    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=isFolder)


def build_url(query):
    return '{0}?{1}'.format(addon_base_url, urlencode(query))


def showVideos(category, page, maxpage):
    videos = []
    status_code = 200

    while status_code == 200 and len(videos) <= 30 and page is not False and page <= maxpage:
        url = urljoin(HOST, 'wp-admin/admin-ajax.php')
        data = {'action': 'sky_video_index', 'categories[]': category, 'paged': page}
        res = requests.post(url, data=data)
        status_code = res.status_code
        if status_code == 200:
            res_json = res.json()
            maxpage = res_json.get('max_num_pages')

            matches = re.finditer('src=\"([^\"]*).*\s*.*\s*.*\s*.*\s*.*\s*.*datetime=\"([\d-]*).*[\n\s]*.*<a href=\"([^\"]*)[^>]*>([^<]*).*<p>([^<]*)', res_json.get('content'))
            if matches:
                for match in matches:
                    label = html_parser.unescape(match.group(4))
                    date = datetime.fromtimestamp(time.mktime(time.strptime(match.group(2), '%Y-%m-%d'))).strftime('%d.%m.%Y')
                    plot = 'Verfügbar seit: {0}\n\n{1}'.format(date, html_parser.unescape(match.group(5)))
                    image = match.group(1)
                    url = build_url({'action': 'playVoD', 'path': match.group(3)})

                    video = {
                        'label': label,
                        'infoLabels': {'title': label, 'plot': plot},
                        'image': image,
                        'url': url
                    }
                    videos.append(video)

            page = res_json.get('next_page')

    for video in videos:
        addVideo(video.get('label'), video.get('url'), video.get('image'), video.get('infoLabels'))

    if page is not False and page < maxpage:
        url = build_url({'action': 'showVideos', 'category': category, 'page': page, 'maxpage': maxpage})
        addDir('Nächste Seite', url)

    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=True)


def getVideoIdFromCache(path):
    return cache.cacheFunction(getVideoId, path)


def getVideoId(path):
    video_id = {'id': None}

    url = urljoin(HOST, path)
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')

    scripts = soup.findAll('script')
    for script in scripts:
        script = script.text
        match = re.search('OO\.Player\.create[^,]*,\s?"([^"]*)', script)
        if match is not None:
            video_id.update({'id': match.group(1)})

    return video_id


def playVoD(path):
    video_id = getVideoIdFromCache(path).get('id')
    if video_id is not None:
        li = getVideoListItem(video_id)
    else:
        li = xbmcgui.ListItem()
    xbmcplugin.setResolvedUrl(addon_handle, True, li)


def playLive():
    li = getVideoListItem(None)
    xbmcplugin.setResolvedUrl(addon_handle, True, li)


def getVideoListItem(video_id):
    li = xbmcgui.ListItem()

    maxbandwith = int(addon.getSetting('maxbandwith'))
    maxresolution = int(addon.getSetting('maxresolution').replace('p', ''))

    if video_id is None:
        url = getHLSUrl(LIVE_URL_HSL, maxbandwith, maxresolution)
    else:
        url = getHLSUrl(VIDEO_URL_HSL.format(video_id), maxbandwith, maxresolution)

    li.setPath('{0}|{1}'.format(url, USER_AGENT))

    return li


def getHLSUrl(url, maxbandwith, maxresolution):
    response = requests.get(url)
    xbmc.log('response.status_code = {0}'.format(response.status_code))
    if response.status_code == 200:
        xbmc.log('response.text = {0}'.format(response.text))
        matches = re.findall('BANDWIDTH=(\d*).*RESOLUTION=\d*x(\d*).*\s*(.*)', response.text)
        if matches:
            resolutions = [360, 480, 720, 1080, 0]
            for m_bandwidth, m_resolution, m_url in matches:
                if (maxbandwith == 0 or int(m_bandwidth) <= maxbandwith) and (resolutions[maxresolution] == 0 or int(m_resolution) <= resolutions[maxresolution]):
                    url = m_url

        response.close()

    return url


def clearCache():
    cache.delete('%')
    xbmcgui.Dialog().notification('Sky Sport Austria Mediathek', 'Leeren des Caches erfolgreich', xbmcgui.NOTIFICATION_INFO, 5000, True)


if __name__ == '__main__':
    params = dict(parse_qsl(sys.argv[2][1:]))
    if 'action' in params:

        xbmc.log('params = {0}'.format(params))

        if params.get('action') == 'playLive':
            playLive()
        elif params.get('action') == 'showVideos':
            showVideos(params.get('category'), int(params.get('page')), int(params.get('maxpage', 1)))
        elif params.get('action') == 'playVoD':
            playVoD(params.get('path'))
        elif params.get('action') == 'clearCache':
            clearCache()
    else:
        rootDir()