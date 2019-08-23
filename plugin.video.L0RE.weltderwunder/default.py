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
SEP = os.sep
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath  = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath     = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
temp             = xbmc.translatePath(os.path.join(dataPath, 'temp', ''))
masterOLD  = "kaltura.py"
masterNEW = "kaltura.py"
masterBACK = "(BACKUP)kaltura.py"
sourceOLD = os.path.join('special:'+SEP+SEP+'home'+SEP+'addons'+SEP+'plugin.video.L0RE.weltderwunder'+SEP+'lib'+SEP, masterOLD)
sourceNEW = os.path.join('special:'+SEP+SEP+'home'+SEP+'addons'+SEP+'script.module.youtube.dl'+SEP+'lib'+SEP+'youtube_dl'+SEP+'extractor'+SEP, masterNEW)
sourceBACK = os.path.join('special:'+SEP+SEP+'home'+SEP+'addons'+SEP+'plugin.video.L0RE.weltderwunder'+SEP+'lib'+SEP, masterBACK)
prefQUALITY = int(addon.getSetting('prefVideoQuality'))
useThumbAsFanart = addon.getSetting('useThumbAsFanart') == "true"
enableAdjustment = addon.getSetting('show_settings') == "true"
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
baseURL = "http://www.weltderwunder.de"


xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)

if xbmcvfs.exists(sourceOLD) and xbmcvfs.exists(sourceNEW):
	xbmcvfs.copy(sourceOLD, sourceNEW)
	xbmcvfs.rename(sourceOLD, sourceBACK)

if xbmcvfs.exists(temp) and os.path.isdir(temp):
	shutil.rmtree(temp, ignore_errors=True)
	xbmc.sleep(500)
xbmcvfs.mkdirs(temp)
cookie = os.path.join(temp, 'cookie.lwp')
cj = LWPCookieJar()

if xbmcvfs.exists(cookie):
	cj.load(cookie, ignore_discard=True, ignore_expires=True)

def py2_enc(s, encoding='utf-8'):
	if PY2 and isinstance(s, unicode):
		s = s.encode(encoding)
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
	LANGUAGE = addon.getLocalizedString(id)
	LANGUAGE = py2_enc(LANGUAGE)
	return LANGUAGE

def failing(content):
	log(content, xbmc.LOGERROR)

def debug(content):
	log(content, xbmc.LOGDEBUG)

def log(msg, level=xbmc.LOGNOTICE):
	msg = py2_enc(msg)
	xbmc.log("["+addon.getAddonInfo('id')+"-"+addon.getAddonInfo('version')+"]"+msg, level)

