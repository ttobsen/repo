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
elif PY3:
	from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode  # Python 3+
import json
import xbmcvfs
import shutil
import socket
import time
from datetime import datetime
import requests
try:
	from requests.packages.urllib3.exceptions import InsecureRequestWarning
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except: pass

global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
temp        = xbmc.translatePath(os.path.join(dataPath, 'temp', '')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
langSHORTCUT = addon.getSetting("language")
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == 'true'
baseURL = "https://sovietmoviesonline.com"

__HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0','Accept-Encoding': 'gzip, deflate'}
xbmcplugin.setContent(int(sys.argv[1]), 'movies')


def py2_enc(s, encoding='utf-8'):
	if PY2:
		if not isinstance(s, basestring):
			s = str(s)
		s = s.encode(encoding) if isinstance(s, unicode) else s
	return s

def translation(id):
	return py2_enc(addon.getLocalizedString(id))

def failing(content):
	log(content, xbmc.LOGERROR)

def debug(content):
	log(content, xbmc.LOGDEBUG)

def log(msg, level=xbmc.LOGNOTICE):
	xbmc.log("["+addon.getAddonInfo('id')+"-"+addon.getAddonInfo('version')+"]"+py2_enc(msg), level)

def getUrl(url, method, allow_redirects=False, verify=False, headers="", data="", timeout=40):
	response = requests.Session()
	if method == 'GET':
		content = response.get(url, allow_redirects=allow_redirects, verify=verify, headers=headers, data=data, timeout=timeout).text
	elif method == 'POST':
		content = response.post(url, data=data, allow_redirects=allow_redirects, verify=verify).text
	return content

def index():
	debug("(index) -------------------------------------------------- START = index --------------------------------------------------")
	if langSHORTCUT == "EN":
		startURL = baseURL
	else:
		startURL = baseURL+"/ru"
	addDir(translation(30601), startURL+"/all_movies.html", "listVideos", icon)
	addDir(translation(30602), "", "listTopics", icon, category="Genres")
	addDir(translation(30603), "", "listTopics", icon, category="Decades")
	addDir(translation(30604), "", "listTopics", icon, category="Directors")
	addDir(translation(30608), "", "aSettings", icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def listTopics(category=""):
	debug("(listTopics) -------------------------------------------------- START = listTopics --------------------------------------------------")
	if langSHORTCUT == "EN":
		startURL = baseURL
	else:
		startURL = baseURL+"/ru/"
	debug("(listTopics) ##### startURL : "+startURL+" ##### Category : "+category+" #####")
	content = getUrl(startURL, 'GET', False, False, __HEADERS)
	if category == "Genres":
		result = content[content.find('<span class="link movie-popup-link">')+1:]
		result = result[:result.find('</div>')]
	elif category == "Decades":
		result = content[content.find('<div id="decades">')+1:]
		result = result[:result.find('</div>')]
	elif category == "Directors":
		result = content[content.find('<div id="directors">')+1:]
		result = result[:result.find('<div class="clear"></div>')]
	if category == "Genres" or category == "Decades":
		match = re.compile('<a href="([^"]+?)">(.+?)</a>', re.DOTALL).findall(result)
		for url2, title in match:
			if url2[:4] != "http":
				url2 = baseURL+url2
			name = py2_enc(re.sub('\<.*?\>', '', title))
			if category == "Decades" and langSHORTCUT == "EN":
				name += " 's"
			elif category == "Decades" and langSHORTCUT == "RU":
				name += " -e"
			debug("(listTopics) no.1 ### TITLE : "+name+" ### URL-2 : "+url2+" ###")
			addDir(name, url2, "listVideos", icon)
	else:
		match = re.compile(' href="([^"]+?)">.*?<img src="([^"]+?)" alt="([^"]+?)".*?</span>', re.DOTALL).findall(result)
		for url2, thumb, title in match:
			if url2[:4] != "http":
				url2 = baseURL+url2
			if thumb[:4] != "http":
				thumb = baseURL+thumb
			name = py2_enc(re.sub('\<.*?\>', '', title))
			log("(listTopics) no.2 ### TITLE : "+name+" ### URL-2 : "+url2+" ###")
			log("(listTopics) no.2 ### THUMB : "+thumb+" ###")
			addDir(name, url2, "listVideos", thumb)
	xbmcplugin.endOfDirectory(pluginhandle)

def listVideos(url):
	debug("(listVideos) -------------------------------------------------- START = listVideos --------------------------------------------------")
	debug("(listVideos) ##### startURL : "+url+" #####")
	un_WANTED = ['sovietmoviesonline.com/blog/', 'sovietmoviesonline.com/ru/blog/']
	startURL = url
	content = getUrl(url, 'GET', False, False, __HEADERS)
	part = content.split('<!--small movie-->')
	for i in range(1, len(part), 1):
		entry = part[i]
		debug("(listVideos) xxxxx ENTRY : "+str(entry)+" xxxxx")
		try:
			url2 = re.compile('<a href="([^"]+?)"', re.DOTALL).findall(entry)[0]
			if url2[:4] != "http":
				url2 = baseURL+url2
			if not any(x in url2 for x in un_WANTED):
				thumb = re.compile('src="([^"]+?)"', re.DOTALL).findall(entry)[0]
				if thumb[:4] != "http":
					thumb = baseURL+thumb
				Title1 = re.compile('<div class="small-title">(.+?)</div>', re.DOTALL).findall(entry)[0]
				Title2 = re.compile('<div class="title">(.+?)</div>', re.DOTALL).findall(entry)[0]
				CPtitle1 = re.sub('\<.*?\>', '', Title1)
				CPtitle2 = re.sub('\<.*?\>', '', Title2)
				if langSHORTCUT == "RU" and "/all_movies" in startURL:
					name = cleanTitle(CPtitle1)+"  ("+cleanTitle(CPtitle2)+")"
				else:
					name = cleanTitle(CPtitle2)+"  ("+cleanTitle(CPtitle1)+")"
				year = re.compile('<div class="year">(.+?)</div>', re.DOTALL).findall(entry)[0]
				#if "teleserial" in url2 or "mini-serial" in url2:
					#addDir(name, url2, "listSeries", thumb)
				#else:
				debug("(listVideos) ### TITLE : "+name+" ### URL-2 : "+url2+" ###")
				debug("(listVideos) ### YEAR : "+year+" ### THUMB : "+thumb+" ###")
				addLink(name, url2, "playVideo", thumb, year=year)
		except:
			failing("(listVideos) ERROR - ERROR - ERROR ### {0} ###".format(str(entry)))
	xbmcplugin.endOfDirectory(pluginhandle)

def listSeries(url, photo):
	debug("(listSeries) -------------------------------------------------- START = listSeries --------------------------------------------------")
	debug("(listSeries)  ##### startURL : "+url+" ##### IMAGE : "+image+" #####")
	startURL = url
	content = getUrl(url, 'GET', False, False, __HEADERS)
	pos = 0
	result = content[content.find('<div id="video">')+1:]
	result = result[:result.find('<script type="text/javascript" src=')]
	videoPARTS = result.find('<div class="episodes-links')
	if videoPARTS != -1:
		if langSHORTCUT == "EN":
			EPlinks = re.findall('<div class="episodes-links en">(.+?)</div>', result, re.DOTALL)
		else:
			EPlinks = re.findall('<div class="episodes-links ru">(.+?)</div>', result, re.DOTALL)
		for chtml in EPlinks:
			debug("(listSeries) no.1 ### TITLE : Episode 1 ### URL-2 : "+startURL+" ###")
			addLink("Episode 1", startURL, "playVideo", photo)
			match = re.compile('<a href="([^"]+?)">(.+?)</a>', re.DOTALL).findall(chtml)
			for url2, title in match:
				pos += 1
				if url2[:4] != "http":
					url2 = baseURL+url2
				name = py2_enc(re.sub('\<.*?\>', '', title))
				debug("(listSeries) no.2 ### TITLE : "+name+" ### URL-2 : "+url2+" ###")
				addLink("Episode "+name, url2, "playVideo", photo)
	if pos == 0:
		playVideo(url)
	xbmcplugin.endOfDirectory(pluginhandle)
  
def playVideo(url):
	debug("(playVideo) -------------------------------------------------- START = playVideo --------------------------------------------------")
	debug("(playVideo)  ##### startURL : "+url+" #####")
	finalURL = False
	content = getUrl(url, 'GET', False, False, __HEADERS)
	try:
		finalURL = re.compile('<iframe src="([^"]+?)" width', re.DOTALL).findall(content)[0]
		finalURL = "https://vimeo.com/"+finalURL.split('/')[-1]
		try:
			if langSHORTCUT == "EN":
				SUB = re.compile('track src="([^"]+?)"', re.DOTALL).findall(content)[0]
			else:
				SUB = re.compile('track src="([^"]+?)"', re.DOTALL).findall(content)[1]
			subContent = getUrl(baseURL+SUB)
			subFile = temp+"/sub.srt"
			fh = open(subFile, 'wb')
			fh.write(subContent)
			fh.close()
		except:
			SUB = ""
			subFile = ""
		debug("(playVideo) ### finalURL : "+str(finalURL)+" ###")
		debug("(playVideo) ### subTITLE : "+SUB+" ###")
		if finalURL:
			listitem = xbmcgui.ListItem(path=finalURL)
			listitem.setSubtitles([subFile])
			xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
			log("(playVideo) streamURL : {0}".format(finalURL))
	except:
		if '<div id="dle-info"  title="Error">' in content or '<div id="dle-info"  title="Ошибка">' in content:
			xbmcgui.Dialog().notification(addon.getAddonInfo('id')+translation(30521), translation(30522), icon, 8000)
		else:
			failing("(playVideo) PlayLink-00 : *Intern* Error requesting the play link !!!")

def cleanTitle(title):
	title = py2_enc(title)
	title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
	title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
	return title.strip()

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
	u = sys.argv[0]+"?url="+quote_plus(url)+"&mode="+str(mode)+"&image="+quote_plus(image)+"&category="+str(category)
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon:
		liz.setArt({'fanart': image})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

def addLink(name, url, mode, image, plot=None, duration=None, year=""):
	u = sys.argv[0]+"?url="+quote_plus(url)+"&mode="+str(mode)
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot, 'Duration': duration, 'Year': year, 'Studio': 'sovietmovies'})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon:
		liz.setArt({'fanart': image})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	liz.setContentLookup(False)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
category = unquote_plus(params.get('category', ''))

if mode == 'listTopics':
	listTopics(category)
elif mode == 'listVideos':
	listVideos(url)
elif mode == 'listSeries':
	listSeries(url, image)
elif mode == 'playVideo':
	playVideo(url)
elif mode == 'aSettings':
	addon.openSettings()
else:
	index()