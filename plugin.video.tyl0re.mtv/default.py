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
	from urllib2 import build_opener, Request, urlopen  # Python 2.X
	from urlparse import urljoin, urlparse, urlunparse  # Python 2.X
elif PY3:
	from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode, urljoin, urlparse, urlunparse  # Python 3+
	from urllib.request import build_opener, Request, urlopen  # Python 3+
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
import random
from bs4 import BeautifulSoup
import ssl

try: _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context


global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg') or os.path.join(addonPath, 'resources', 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png') or os.path.join(addonPath, 'resources', 'icon.png')
artpic = os.path.join(addonPath, 'resources', 'media', '').encode('utf-8').decode('utf-8')
cachePERIOD = int(addon.getSetting('cacherhythm'))
cache = StorageServer.StorageServer(addon.getAddonInfo('id'), cachePERIOD) # (Your plugin name, Cache time in hours)
enableInputstream = addon.getSetting('inputstream') == 'true'
showALL = addon.getSetting('show_complete') == 'true'
useThumbAsFanart = addon.getSetting('useThumbAsFanart') == 'true'
enableAdjustment = addon.getSetting('show_settings') == 'true'
DEB_LEVEL = (xbmc.LOGNOTICE if addon.getSetting('enableDebug') == 'true' else xbmc.LOGDEBUG)
baseURL = 'http://www.mtv.de'

xbmcplugin.setContent(pluginhandle, 'tvshows')

if not xbmcvfs.exists(dataPath):
	xbmcvfs.mkdirs(dataPath)

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

def get_sec(info):
	try:
		if len(info) > 5:
			h, m, s = info.split(':')
			return int(h)*3600+int(m)*60+int(s)
		elif len(info) < 6:
			m, s = info.split(':')
			return int(m)*60+int(s)
	except: return ""

def get_desc(info):
	depl = ""
	if 'fullDescription' in info and info['fullDescription'] and len(info['fullDescription']) > 10:
		depl = _clean(info['fullDescription'])
	if depl == "" and 'description' in info and info['description'] and len(info['description']) > 10:
		depl = _clean(info['description'])
	if depl == "" and 'shortDescription' in info and info['shortDescription'] and len(info['shortDescription']) > 10:
		depl = _clean(info['shortDescription'])
	return depl

def translation(id):
	return py2_enc(addon.getLocalizedString(id))

def failing(content):
	log(content, xbmc.LOGERROR)

def debug_MS(content):
	log(content, DEB_LEVEL)

def log(msg, level=xbmc.LOGNOTICE):
	xbmc.log('[{0} v.{1}]{2}'.format(addon.getAddonInfo('id'), addon.getAddonInfo('version'), py2_enc(msg)), level)

def makeREQUEST(url):
	return cache.cacheFunction(getUrl, url)

def getUrl(url, header=None, referer=None, agent='Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0'):
	opener = build_opener()
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
	debug_MS("(clearCache) -------------------------------------------------- START = clearCache --------------------------------------------------")
	debug_MS("(clearCache) ========== Lösche jetzt den Addon-Cache ==========")
	cache.delete('%')
	xbmc.sleep(1000)
	xbmcgui.Dialog().ok(addon.getAddonInfo('id'), translation(30502))

def index():
	addDir(translation(30601), baseURL+'/shows', 'listTvshows', icon)
	addDir(translation(30602), baseURL+'/musik', 'listMusics', icon)
	addDir(translation(30603), baseURL+'/charts/c6mc86/single-top-100', 'listCharts', icon)
	addDir(translation(30604), baseURL+'/playlists', 'playlistPart', icon)
	addDir(translation(30605), '0', 'listAlphabet', icon)
	addDir(translation(30606), baseURL+'/live/0h9eak/mtv-germany-live', 'playLIVE', artpic+'livestream.png', folder=False)
	addDir(translation(30607).format(str(cachePERIOD)), "", 'clearCache', icon)
	if enableAdjustment:
		addDir(translation(30608), "", 'aSettings', artpic+'settings.png')
		if enableInputstream and ADDON_operate('inputstream.adaptive'):
			addDir(translation(30609), "", 'iSettings', artpic+'settings.png')
		else:
			addon.setSetting('inputstream', 'false')
	xbmcplugin.endOfDirectory(pluginhandle)