def getUrl(url, header=None):
	global cj
	opener = build_opener(HTTPCookieProcessor(cj))
	try:
		if header:
			opener.addheaders = header
		else:
			opener.addheaders =[('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0')]
			opener.addheaders = [('Accept-Encoding', 'gzip, deflate')]
		response = opener.open(url, timeout=30)
		if response.info().get('Content-Encoding') == 'gzip':
			content = py3_dec(gzip.GzipFile(fileobj=io.BytesIO(response.read())).read())
		else:
			content = py3_dec(response.read())
	except Exception as e:
		failure = str(e)
		if hasattr(e, 'code'):
			failing("(getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
		elif hasattr(e, 'reason'):
			failing("(getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
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
	if enableAdjustment:
		addDir(translation(30604), "", 'aSettings', icon)
	liveTV()
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
		addDir(title, link, 'videosThemes', icon, originalSERIE=title)
	xbmcplugin.endOfDirectory(pluginhandle)

def videosThemes(url, originalSERIE, page=1):
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
		addLink(title, link, 'playVideo', img, plot, duration, seriesname=originalSERIE)
	if FOUND > 29:
		addDir(translation(30610), url, 'videosThemes', icon, page=int(page)+1, originalSERIE=originalSERIE)
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
			addDir(title.title(), link, 'listSeasons', img, originalSERIE=title.title())
	xbmcplugin.endOfDirectory(pluginhandle)

def listSeasons(url, originalSERIE, pic):
	debug("(listSeasons) ------------------------------------------------ START = listSeasons -----------------------------------------------")
	xbmcplugin.setContent(pluginhandle, 'tvshows')
	content = getUrl(url)
	htmlPage = BeautifulSoup(content, 'html.parser')
	try: plot = htmlPage.find('div',attrs={'class':'modal-body'}).text.encode('utf-8')
	except: plot = ""
	staffeln_liste = htmlPage.find('select',attrs={'class':'form-control'})
	staffeln = staffeln_liste.find_all('option') 
	for staffel in staffeln:
		addDir(staffel.text.encode('utf-8'), url+"?staffel="+str(staffel['value']), 'videosSeasons', cleanPhoto(pic), plot, originalSERIE=originalSERIE)  
	xbmcplugin.endOfDirectory(pluginhandle)
  
def videosSeasons(url, originalSERIE):
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
		addLink(title, link, 'playVideo', img, plot, seriesname=originalSERIE)  
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
	vid = YDStreamExtractor.getVideoInfo(url, quality=prefQUALITY) # quality is 0=SD, 1=720p, 2=1080p and is max
	stream_url = vid.streamURL() # This is what Kodi will play
	stream_url = stream_url.split('|')[0]
	xbmcplugin.setResolvedUrl(pluginhandle, True, xbmcgui.ListItem(path=stream_url))

def playLive(url, name):
	listitem = xbmcgui.ListItem(path=url, label=name)  
	listitem.setMimeType('application/vnd.apple.mpegurl')
	xbmc.Player().play(item=url, listitem=listitem)

def liveTV():
	debug("(liveTV) ------------------------------------------------ START = liveTV -----------------------------------------------")
	items = []
	items.append(['[COLOR lime]* Welt der Wunder - LIVE TV *[/COLOR]', 'http://live.vidoo.de/live/weltderwunder/chunklist.m3u8', icon])
	for item in items:
		listitem = xbmcgui.ListItem(path=item[1], label=item[0], iconImage=item[2], thumbnailImage=item[2])
		listitem.setArt({'fanart': defaultFanart})
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sys.argv[0]+'?mode=playLive&url='+quote_plus(item[1])+'&name='+item[0], listitem=listitem)  
	xbmcplugin.endOfDirectory(pluginhandle)

def cleanPhoto(string):
	string = py2_enc(string)
	string = string.replace(' ', '%20').replace('ß', '%C3%9F').replace('ä', '%C3%A4').replace('ö', '%C3%B6').replace('ü', '%C3%BC').replace('width/500', 'width/1280').strip()
	return string

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, plot=None, page=1, originalSERIE=""):
	u = sys.argv[0]+'?url='+quote_plus(url)+'&mode='+str(mode)+'&page='+str(page)+'&image='+str(image)+'&originalSERIE='+quote_plus(originalSERIE)
	liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=image)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	liz.setArt({'poster': image})
	if useThumbAsFanart and image != icon:
		liz.setArt({'fanart': image})
	else:
		liz.setArt({'fanart': defaultFanart})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

def addLink(name, url, mode, image, plot=None, duration=None, seriesname=None, season=None, episode=None, genre=None, year=None, begins=None):
	u = sys.argv[0]+'?url='+quote_plus(url)+'&mode='+str(mode)
	liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=image)
	ilabels = {}
	ilabels['Season'] = season
	ilabels['Episode'] = episode
	ilabels['Tvshowtitle'] = seriesname
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
	liz.setArt({'poster': image})
	if useThumbAsFanart and image != icon:
		liz.setArt({'fanart': image})
	else:
		liz.setArt({'fanart': defaultFanart})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	liz.setContentLookup(False)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
page = unquote_plus(params.get('page', ''))
originalSERIE = unquote_plus(params.get('originalSERIE', ''))
 
if mode == 'aSettings':
	addon.openSettings()
elif mode == 'listThemes':
	listThemes(url)
elif mode == 'videosThemes':
	videosThemes(url, originalSERIE, page)
elif mode == 'listShowsA_Z':
	listShowsA_Z(url)
elif mode == 'listSeasons':
	listSeasons(url, originalSERIE, image)
elif mode == 'videosSeasons':
	videosSeasons(url, originalSERIE)
elif mode == 'Searching':
	Searching()
elif mode == 'playVideo':
	playVideo(url)
elif mode == 'playLive':
	playLive(url, name)
elif mode == 'liveTV':
	liveTV()
else:
	index()