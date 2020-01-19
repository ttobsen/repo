#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
	from urllib import quote, unquote, quote_plus, unquote_plus, urlencode  # Python 2.X
	from urllib2 import build_opener, HTTPCookieProcessor, Request, urlopen  # Python 2.X
	from cookielib import LWPCookieJar  # Python 2.X
	from urlparse import urljoin, urlparse, urlunparse  # Python 2.X
elif PY3:
	from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode, urljoin, urlparse, urlunparse  # Python 3+
	from urllib.request import build_opener, HTTPCookieProcessor, Request, urlopen  # Python 3+
	from http.cookiejar import LWPCookieJar  # Python 3+
try: import StorageServer
except: from . import storageserverdummy as StorageServer
import json
import xbmcvfs
import shutil
import socket
import time
from datetime import datetime, timedelta
import io
import gzip


global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
socket.setdefaulttimeout(40)
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
temp        = xbmc.translatePath(os.path.join(dataPath, 'temp', '')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
artpic = os.path.join(addonPath, 'resources', 'media', '').encode('utf-8').decode('utf-8')
enableInputstream = addon.getSetting('inputstream') == 'true'
prefSTREAM = addon.getSetting('streamSelection')
prefQUALITY = {0: 'hd720', 1: 'mediumlarge', 2: 'medium', 3: 'small'}[int(addon.getSetting('prefVideoQuality'))]
cachePERIOD = int(addon.getSetting('cacherhythm'))
cache = StorageServer.StorageServer(addon.getAddonInfo('id'), cachePERIOD) # (Your plugin name, Cache time in hours)
baseURL = "http://3plus.tv"

xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

if xbmcvfs.exists(temp) and os.path.isdir(temp):
	shutil.rmtree(temp, ignore_errors=True)
	xbmc.sleep(500)
xbmcvfs.mkdirs(temp)
cookie = os.path.join(temp, 'cookie.lwp')
cj = LWPCookieJar()

if xbmcvfs.exists(cookie):
	cj.load(cookie, ignore_discard=True, ignore_expires=True)

def py2_enc(s, encoding='utf-8'):
	if PY2:
		if not isinstance(s, basestring):
			s = str(s)
		s = s.encode(encoding) if isinstance(s, unicode) else s
	return s

def py2_uni(s, encoding='utf-8'):
	if PY2 and isinstance(s, str):
		s = unicode(s, encoding)
	return s

def py3_dec(d, encoding='utf-8'):
	if PY3 and isinstance(d, bytes):
		d = d.decode(encoding)
	return d

def translation(id):
	return py2_enc(addon.getLocalizedString(id))

def failing(content):
	log(content, xbmc.LOGERROR)

def debug(content):
	log(content, xbmc.LOGDEBUG)

def log(msg, level=xbmc.LOGNOTICE):
	xbmc.log("["+addon.getAddonInfo('id')+"-"+addon.getAddonInfo('version')+"]"+py2_enc(msg), level)

def makeREQUEST(url):
	return cache.cacheFunction(getUrl, url)

def getUrl(url, header=None, referer=None, agent='Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0'):
	global cj
	for cook in cj:
		debug("(getUrl) Cookie : {0}".format(str(cook)))
	opener = build_opener(HTTPCookieProcessor(cj))
	opener.addheaders = [('User-Agent', agent), ('Accept-Encoding', 'gzip, deflate')]
	try:
		if header: opener.addheaders = header
		if referer: opener.addheaders = [('Referer', referer)]
		response = opener.open(url, timeout=40)
		if response.info().get('Content-Encoding') == 'gzip':
			content = py3_dec(gzip.GzipFile(fileobj=io.BytesIO(response.read())).read())
		else:
			content = py3_dec(response.read())
	except Exception as e:
		failure = str(e)
		failing("(getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
		xbmcgui.Dialog().notification(translation(30521).format('URL'), "ERROR = [COLOR red]{0}[/COLOR]".format(failure), icon, 15000)
		content = ""
		return sys.exit(0)
	opener.close()
	try: cj.save(cookie, ignore_discard=True, ignore_expires=True)
	except: pass
	return content

def ADDON_operate(IDD):
	js_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.GetAddonDetails", "params": {"addonid":"'+IDD+'", "properties": ["enabled"]}, "id":1}')
	if '"enabled":false' in js_query:
		try:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.SetAddonEnabled", "params": {"addonid":"'+IDD+'", "enabled":true}, "id":1}')
			failing("(ADDON_operate) ERROR - ERROR - ERROR :\n##### Das benötigte Addon : *{0}* ist NICHT aktiviert !!! #####\n##### Es wird jetzt versucht die Aktivierung durchzuführen !!! #####".format(IDD))
		except: pass
	if '"error":' in js_query:
		xbmcgui.Dialog().ok(addon.getAddonInfo('id'), translation(30501).format(IDD))
		failing("(ADDON_operate) ERROR - ERROR - ERROR :\n##### Das benötigte Addon : *{0}* ist NICHT installiert !!! #####".format(IDD))
		return False
	if '"enabled":true' in js_query:
		return True

def clearCache():
	debug("(clearCache) -------------------------------------------------- START = clearCache --------------------------------------------------")
	debug("(clearCache) ========== Lösche jetzt den Addon-Cache ==========")
	cache.delete('%')
	xbmc.sleep(1000)
	xbmcgui.Dialog().ok(addon.getAddonInfo('id'), translation(30502))

def index():
	addDir(translation(30601), "", 'listSeries', icon)
	addDir(translation(30602).format(str(cachePERIOD)), "", 'clearCache', icon)
	addDir(translation(30603), "", 'aSettings', icon)
	if enableInputstream:
		if ADDON_operate('inputstream.adaptive'):
			addDir(translation(30604), "", 'iSettings', icon)
		else:
			addon.setSetting("inputstream", "false")
	xbmcplugin.endOfDirectory(pluginhandle)

def listSeries():
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	un_WANTED = ['free-tv', 'jubiläumsfilm', 'trailer', 'weihnachtsüber']
	html = makeREQUEST(baseURL+'/videos') 
	content = html[html.find('class="view view-videos view-id-videos view-display-id-block_8 view-dom-id-4"')+1:]
	content = content[:content.find('</div>')]
	series = re.findall('<a href="([^"]+?)">(.*?)</a>', content, re.DOTALL)
	for link, title in series:
		if link[:4] != 'http': link = baseURL+link
		title = cleanTitle(title)
		photo = artpic+link.lower().split('videos/')[1]+'.jpg'
		if not any(x in title.lower() for x in un_WANTED):
			addDir(title, link, 'listSeasons', photo)
	xbmcplugin.endOfDirectory(pluginhandle)

def listSeasons(url):
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
	un_WANTED = ['aufruf', 'talk', 'trailer']
	html = makeREQUEST(url)
	seasons = re.findall('div class="views-field-title-1(.*?)</div>', html, re.DOTALL)
	for entry in seasons:
		matchUT = re.compile('<a href="([^"]+?)">(.*?)</a>', re.DOTALL).findall(entry)
		link = matchUT[0][0].strip()
		if link[:4] != 'http': link = baseURL+link
		title = cleanTitle(matchUT[0][1])
		photo = artpic+link.lower().split('/')[-2]+'.jpg'
		if not any(x in title.lower() for x in un_WANTED):
			addDir(title, link, 'listEpisodes', photo)
	xbmcplugin.endOfDirectory(pluginhandle)

def listEpisodes(CONN, url):
	pos = 0
	videoIsolated = set()
	myList = []
	imgCODE = ['aufruf', 'artboard', '_rz_', '_sn_', 'snippets', 'standphoto', 'web']
	wanted = ['big pictures', 'episode', 'folge', 'vorstellung', 'zur alten', ' (', '_portrait']
	un_WANTED = ['anmelden', 'aufruf', 'highlights', 'talk', 'teaser', 'trailer']
	html = makeREQUEST(url)
	if '<div class="views-field-title-1">' in html:
		seasons2 = re.findall('div class="views-field-title-1(.*?)</div>', html, re.DOTALL)
		for entry in seasons2:
			matchUT = re.compile('<a href="([^"]+?)(?:">|" class="active">)(.*?)</a>', re.DOTALL).findall(entry)
			link2 = matchUT[0][0].strip()
			if link2[:4] != 'http': link2 = baseURL+link2
			title2 = cleanTitle(matchUT[0][1])
			if '<H6>' in title2: title2 = title2.split('<H6>')[0]
			debug("(listEpisodes) ##### Seasons_2-Url : "+link2+" #####")
			myList.append([title2, link2])
	else:
		link2 = url
		title2 = CONN
		myList.append([title2, link2])
	for title2, link2 in myList:
		content = makeREQUEST(link2)
		result = content[content.find('<div id="video_list_placeholder">')+1:]
		part = result.split('<li class="views-row views-row')
		for i in range(1, len(part), 1):
			element = part[i]
			debug("(listEpisodes) ##### ELEMENT : "+str(element)+" #####")
			try:
				token = re.compile('class="views-field-field-threeq-value.+?class="field-content ">([^<]+?)</div>', re.DOTALL).findall(element)[0].strip()
				debug("(listEpisodes) ##### TOKEN : "+token+" #####")
			except: continue
			name = re.compile('class="views-field-title.+?class="field-content ">(.+?)</div>', re.DOTALL).findall(element)[0]
			name = cleanTitle(name)
			photo = re.compile('class="views-field-field-playlist-thumb-fid.+?<img src="([^"]+?)"', re.DOTALL).findall(element)[0].strip().replace('/imagecache/playlist_video', '').replace('/imagecache/playlist_big', '')
			if any(p in photo.lower() for p in imgCODE) and not any(q in photo.lower() for q in wanted) and not any(y in name.lower() for y in wanted):
				debug("(listEpisodes) ##### PHOTO (not wanted)  : "+photo+" #####")
				continue
			if name in videoIsolated:
				debug("(listEpisodes) ##### NAME (double deleted) : "+name+" #####")
				continue
			videoIsolated.add(name)
			if (not any(x in name.lower() for x in un_WANTED)) and ((any(y in name.lower() for y in wanted)) or not any(y in name.lower() for y in wanted)):
				pos += 1
				addLink(name, token, 'playVideo', photo)
			if any(x in name.lower() for x in un_WANTED) and pos < 1:
				addLink(name, token, 'playVideo', photo)
	xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(token1):
	headerfields = "User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0"
	QUALITIES = ['hd720', 'mediumlarge', 'medium', 'small']
	DATA = {}
	DATA['media'] = []
	RESERVE = {}
	RESERVE['media'] = []
	finalURL = False
	streamTYPE = False
	# firstUrl = http://playout.3qsdn.com/7b26f470-e224-11e6-a78b-0cc47a188158?timestamp=0&autoplay=false&key=0&js=true&container=sdnPlayer&width=100%&height=100%&protocol=http&vastid=0&playlistbar=false
	firstUrl = "http://playout.3qsdn.com/"+token1+"?timestamp=0&key=0&js=true&container=sdnPlayer&width=100%&height=100%&protocol=http&vastid=0&wmode=direct&preload=true&amp=false"
	ref1 = "http://playout.3qsdn.com/"+token1
	content1 = getUrl(firstUrl, referer=ref1)
	debug("(playVideo) ##### firstURL : "+firstUrl+" #####")
	content1 = cleanSymbols(content1)
	videos1 = re.compile("{src:'(.+?)', type: '(.+?)', quality: '(.+?)'", re.DOTALL).findall(content1) 
	for found in QUALITIES:
		for vid, type, quality in videos1:
			if (type == "application/vnd.apple.mpegURL" or type == "application/x-mpegurl" or type== "video/mp4") and quality == found:
				DATA['media'].append({'url': vid, 'mimeType': type, 'standard': quality})
				debug("(playVideo) listing1_DATA[media] ### standard : "+quality+" ### url : "+vid+" ### mimeType : "+type+" ###")
	if DATA['media']:
		for found in QUALITIES:
			for item in DATA['media']:
				if enableInputstream:
					if ADDON_operate('inputstream.adaptive'):
						if item['mimeType'].lower() == 'application/vnd.apple.mpegurl' and item['standard'].lower() == found:
							finalURL = item['url']
							streamTYPE = 'HLS'
							debug("(playVideo) listing1_HLS ### standard : "+item['standard']+" ### finalURL : "+finalURL+" ### mimeType : "+item['mimeType']+" ### streamTYPE : "+streamTYPE+" ###")
					else:
						addon.setSetting("inputstream", "false")
				if not enableInputstream and prefSTREAM == "0" and item['mimeType'].lower() == 'application/x-mpegurl' and item['standard'].lower() == found:
					finalURL = item['url']
					streamTYPE = 'M3U8'
					debug("(playVideo) listing1_M3U8 ### standard : "+item['standard']+" ### finalURL : "+finalURL+" ### mimeType : "+item['mimeType']+" ### streamTYPE : "+streamTYPE+" ###")
				if not enableInputstream and prefSTREAM == "1" and item['mimeType'].lower() == 'video/mp4' and item['standard'].lower() == prefQUALITY:
					finalURL = item['url']
					streamTYPE = 'MP4'
					debug("(playVideo) listing1_MP4 ### standard : "+item['standard']+" ### finalURL : "+finalURL+" ### mimeType : "+item['mimeType']+" ### streamTYPE : "+streamTYPE+" ###")
	if not finalURL and DATA['media']:
		for found in QUALITIES:
			for item in DATA['media']:
				if item['mimeType'].lower() == 'video/mp4' and item['standard'].lower() == found:
					RESERVE['media'].append({'url': item['url'], 'mimeType': item['mimeType'], 'standard': item['standard']})
		finalURL = RESERVE['media'][0]['url']
		streamTYPE = 'MP4'
		debug("(playVideo) listing1_Reserve_MP4 ### standard : "+RESERVE['media'][0]['standard']+" ### finalURL : "+finalURL+" ### mimeType : "+RESERVE['media'][0]['mimeType']+" ### streamTYPE : "+streamTYPE+" ###")
	if not finalURL and not streamTYPE:
		token2 = re.compile("sdnPlayoutId:'(.+?)'", re.DOTALL).findall(content1)[0]
		# secondUrl =  http://playout.3qsdn.com/0702727c-0d5d-11e7-a78b-0cc47a188158?timestamp=0&key=0&js=true&autoplay=false&container=sdnPlayer_player&width=100%25&height=100%25&protocol=http&token=0&vastid=0&jscallback=sdnPlaylistBridge
		secondUrl = "http://playout.3qsdn.com/"+token2+"?timestamp=0&key=0&js=true&autoplay=false&container=sdnPlayer_player&width=100%25&height=100%25&protocol=http&token=0&vastid=0&jscallback=sdnPlaylistBridge"
		ref2 = "http://playout.3qsdn.com/"+token2
		content2 = getUrl(secondUrl, referer=ref2)
		debug("(playVideo) ##### secondURL : "+secondUrl+" #####")
		content2 = cleanSymbols(content2)
		videos2 = re.compile("{src:'(.+?)', type: '(.+?)', quality: '(.+?)'", re.DOTALL).findall(content2)
		for found in QUALITIES:
			for vid, type, quality in videos2:
				if (type == "application/vnd.apple.mpegURL" or type == "application/x-mpegurl" or type== "video/mp4") and quality == found:
					DATA['media'].append({'url': vid, 'mimeType': type, 'standard': quality})
					debug("(playVideo) listing2_DATA[media] ### standard : "+quality+" ### url : "+vid+" ### mimeType : "+type+" ###")
		if DATA['media']:
			for found in QUALITIES:
				for item in DATA['media']:
					if enableInputstream:
						if ADDON_operate('inputstream.adaptive'):
							if item['mimeType'].lower() == 'application/vnd.apple.mpegurl' and item['standard'].lower() == found:
								finalURL = item['url']
								streamTYPE = 'HLS'
								debug("(playVideo) listing2_HLS ### standard : "+item['standard']+" ### finalURL : "+finalURL+" ### mimeType : "+item['mimeType']+" ### streamTYPE : "+streamTYPE+" ###")
						else:
							addon.setSetting("inputstream", "false")
					if not enableInputstream and prefSTREAM == "0" and item['mimeType'].lower() == 'application/x-mpegurl' and item['standard'].lower() == found:
						finalURL = item['url']
						streamTYPE = 'M3U8'
						debug("(playVideo) listing2_M3U8 ### standard : "+item['standard']+" ### finalURL : "+finalURL+" ### mimeType : "+item['mimeType']+" ### streamTYPE : "+streamTYPE+" ###")
					if not enableInputstream and prefSTREAM == "1" and item['mimeType'].lower() == 'video/mp4' and item['standard'].lower() == prefQUALITY:
						finalURL = item['url']
						streamTYPE = 'MP4'
						debug("(playVideo) listing2_MP4 ### standard : "+item['standard']+" ### finalURL : "+finalURL+" ### mimeType : "+item['mimeType']+" ### streamTYPE : "+streamTYPE+" ###")
	if not finalURL and DATA['media']:
		for found in QUALITIES:
			for item in DATA['media']:
				if item['mimeType'].lower() == 'video/mp4' and item['standard'].lower() == found:
					RESERVE['media'].append({'url': item['url'], 'mimeType': item['mimeType'], 'standard': item['standard']})
		finalURL = RESERVE['media'][0]['url']
		streamTYPE = 'MP4'
		debug("(playVideo) listing2_Reserve_MP4 ### standard : "+RESERVE['media'][0]['standard']+" ### finalURL : "+finalURL+" ### mimeType : "+RESERVE['media'][0]['mimeType']+" ### streamTYPE : "+streamTYPE+" ###")
	if finalURL and streamTYPE:
		if streamTYPE == 'M3U8':
			log("(playVideo) M3U8_stream : {0}".format(finalURL))
			finalURL = finalURL.split(".m3u8")[0]+".m3u8"
		if streamTYPE == 'MP4':
			log("(playVideo) MP4_stream : {0}".format(finalURL))
			finalURL = finalURL.split(".mp4")[0]+".mp4"
		listitem = xbmcgui.ListItem(path=finalURL)
		if streamTYPE == 'HLS':
			log("(playVideo) HLS_stream : {0}".format(finalURL))
			listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
			listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
			listitem.setMimeType('application/vnd.apple.mpegurl')
		listitem.setContentLookup(False)
		xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
	else: 
		failing("(playVideo) ##### Abspielen des Videos NICHT möglich - URL : {0} - #####\n    ########## KEINEN Stream-Eintrag auf der Webseite von *3plus.tv* gefunden !!! ##########".format(url))
		xbmcgui.Dialog().notification(translation(30521).format('PLAY'), translation(30523), icon, 8000)

def cleanSymbols(sym):
	sym = py2_enc(sym)
	for y in (('\\x2A', '*'), ('\\x2B', '+'), ('\\x2D', '-'), ('\\x2E', '.'), ('\\x2F', '/'), ('\\x5F', '_')
		, ('\\u002A', '*'), ('\\u002B', '+'), ('\\u002D', '-'), ('\\u002E', '.'), ('\\u002F', '/'), ('\\u005F', '_'), ('\/', '/')):
		sym = sym.replace(*y)
	return sym

def cleanTitle(text):
	text = py2_enc(text)
	for n in (('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'), ('&apos;', "'"), ("&#x27;", "'"), ('&#34;', '"'), ('&#39;', '\''), ('&#039;', '\''), ('►', '>'), ('3+ ', '')
		, ('&#x00c4', 'Ä'), ('&#x00e4', 'ä'), ('&#x00d6', 'Ö'), ('&#x00f6', 'ö'), ('&#x00dc', 'Ü'), ('&#x00fc', 'ü'), ('&#x00df', 'ß'), ('&#xD;', ''), ('\xc2\xb7', '-')
		, ('&quot;', '"'), ('&szlig;', 'ß'), ('&ndash;', '-'), ('&Auml;', 'Ä'), ('&Ouml;', 'Ö'), ('&Uuml;', 'Ü'), ('&auml;', 'ä'), ('&ouml;', 'ö'), ('&uuml;', 'ü')
		, ('&agrave;', 'à'), ('&aacute;', 'á'), ('&acirc;', 'â'), ('&egrave;', 'è'), ('&eacute;', 'é'), ('&ecirc;', 'ê'), ('&igrave;', 'ì'), ('&iacute;', 'í'), ('&icirc;', 'î')
		, ('&ograve;', 'ò'), ('&oacute;', 'ó'), ('&ocirc;', 'ô'), ('&ugrave;', 'ù'), ('&uacute;', 'ú'), ('&ucirc;', 'û')):
		text = text.replace(*n)
	return text.strip()

def addQueue(param):
	PL = xbmc.PlayList(1)
	MEDIA_entry = param[param.find('###START'):]
	MEDIA_entry = MEDIA_entry[:MEDIA_entry.find('END###')]
	url = MEDIA_entry.split('###')[2]
	name = MEDIA_entry.split('###')[3]
	image = MEDIA_entry.split('###')[4]
	listitem = xbmcgui.ListItem(name)
	listitem.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	listitem.setProperty('IsPlayable', 'true')
	listitem.setContentLookup(False)
	PL.add(url, listitem)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, plot=None):
	u = sys.argv[0]+'?url='+quote_plus(url)+'&mode='+str(mode)
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if image != icon:
		liz.setArt({'fanart': image})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
  
def addLink(name, url, mode, image, plot=None, duration=None, genre=None, studio=None):
	u = sys.argv[0]+'?url='+quote_plus(url)+'&mode='+str(mode)
	liz = xbmcgui.ListItem(name)
	ilabels = {}
	ilabels['Season'] = None
	ilabels['Episode'] = None
	ilabels['Tvshowtitle'] = None
	ilabels['Title'] = name
	ilabels['Tagline'] = None
	ilabels['Plot'] = plot
	ilabels['Duration'] = duration
	ilabels['Year'] = None
	ilabels['Genre'] = genre
	ilabels['Director'] = None
	ilabels['Writer'] = None
	ilabels['Studio'] = '3plus.tv'
	ilabels['Mpaa'] = None
	ilabels['Mediatype'] = 'video'
	liz.setInfo(type='Video', infoLabels=ilabels)
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if image != icon:
		liz.setArt({'fanart': image})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	liz.setContentLookup(False)
	xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
	playInfos = '###START###{0}###{1}###{2}###END###'.format(u, name, image)
	liz.addContextMenuItems([(translation(30654), 'RunPlugin('+sys.argv[0]+'?mode=addQueue&url='+quote_plus(playInfos)+')')])
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
referer = unquote_plus(params.get('referer', ''))

if mode == 'aSettings':
	xbmcaddon.Addon('plugin.video.3plus_ch').openSettings()
elif mode == 'iSettings':
	xbmcaddon.Addon('inputstream.adaptive').openSettings()
elif mode == 'clearCache':
	clearCache()
elif mode == 'listSeries':
	listSeries()
elif mode == 'listSeasons':
	listSeasons(url)
elif mode == 'listEpisodes':
	listEpisodes(name, url)
elif mode == 'playVideo':
	playVideo(url)
elif mode == 'addQueue':
	addQueue(url)
else:
	index()