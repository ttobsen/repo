# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from kodi_six.utils import py2_encode
import socket
import sys
import os
import re
import ast
import xbmcplugin
import xbmcaddon, xbmc
import xbmcgui, json
import requests, xbmcvfs
import datetime, time

try:
    from urllib.parse import quote_plus, unquote_plus, parse_qsl, urlencode
    from http import cookiejar as cookielib
except:
    from urllib import quote_plus, unquote_plus, urlencode
    from urlparse import parse_qsl
    import cookielib

addon = xbmcaddon.Addon()
socket.setdefaulttimeout(30)
addonhandle = int(sys.argv[1])
addonID = addon.getAddonInfo('id')
translation = addon.getLocalizedString

cj = cookielib.LWPCookieJar();
language = addon.getSetting('language')

try:
   import StorageServer
except:
   import storageserverdummy as StorageServer

cachezeit = addon.getSetting('cachetime')
cache = StorageServer.StorageServer(py2_encode(addonID), cachezeit)


def debug(content):
    log(content, xbmc.LOGDEBUG)


def notice(content):
    log(content, xbmc.LOGNOTICE)


def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('{0}: {1}'.format(addonID, msg), level)


debug('Start Addon')


def addLink(name, url, mode, infoLabels=None, art=None):
    u = '{0}?{1}'.format(sys.argv[0], urlencode({
        'url': url,
        'mode': mode,
        'name': py2_encode(name)
    }))
    ok = True
    liz = xbmcgui.ListItem(name)
    if infoLabels:
        liz.setInfo(type='video', infoLabels=infoLabels)
    if art:
        liz.setArt(art)
    liz.setProperty('IsPlayable', 'true')
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    ok = xbmcplugin.addDirectoryItem(handle=addonhandle, url=u, listitem=liz)
    return ok


def addDir(name, url, mode, icon=None, desc=None, text='', page=None, addtype=0):
    u = '{0}?{1}'.format(sys.argv[0], urlencode({
        'url': url,
        'mode': mode,
        'name': py2_encode(name),
        'text': text,
        'page': page
    }))
    ok = True
    liz = xbmcgui.ListItem(name)
    if addtype == 1:
        commands = []
        updatestd = addon.getSetting("updatestd")
        debug('UPDATETIME: {0}'.format(updatestd))
        link = '{0}?{1}'.format(sys.argv[0], urlencode({
            'url': url,
            'mode': 'tolibrary',
            'name': py2_encode(name),
            'stunden': updatestd
        }))
        # debug("LINK :"+link)
        commands.append(('Add to library', 'XBMC.RunPlugin({0})'.format(link)))
        liz.addContextMenuItems(commands)
    liz.setInfo(type='video', infoLabels={'title': name, 'plot': desc})
    if icon:
        liz.setArt({'thumb': icon})
    ok = xbmcplugin.addDirectoryItem(handle=addonhandle, url=u, listitem=liz, isFolder=True)
    return ok


params = dict(parse_qsl(sys.argv[2][1:]))
mode = unquote_plus(params.get('mode', ''))
url = unquote_plus(params.get('url', ''))
page = unquote_plus(params.get('page', ''))
name = unquote_plus(params.get('name', ''))
stunden = unquote_plus(params.get('stunden', ''))


def index():
    addDir('Neueste Trailer', 'https://res.cinetrailer.tv/api/v1/{0}/movies/newest?pageSize=20&isDebug=false'.format(language), 'newlist', '', page=1, addtype=1)
    addDir('Demnächst im Kino', 'https://res.cinetrailer.tv/api/v1/{0}/movies/comingsoon?pageSize=20&isDebug=false'.format(language), 'newlist', '', page=1, addtype=1)
    addDir('Home Video', 'https://res.cinetrailer.tv/api/v1/{0}/movies/homevideo?pageSize=20&isDebug=false'.format(language), 'newlist', '', page=1, addtype=1)
    addDir('Im Kino', 'https://res.cinetrailer.tv/api/v1/{0}/movies/incinemas?orderBy=&pageSize=20&isDebug=false'.format(language), 'newlist', '', page=1, addtype=1)
    addDir('Genres', '', 'genres')
    addDir('Settings', '', 'Settings')
    xbmcplugin.endOfDirectory(addonhandle)


