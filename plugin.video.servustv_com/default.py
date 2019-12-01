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
import json
import xbmcvfs
import shutil
import socket
import time
import io
import gzip


global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath    = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
temp        = xbmc.translatePath(os.path.join(dataPath, 'temp', '')).encode('utf-8').decode('utf-8')
channelFavsFile = os.path.join(dataPath, 'my_SERVUSTV_favourites.txt').encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
enableInputstream = addon.getSetting('inputstream') == 'true'
siteVersion = {0: 'de-de', 1: 'de-at'}[int(addon.getSetting('country'))]
useThumbAsFanart = addon.getSetting('useThumbAsFanart') == 'true'
enableAdjustment = addon.getSetting('show_settings') == 'true'
baseURL = 'https://www.servustv.com'

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

def getUrl(url, header=None, agent='Dalvik/2.1.0 (Linux; U; Android 7.1.2;)'):
	global cj
	for cook in cj:
		debug("(getUrl) Cookie : {0}".format(str(cook)))
	opener = build_opener(HTTPCookieProcessor(cj))
	opener.addheaders = [('User-Agent', agent), ('Accept-Encoding', 'gzip, deflate'), ('Accept-Language', siteVersion), ('Authorization', 'DeviceId 427502496159111')]
	try:
		if header: opener.addheaders = header
		response = opener.open(url, timeout=30)
		if response.info().get('Content-Encoding') == 'gzip':
			content = py3_dec(gzip.GzipFile(fileobj=io.BytesIO(response.read())).read())
		else:
			content = py3_dec(response.read())
	except Exception as e:
		failure = str(e)
		failing("(getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
		#xbmcgui.Dialog().notification(translation(30521).format('URL'), "ERROR = [COLOR red]{0}[/COLOR]".format(failure), icon, 15000)
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

def index():
	addDir(translation(30601), "", 'listShowsFavs', icon)
	addDir(translation(30602), "https://api.servustv.com/videolists?start&broadcast_limit=5", 'listStartpage', icon)
	addDir(translation(30603), "https://api.servustv.com/topics", 'listTopics', icon)
	addDir(translation(30604), "https://api.servustv.com/series", 'listAllShows', icon)
	addDir(translation(30605), "", 'play_LIVE', icon, folder=False)
	if enableAdjustment:
		addDir(translation(30608), "", 'aSettings', icon)
		if enableInputstream:
			if ADDON_operate('inputstream.adaptive'):
				addDir(translation(30609), "", 'iSettings', icon)
			else:
				addon.setSetting('inputstream', 'false')
	xbmcplugin.endOfDirectory(pluginhandle)

def listStartpage(url, typus):
	debug("(listStartpage) ------------------------------------------------ START = listStartpage -----------------------------------------------")
	content = getUrl(url)
	debug("++++++++++++++++++++++++")
	debug("(listStartpage) CONTENT : {0}".format(str(content)))
	debug("++++++++++++++++++++++++")
	ISOLATED = set()
	DATA = json.loads(content) 
	for element in DATA['videolists']:
		debug("(listStartpage) ### ELEMENT : {0} ###".format(str(element)))
		title = py2_enc(element['title']).strip()
		debug("(listStartpage) ### TITLE = {0} || TYPUS = {1} ###".format(title, str(typus)))
		if typus == "":
			addDir(title, url, 'listStartpage', icon, typus=title)
		else:
			if typus == "Alles" or typus==title:
				for item in element['broadcasts']:
					if 'has_video' in item and item['has_video'] == True:
						idd = str(item['id'])
						if idd in ISOLATED:
							continue
						ISOLATED.add(idd)
						name = py2_enc(item['title']).strip()
						subtitle = py2_enc(item['subtitle']).strip()
						duration = item['vod_duration']
						try: photo = item['images'][0]['url']#.replace('w_930,h_521,', 'w_1280,h_720,')
						except: photo =""
						addLink(name +" - "+subtitle, idd, 'playVideo', photo, duration)
	if typus == "":
		addDir("Alles", url, 'listStartpage', icon, typus="Alles")
	xbmcplugin.endOfDirectory(pluginhandle)

def listTopics(url):
	debug("(listTopics) ------------------------------------------------ START = listTopics -----------------------------------------------")
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
	content = getUrl(url)
	debug("++++++++++++++++++++++++")
	debug("(listTopics) CONTENT : {0}".format(str(content)))
	debug("++++++++++++++++++++++++")
	DATA = json.loads(content)
	for element in DATA['topics']:
		idd = str(element['id'])
		title = py2_enc(element['title']).strip()
		debug("(listTopics) ### TITLE = {0} || IDD = {1} ###".format(title, idd))
		addDir(title, idd, 'listSubTopics', icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def listSubTopics(Xidd):
	debug("(listSubTopics) ------------------------------------------------ START = listSubTopics -----------------------------------------------")
	url_1 = "https://api.servustv.com/topics/"+Xidd+"/series?vod_only&broadcast_limit=50&limit=500"  
	content1 = getUrl(url_1)
	debug("++++++++++++++++++++++++")
	debug("(listSubTopics) CONTENT-01 : {0}".format(str(content1)))
	debug("++++++++++++++++++++++++")
	DATA_1 = json.loads(content1)
	for element in DATA_1['series']:
		if 'broadcast_count' in element and int(element['broadcast_count']) >= 1:
			xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
			idd_1 = str(element['id'])
			title_1 = py2_enc(element['title']).strip()
			try: photo_1 = element['images'][0]['url']
			except: photo_1 =""
			addType=1
			if os.path.exists(channelFavsFile):
				with open(channelFavsFile, 'r') as output:
					lines = output.readlines()
					for line in lines:
						if line.startswith('###START'):
							part = line.split('###')
							idd_FS = part[2]
							if idd_1 == idd_FS: addType=2
			debug("(listSubTopics) ### TITLE-1 = {0} || IDD-1 = {1} || PHOTO-1 = {2} ###".format(title_1, idd_1, photo_1))
			addDir(title_1, idd_1, 'listEpisodes', photo_1, originalSERIE=title_1, addType=addType)
	url_2 = "https://api.servustv.com/topics/"+Xidd+"/broadcasts?vod_only&no_series=&broadcast_limit=5"
	content2 = getUrl(url_2)
	debug("++++++++++++++++++++++++")
	debug("(listSubTopics) CONTENT-02 : {0}".format(str(content2)))
	debug("++++++++++++++++++++++++")
	DATA_2 = json.loads(content2)
	for vid in DATA_2['broadcasts']:
		if 'has_video' in vid and vid['has_video'] == True:
			idd_2 = str(vid['id'])
			name_2 = py2_enc(vid['title']).strip()
			subtitle_2 = py2_enc(vid['subtitle']).strip()
			duration_2 = vid['vod_duration']
			try: photo_2 = vid['images'][0]['url']
			except: photo_2 =""
			debug("(listSubTopics) ### TITLE-2 = {0} || IDD-2 = {1} || PHOTO-2 = {2} ###".format(name_2+" - "+subtitle_2, idd_2, photo_2))
			addLink(name_2+" - "+subtitle_2, idd_2, 'playVideo', photo_2, duration_2)
	xbmcplugin.endOfDirectory(pluginhandle)

def listAllShows():
	debug("(listAllShows) ------------------------------------------------ START = listAllShows -----------------------------------------------")
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
	content = getUrl("https://api.servustv.com/series")
	debug("++++++++++++++++++++++++")
	debug("(listAllShows) CONTENT : {0}".format(str(content)))
	debug("++++++++++++++++++++++++")
	DATA = json.loads(content) 
	for element in DATA['series']:
		if 'broadcast_count' in element and int(element['broadcast_count']) >= 1:
			idd = str(element['id'])
			title = py2_enc(element['title']).strip()
			try: photo = element['images'][0]['url']
			except:
				try: photo = element['2'][0]['url']
				except: photo = ""
			addType=1
			if os.path.exists(channelFavsFile):
				with open(channelFavsFile, 'r') as output:
					lines = output.readlines()
					for line in lines:
						if line.startswith('###START'):
							part = line.split('###')
							idd_FS = part[2]
							if idd == idd_FS: addType=2
			debug("(listAllShows) ### TITLE = {0} || IDD = {1} || PHOTO = {2} ###".format(title, idd, photo))
			addDir(title, idd, 'listEpisodes', photo, originalSERIE=title, addType=addType)
	xbmcplugin.endOfDirectory(pluginhandle)  

def listEpisodes(Xidd, originalSERIE):
	debug("(listEpisodes) ------------------------------------------------ START = listEpisodes -----------------------------------------------")
	url = "https://api.servustv.com/series/"+Xidd+"?vod_only&broadcast_limit=500"
	content = getUrl(url)
	debug("++++++++++++++++++++++++")
	debug("(listEpisodes) CONTENT : {0}".format(str(content)))
	debug("++++++++++++++++++++++++")
	DATA = json.loads(content)
	FOUND = False
	for vid in  DATA['series']['broadcasts']:
		if 'has_video' in vid and vid['has_video'] == True:
			FOUND = True
			idd = str(vid['id'])
			name = py2_enc(vid['title']).strip()
			subtitle = py2_enc(vid['subtitle']).strip()
			mpaa =""
			if 'fsk' in vid and vid['fsk'] != "" and str(vid['fsk']) != "0" and vid['fsk'] != None:
				mpaa = translation(30611).format(str(vid['fsk']))
			plot = ""
			if 'description' in vid and vid['description'] != "" and vid['description'] != None:
				plot = py2_enc(vid['description']).replace('<br />', '').strip()
			duration = vid['vod_duration']
			try: photo = vid['images'][0]['url']
			except: photo =""
			debug("(listEpisodes) ### TITLE = {0} || IDD = {1} || PHOTO = {2} ###".format(name+" - "+subtitle, idd, photo))
			addLink(name+" - "+subtitle, idd, 'playVideo', photo, duration, plot, mpaa)
	if not FOUND:
		debug("(listepisodes) ##### Keine Episode in der Liste - Kein Eintrag gefunden #####")
		return xbmcgui.Dialog().notification(translation(30523), translation(30524).format(originalSERIE), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle) 

def playVideo(Xidd):
	debug("(playVideo) ------------------------------------------------ START = playVideo -----------------------------------------------")
	url = "https://api.servustv.com/broadcasts/"+Xidd
	content = getUrl(url)
	debug("++++++++++++++++++++++++")
	debug("(playVideo) CONTENT : {0}".format(str(content)))
	debug("++++++++++++++++++++++++")
	finalURL = json.loads(content)['broadcast']['vod_hls_link']
	log("(playVideo) HLS_stream : {0}".format(finalURL))
	listitem = xbmcgui.ListItem(path=finalURL)
	if enableInputstream and 'm3u8' in finalURL:
		if ADDON_operate('inputstream.adaptive'):
			listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
			listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
			listitem.setMimeType('application/vnd.apple.mpegurl')
		else:
			addon.setSetting('inputstream', 'false')
	xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def play_LIVE():
	debug("(play_LIVE) ------------------------------------------------ START = play_LIVE -----------------------------------------------")
	# https://liveservustv-i.akamaihd.net/hls/live/271000/ServusTV_DE/master.m3u8
	# https://liveservustv-i.akamaihd.net/hls/live/270998/ServusTV_AT/master.m3u8
	live_url = 'https://rbmn-live.akamaized.net/hls/live/2002830/geoSTVDEweb/master.m3u8'
	title = '[COLOR lime]* ServusTV-DE LIVE-TV *[/COLOR]'
	if siteVersion == 'de-at':
		live_url = 'https://rbmn-live.akamaized.net/hls/live/2002825/geoSTVATweb/master.m3u8'
		title = '[COLOR lime]* ServusTV-AT LIVE-TV *[/COLOR]'
	debug("(play_LIVE) ### LIVEurl : {0} ###".format(live_url))
	listitem = xbmcgui.ListItem(path=live_url, label=title)
	listitem.setMimeType('application/vnd.apple.mpegurl')
	xbmc.Player().play(item=live_url, listitem=listitem)

def listShowsFavs():
	debug("(listShowsFavs) ------------------------------------------------ START = listShowsFavs -----------------------------------------------")
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
	if os.path.exists(channelFavsFile):
		with open(channelFavsFile, 'r') as textobj:
			lines = textobj.readlines()
			for line in lines:
				if line.startswith('###START'):
					part = line.split('###')
					addDir(name=part[3], url=part[2], mode='listEpisodes', image=part[4].strip(), originalSERIE=part[3], FAVdel=True)
					debug("(listShowsFavs) ### TITLE = {0} || IDD = {1} || PHOTO = {2} ###".format(str(part[3]), str(part[2]), str(part[4])))
	xbmcplugin.endOfDirectory(pluginhandle)

def favs(param):
	mode = param[param.find('MODE=')+5:+8]
	SERIES_entry = param[param.find('###START'):]
	SERIES_entry = SERIES_entry[:SERIES_entry.find('END###')]
	name = SERIES_entry.split('###')[3]
	url = SERIES_entry.split('###')[2]
	if mode == 'ADD':
		if os.path.exists(channelFavsFile):
			with open(channelFavsFile, 'a+') as textobj:
				content = textobj.read()
				if content.find(SERIES_entry) == -1:
					textobj.seek(0,2) # change is here (for Windows-Error = "IOError: [Errno 0] Error") - because Windows don't like switching between reading and writing at same time !!!
					textobj.write(SERIES_entry+'END###\n')
		else:
			with open(channelFavsFile, 'a') as textobj:
				textobj.write(SERIES_entry+'END###\n')
		xbmc.sleep(500)
		xbmcgui.Dialog().notification(translation(30525), translation(30526).format(name), icon, 8000)
	elif mode == 'DEL':
		with open(channelFavsFile, 'r') as output:
			lines = output.readlines()
		with open(channelFavsFile, 'w') as input:
			for line in lines:
				if url not in line:
					input.write(line)
		xbmc.executebuiltin('Container.Refresh')
		xbmc.sleep(1000)
		xbmcgui.Dialog().notification(translation(30525), translation(30527).format(name), icon, 8000)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

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

def addLink(name, url, mode, image, duration=None, plot=None, mpaa=None, genre=None):
	u = sys.argv[0]+'?url='+quote_plus(url)+'&mode='+str(mode)
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot, 'Duration': duration, 'Genre': genre, 'Mpaa': mpaa, 'Studio': 'ServusTV'})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon:
		liz.setArt({'fanart': image})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	liz.setContentLookup(False)
	playInfos = '###START###{0}###{1}###{2}###END###'.format(u, name, image)
	liz.addContextMenuItems([(translation(30653), 'RunPlugin('+sys.argv[0]+'?mode=addQueue&url='+quote_plus(playInfos)+')')])
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

