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
from datetime import datetime, timedelta
from django.utils.encoding import smart_str
import io
import gzip
from collections import OrderedDict


global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath    = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
temp           = xbmc.translatePath(os.path.join(dataPath, 'temp', '')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
langSHORTCUT = {0: 'www', 1: 'gr', 2: 'fr', 3: 'de', 4: 'it', 5: 'es', 6: 'pt', 7: 'hu', 8: 'ru', 9: 'ua', 10: 'tr', 11: 'arabic', 12: 'fa'}[int(addon.getSetting('language'))]
# Spachennummerierung(settings) ~ English=0|Greek=1|French=2|German=3|Italian=4|Spanish=5|Portuguese=6|Hungarian=7|Russian=8|Ukrainian=9|Turkish=10|Arabic=11|Persian=12
#         Webseitenkürzel(euronews) = 0: www|1: gr|2: fr|3: de|4: it|5: es|6: pt|7: hu|8: ru|9: ua|10: tr|11: arabic|12: fa
baseURL = "https://"+langSHORTCUT+".euronews.com"

xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

if not os.path.exists(os.path.join(dataPath, 'settings.xml')):
	addon.openSettings()

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
			opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0')]
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
			xbmcgui.Dialog().notification((translation(30521).format("URL")), "ERROR = [COLOR red]{0}[/COLOR]".format(failure), icon, 12000)
		elif hasattr(e, 'reason'):
			failing("(getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
			xbmcgui.Dialog().notification((translation(30521).format("URL")), "ERROR = [COLOR red]{0}[/COLOR]".format(failure), icon, 12000)
		content = ""
		return sys.exit(0)
	opener.close()
	try: cj.save(cookie, ignore_discard=True, ignore_expires=True)
	except: pass
	return content

def TopicsIndex():
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
	debug("(TopicsIndex) -------------------------------------------------- START = TopicsIndex --------------------------------------------------")
	debug("(TopicsIndex) ##### baseURL : "+baseURL+" #####")
	un_WANTED = ['Video', 'Living It']
	ISOLATED = set()
	content = getUrl(baseURL)
	result = content[content.find('<div class="js-programs-menu c-programs-menu c-header-sub-menu')+1:]
	result = result[:result.find('<div class="c-programs-menu__footer">')]
	part = result.split('<div class="list-item')
	debug("(TopicsIndex) xxxxx RESULT : "+str(result)+" xxxxx")
	for i in range(1,len(part),1):
		entry = part[i]
		if '<li class="list-item' in entry:
			mainTHEME = re.compile(r'class=["\']title["\']>([^<]+?)(?:</a>|</span>)', re.DOTALL).findall(entry)[0]
			newMAIN = smart_str(mainTHEME).strip()
			showXTRA = "OKAY"
			try: mainURL = re.compile(r'<a href=["\'](.+?)["\'] class=["\']title["\']>', re.DOTALL).findall(entry)[0]
			except: 
				mainURL = newMAIN
				showXTRA = "NEIN"
			if not any(x in newMAIN for x in un_WANTED):
				newNAME = newMAIN.lower()
				if newNAME in ISOLATED:
					continue
				ISOLATED.add(newNAME)
				debug("(TopicsIndex) ### TITLE : "+str(newMAIN)+" ### URL : "+str(mainURL)+" ###")
				addDir(newMAIN, mainURL, "SubTopics", icon, category=showXTRA)
	liveTV(baseURL+"/api/watchlive.json")
	xbmcplugin.endOfDirectory(pluginhandle)

def SubTopics(firstURL, showXTRA):
	debug("(SubTopics) -------------------------------------------------- START = SubTopics --------------------------------------------------")
	debug("(SubTopics) ##### startURL : "+str(firstURL)+" ##### showXTRA : "+str(showXTRA)+" #####")
	ISOLATED = set()
	content = getUrl(baseURL)
	if showXTRA == "OKAY":
		addDir("NEWS", firstURL, "listVideos", icon)
	result = content[content.find('<div class="js-programs-menu c-programs-menu c-header-sub-menu')+1:]
	result = result[:result.find('<div class="c-programs-menu__footer">')]
	debug("(SubTopics) xxxxx RESULT : "+str(result)+" xxxxx")
	part = result.split('<div class="list-item')
	for i in range(1,len(part),1):
		entry = part[i]
		if '<li class="list-item' in entry:
			try: mainURL = re.compile(r'<a href=["\'](.+?)["\'] class=["\']title["\']>', re.DOTALL).findall(entry)[0]
			except: mainURL = "Nothing"
			mainTHEME = re.compile(r'class=["\']title["\']>([^<]+?)(?:</a>|</span>)', re.DOTALL).findall(entry)[0]
			newMAIN = smart_str(mainTHEME).strip()
			debug("(SubTopics) ### newMAIN : "+str(newMAIN)+" ### firstURL : "+str(firstURL)+" ### mainURL : "+str(mainURL)+" ###")
			if firstURL == mainURL or firstURL == newMAIN:
				match = re.compile('<li class="list-item"><a href="([^"]+?)".*?list-item__link(.+?)</a></li>', re.DOTALL).findall(entry)
				for link, title in match:
					newURL = link.split('/')[-1].strip()
					if newURL in ISOLATED:
						continue
					ISOLATED.add(newURL)
					name = smart_str(title).replace('"', '').replace('>', '').strip()
					if showXTRA == "OKAY":
						addDir(name, "/api/program/"+newURL, "listVideos", icon, category=name)
						debug("(SubTopics) ### SHOW : "+str(name)+" ### newURL : /api/program/"+newURL+" ###")
					else:
						addDir(name, link, "listVideos", icon, category=name)
						debug("(SubTopics) ### SHOW : "+str(name)+" ### LINK : "+link+" ###")
	xbmcplugin.endOfDirectory(pluginhandle)

def listVideos(url, adress):
	debug("(listVideos) -------------------------------------------------- START = listVideos --------------------------------------------------")
	debug("(listVideos) ##### startURL : "+url+" ##### CATEGORY : "+str(adress)+" #####")
	finalURL = False
	FOUND = False
	ISOLATED = set()
	if not "/api/program/" in url: # https://de.euronews.com/api/program/state-of-the-union?before=1519998565&extra=1&offset=13
		content1 = getUrl(baseURL+url)
		url = re.compile('data-api-url="(.+?)"', re.DOTALL).findall(content1)[0]
	if url[:2] == "//": url2 = "https:"+url+"?extra=1"
	else: url2 = baseURL+url+"?extra=1"
	debug("(listVideos) ### URL-2 : "+url2+" ###")
	content2 = getUrl(url2)  
	DATA = json.loads(content2, object_pairs_hook=OrderedDict)
	if "articles" in DATA:
		DATA = DATA['articles']
	for article in DATA:
		debug("(listVideos) xxxxx ARTIKEL : "+str(article)+" xxxxx")
		name = smart_str(article['title']).strip()
		thumb = article['images'][0]['url'].replace('{{w}}x{{h}}', '861x485')
		aired = None
		Note_1 = ""
		Note_2 = ""
		if "publishedAt" in article and article['publishedAt'] != "" and article['publishedAt'] != None:
			aired = datetime.fromtimestamp(article['publishedAt']).strftime('%d.%m.%Y')
			Note_1 = datetime.fromtimestamp(article['publishedAt']).strftime('%d-%m-%Y • %H:%M')
		if Note_1 != "": Note_1 = "[COLOR chartreuse]"+smart_str(Note_1)+"[/COLOR][CR][CR]"
		if "leadin" in article and article['leadin'] != "" and article['leadin'] != None:
			Note_2 = smart_str(article['leadin']).strip()
		plot = Note_1+Note_2
		debug("(listVideos) ### TITLE : "+str(name)+" ### THUMB : "+thumb+" ###")
		if "videos" in article:
			for video in article['videos']:
				if "youtubeId" in video and video['youtubeId'] != "" and video['youtubeId'] != None:
					YOUTUBE_id = video['youtubeId']
				else: YOUTUBE_id = None
				if "duration" in video and video['duration'] != "" and video['duration'] != None:
					duration = int(video['duration'])/1000
				else: duration = ""
				if "quality" in video and video['quality'] == "hd":
					if video['url'] != "" and video['url'] != None:
						finalURL = video['url']
						FOUND = True
				if not FOUND and "quality" in video and video['quality'] == "md":
					if video['url'] != "" and video['url'] != None:
						finalURL = video['url']
						FOUND = True
		if not finalURL or finalURL in ISOLATED:
			continue
		ISOLATED.add(finalURL)
		debug("(listVideos) ### YT-ID : "+str(YOUTUBE_id)+" ### VIDEO : "+str(finalURL)+" ###")
		addLink(name, finalURL, "playVideo", thumb, plot, duration, aired, str(YOUTUBE_id))
	if not FOUND:
		return xbmcgui.Dialog().notification((translation(30522).format('Videos')), (translation(30524).format(adress)), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)   

def liveTV(url):
	debug("(liveTV) -------------------------------------------------- START = liveTV --------------------------------------------------")
	debug("(liveTV) ##### startURL : "+url+" #####")
	content = getUrl(url)
	url1 = re.compile('"url":"(.+?)"', re.DOTALL).findall(content)[0]
	url1 = url1.replace("\/","/").split('//')[1]
	debug("(liveTV) ##### URL-1 : https://"+url1+" #####")
	content1 = getUrl("https://"+url1)
	url2 = re.compile('"primary":"(.+?)"', re.DOTALL).findall(content1)[0]
	url2 = url2.replace("\/","/").split('//')[1]
	debug("(liveTV) ##### URL-2 : https://"+url2+" #####")
	listitem = xbmcgui.ListItem(path="https://"+url2, label="[COLOR lime]* EURONEWS LIVE-TV *[/COLOR]", iconImage=icon, thumbnailImage=icon)
	listitem.setArt({'fanart': defaultFanart})
	xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sys.argv[0]+"?mode=playLive&url="+quote_plus("https://"+url2)+"&category=[COLOR lime]* EURONEWS LIVE-TV *[/COLOR]", listitem=listitem)  
	xbmcplugin.endOfDirectory(pluginhandle)

def playLive(url, name):
	listitem = xbmcgui.ListItem(path=url, label=name)
	listitem.setMimeType('application/vnd.apple.mpegurl')
	xbmc.Player().play(item=url, listitem=listitem)

def playVideo(url, YTID):
	debug("(playVideo) -------------------------------------------------- START = playVideo --------------------------------------------------")
	log("(playVideo) ### YoutubeID = "+str(YTID)+" | Standard-URL = "+url+" ###")
	stream = url
	if (addon.getSetting('YOUTUBE_LINK') == 'true' and YTID):
		try:
			code = urlopen('https://www.youtube.com/oembed?format=json&url=http://www.youtube.com/watch?v='+YOUTUBE_id).getcode()
			if str(code) == '200': stream = 'plugin://plugin.video.youtube/play/?video_id='+YTID
		except: pass
	listitem = xbmcgui.ListItem(path=stream)
	xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, plot=None, category=""):
	u = sys.argv[0]+"?url="+quote_plus(url)+"&mode="+str(mode)+"&category="+str(category)
	liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=image)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	if image != icon:
		liz.setArt({'fanart': image})
	else:
		liz.setArt({'fanart': defaultFanart})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

def addLink(name, url, mode, image, plot=None, duration=None, aired=None, YOUTUBE_id=None, category=""):
	u = sys.argv[0]+"?url="+quote_plus(url)+"&mode="+str(mode)+"&YOUTUBE_id="+str(YOUTUBE_id)+"&category="+str(category)
	liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=image)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot, 'Duration': duration, 'Date': aired, 'Genre': 'News', 'Studio': 'euronews'})
	if image != icon:
		liz.setArt({'fanart': image})
	else:
		liz.setArt({'fanart': defaultFanart})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	liz.setContentLookup(False)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)

params = parameters_string_to_dict(sys.argv[2])
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
YOUTUBE_id = unquote_plus(params.get('YOUTUBE_id', ''))
category = unquote_plus(params.get('category', ''))

if mode == "SubTopics":
	SubTopics(url, category)
elif mode == "listVideos":
	listVideos(url, category)
elif mode  == "liveTV":
	liveTV(url)
elif mode == "playLive":
	playLive(url, category)
elif mode == "playVideo":
	playVideo(url, YOUTUBE_id)
else:
	TopicsIndex()