def getUrl(url, method, allow_redirects=False, verify=False, cookies='', headers='', data=''):
    if method == 'GET':
        content = py2_encode(requests.get(url, allow_redirects=allow_redirects, verify=verify, cookies=cookies, headers=headers, data=data).text)
    if method == 'POST':
        content = py2_encode(requests.post(url, data=data, allow_redirects=allow_redirects, verify=verify, cookies=cookies).text)
    return content


def genres():
    url = 'https://res.cinetrailer.tv/api/v1/{0}/categories'.format(language)
    token = getsession()
    values = {
        'Model' : 'Huawei MLA-TL10',
        'AppVersion' : '3.3.15',
        'OsVersion': '4.4.4',
        'OsName': 'android',
        'Market': 'android',
        'Authorization': 'Bearer {0}'.format(token),
        # 'TimeStamp': '2017-09-04 11:04:45'
    }
    content = cache.cacheFunction(getUrl, url, 'GET', False, False, cj, values)
    struktur = json.loads(content)
    for genre in struktur['categories']:
        idd = genre['id']
        title = genre['title']
        url = 'https://res.cinetrailer.tv/api/v1/{0}/movies/search?pageSize=20&desc=true&orderBy=date&categoryId={1}'.format(language, idd)
        addDir(title, url, 'newlist', page=1)
    xbmcplugin.endOfDirectory(addonhandle)


def getsession():
    url = 'https://res.cinetrailer.tv/Token'
    values = {
        'client_id' : 'cinetrailer_android',
        'client_secret' : 'pKQvtSL9FdpB3u38GMHtNMA3',
        'grant_type': 'client_credentials',
    }
    content = cache.cacheFunction(getUrl, url, 'POST', False, False, cj, '', values)
    struktur = json.loads(content)
    return struktur['access_token']


def Play(url):
    token = getsession()
    values = {
        'Model' : 'Huawei MLA-TL10',
        'AppVersion' : '3.3.15',
        'OsVersion': '4.4.4',
        'OsName': 'android',
        'Market': 'android',
        'Authorization': 'Bearer {0}'.format(token),
        # 'TimeStamp': '2017-09-04 11:04:45'
    }
    urln = 'https://res.cinetrailer.tv/api/v1/{0}/movie/{1}/trailers'.format(language, url)
    quality = str(addon.getSetting('quality'))
    content = cache.cacheFunction(getUrl, urln, 'GET', False, False, cj, values)
    struktur = json.loads(content)
    debug('PLAY')
    debug('URLN: {0}'.format(urln))
    debug(struktur)
    url = struktur['items'][0]['clips'][0]['url']
    for video in struktur['items'][0]['clips']:
        if quality == video['quality']:
            url = video['url']
    listitem = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(addonhandle, True, listitem)
    debug(struktur)


def newlist(url, page=1):
    token = getsession()
    nurl = '{0}&pageNumber={1}'.format(url, page)
    debug('URL newlist: {0}'.format(url))
    values = {
         'Model' : 'Huawei MLA-TL10',
         'AppVersion' : '3.3.15',
         'OsVersion': '4.4.4',
         'OsName': 'android',
         'Market': 'android',
         'Authorization': 'Bearer {0}'.format(token),
         # 'TimeStamp': '2017-09-04 11:04:45'
     }
    debug('Newlist url: {0} '.format(url))
    content = cache.cacheFunction(getUrl, nurl, 'GET', False, False, cj, values)
    struktur = json.loads(content)
    debug(struktur)
    count = 0
    for trailer in struktur['items']:
        id = trailer['id']
        image = trailer['poster_high']
        name = trailer['title']
        plot = 'Premiere: {0}'.format(datetime.datetime.fromtimestamp(time.mktime(time.strptime(trailer.get('premiere_date'), '%Y-%m-%dT%H:%M:%SZ'))).strftime('%d.%m.%Y'))
        genre = [genre.get('title') for genre in trailer.get('categories')]
        cast = [actor.get('name') for actor in trailer.get('cast').get('actors')]
        director = [director.get('name') for director in trailer.get('cast').get('directors')]
        infoLabels = {'title': name, 'plot': plot, 'year': trailer.get('premiere_date'), 'duration': trailer.get('duration'), \
                      'genre': genre, 'cast': cast, 'director': director, 'mediatype': 'movie'}
        addLink(name, id, 'Play', infoLabels=infoLabels, art={'icon': image, 'thumb': image, 'poster': image})
        count += 1
    if int(struktur['page_count']) > int(page):
        debug('## NEXT ##')
        addDir('Next', url, 'newlist', page=(int(page) + 1))
    xbmcplugin.endOfDirectory(addonhandle)