def addDir(name, url, mode, image, plot=None, typus="", originalSERIE="", folder=True, addType=0, FAVdel=False):
	u = sys.argv[0]+'?url='+quote_plus(url)+'&mode='+str(mode)+'&typus='+str(typus)+'&originalSERIE='+quote_plus(originalSERIE)
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon:
		liz.setArt({'fanart': image})
	entries = []
	if addType == 1 and FAVdel == False:
		playInfos_1 = 'MODE=ADD###START###{0}###{1}###{2}###END###'.format(url, originalSERIE, image)
		entries.append([translation(30651), 'RunPlugin('+sys.argv[0]+'?mode=favs&url='+quote_plus(playInfos_1)+')'])
	if FAVdel == True:
		playInfos_2 = 'MODE=DEL###START###{0}###{1}###{2}###END###'.format(url, name, image)
		entries.append([translation(30652), 'RunPlugin('+sys.argv[0]+'?mode=favs&url='+quote_plus(playInfos_2)+')'])
	liz.addContextMenuItems(entries, replaceItems=False)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=folder)

params = parameters_string_to_dict(sys.argv[2])
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
typus = unquote_plus(params.get('typus', ''))
originalSERIE = unquote_plus(params.get('originalSERIE', ''))

if mode == 'listStartpage':
	listStartpage(url, typus)
elif mode == 'listTopics':
	listTopics(url)
elif mode == 'listSubTopics':
	listSubTopics(url)
elif mode == 'listAllShows':
	listAllShows()
elif mode == 'listEpisodes':
	listEpisodes(url, originalSERIE)
elif mode == 'playVideo':
	playVideo(url)
elif mode == 'play_LIVE':
	play_LIVE()
elif mode == 'listShowsFavs':
	listShowsFavs()
elif mode == 'favs':
	favs(url)
elif mode == 'addQueue':
	addQueue(url)
elif mode == 'aSettings':
	addon.openSettings()
elif mode == 'iSettings':
	xbmcaddon.Addon('inputstream.adaptive').openSettings()
else:
	index()