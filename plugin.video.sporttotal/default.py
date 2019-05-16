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
	try:
		import StorageServer
	except:
		from resources.lib import storageserverdummy as StorageServer
elif PY3:
	from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode, urljoin, urlparse, urlunparse  # Python 3+
	from urllib.request import build_opener, HTTPCookieProcessor, Request, urlopen  # Python 3+
	from http.cookiejar import LWPCookieJar  # Python 3+
import json
import xbmcvfs
import shutil
import socket
import time
import datetime
import io
import gzip

global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
socket.setdefaulttimeout(40)
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath    = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
enableInputstream = addon.getSetting("inputstream") == "true"
enableAdjustment = addon.getSetting("show_settings") == "true"
if PY2:
	cachePERIOD = int(addon.getSetting("cacheTime"))
	cache = StorageServer.StorageServer(addon.getAddonInfo('id'), cachePERIOD) # (Your plugin name, Cache time in hours)
baseURL = "https://www.sporttotal.tv"

xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

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

def makeREQUEST(url):
	if PY2:
		INQUIRE = cache.cacheFunction(getUrl, url)
	elif PY3:
		INQUIRE = getUrl(url)
	return INQUIRE

def getUrl(url, header=None, referer=None):
	debug("(getUrl) -------------------------------------------------- START = getUrl --------------------------------------------------")
	req = Request(url)
	try:
		if header:
			req.add_header = header
		else:
			req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0')
			req.add_header('Accept-Encoding', 'gzip, deflate')
		if referer:
			req.add_header = ('Referer', referer)
		response = urlopen(req, timeout=40)
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
	response.close()
	return content

def ADDON_operate(INPUT_STREAM):
	js_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.GetAddonDetails", "params": {"addonid":"'+INPUT_STREAM+'", "properties": ["enabled"]}, "id":1}')
	if '"enabled":false' in js_query:
		try:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.SetAddonEnabled", "params": {"addonid":"'+INPUT_STREAM+'", "enabled":true}, "id":1}')
			failing("(ADDON_operate) ERROR - ERROR - ERROR :\n##### Das benötigte Addon : *inputstream.adaptive* ist NICHT aktiviert !!! #####\n##### Es wird jetzt versucht die Aktivierung durchzuführen !!! #####")
		except: pass
	if '"error":' in js_query:
		xbmcgui.Dialog().ok(addon.getAddonInfo('id'), translation(30501))
		failing("(ADDON_operate) ERROR - ERROR - ERROR :\n##### Das benötigte Addon : *inputstream.adaptive* ist NICHT installiert !!! #####\n##### Bitte KODI-Krypton (Version 17 oder höher) installieren, Diese enthalten das erforderliche Addon im Setup !!! #####")
		return False
	if '"enabled":true' in js_query:
		return True

def clearCache():
	debug("(clearCache) -------------------------------------------------- START = clearCache --------------------------------------------------")
	if PY2:
		debug("(clearCache) ========== Lösche jetzt den Addon-Cache ==========")
		cache.delete("%")
		xbmc.sleep(2000)
		xbmcgui.Dialog().ok(addon.getAddonInfo('id'), translation(30502))
	elif PY3:
		Python_Version = str(sys.version).split(')')[0].strip()+")"
		xbmcgui.Dialog().ok(addon.getAddonInfo('id'), (translation(30503).format(Python_Version)))

def index():
	debug("(index) -------------------------------------------------- START = index --------------------------------------------------")
	addDir(translation(30601), baseURL+"/live", "Sportarts_Overview", icon, ffilter="Uebertragungen")
	addDir(translation(30602), baseURL, "Sportarts_Overview", icon, ffilter="Anderes")
	addDir(translation(30603), baseURL+"/ligen", "Sportarts_Overview", icon, ffilter="Ligen")
	addDir(translation(30604), baseURL+"/amator", "Clips_Categories", icon, category="AMATor")
	if enableAdjustment:
		addDir(translation(30605), "", "aSettings", icon)
		if enableInputstream:
			if ADDON_operate('inputstream.adaptive'):
				addDir(translation(30606), "", "iSettings", icon)
			else:
				addon.setSetting("inputstream", "false")
	xbmcplugin.endOfDirectory(pluginhandle)