def tolibrary(url, name, stunden):
    mediapath = addon.getSetting('mediapath')
    if mediapath == '':
      dialog = xbmcgui.Dialog()
      dialog.notification('Error', 'Pfad setzen in den Settings', xbmcgui.NOTIFICATION_ERROR)
      return
    urlx = quote_plus(url)
    name = quote_plus(name)
    urln = 'plugin://plugin.video.L0RE.cinetrailer?mode=generatefiles&url={0}&name={1}'.format(urlx, name)
    urln = quote_plus(urln)
    debug('tolibrary urln: {0}'.format(urln))
    xbmc.executebuiltin('XBMC.RunPlugin(plugin://service.L0RE.cron/?mode=adddata&name={0}&stunden={1}&url={2})'.format(name, stunden, urln))
    # xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)


def generatefiles(url, fname):
   debug('Start generatefiles')
   mediapath = addon.getSetting('mediapath')
   pageanz = addon.getSetting('pages_anz')
   for page in range(1, int(pageanz) + 1):
        debug('Start Page: {0}'.format(page))
        token = getsession()
        nurl = '{0}&pageNumber={1}'.format(url, page)
        debug('URL newlist: {0}'.format(url))
        values = {
            'Model' : 'Huawei MLA-TL10',
            'AppVersion' : '3.3.15',
            'OsVersion': '4.4.4',
            'OsName': 'android',
            'Market': 'android',
            'Authorization': 'Bearer {0}'.format(token),
            # 'TimeStamp': '2017-09-04 11:04:45'
        }
        debug('Newlist url: {0}'.format(url))
        content = cache.cacheFunction(getUrl, nurl, 'GET', False, False, cj, values)
        struktur = json.loads(content)
        debug(struktur)
        count = 0
        once = 0
        for trailer in struktur['items']:
            id = trailer['id']
            image = trailer['poster_high']
            name = trailer['title']
            ppath = os.path.join(mediapath, fname.replace(' ', '_'), '')
            debug('ppath: {0}'.fomat(ppath))
            addLink(name, id, 'Play', image)
            count += 1
            filename = os.path.join(ppath, '{0}.strm'.format(name))
            if xbmcvfs.exists(ppath):
                if once == 1:
                    shutil.rmtree(ppath)
                    once = 0
                    xbmcvfs.mkdir(ppath)
            else:
               ret = xbmcvfs.mkdir(ppath)
               debug('Angelegt ppath {0}'.format(ret))
               once = 0
            file = xbmcvfs.File(filename, 'w')
            file.write('plugin://plugin.video.L0RE.cinetrailer/?mode=Play&url={0}'.format(id))
            file.close()
   xbmcplugin.endOfDirectory(addonhandle)


def clearCache():
    cache.delete('%')
    xbmcgui.Dialog().notification('Cinetrailer: Cache', 'Leeren des Caches erfolgreich', xbmcgui.NOTIFICATION_INFO, 2000, True)


if mode == '':
    index()
elif mode == 'newlist':
    newlist(url, page)
elif mode == 'Play':
    Play(url)
elif mode == 'genres':
    genres()
elif mode == 'Settings':
    addon.openSettings()
elif mode == 'tolibrary':
    tolibrary(url, name, stunden)
elif mode == 'generatefiles':
    generatefiles(url, name)
elif mode == 'clearCache':
    clearCache()