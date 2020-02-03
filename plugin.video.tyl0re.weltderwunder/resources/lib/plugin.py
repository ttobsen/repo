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
from bs4 import BeautifulSoup
import YDStreamExtractor


global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath  = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
temp        = xbmc.translatePath(os.path.join(dataPath, 'temp', '')).encode('utf-8').decode('utf-8')
prefQUALITY = int(addon.getSetting('prefVideoQuality'))
useThumbAsFanart = addon.getSetting('useThumbAsFanart') == "true"
enableAdjustment = addon.getSetting('show_settings') == "true"
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
baseURL = "http://www.weltderwunder.de"


xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)

if xbmcvfs.exists(temp) and os.path.isdir(temp):
	shutil.rmtree(temp, ignore_errors=True)
	xbmc.sleep(500)
xbmcvfs.mkdirs(temp)
cookie = os.path.join(temp, 'cookie.lwp')
cj = LWPCookieJar()

f xbmcvfs.exists(cookie):
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

def getUrl(url, header=None, agent='Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0'):
	global cj
	opener = build_opener(HTTPCookieProcessor(cj))
	opener.addheaders = [('User-Agent', agent), ('Accept-Encoding', 'gzip, deflate')]
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
  
def index():   
	addDir(translation(30601), baseURL+'/sendungen', 'listShowsA_Z', icon)
	addDir(translation(30602) , baseURL+'/videos', 'listThemes', icon)
	addDir(translation(30603), "", 'Searching', icon)
	addDir(translation(30604), baseURL+'/videos/live', 'play_LIVE', icon, folder=False)
	if enableAdjustment:
		addDir(translation(30605), "", 'aSettings', icon)
	xbmcplugin.endOfDirectory(pluginhandle) 

def listThemes(url):
	debug("(listThemes) ------------------------------------------------ START = listThemes -----------------------------------------------")
	xbmcplugin.setContent(pluginhandle, 'tvshows')
	content = getUrl(url)
	htmlPage = BeautifulSoup(content, 'html.parser')
	themen = htmlPage.find_all('h2',attrs={'class':'section-global-h2'})
	for thema in themen:
		title = thema.text.encode('utf-8').replace('» Alle Anzeigen', '')
		link = baseURL+thema.find('a')['href']
		addDir(title, link, 'videosThemes', icon, origSERIE=title)
	xbmcplugin.endOfDirectory(pluginhandle)

def videosThemes(url, origSERIE, page=1):
	debug("(videosThemes) ------------------------------------------------ START = videosThemes -----------------------------------------------")
	xbmcplugin.setContent(pluginhandle, 'episodes')
	newurl = url+"_load?page="+str(page)
	content = getUrl(newurl)
	FOUND = 0
	htmlPage = BeautifulSoup(content, 'html.parser')
	videos = htmlPage.find_all('div',attrs={'class':'col-md-3 col-sm-6 item-video item-video-global'})
	for video in videos:
		img = cleanPhoto(video.find('img')['src'])
		link = baseURL+video.find('a')['href']
		title = video.find('h4').text.encode('utf-8')
		FOUND += 1
		plot = video.find('p').text.encode('utf-8')
		durationstring = video.find('div',attrs={'class':'item-video-duration-global'}).text.encode('utf-8')
		zeit = re.compile('([0-9]+):([0-9]+)', re.DOTALL).findall(durationstring)
		for MINS, SECS in zeit:
			duration = int(MINS)*60+int(SECS)
		addLink(title, link, 'playVideo', img, plot, duration, origSERIE=origSERIE)
	if FOUND > 29:
		addDir(translation(30610), url, 'videosThemes', icon, page=int(page)+1, origSERIE=origSERIE)
	xbmcplugin.endOfDirectory(pluginhandle)

def listShowsA_Z(url):
	debug("(listShowsA_Z) ------------------------------------------------ START = listShowsA_Z -----------------------------------------------")
	xbmcplugin.setContent(pluginhandle, 'tvshows')
	content = getUrl(url)
	htmlPage = BeautifulSoup(content, 'html.parser')
	series = htmlPage.find_all('div',attrs={'class':'col-md-3 col-sm-3 col-xs-6 program-thumbnail'})
	for SE in series:  
		img = cleanPhoto(SE.find('img')['src'])
		link = baseURL+SE.find('a')['href']
		title = re.compile('.+/([^/]+)$', re.DOTALL).findall(link)[0].replace('-', ' ')
		if title != 'life goes on':
			addDir(title.title(), link, 'listSeasons', img, origSERIE=title.title())
	xbmcplugin.endOfDirectory(pluginhandle)

def listSeasons(url, origSERIE, pic):
	debug("(listSeasons) ------------------------------------------------ START = listSeasons -----------------------------------------------")
	xbmcplugin.setContent(pluginhandle, 'tvshows')
	content = getUrl(url)
	htmlPage = BeautifulSoup(content, 'html.parser')
	try: plot = htmlPage.find('div',attrs={'class':'modal-body'}).text.encode('utf-8')
	except: plot = ""
	staffeln_liste = htmlPage.find('select',attrs={'class':'form-control'})
	staffeln = staffeln_liste.find_all('option') 
	for staffel in staffeln:
		addDir(staffel.text.encode('utf-8'), url+"?staffel="+str(staffel['value']), 'videosSeasons', cleanPhoto(pic), plot, origSERIE=origSERIE)  
	xbmcplugin.endOfDirectory(pluginhandle)
  