def Sportarts_Overview(url, ffilter=""):
	debug("(Sportarts_Overview) -------------------------------------------------- START = Sportarts_Overview --------------------------------------------------")
	debug("(Sportarts_Overview) ### URL = {0} ### FFILTER = {1} ###".format(url, ffilter))
	content = makeREQUEST(url)
	if ffilter == "Anderes":
		result = content[content.find('<h1>SPORTARTEN</h1>')+1:]
		result = result[:result.find('<h1>')]
	else:
		result = content[content.find('<nav class="sport-selector"')+1:]
		result = result[:result.find('</nav>')]
	selection = re.findall('a href="([^"]+?)".*?<i class="([^"]+?)".*?</a>', result, re.DOTALL)
	for url2, title in selection:
		if title != "":
			name = title.replace('far fa-futbol', 'Fussball').replace('fal fa-volleyball-ball', 'Volleyball').replace('fal fa-field-hockey', 'Feldhockey').replace('fal fa-hockey-sticks', 'Eishockey').replace('far fa-football-ball', 'American Football').replace('fal fa-futbol', 'Futsal').replace('fal fa-basketball-ball', 'Basketball')
			if ffilter == "Uebertragungen":
				if url2[:4] != "http":
					url2 = baseURL+"/live"+url2
				addDir(name, url2, "Livegames_Videos", icon, category=name)
			elif ffilter == "Anderes":
				if url2[:4] != "http":
					url2 = baseURL+url2
				addDir(name, url2, "Clips_Categories", icon, category=name)
			elif ffilter == "Ligen":
				if url2[:4] != "http":
					url2 = baseURL+url2
				addDir(name, url2, "Leagues_Overview", icon, category=name)
			debug("(Sportarts_Overview) NAME = {0} ##### URL2 = {1}".format(name, url2))
	xbmcplugin.endOfDirectory(pluginhandle)

