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
from datetime import datetime, timedelta
import requests
try:
	from requests.packages.urllib3.exceptions import InsecureRequestWarning
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except: pass


global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath    = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg') or os.path.join(addonPath, 'resources', 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png') or os.path.join(addonPath, 'resources', 'icon.png')
baseURL = 'http://www.zeeone.de'

__HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0', 'Accept-Encoding': 'gzip, deflate'}
xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

if not xbmcvfs.exists(dataPath):
	xbmcvfs.mkdirs(dataPath)

def py2_enc(s, encoding='utf-8'):
	if PY2:
		if not isinstance(s, basestring):
			s = str(s)
		s = s.encode(encoding) if isinstance(s, unicode) else s
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
	xbmc.log('[{0} v.{1}]{2}'.format(addon.getAddonInfo('id'), addon.getAddonInfo('version'), py2_enc(msg)), level)

def getUrl(url, method, allow_redirects=False, verify=False, stream=False, headers="", data="", timeout=40):
	response = requests.Session()
	if method == 'GET':
		content = response.get(url, allow_redirects=allow_redirects, verify=verify, stream=stream, headers=headers, data=data, timeout=timeout).text
	elif method == 'POST':
		content = response.post(url, data=data, allow_redirects=allow_redirects, verify=verify).text
	content = py2_enc(content)
	return content

def index():  
	html = getUrl(baseURL+'/BollyThek', 'GET', False, False, False, __HEADERS)
	categories = re.findall('<a class=["\'] dropdown-toggle["\'] href=["\'](.+?)["\']>([^<]+)<span class=["\']caret["\']>', html, re.DOTALL)
	for link, title in categories:
		link = link+'.aspx?aspxerrorpath='+link
		if link[:4] != 'http': link = baseURL+link
		title = _clean(title)
		debug("(index) ### NAME : {0} || LINK : {1} ###".format(str(title), link))
		addDir(title, link, 'listEpisodes', icon, nosub=title)
	xbmcplugin.endOfDirectory(pluginhandle)

def listEpisodes(url, cat):
	debug("(listEpisodes) ------------------------------------------------ START = listEpisodes -----------------------------------------------")
	debug("(listEpisodes) ### URL = {0} ### CAT = {1} ###".format(url, cat))
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
	UNIKAT = set()
	FOUND = 0
	html = getUrl(url, 'GET', False, False, False, __HEADERS)
	carousel = re.findall('<div class=["\']carouselbox["\']>(.+?)</div>', html, re.DOTALL)
	for chtml in carousel:
		debug("(listEpisodes) ### ENTRY = {0} ###".format(str(chtml)))
		FOUND = 1
		link = re.compile('href=["\']([^"\']+)["\']>', re.DOTALL).findall(chtml)[0]
		if link[:4] != 'http': link = baseURL+link
		title = re.compile('<h3 class=["\']pg-name["\']>([^<]+)</h3>', re.DOTALL).findall(chtml)[0]
		name = _clean(title)
		origSERIE = name
		subtitle = ""
		EPnom = None
		try:
			title2 = re.compile('<span >(.+?)</span>', re.DOTALL).findall(chtml)[0]
			subtitle = re.sub('\<.*?\>', '', title2).replace('Folge', 'Folge ').replace('FOLGE', 'Folge ')
			EPnom = re.findall('([0-9]+)', subtitle, re.S)[0].strip().zfill(4)
		except: pass
		if subtitle != "" and name not in subtitle:
			name = name+' | '+subtitle
		if name in UNIKAT:
			continue
		UNIKAT.add(name)
		photo = re.compile('<img data-lazy=["\']([^"\']+)["\']', re.DOTALL).findall(chtml)[0]
		desc = re.compile('<p class[^>]*>(.*?)</p>', re.DOTALL).findall(chtml)[0]
		desc = re.sub('\<.*?\>', '', desc)
		plot = origSERIE+translation(30610).format(_clean(desc))
		debug("(listEpisodes) ##### NAME : {0} || LINK : {1} || IMG : {2} #####".format(str(name), link, str(photo)))
		addLink(name, link,'playVideo', photo, plot, origSERIE, episode=EPnom)
	if FOUND == 0:
		return xbmcgui.Dialog().notification(translation(30522).format('Einträge'), translation(30524).format(cat), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url, filter):
	debug("(playVideo) -------------------------------------------------- START = playVideo --------------------------------------------------")
	debug("(playVideo) ### URL = {0} ### FILTER = {1} ###".format(url, filter))
	finalURL = False
	html = getUrl(url, 'GET', False, False, False, __HEADERS)
	finalURL = re.compile('file: ["\']([^"\']+)["\'],', re.DOTALL).findall(html)[0]
	if finalURL:
		log("(playVideo) StreamURL : {0}".format(finalURL))
		listitem = xbmcgui.ListItem(path=finalURL)
		xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
	else:
		failing("(playVideo) ##### Abspielen des Streams NICHT möglich ##### URL : {0} #####\n   ########## KEINEN Stream-Eintrag auf der Webseite von *zeeone.de* gefunden !!! ##########".format(url))
		return xbmcgui.Dialog().notification(translation(30521).format('PlayerUrl'), translation(30525), icon, 8000)