def listTvshows(url):
	debug_MS("(listTvshows) ------------------------------------------------ START = listTvshows -----------------------------------------------")
	prefer = {'INTL_M150':'Alle Shows von A-Z', 'INTL_M300':'Neueste Folgen', 'INTL_M012':'Highlights'}
	url1 = 'http://www.mtv.de/feeds/triforce/manifest/v8?url='+quote_plus(url)
	debug_MS("(listTvshows) ### URL : {0} ###".format(url1))
	content = makeREQUEST(url1)
	DATA = json.loads(content)
	for modul, name in prefer.items():
		nosub = 1
		spez = 'listSeries'
		if 'M300' in modul: spez = 'listEpisodes'
		if 'M012' in modul: nosub = 2
		for key, value in DATA['manifest']['zones'].items():
			if value['moduleName'] == modul:
				debug_MS("(listTvshows) ##### NAME : {0} || URL : {1} #####".format(str(name), value['feed']))
				addDir(name, value['feed'], spez, icon, nosub=nosub)
	addDir(translation(30610), baseURL+'/buzz', 'listArtist', icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def listSeries(url, filter):
	debug_MS("(listSeries) ------------------------------------------------ START = listSeries -----------------------------------------------")
	debug_MS("(listSeries) ### URL : {0} ### FILTER : {1} ###".format(url, str(filter)))
	content = makeREQUEST(url)
	DATA = json.loads(content)
	if int(filter) == 2:
		for item in DATA['result']['data']['items']:
			title = _clean(item['title'])
			canonical = item['canonicalURL']
			photo = item['images']['url']
			addDir(title, canonical, 'listSeasons', photo, nosub=photo)
			debug_MS("(listSeries) no.01 ##### NAME : {0} || canonicalURL : {1} #####".format(str(title), canonical))
	else:
		for letter in DATA['result']['shows']:
			for serie in letter['value']:
				IDD = str(serie['itemId'])
				title = _clean(serie['title'])
				newURL = serie['url']
				photo = 'http://mtv-intl.mtvnimages.com/uri/mgid:arc:content:mtv.de:'+IDD+'?ep=mtv.de&stage=live&format=jpg&quality=0.8&quality=0.8&quality=0.85&width=1047&height=588&crop=true'
				addDir(title, newURL, 'listSeasons', photo, nosub=photo)
				debug_MS("(listSeries) no.02 ##### NAME : {0} || newURL : {1} #####".format(str(title), newURL))
	xbmcplugin.endOfDirectory(pluginhandle)

def listSeasons(url, thumb):
	debug_MS("(listSeasons) ------------------------------------------------ START = listSeasons -----------------------------------------------")
	FOUND = 0
	url1 = 'http://www.mtv.de/feeds/triforce/manifest/v8?url='+quote_plus(url)
	content_1 = makeREQUEST(url1)
	url2 = json.loads(content_1)['manifest']['zones']['t2_lc_promo1']['feed']
	content_2 = makeREQUEST(url2)
	debug_MS("(listSeasons) ### URL-1 : {0} ### URL-2 : {1} ###".format(url1, url2))
	DATA = json.loads(content_2)['result']['data']['seasons']
	for item in DATA:
		FOUND += 1
		IDD = item['id']
		title = _clean(item['eTitle'])
		plot = get_desc(item)
		canonical = item['canonicalURL']
		addDir(title, canonical, 'seasonPart', thumb, plot=plot)
		debug_MS("(listSeasons) ##### NAME : {0} || canonicalURL : {1} #####".format(str(title), canonical))
	if FOUND == 0: 
		return xbmcgui.Dialog().notification(translation(30522).format('Einträge'), translation(30524), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def seasonPart(url):
	url1 = 'http://www.mtv.de/feeds/triforce/manifest/v8?url='+quote_plus(url)
	content = makeREQUEST(url1)
	newURL = json.loads(content)['manifest']['zones']['t4_lc_promo1']['feed'] 
	listEpisodes(newURL, 0)

def listEpisodes(url, filter):
	debug_MS("(listEpisodes) ------------------------------------------------ START = listEpisodes -----------------------------------------------")
	debug_MS("(listEpisodes) ### URL : {0} ### FILTER : {1} ###".format(url, str(filter)))
	COMBI_EPISODE = []
	UNIKAT = set()
	Pagination = 8
	pos = 0
	pageNUMBER = 1
	position = 0
	total = 1
	while total > 0 and pageNUMBER <= Pagination:
		newURL = url+'&pageNumber='+str(pageNUMBER)
		try:
			content = makeREQUEST(newURL)
			debug_MS("(listEpisodes) ##### newURL : {0} #####".format(newURL))
			DATA = json.loads(content)['result']['data']['items']
			for item in DATA:
				debug_MS("(listEpisodes) no.1 XXXXX FOLGE : {0} XXXXX".format(str(item)))
				Note_1 = ""
				Note_2 = ""
				canonical = item['canonicalURL']
				if int(filter) == 1 and 'headline' in item and item['headline']:
					Note_1 = '[COLOR yellow]'+_clean(item['headline'])+'[/COLOR][CR][CR]'
				elif int(filter) == 0 and 'showTitle' in item and item['showTitle'] and 'headline' in item and item['headline']:
					Note_1 = '[COLOR yellow]'+_clean(item['showTitle'])+' - '+_clean(item['headline'])+'[/COLOR][CR][CR]'
				Note_2 = get_desc(item)
				plot = Note_1+Note_2
				duration = get_sec(item['duration'])
				IDD = str(item['id'])
				if IDD in UNIKAT:
					continue
				UNIKAT.add(IDD)
				photo = item['images']['url']
				title = _clean(item['contentLabel'])
				if not 'Episode' in item['title'] and not item['title'] in title:
					title = title+' - '+_clean(item['title'])
				season = '0'
				if 'season' in item and item['season']:
					season = str(item['season']).zfill(4)
				episode = '0'
				if 'episode' in item and item['episode']:
					episode = str(item['episode']).zfill(4)
				else: pos += 1
				position += 1
				COMBI_EPISODE.append([episode, season, title, canonical, photo, duration, plot, pos, IDD])
		except:
			total = 0
			pageNUMBER = 9
		pageNUMBER += 1
	if COMBI_EPISODE:
		if pos <= 5 and int(filter) == 0:
			COMBI_EPISODE = sorted(COMBI_EPISODE, key=lambda no:no[0], reverse=True)
		for episode, season, title, canonical, photo, duration, plot, pos, IDD in COMBI_EPISODE:
			debug_MS("(listEpisodes) no.2 ##### TITLE = {0} || canonicalURL = {1} || IDD = {2} #####".format(str(title), canonical, IDD))
			addLink(title, canonical, 'playVideo', photo, plot=plot, duration=duration, nosub=IDD)
	xbmcplugin.endOfDirectory(pluginhandle)

def listCharts(url):
	debug_MS("(listCharts) ------------------------------------------------ START = listCharts -----------------------------------------------")
	url1 = 'http://www.mtv.de/feeds/triforce/manifest/v8?url='+quote_plus(url)
	content_1 = makeREQUEST(url1)
	url2 = json.loads(content_1)['manifest']['zones']['t2_lc_promo1']['feed']
	content_2 = makeREQUEST(url2)
	debug_MS("(listCharts) ### URL-1 : {0} ### URL-2 : {1} ###".format(url1, url2))
	DATA = json.loads(content_2)['result']['featuredChartTypes']
	for item in DATA:
		title = _clean(item['title']).replace('Offizielle ', '')
		shortTitle = item['shortTitle']
		canonical = item['canonicalURL']
		if not 'Album' in shortTitle and not 'Hip Hop' in shortTitle:
			addDir(title, canonical, 'chartPart', icon)
			debug_MS("(listCharts) ##### NAME : {0} || canonicalURL : {1} #####".format(str(title), canonical))
	xbmcplugin.endOfDirectory(pluginhandle)

def chartPart(url):
	url1 = 'http://www.mtv.de/feeds/triforce/manifest/v8?url='+quote_plus(url)
	content = makeREQUEST(url1)
	newURL = json.loads(content)['manifest']['zones']['t4_lc_promo1']['feed'] 
	chartVideos(newURL) 

def chartVideos(url):
	debug_MS("(chartVideos) ------------------------------------------------ START = chartVideos -----------------------------------------------")
	debug_MS("(chartVideos) ### URL : {0} ###".format(url))
	content = makeREQUEST(url)  
	DATA = json.loads(content)['result']
	for item in DATA['data']['items']:
		song = _clean(item['title'])
		artist = ""
		if 'shortTitle' in item and item['shortTitle']:
			artist = _clean(item['shortTitle'])
		if artist == "" and 'artists' in item and 'name' in str(item['artists']):
			artist = _clean(item['artists'][0]['name'])
		chartpos = item['chartPosition']['current']
		photo = item['images'][0]['url']   
		try: videoUrl = item['videoUrl']
		except:
			try: videoUrl = re.compile("'videoUrl'[^']+'(.+?)'", re.DOTALL).findall(str(item))[0]
			except: videoUrl = "00"
		oldpos = ""
		try:
			down = item['chartPosition']['moveDown']
			old = item['chartPosition']['previous']
			oldpos = '[COLOR red]  ( - '+str(chartpos-old) + ' )[/COLOR]'
			debug(oldpos)
		except: pass
		try:
			down = item['chartPosition']['moveUp']
			old = int(item['chartPosition']['previous'])
			oldpos = '[COLOR green]  ( + '+str(old-chartpos) + ' )[/COLOR]'
			debug(oldpos)
		except: pass
		try:
			neu = item['chartPosition']['variation'] 
			if neu == 'neu':
				oldpos = '[COLOR deepskyblue]  ( NEU )[/COLOR]'
			elif neu == "-":
				oldpos = "  ( - )"
			debug(oldpos)
		except: pass
		debug_MS("(chartVideos) ##### TITLE = {0} || videoUrl = {1} || FOTO = {2} #####".format(str(chartpos)+'. '+song+' - '+artist, videoUrl, str(photo)))
		if videoUrl != "00":
			title = '[COLOR chartreuse]'+str(chartpos)+' •  [/COLOR]'+song+' - '+artist+oldpos
			addLink(title, videoUrl, 'playVideo', photo, artist=artist, tracknumber=chartpos, nosub='unknown')
		else:
			if showALL:
				title = str(chartpos)+' •  '+song+' - '+artist+oldpos+'[COLOR orangered]  [No Video][/COLOR]'
				addLink(title, videoUrl, 'nothing', photo, artist=artist, tracknumber=chartpos)
	try:   
		nexturl = DATA['nextPageURL']
		chartVideos(nexturl)
	except: pass
	xbmcplugin.endOfDirectory(pluginhandle)

def listMusics(url):
	debug_MS("(listMusics) ------------------------------------------------ START = listMusics -----------------------------------------------")
	prefer = {'t4_lc_promo1':'Neueste Musikvideos', 't5_lc_promo1':'Hits', 't6_lc_promo1':'Made In Germany', 't7_lc_promo1':'Hip Hop', 't8_lc_promo1':'Upcoming', 't9_lc_promo1':'Alternative', 't10_lc_promo1':'Dance', 't11_lc_promo1':'Pop'}
	url1 = 'http://www.mtv.de/feeds/triforce/manifest/v8?url='+quote_plus(url)
	debug_MS("(listMusics) ### URL : {0} ###".format(url1))
	content = makeREQUEST(url1)
	DATA = json.loads(content)
	for modul, name in prefer.items():
		for key, value in DATA['manifest']['zones'].items():
			if value['zone'] == modul:
				debug_MS("(listMusics) ##### NAME : {0} || URL : {1} #####".format(str(name), value['feed']))
				addDir(name, value['feed'], 'playlistVideos', icon, nosub='musicvideo')
	xbmcplugin.endOfDirectory(pluginhandle)

def playlistPart(url):
	url1 = 'http://www.mtv.de/feeds/triforce/manifest/v8?url='+quote_plus(url)
	content = makeREQUEST(url1)
	newURL = json.loads(content)['manifest']['zones']['t4_lc_promo1']['feed'] 
	playlistVideos(newURL, "") 
    
def playlistVideos(url, filter):
	debug_MS("(playlistVideos) ------------------------------------------------ START = playlistVideos -----------------------------------------------")
	debug_MS("(playlistVideos) ### URL : {0} ### FILTER : {1} ###".format(url, str(filter)))
	content = makeREQUEST(url)  
	DATA = json.loads(content)['result']
	for item in DATA['data']['items']:
		debug_MS("(playlistVideos) no.1 XXXXX FOLGE : {0} XXXXX".format(str(item)))
		song = _clean(item['title'])
		artist = ""
		if 'artist' in item and item['artist']:
			artist = _clean(item['artist'])
		if artist != "": Name = song+' - '+artist
		else: Name = song
		canonical = item['canonicalURL']
		photo = item['images']['url']
		duration = get_sec(item['duration'])
		count = ""
		if 'itemNumber' in item and item['itemNumber']:
			count = str(item['itemNumber'])
		debug_MS("(playlistVideos) no.2 ##### NAME = {0} || canonicalURL = {1} || FOTO = {2} #####".format(str(Name), canonical, str(photo)))
		if filter == 'musicvideo':
			if count != "": Name = '[COLOR chartreuse]'+str(count)+' •  [/COLOR]'+Name
			addLink(Name, canonical, 'playVideo', photo, duration, nosub='unknown')
		else:
			addDir(Name, canonical, 'playPLAYLIST', photo, play=1)
	try:   
		nexturl = DATA['nextPageURL']
		playlistVideos(nexturl, filter)
	except: pass
	xbmcplugin.endOfDirectory(pluginhandle)

def playPLAYLIST(url):
	debug_MS("(playPLAYLIST) ------------------------------------------------ START = playPLAYLIST -----------------------------------------------")
	content_1 = makeREQUEST(url)
	musicVideos = []
	PL = xbmc.PlayList(1)
	PL.clear()
	htmlPage = BeautifulSoup(content_1, 'html.parser')
	element = htmlPage.find('div',attrs={'id':'t1_lc_promo1'})
	playindexUrl = element['data-tffeed']
	debug_MS("(playPLAYLIST) ### playindexUrl : {0} ###".format(playindexUrl))
	content_2 = makeREQUEST(playindexUrl)
	DATA = json.loads(content_2)['result']
	for item in DATA['data']['items']:
		canonical = item['canonicalURL']
		#nosub = 'unknown'
		plot = get_desc(item)
		duration = get_sec(item['duration'])
		IDD = str(item['id'])
		videoUrl = getVideo(canonical, IDD)
		song = _clean(item['title'])
		artist = ""
		if 'artist' in item and item['artist']:
			artist = _clean(item['artist'])
		if artist != "": Name = song+' - '+artist
		else: Name = song
		photo = item['images']['url']
		musicVideos.append([Name, videoUrl, photo, duration, plot])
	random.shuffle(musicVideos)
	for Name, videoUrl, photo, duration, plot in musicVideos:
		debug_MS("(playPLAYLIST) ##### TITLE = {0} || videoUrl = {1} || FOTO = {2} #####".format(str(Name), videoUrl, str(photo)))
		listitem = xbmcgui.ListItem(Name)
		listitem.setInfo(type='Video', infoLabels={'Title': Name, 'Plot': plot, 'Duration': duration, 'Mediatype': 'video'})
		listitem.setArt({'icon': icon, 'thumb': photo, 'poster': photo})
		PL.add(url=videoUrl, listitem=listitem)
	xbmc.Player().play(PL)

def listAlphabet():
	debug_MS("(listAlphabet) ------------------------------------------------ START = listAlphabet -----------------------------------------------")
	for letter in '#ABCDEFGHIJKLMNOPQRSTUVWXYZ':
		addDir(letter, baseURL+'/kuenstler/'+letter.replace('#', '0-9').lower()+'/1', 'listCatalog', icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def listCatalog(url):
	debug_MS("(listCatalog) ------------------------------------------------ START = listCatalog -----------------------------------------------")
	content = makeREQUEST(url)
	htmlPage = BeautifulSoup(content, 'html.parser')
	element = htmlPage.find('div',attrs={'class':'artists'})
	links = element.find_all('li')
	for item in links:
		artist_string = str(item)
		newURL = re.compile('"@id":"(.+?)"', re.DOTALL).findall(artist_string)[0]
		name = re.compile('"name":"(.+?)"', re.DOTALL).findall(artist_string)[0]
		name = _edit(name)
		photo = re.compile('"image":"(.+?)"', re.DOTALL).findall(artist_string)[0]
		addDir(name, newURL, 'listArtist', photo, nosub=name)
		debug_MS("(listCatalog) ##### NAME = {0} || newURL = {1} || FOTO = {2} #####".format(str(name), newURL, str(photo)))
	try:
		nexturl = htmlPage.find('a',attrs={'class':'page next link'})
		addDir(translation(30620), nexturl['href'], 'listCatalog', artpic+'nextpage.png')
	except: pass
	xbmcplugin.endOfDirectory(pluginhandle)

def listArtist(url, category):
	debug_MS("(listArtist) ------------------------------------------------ START = listArtist -----------------------------------------------")
	UNIKAT = set()
	url1 = 'http://www.mtv.de/feeds/triforce/manifest/v8?url='+quote_plus(url)
	content_1 = makeREQUEST(url1)
	url2 = json.loads(content_1)['manifest']['zones']['t4_lc_promo1']['feed']
	content_2 = makeREQUEST(url2)
	debug_MS("(listArtist) ### URL-1 : {0} ### URL-2 : {1} ###".format(url1, url2))
	DATA = json.loads(content_2)
	if 'result' in DATA and 'data' in DATA['result'] and 'items' in DATA['result']['data'] and DATA['result']['data']['items']:
		for item in DATA['result']['data']['items']:
			IDD = str(item['id'])
			if IDD in UNIKAT:
				continue
			UNIKAT.add(IDD)
			canonical = item['canonicalURL']
			plot = get_desc(item)
			duration = get_sec(item['duration'])
			title = _clean(item['contentLabel'])
			if not 'Episode' in item['title']:
				title = title+' - '+_clean(item['title'])
			photo = item['images']['url']
			addLink(title, canonical, 'playVideo', photo, duration, plot, nosub=IDD)
			debug_MS("(listArtist) ##### TITLE = {0} || canonicalURL = {1} || FOTO = {2} #####".format(str(title), canonical, str(photo)))
	else: 
		return xbmcgui.Dialog().notification(translation(30522).format('Einträge'), translation(30525).format(category), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def getVideo(url, filter):
	if filter == 'unknown':
		content = getUrl(url)
		filter = re.compile('"itemId":"(.+?)"', re.DOTALL).findall(content)[0]
	firstURL = 'http://media.mtvnservices.com/pmt/e1/access/index.html?uri=mgid:arc:episode:mtv.de:'+filter+'&configtype=edge'
	content_1 = getUrl(firstURL, referer=url)
	debug_MS("++++++++++++++++++++++++")
	debug_MS("(getVideo) XXXXX CONTENT-01 : {0} XXXXX".format(str(content_1)))
	debug_MS("++++++++++++++++++++++++")
	DATA_1 = json.loads(content_1)
	try: guid = DATA_1['feed']['items'][0]['guid']
	except: guid=DATA_1['uri']
	mediaURL = DATA_1['mediaGen'].replace('&device={device}', '').replace('{uri}', guid)
	#https://media-utils.mtvnservices.com/services/MediaGenerator/mgid:arc:video:mtv.de:837234d4-7002-11e9-a442-0e40cf2fc285?arcStage=live&format=json&acceptMethods=hls&clang=de&https=true
	content_2 = getUrl(mediaURL, referer=url)
	debug_MS("++++++++++++++++++++++++")
	debug_MS("(getVideo) XXXXX CONTENT-02 : {0} XXXXX".format(str(content_2)))
	debug_MS("++++++++++++++++++++++++")
	DATA_2 = json.loads(content_2)
	try:
		videoURL = DATA_2['package']['video']['item'][0]['rendition'][0]['src']
	except:
		text = DATA_2['package']['video']['item'][0]['text']
		code = DATA_2['package']['video']['item'][0]['code'].upper()
		xbmcgui.Dialog().notification(code, text, icon, 8000)
		videoURL = ""
	return videoURL

def playVideo(url, filter):
	debug_MS("(playVideo) -------------------------------------------------- START = playVideo --------------------------------------------------")
	debug_MS("(playVideo) ### URL : {0} ### FILTER : {1} ###".format(url, str(filter)))
	finalURL = getVideo(url, filter)
	log("(playVideo) StreamURL : {0}".format(finalURL))
	if finalURL == "": return
	listitem = xbmcgui.ListItem(path=finalURL)
	if enableInputstream and 'm3u8' in finalURL:
		if ADDON_operate('inputstream.adaptive'):
			listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
			listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
			listitem.setMimeType('application/vnd.apple.mpegurl')
		else:
			addon.setSetting('inputstream', 'false')
	xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def playLIVE(url):
	debug_MS("(playLIVE) ------------------------------------------------ START = playLIVE -----------------------------------------------")
	live_url = getVideo(url, 'unknown')
	if live_url != "":
		newM3U8 = getUrl(live_url)
		M3U8_Url = re.compile('(https?://.*?.m3u8)', re.DOTALL).findall(newM3U8)[-1]
		log("(playLIVE) LIVEurl : {0}".format(M3U8_Url))
		listitem = xbmcgui.ListItem(path=M3U8_Url, label=translation(30606))
		listitem.setMimeType('application/vnd.apple.mpegurl')
		xbmc.Player().play(item=M3U8_Url, listitem=listitem)
	else:
		failing("(liveTV) ##### Abspielen des Live-Streams NICHT möglich ##### URL : {0} #####\n   ########## KEINEN Live-Stream-Eintrag auf der Webseite von *mtv.de* gefunden !!! ##########".format(url))
		return xbmcgui.Dialog().notification(translation(30521).format('LIVE'), translation(30526), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def _clean(text):
	text = py2_enc(text)
	for n in (('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'), ('&apos;', "'"), ("&#x27;", "'"), ('&#34;', '"'), ('&#39;', '\''), ('&#039;', '\''), ('►', '>')
		, ('&#x00c4', 'Ä'), ('&#x00e4', 'ä'), ('&#x00d6', 'Ö'), ('&#x00f6', 'ö'), ('&#x00dc', 'Ü'), ('&#x00fc', 'ü'), ('&#x00df', 'ß'), ('&#xD;', ''), ('\xc2\xb7', '-')
		, ('&quot;', '"'), ('&szlig;', 'ß'), ('&ndash;', '-'), ('&Auml;', 'Ä'), ('&Ouml;', 'Ö'), ('&Uuml;', 'Ü'), ('&auml;', 'ä'), ('&ouml;', 'ö'), ('&uuml;', 'ü')
		, ('&agrave;', 'à'), ('&aacute;', 'á'), ('&acirc;', 'â'), ('&egrave;', 'è'), ('&eacute;', 'é'), ('&ecirc;', 'ê'), ('&igrave;', 'ì'), ('&iacute;', 'í'), ('&icirc;', 'î')
		, ('&ograve;', 'ò'), ('&oacute;', 'ó'), ('&ocirc;', 'ô'), ('&ugrave;', 'ù'), ('&uacute;', 'ú'), ('&ucirc;', 'û'), ("\\'", "'")):
		text = text.replace(*n)
	return text.strip()

def _edit(input, nom='utf-8', esc='unicode_escape', ign='ignore'):
	if PY2 and  isinstance(input, str):
		input = input.decode(esc, ign).encode(nom) #UnicodeDecodeError: 'utf8' codec can't decode byte 0x9c
	elif PY2 and isinstance(input, bytes):
		input = input.decode(esc, ign).encode(nom)
	return input

def addQueue(vid):
	PL = xbmc.PlayList(1)
	STREAMe = vid[vid.find('###START'):]
	STREAMe = STREAMe[:STREAMe.find('END###')]
	url = STREAMe.split('###')[2]
	name = STREAMe.split('###')[3]
	image = STREAMe.split('###')[4]
	listitem = xbmcgui.ListItem(name)
	listitem.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	listitem.setProperty('IsPlayable', 'true')
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

def addDir(name, url, mode, image, plot=None, nosub=0, play=0, folder=True): 
	u = '{0}?url={1}&mode={2}&nosub={3}'.format(sys.argv[0], quote_plus(url), str(mode), str(nosub))
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon and not artpic in image:
		liz.setArt({'fanart': image})
	if play == 1: 
		liz.setProperty('IsPlayable', 'true')
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=folder)

def addLink(name, url, mode, image, duration=None, plot=None, tagline=None, rating=None, votes=None, nosub=0, genre=None, year=None, begins=None, artist=[], tracknumber=""):
	u = '{0}?url={1}&mode={2}&nosub={3}'.format(sys.argv[0], quote_plus(py2_enc(url)), str(mode), str(nosub))
	liz = xbmcgui.ListItem(name)
	ilabels = {}
	ilabels['Season'] = None
	ilabels['Episode'] = None
	ilabels['Tracknumber'] = tracknumber
	ilabels['Artist'] = [artist]
	ilabels['Title'] = name
	ilabels['Tagline'] = tagline
	ilabels['Plot'] = plot
	ilabels['Duration'] = duration
	if begins != None:
		ilabels['Date'] = begins
	ilabels['Year'] = year
	ilabels['Genre'] = genre
	ilabels['Rating'] = rating
	ilabels['Votes'] = votes
	ilabels['Studio'] = 'MTV'
	ilabels['Mpaa'] = None
	ilabels['Mediatype'] = 'video'
	liz.setInfo(type='Video', infoLabels=ilabels)
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon and not artpic in image:
		liz.setArt({'fanart': image})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	liz.setContentLookup(False)
	playInfos = '###START###{0}###{1}###{2}###END###'.format(u, name, image)
	liz.addContextMenuItems([(translation(30654), 'RunPlugin('+sys.argv[0]+'?mode=addQueue&url='+quote_plus(playInfos)+')')])
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
  
params = parameters_string_to_dict(sys.argv[2])
mode = unquote_plus(params.get('mode', ''))
url = unquote_plus(params.get('url', ''))
nosub= unquote_plus(params.get('nosub', ''))
referer = unquote_plus(params.get('referer', ''))

if mode == 'aSettings':
	addon.openSettings()
elif mode == 'iSettings':
	xbmcaddon.Addon('inputstream.adaptive').openSettings()
elif mode == 'clearCache':
	clearCache()
elif mode == 'listTvshows':
	listTvshows(url)
elif mode == 'listSeries':
	listSeries(url, nosub) 
elif mode == 'listSeasons':
	listSeasons(url, nosub)
elif mode == 'seasonPart':
	seasonPart(url)
elif mode == 'listEpisodes':
	listEpisodes(url, nosub)
elif mode == 'listCharts':
	listCharts(url)
elif mode == 'chartPart':
	chartPart(url)
elif mode == 'chartVideos':
	chartVideos(url)
elif mode == 'listMusics':
	listMusics(url)
elif mode == 'playlistPart':
	playlistPart(url)
elif mode == 'playlistVideos':
	playlistVideos(url, nosub)
elif mode == 'playPLAYLIST':
	playPLAYLIST(url) 
elif mode == 'listAlphabet':
	listAlphabet()
elif mode == 'listCatalog':
	listCatalog(url)
elif mode == 'listArtist':
	listArtist(url, nosub)
elif mode == 'playVideo':
	playVideo(url, nosub)
elif mode == 'playLIVE':
	playLIVE(url)
elif mode == 'nothing':
	pass
elif mode == 'addQueue':
	addQueue(url)
else:
	index()