def Livegames_Videos(url, category=""):
	debug("(Livegames_Videos) -------------------------------------------------- START = Livegames_Videos --------------------------------------------------")
	debug("(Livegames_Videos) ### URL = {0} ### CATEGORY = {1} ###".format(url, category))
	SPORTSNAME = unquote_plus(category)
	COMBINATION1 = []
	COMBINATION2 = []
	unWANTED_1 = ""
	videoIsolated_List1 = set()
	videoIsolated_List2 = set()
	count = 0
	pos1 = 0
	pos2 = 0
	content = getUrl(url)
	if '<div id="livegames" class="livegame-table">' in content or '<div id="upcoming-games" class="livegame-table">' in content or '<section class="event-meta player-meta">' in content:
		if '<div id="livegames" class="livegame-table">' in content:
			result = content[content.find('<div id="livegames" class="livegame-table">')+1:]
			result = result[:result.find('</tbody>')]
			part = result.split('class="table-link"')
			for i in range(1, len(part), 1):
				element = part[i]
				try:
					vidURL = re.compile('onclick="tableLink(.+?)">', re.DOTALL).findall(element)[0].replace('"', '').replace("'", "").replace('(', '').replace(')', '')
					if vidURL[:4] != "http":
						vidURL = baseURL+vidURL
					teams = re.compile('class="teams-filter">(.+?)</span>', re.DOTALL).findall(element)[0]
					teams = cleanTitle(teams)
					if teams =="":
						continue
					relevance = re.compile('class="date-filter">(.+?)</span>', re.DOTALL).findall(element)[0].strip()
					try:
						datetime_object = datetime.datetime.strptime(relevance, '%d.%m.%Y %H:%M')
					except TypeError:
						datetime_object = datetime.datetime(*(time.strptime(relevance, '%d.%m.%Y %H:%M')[0:6]))
					actualTIME = datetime_object.strftime("%H:%M")
					title = relevance+" - "+teams
					if title in videoIsolated_List1:
						continue
					videoIsolated_List1.add(title)
					try: photo = re.compile('<img.+?src="([^"]+?)"', re.DOTALL).findall(element)[0].replace('&#223;', '%C3%9F') # -ß- Esszett für Browser-URL deklarieren, damit das Bild angezeigt wird
					except: photo = ""
					if photo != "" and photo[:4] != "http":
						photo = baseURL+photo
					if photo != "" and "?w=" in photo:
						photo = photo.split('?w=')[0]+"?w=300"
					if photo != "" and not "?w=" in photo:
						photo = photo+"?w=300"
					if photo == "":
						photo = baseURL+"/assets/clublogo_placeholder.png"
					unWANTED_1 = title # to hide double-entries to second LIST
					name = "[COLOR chartreuse][B]~ ~ ~  ( LIVE )[/B][/COLOR]  ["+actualTIME+"]  "+teams+"  [COLOR chartreuse][B]~ ~ ~[/B][/COLOR]"
					COMBINATION1.append([datetime_object, name, vidURL, photo])
				except:
					pos1 += 1
					failing("(Live_Games) Fehler-Eintrag-01 : {0} #####".format(str(element)))
					if pos1 > 1 and count == 0:
						count += 1
						xbmcgui.Dialog().notification((translation(30521).format('DISPLAY')), translation(30523), icon, 8000)
		if '<div id="upcoming-games" class="livegame-table">' in content:
			result = content[content.find('<div id="upcoming-games" class="livegame-table">')+1:]
			result = result[:result.find('</tbody>')]
			part = result.split('class="table-link"')
			for i in range(1, len(part), 1):
				element = part[i]
				try:
					vidURL = re.compile('onclick="tableLink(.+?)">', re.DOTALL).findall(element)[0].replace('"', '').replace("'", "").replace('(', '').replace(')', '')
					if vidURL[:4] != "http":
						vidURL = baseURL+vidURL
					try:
						division = re.compile('class="division">(.+?)</div>', re.DOTALL).findall(element)[0]
						division = cleanTitle(division)
					except: division = ""
					teams = re.compile('class="teams-filter">(.+?)</span>', re.DOTALL).findall(element)[0]
					teams = cleanTitle(teams)
					if teams =="":
						continue
					relevance = re.compile('class="date-filter">(.+?)</span>', re.DOTALL).findall(element)[0].strip()
					try:
						datetime_object = datetime.datetime.strptime(relevance, '%d.%m.%Y %H:%M')
					except TypeError:
						datetime_object = datetime.datetime(*(time.strptime(relevance, '%d.%m.%Y %H:%M')[0:6]))
					actualTIME = datetime_object.strftime("%H:%M")
					title = relevance+" - "+teams
					if title in videoIsolated_List2:
						continue
					videoIsolated_List2.add(title)
					try: photo = re.compile('<img.+?src="([^"]+?)"', re.DOTALL).findall(element)[0].replace('&#223;', '%C3%9F') # -ß- Esszett für Browser-URL deklarieren, damit das Bild angezeigt wird
					except: photo = ""
					if photo != "" and photo[:4] != "http":
						photo = baseURL+photo
					if photo != "" and "?w=" in photo:
						photo = photo.split('?w=')[0]+"?w=300"
					if photo != "" and not "?w=" in photo:
						photo = photo+"?w=300"
					if photo == "":
						photo = baseURL+"/assets/clublogo_placeholder.png"
					unWANTED_2 = title # hide double-entries from first LIST
					if unWANTED_1 != "" and unWANTED_1 in unWANTED_2:
						continue
					if division == "":
						name = relevance+" - "+teams
					else:
						name = relevance+" - "+teams+"  ("+division+")"
					COMBINATION2.append([datetime_object, name, vidURL, photo])
				except:
					pos2 += 1
					failing("(Live_Games) Fehler-Eintrag-02 : {0} #####".format(str(element)))
					if pos2 > 1 and count == 0:
						count += 1
						xbmcgui.Dialog().notification((translation(30521).format('DISPLAY')), translation(30523), icon, 8000)
		if not '<div id="livegames" class="livegame-table">' in content and '<section class="event-meta player-meta">' in content:
			try:
				meta_video = re.compile('<section class="event-meta player-meta">(.+?)</section>', re.DOTALL).findall(content)[0]
				vidURL = url
				teams = re.compile('class="meta-title">(.+?)</p>', re.DOTALL).findall(meta_video)[0]
				teams = cleanTitle(teams).replace(' - ', ' : ')
				try: photo = re.compile(r'style="background-image.+?(?:\(|\")([^)"]+?)(?:\)|\")', re.DOTALL).findall(meta_video)[0].replace('&#223;', '%C3%9F') # -ß- Esszett für Browser-URL deklarieren, damit das Bild angezeigt wird
				except: photo = ""
				if photo != "" and photo[:4] != "http":
					photo = baseURL+photo
				if photo != "" and "?w=" in photo:
					photo = photo.split('?w=')[0]+"?w=300"
				if photo != "" and not "?w=" in photo:
					photo = photo+"?w=300"
				if photo == "":
					photo = baseURL+"/assets/clublogo_placeholder.png"
				name = "[COLOR chartreuse][B]~ ~ ~  ( LIVE )[/B][/COLOR]  "+teams+"  [COLOR chartreuse][B]~ ~ ~[/B][/COLOR]"
				addDir(translation(30610), "", "Livegames_Videos", icon)
				addLink(name, vidURL, "playVideo", photo, background="KEIN HINTERGRUND")
			except: pass
		if COMBINATION1:
			addDir(translation(30610), "", "Livegames_Videos", icon)
			for datetime_object, name, vidURL, photo in sorted(COMBINATION1, key=lambda item:item[0], reverse=False):
				addLink(name, vidURL, "playVideo", photo, background="KEIN HINTERGRUND")
		if COMBINATION2:
			addDir(translation(30611), "", "Livegames_Videos", icon)
			for datetime_object, name, vidURL, photo in sorted(COMBINATION2, key=lambda item:item[0], reverse=False):
				addLink(name, vidURL, "playVideo", photo, background="KEIN HINTERGRUND")
	else:
		return xbmcgui.Dialog().notification((translation(30522).format('Einträge')), (translation(30525).format(SPORTSNAME.upper()+' - LIVE')), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def Clips_Categories(url, ffilter="", category=""):
	debug("(Clips_Categories) -------------------------------------------------- START = Clips_Categories --------------------------------------------------")
	debug("(Clips_Categories) ### URL = {0} ### FFILTER = {1} ### CATEGORY = {2} ###".format(url, ffilter, category))
	Supported = ['top clips', 'highlights', 'wiederholungen', 'monats-gewinner', 'monats-kandidaten', 'jahres-gewinner']
	CHOICE = category
	FOUND = False
	content = makeREQUEST(url)
	if category == "AMATor" and '<div class="player-meta item-meta">' in content:
		try:
			meta_video = re.compile('<div class="player-meta item-meta">(.+?)<h1 class="grid-header max-width-padding">', re.DOTALL).findall(content)[0]
			vidURL = url
			title = re.compile('<h1>(.+?)</h1>', re.DOTALL).findall(meta_video)[0]
			title = cleanTitle(title)
			try: photo = re.compile(r'style="background-image.+?(?:\(|\")([^)"]+?)(?:\)|\")', re.DOTALL).findall(meta_video)[0].replace('&#223;', '%C3%9F') # -ß- Esszett für Browser-URL deklarieren, damit das Bild angezeigt wird
			except: photo = ""
			if photo != "" and photo[:4] != "http":
				photo = baseURL+photo
			if photo != "" and "?w=" in photo:
				photo = photo.split('?w=')[0]+"?w=1280"
			if photo != "" and not "?w=" in photo:
				photo = photo+"?w=1280"
			if photo == "":
				photo = baseURL+"/assets/no_thumb_placeholder.jpg"
			if title !="":
				FOUND = True
				name = title.replace("HIGHLIGHTS", "").replace("Highlights", "").replace("HIGHLIGHT", "").replace("Highlight", "").replace("HYUNDAI-", "").replace("Hyundai-", "").replace("HYUNDAI ", "").replace("Hyundai ", "")
				addLink((translation(30612).format(name)), vidURL, "playVideo", photo)
		except: pass
	match = re.findall('<h1 class="grid-header max-width-padding">(.*?)</h1>', content, re.DOTALL)
	for title in match:
		name = title.replace('Weiderholungen', 'Wiederholungen')
		if name !="" and any(x in name.lower() for x in Supported):
			FOUND = True
			if ffilter == "umdrehen":
				addDir(name, url, "Clips_Videos", icon, ffilter="umdrehen", category=title)
			else:
				addDir(name, url, "Clips_Videos", icon, category=title)
			debug("(Clips_Categories) TITLE = {0} #####".format(title))
	if not FOUND:
		return xbmcgui.Dialog().notification((translation(30522).format('Einträge')), (translation(30525).format(CHOICE)), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def Clips_Videos(url, ffilter="", category=""):
	debug("(Clips_Videos) -------------------------------------------------- START = Clips_Videos --------------------------------------------------")
	debug("(Clips_Videos) no.1 ### URL = {0} ### FFILTER = {1} ### CATEGORY = {2} ###".format(url, ffilter, category))
	CHOICE = unquote_plus(category)
	COMBINATION = []
	videoIsolated_List = set()
	count = 0
	pos1 = 0
	content = makeREQUEST(url)
	section = re.findall('<h1 class="grid-header max-width-padding">(.+?)</h1>', content, re.DOTALL)
	debug("(Clips_Videos) no.2 ### SECTION = {0} ### CHOICE = {1} ###".format(section, CHOICE))
	for RUBRIK in section:
		if RUBRIK == CHOICE:
			debug("(Clips_Videos) no.3 ### RUBRIK = {0} ### CHOICE = {1} ###".format(RUBRIK, CHOICE))
			result = content[content.find('<h1 class="grid-header max-width-padding">'+RUBRIK+'</h1>')+6:]
			result = result[:result.find('</section>')]
			videos = re.compile('class="clip-teaser"(.+?)</a>', re.DOTALL).findall(result)
			for video in videos:
				try:
					vidURL = re.compile('href="([^"]+?)"', re.DOTALL).findall(video)[0]
					if vidURL[:4] != "http":
						vidURL = baseURL+vidURL
					try: photo = re.compile(r'style="background-image.+?(?:\(|\")([^)"]+?)(?:\)|\")', re.DOTALL).findall(video)[0].replace('&#223;', '%C3%9F').replace('/dev-automatic-video-thumbnails', '') # [1.] -ß- Esszett für Browser-URL deklarieren, damit das Bild angezeigt wird /// [2.] Unnötigen+falschen Text aus Link entfernen, da sonst KEINE Bildanzeige
					except: photo = ""
					if photo != "" and photo[:4] != "http":
						photo = baseURL+photo
					if photo != "" and "?w=" in photo:
						photo = photo.split('?w=')[0]+"?w=1280"
					if photo != "" and not "?w=" in photo:
						photo = photo+"?w=1280"
					if photo == "":
						photo = baseURL+"/assets/no_thumb_placeholder.jpg"
					title = re.compile('<h1>(.+?)</h1>', re.DOTALL).findall(video)[0]
					if "Wiederholungen" in RUBRIK or "Weiderholungen" in RUBRIK:
						title = title.replace(' - ', ' : ')
					title = title.replace("HIGHLIGHTS", "").replace("Highlights", "").replace("HIGHLIGHT", "").replace("Highlight", "").replace("HYUNDAI-", "").replace("Hyundai-", "").replace("HYUNDAI ", "").replace("Hyundai ", "")
					title = cleanTitle(title)
					if title =="":
						continue
					relevance = re.compile('class="date">(.+?)<', re.DOTALL).findall(video)[0].strip()
					try:
						datetime_object = datetime.datetime.strptime(relevance, '%d.%m.%Y')
					except TypeError:
						datetime_object = datetime.datetime(*(time.strptime(relevance, '%d.%m.%Y')[0:6]))
					try: 
						division1 = re.compile('<h1>(.+?)</h1>', re.DOTALL).findall(video)[1]
						division1 = cleanTitle(division1)
					except: division1 = ""
					try: 
						division2 = re.compile('<h1>(.+?)</h1>', re.DOTALL).findall(video)[2]
						division2 = cleanTitle(division2)
					except: division2 = ""
					if division1 != "" and division2 != "":
						name = relevance+" - "+title+" - "+division1+"  ("+division2+")"
					elif division1 != "" and division2 == "":
						name = relevance+" - "+title+"  ("+division1+")"
					elif division1 == "" and division2 == "":
						name = relevance+" - "+title
					if name in videoIsolated_List:
						continue
					videoIsolated_List.add(name)
					COMBINATION.append([datetime_object, name, vidURL, photo])
				except:
					pos1 += 1
					failing("(Clips_Videos) Fehler-Eintrag-01 : {0} #####".format(str(video)))
					if pos1 > 1 and count == 0:
						count += 1
						xbmcgui.Dialog().notification((translation(30521).format('DISPLAY')), translation(30523), icon, 8000)
	if COMBINATION:
		if ffilter == "umdrehen":
			for datetime_object, name, vidURL, photo in sorted(COMBINATION, key=lambda item:item[0], reverse=True):
				addLink(name, vidURL, "playVideo", photo)
		else:
			for datetime_object, name, vidURL, photo in COMBINATION:
				addLink(name, vidURL, "playVideo", photo)
	xbmcplugin.endOfDirectory(pluginhandle)

def Leagues_Overview(url):
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_TITLE)
	debug("(Leagues_Overview) -------------------------------------------------- START = Leagues_Overview --------------------------------------------------")
	debug("(Leagues_Overview) ### URL = {0} ###".format(url))
	FOUND = False
	videoIsolated_List = set()
	content = makeREQUEST(url)
	result = content[content.find('<h1 class="grid-header max-width-padding">Ligen</h1>')+1:]
	result = result[:result.find('</section>')]
	selection = re.findall('onclick="tableLink(.+?)">(.+?)</button>', result, re.DOTALL)
	for url2, title in selection:
		if title != "":
			FOUND = True
			url2 = url2.replace('"', '').replace("'", "").replace('(', '').replace(')', '')
			if url2[:4] != "http":
				url2 = baseURL+url2
			name = cleanTitle(title)
			if name in videoIsolated_List:
				continue
			videoIsolated_List.add(name)
			addDir(name, url2, "Leagues_Teams", icon, category=name)
			debug("(Leagues_Overview) NAME = {0} ##### URL2 = {1} #####".format(name, url2))
	if not FOUND:
		return xbmcgui.Dialog().notification((translation(30522).format('Ergebnisse')), translation(30524), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def Leagues_Teams(url, category=""):
	debug("(Leagues_Teams) -------------------------------------------------- START = Leagues_Teams --------------------------------------------------")
	debug("(Leagues_Teams) ### URL = {0} ### CATEGORY = {1} ###".format(url, category))
	Supported = ['top clips', 'highlights', 'wiederholungen']
	CHOICE = category
	FOUND = False
	COMBINATION = []
	videoIsolated_List = set()
	count = 0
	pos1 = 0
	content = makeREQUEST(url)
	result = content[content.find('<h1 class="grid-header max-width-padding">Vereine</h1>')+1:]
	result = result[:result.find('</section>')]
	if 'class="clip-teaser clip-info"' in result:
		part = result.split('class="clip-teaser clip-info"')
		for i in range(1, len(part), 1):
			element = part[i]
			try:
				url2 = re.compile('href="(.+?)">', re.DOTALL).findall(element)[0]
				if url2[:4] != "http":
					url2 = baseURL+url2
				try: photo = re.compile('<img.+?src="([^"]+?)"', re.DOTALL).findall(element)[0].replace('&#223;', '%C3%9F') # -ß- Esszett für Browser-URL deklarieren, damit das Bild angezeigt wird
				except: photo = ""
				if photo != "" and photo[:4] != "http":
					photo = baseURL+photo
				if photo != "" and "?w=" in photo:
					photo = photo.split('?w=')[0]+"?w=300"
				if photo != "" and not "?w=" in photo:
					photo = photo+"?w=300"
				if photo == "":
					photo = baseURL+"/assets/clublogo_placeholder.png"
				title = re.compile('<h1>(.+?)</h1>', re.DOTALL).findall(element)[0]
				name = cleanTitle(title)
				if name in videoIsolated_List:
					continue
				videoIsolated_List.add(name)
				if name !="":
					COMBINATION.append([name, url2, photo])
			except:
				pos1 += 1
				failing("(Leagues_Teams) Fehler-Eintrag-01 : {0} #####".format(str(element)))
				if pos1 > 1 and count == 0:
					count += 1
					xbmcgui.Dialog().notification((translation(30521).format('DISPLAY')), translation(30523), icon, 8000)
	match = re.findall('<h1 class="grid-header max-width-padding">(.*?)</h1>', content, re.DOTALL)
	for title in match:
		name = title.replace('Weiderholungen', 'Wiederholungen')
		if name !="" and any(x in name.lower() for x in Supported):
			FOUND = True
			addDir((translation(30613).format(name.upper(), CHOICE)), url, "Clips_Videos", icon, ffilter="umdrehen", category=title)
			debug("(Leagues_Teams) TITLE = {0} #####".format(title))
	if COMBINATION:
		FOUND = True
		for name, url2, photo in sorted(COMBINATION, key=lambda item:item[0], reverse=False):
			addDir(name, url2, "Clips_Categories", photo, ffilter="umdrehen", category=name, background="KEIN HINTERGRUND")
	if not FOUND:
		return xbmcgui.Dialog().notification((translation(30522).format('Einträge')), (translation(30525).format(CHOICE)), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url):
	debug("(playVideo) -------------------------------------------------- START = playVideo --------------------------------------------------")
	debug("(playVideo) no.1 ### URL = {0} ###".format(url))
	fileURL = False
	testURL = False
	content = getUrl(url)
	try:
		stream = re.compile('playerSource = decodeHtml.+?(https?://[^"]+?)"', re.DOTALL|re.UNICODE).findall(content)[0].replace('\n', '')
		fileURL = True
	except: 
		failing("(playVideo) ##### Abspielen des Streams NICHT möglich ##### URL : {0} #####\n   ########## KEINEN Stream-Eintrag auf der Webseite von *sporttotal.tv* gefunden !!! ##########".format(url))
		xbmcgui.Dialog().notification((translation(30521).format('URL 1')), translation(30526), icon, 8000)
		return
	standardSTREAM = re.compile(r'(?:/[^/]+?\.mp4|/[^/]+?\.m3u8|/[^/]+?\.ism/manifest)', re.DOTALL).findall(stream)[0]
	correctSTREAM = quote(cleanTitle(standardSTREAM))
	debug("(playVideo) no.2 ### standardSTREAM = {0} ### correctSTREAM = {1} ###".format(standardSTREAM, correctSTREAM))
	finalURL = stream.replace(standardSTREAM, correctSTREAM)
	try:
		code = urlopen(finalURL).getcode()
		if str(code) == "200":
			testURL = True
	except: pass
	if fileURL and testURL:
		log("(playVideo) StreamURL : {0}".format(finalURL))
		listitem = xbmcgui.ListItem(path=finalURL)
		if enableInputstream and 'hls.m3u8' in finalURL:
			if ADDON_operate('inputstream.adaptive'):
				listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
				listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
				listitem.setMimeType('application/vnd.apple.mpegurl')
			else:
				addon.setSetting("inputstream", "false")
		xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
	else:
		failing("(playVideo) ##### Abspielen des Streams NICHT möglich ##### URL : {0} #####\n   ########## Die Stream-Url auf der Webseite von *sporttotal.tv* ist OFFLINE !!! ##########".format(finalURL))
		xbmcgui.Dialog().notification((translation(30521).format('URL 2')), translation(30527), icon, 8000)

def cleanTitle(title):
	title = py2_enc(title)
	title = title.replace("&#39;", "'").replace('&#196;', 'Ä').replace('&#214;', 'Ö').replace('&#220;', 'Ü').replace('&#228;', 'ä').replace('&#246;', 'ö').replace('&#252;', 'ü').replace('&#223;', 'ß').replace('&#160;', ' ')
	title = title.replace('&#192;', 'À').replace('&#193;', 'Á').replace('&#194;', 'Â').replace('&#195;', 'Ã').replace('&#197;', 'Å').replace('&#199;', 'Ç').replace('&#200;', 'È').replace('&#201;', 'É').replace('&#202;', 'Ê')
	title = title.replace('&#203;', 'Ë').replace('&#204;', 'Ì').replace('&#205;', 'Í').replace('&#206;', 'Î').replace('&#207;', 'Ï').replace('&#209;', 'Ñ').replace('&#210;', 'Ò').replace('&#211;', 'Ó').replace('&#212;', 'Ô')
	title = title.replace('&#213;', 'Õ').replace('&#215;', '×').replace('&#216;', 'Ø').replace('&#217;', 'Ù').replace('&#218;', 'Ú').replace('&#219;', 'Û').replace('&#221;', 'Ý').replace('&#222;', 'Þ').replace('&#224;', 'à')
	title = title.replace('&#225;', 'á').replace('&#226;', 'â').replace('&#227;', 'ã').replace('&#229;', 'å').replace('&#231;', 'ç').replace('&#232;', 'è').replace('&#233;', 'é').replace('&#234;', 'ê').replace('&#235;', 'ë')
	title = title.replace('&#236;', 'ì').replace('&#237;', 'í').replace('&#238;', 'î').replace('&#239;', 'ï').replace('&#240;', 'ð').replace('&#241;', 'ñ').replace('&#242;', 'ò').replace('&#243;', 'ó').replace('&#244;', 'ô')
	title = title.replace('&#245;', 'õ').replace('&#247;', '÷').replace('&#248;', 'ø').replace('&#249;', 'ù').replace('&#250;', 'ú').replace('&#251;', 'û').replace('&#253;', 'ý').replace('&#254;', 'þ').replace('&#255;', 'ÿ')
	title = title.replace('&#352;', 'Š').replace('&#353;', 'š').replace('&#376;', 'Ÿ').replace('&#402;', 'ƒ')
	title = title.replace('&#8211;', '–').replace('&#8212;', '—').replace('&#8226;', '•').replace('&#8230;', '…').replace('&#8240;', '‰').replace('&#8364;', '€').replace('&#8482;', '™').replace('&#169;', '©').replace('&#174;', '®')
	title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö").replace('&quot;', '"').replace('&szlig;', 'ß').replace('&ndash;', '-')
	title = title.strip()
	return title

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, plot=None, ffilter="", category="", background=""):
	u = sys.argv[0]+"?url="+quote_plus(url)+"&mode="+str(mode)+"&ffilter="+quote_plus(ffilter)+"&category="+quote_plus(category)
	liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=image)
	liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": plot})
	if image != icon and background != "KEIN HINTERGRUND":
		liz.setArt({'fanart': image})
	else:
		liz.setArt({'fanart': defaultFanart})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
  