def videosSeasons(url, origSERIE):
	debug("(videosSeasons) ------------------------------------------------ START = videosSeasons -----------------------------------------------")
	xbmcplugin.setContent(pluginhandle, 'episodes')
	content = getUrl(url)
	htmlPage = BeautifulSoup(content, 'html.parser')
	try: plot = htmlPage.find('div',attrs={'class':'modal-body'}).text.encode('utf-8')
	except: plot = ""
	folgen = htmlPage.find_all('div',attrs={'class':'col-md-3 col-sm-6 item-video item-video-global'})
	for folge in folgen:
		img = cleanPhoto(folge.find('img')['src'])
		link = baseURL+folge.find('a')['href']
		title = folge.find('h4').text
		addLink(title, link, 'playVideo', img, plot, origSERIE=origSERIE)  
	xbmcplugin.endOfDirectory(pluginhandle)

def Searching():
	debug("(Searching) ------------------------------------------------ START = Searching -----------------------------------------------")
	xbmcplugin.setContent(pluginhandle, 'episodes')
	word = xbmcgui.Dialog().input('Suche', type=xbmcgui.INPUT_ALPHANUM)
	word = quote_plus(word, safe='')
	if word == "": return
	url = baseURL+"/search?query="+word
	content = getUrl(url)
	htmlPage = BeautifulSoup(content, 'html.parser')
	videos = htmlPage.find_all('div',attrs={'class':'col-md-11 col-sm-12'})
	for video in videos:
		try:
			img = cleanPhoto(video.find('img')['src'])
			link = baseURL+video.find('a')['href']
			title = video.find('h2').text.encode('utf-8')
			plot = video.find('p').text.encode('utf-8')
			if "VIDEO" in title:
				name = title.replace('VIDEO', '')
				addLink(name, link, 'playVideo', img, plot)
			else:
				addDir(title+translation(30611), link, '0', img, plot)
		except: pass
	xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url):
	debug("(playVideo) ------------------------------------------------ START = playVideo -----------------------------------------------")
	vid = YDStreamExtractor.getVideoInfo(url, quality=prefQUALITY) # Quality is 0=SD, 1=720p, 2=1080p, 3=Highest Available
	stream_url = vid.streamURL() # This is what Kodi (XBMC) will play
	stream_url = stream_url.split('|')[0]
	xbmcplugin.setResolvedUrl(pluginhandle, True, xbmcgui.ListItem(path=stream_url))

def play_LIVE(url):
	debug("(play_LIVE) ------------------------------------------------ START = play_LIVE -----------------------------------------------")
	live_url = False
	try:
		content = getUrl(url)
		stream = re.compile('<video id="live-video".*?<source src="([^"]+?)" type="application/x-mpeg', re.DOTALL).findall(content)[0]
		code = urlopen(stream).getcode()
		if str(code) == '200': live_url = stream
	except: pass
	if live_url:
		debug("(play_LIVE) ### LIVEurl : {0} ###".format(live_url))
		listitem = xbmcgui.ListItem(path=live_url, label=translation(30604))
		listitem.setMimeType('application/vnd.apple.mpegurl')
		xbmc.Player().play(item=live_url, listitem=listitem)
	else:
		failing("(liveTV) ##### Abspielen des Live-Streams NICHT möglich ##### URL : {0} #####\n   ########## KEINEN Live-Stream-Eintrag auf der Webseite von *weltderwunder.de* gefunden !!! ##########".format(url))
		return xbmcgui.Dialog().notification(translation(30521).format('LIVE'), translation(30524), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def cleanPhoto(string):
	string = py2_enc(string)
	string = string.replace(' ', '%20').replace('ß', '%C3%9F').replace('ä', '%C3%A4').replace('ö', '%C3%B6').replace('ü', '%C3%BC').replace('width/500', 'width/1280')
	return string.strip()

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, plot=None, page=1, origSERIE="", folder=True):
	u = '{0}?url={1}&mode={2}&page={3}&image={4}&origSERIE={5}'.format(sys.argv[0], quote_plus(url), str(mode), str(page), str(image), quote_plus(origSERIE))
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon:
		liz.setArt({'fanart': image})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=folder)

def addLink(name, url, mode, image, plot=None, duration=None, origSERIE=None, season=None, episode=None, genre=None, year=None, begins=None):
	u = '{0}?url={1}&mode={2}'.format(sys.argv[0], quote_plus(url), str(mode))
	liz = xbmcgui.ListItem(name)
	ilabels = {}
	ilabels['Season'] = season
	ilabels['Episode'] = episode
	ilabels['Tvshowtitle'] = origSERIE
	ilabels['Title'] = name
	ilabels['Tagline'] = None
	ilabels['Plot'] = plot
	ilabels['Duration'] = duration
	if begins != None:
		ilabels['Date'] = begins
	ilabels['Year'] = None
	ilabels['Genre'] = genre
	ilabels['Director'] = None
	ilabels['Writer'] = None
	ilabels['Studio'] = 'WDW'
	ilabels['Mpaa'] = None
	ilabels['Mediatype'] = 'episode'
	liz.setInfo(type='Video', infoLabels=ilabels)
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon:
		liz.setArt({'fanart': image})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	liz.setContentLookup(False)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

params = parameters_string_to_dict(sys.argv[2])
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
page = unquote_plus(params.get('page', ''))
origSERIE = unquote_plus(params.get('origSERIE', ''))
 
if mode == 'aSettings':
	addon.openSettings()
elif mode == 'listThemes':
	listThemes(url)
elif mode == 'videosThemes':
	videosThemes(url, origSERIE, page)
elif mode == 'listShowsA_Z':
	listShowsA_Z(url)
elif mode == 'listSeasons':
	listSeasons(url, origSERIE, image)
elif mode == 'videosSeasons':
	videosSeasons(url, origSERIE)
elif mode == 'Searching':
	Searching()
elif mode == 'playVideo':
	playVideo(url)
elif mode == 'play_LIVE':
	play_LIVE(url)
else:
	index()