def _clean(text):
	text = py2_enc(text)
	for n in (('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'), ('&Amp;', '&'), ('&apos;', "'"), ("&#x27;", "'"), ('&#34;', '"'), ('&#39;', '\''), ('&#039;', '\'')
		, ('&#x00c4', 'Ä'), ('&#x00e4', 'ä'), ('&#x00d6', 'Ö'), ('&#x00f6', 'ö'), ('&#x00dc', 'Ü'), ('&#x00fc', 'ü'), ('&#x00df', 'ß'), ('&#xD;', ''), ('\xc2\xb7', '-')
		, ('&#xC4;', 'Ä'), ('&#xE4;', 'ä'), ('&#xD6;', 'Ö'), ('&#xF6;', 'ö'), ('&#xDC;', 'Ü'), ('&#xFC;', 'ü'), ('&#xDF;', 'ß'), ('&#x201E;', '„'), ('&#xB4;', '´'), ('&#x2013;', '-'), ('&#xA0;', ' ')
		, ('\\xC4', 'Ä'), ('\\xE4', 'ä'), ('\\xD6', 'Ö'), ('\\xF6', 'ö'), ('\\xDC', 'Ü'), ('\\xFC', 'ü'), ('\\xDF', 'ß'), ('\\x201E', '„'), ('\\x28', '('), ('\\x29', ')'), ('\\x2F', '/'), ('\\x2D', '-'), ('\\x20', ' '), ('\\x3A', ':'), ('\\"', '"')
		, ("&quot;", "\""), ("&Quot;", "\""), ('&szlig;', 'ß'), ('&mdash;', '-'), ('&ndash;', '-'), ('&Auml;', 'Ä'), ('&Euml;', 'Ë'), ('&Iuml;', 'Ï'), ('&Ouml;', 'Ö'), ('&Uuml;', 'Ü')
		, ('&auml;', 'ä'), ('&euml;', 'ë'), ('&iuml;', 'ï'), ('&ouml;', 'ö'), ('&uuml;', 'ü'), ('&#376;', 'Ÿ'), ('&yuml;', 'ÿ')
		, ('&agrave;', 'à'), ('&Agrave;', 'À'), ('&aacute;', 'á'), ('&Aacute;', 'Á'), ('&acirc;', 'â'), ('&Acirc;', 'Â'), ('&egrave;', 'è'), ('&Egrave;', 'È'), ('&eacute;', 'é'), ('&Eacute;', 'É'), ('&ecirc;', 'ê'), ('&Ecirc;', 'Ê')
		, ('&igrave;', 'ì'), ('&Igrave;', 'Ì'), ('&iacute;', 'í'), ('&Iacute;', 'Í'), ('&icirc;', 'î'), ('&Icirc;', 'Î'), ('&ograve;', 'ò'), ('&Ograve;', 'Ò'), ('&oacute;', 'ó'), ('&Oacute;', 'ó'), ('&ocirc;', 'ô'), ('&Ocirc;', 'Ô')
		, ('&ugrave;', 'ù'), ('&Ugrave;', 'Ù'), ('&uacute;', 'ú'), ('&Uacute;', 'Ú'), ('&ucirc;', 'û'), ('&Ucirc;', 'Û'), ('&yacute;', 'ý'), ('&Yacute;', 'Ý')):
		text = text.replace(*n)
	return text.strip()

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, plot=None, nosub='00'):
	u = '{0}?url={1}&mode={2}&nosub={3}'.format(sys.argv[0], quote_plus(url), str(mode), str(nosub))
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if image != icon:
		liz.setArt({'fanart': image})
	return xbmcplugin.addDirectoryItem(pluginhandle, url=u, listitem=liz, isFolder=True)

def addLink(name, url, mode, image, plot=None, origSERIE=None, duration=None, tagline=None, season=None, episode=None, genre=None, year=None, begins=None, nosub='00'):
	u = '{0}?url={1}&mode={2}&nosub={3}'.format(sys.argv[0], quote_plus(url), str(mode), str(nosub))
	liz = xbmcgui.ListItem(name)
	ilabels = {}
	ilabels['Episode'] = episode
	ilabels['Tvshowtitle'] = origSERIE
	ilabels['Title'] = name
	ilabels['Tagline'] = tagline
	ilabels['Plot'] = plot
	ilabels['Duration'] = duration
	if begins != None:
		ilabels['Date'] = begins
	ilabels['Year'] = year
	ilabels['Genre'] = 'Bollywood'
	ilabels['Director'] = None
	ilabels['Writer'] = None
	ilabels['Studio'] = 'Zee.One'
	ilabels['Mpaa'] = None
	if episode != None:
		ilabels['Mediatype'] = 'episode'
	else: ilabels['Mediatype'] = 'video'
	liz.setInfo(type='Video', infoLabels=ilabels)
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if image != icon:
		liz.setArt({'fanart': image})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

params = parameters_string_to_dict(sys.argv[2])
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
nosub = unquote_plus(params.get('nosub', ''))
origSERIE = unquote_plus(params.get('origSERIE', ''))

if mode == 'aSettings':
	addon.openSettings()
elif mode == 'listEpisodes':
	listEpisodes(url, nosub)
elif mode == 'playVideo':
	playVideo(url, nosub)
else:
	index()