def addLink(name, url, mode, image, plot=None, duration=None, studio=None, genre=None, background=""):
	u = sys.argv[0]+"?url="+quote_plus(url)+"&mode="+str(mode)
	liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=image)
	liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": plot, "Duration": duration, "Studio": "Sporttotal.tv", "Genre": "Sport", "mediatype": "video"})
	if image != icon and background != "KEIN HINTERGRUND":
		liz.setArt({'fanart': image})
	else:
		liz.setArt({'fanart': defaultFanart})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	liz.setContentLookup(False)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

params = parameters_string_to_dict(sys.argv[2])
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
ffilter = unquote_plus(params.get('ffilter', ''))
category = unquote_plus(params.get('category', ''))
background = unquote_plus(params.get('background', ''))
referer = unquote_plus(params.get('referer', ''))

if mode == 'aSettings':
	addon.openSettings()
elif mode == 'iSettings':
	xbmcaddon.Addon('inputstream.adaptive').openSettings()
elif mode == 'clearCache':
	clearCache()
elif mode == 'Sportarts_Overview':
	Sportarts_Overview(url, ffilter)
elif mode == 'Livegames_Videos':
	Livegames_Videos(url, category)
elif mode == 'Clips_Categories':
	Clips_Categories(url, ffilter, category)
elif mode == 'Clips_Videos':
	Clips_Videos(url, ffilter, category)
elif mode == 'Leagues_Overview':
	Leagues_Overview(url)
elif mode == 'Leagues_Teams':
	Leagues_Teams(url, category)
elif mode == 'playVideo':
	playVideo(url)
else:
	index()