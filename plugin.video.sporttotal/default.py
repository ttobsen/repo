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
import io
import gzip
from collections import OrderedDict


global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath    = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
enableInputstream = addon.getSetting("inputstream") == "true"
enableAdjustment = addon.getSetting("show_settings") == "true"
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

def index():
	debug("(index) -------------------------------------------------- START = index --------------------------------------------------")
	content = getUrl(baseURL+"/root.js?lang=de").replace('window.config={', '{')
	DATA = json.loads(content, object_pairs_hook=OrderedDict)
	for each in DATA['navbar']:
		debug("(index) ### ENTRY = {0} ###".format(str(each)))
		title = py2_enc(each['title']).strip()
		idd = str(each['id']).strip()+".js?lang=de"
		type = py2_enc(each['type']).strip()
		if type.lower() == 'sport':
			addDir(title, baseURL+"/"+idd, "Clips_Categories", icon, category=title)
	if enableAdjustment:
		addDir(translation(30608), "", "aSettings", icon)
		if enableInputstream:
			if ADDON_operate('inputstream.adaptive'):
				addDir(translation(30609), "", "iSettings", icon)
			else:
				addon.setSetting("inputstream", "false")
	xbmcplugin.endOfDirectory(pluginhandle)

def Clips_Categories(url, ffilter="", category="", thumb=""):
	debug("(Clips_Categories) -------------------------------------------------- START = Clips_Categories --------------------------------------------------")
	debug("(Clips_Categories) ### URL = {0} ### FFILTER = {1} ### CATEGORY = {2} ###".format(url, ffilter, category))
	UN_Supported_1 = ['component']
	UN_Supported_2 = ['adac', 'motorsport']
	COMBI = []
	FOUND = 0
	position = 0
	content = getUrl(url).replace('window.config={', '{')
	DATA = json.loads(content, object_pairs_hook=OrderedDict)
	for each in DATA['components']:
		if each['component'] != 'Description' and 'item' in each['props'] and 'title' in each['props']['item'] and each['props']['item']['title'] != "":
			title = py2_enc(each['props']['item']['title']).strip()
			idd = str(each['props']['item']['id']).strip()+".js?lang=de"
			debug("(Clips_Categories) ### NAME = {0} ### IDD = {1} ###".format(title, idd))
			if not any(x in title.lower() for x in UN_Supported_1):
				FOUND = 1
				name = title
				if 'live' in title.lower():
					position = 1
					name = (translation(30610).format(title))
				if 'nächste' in title.lower():
					position = 2
					name = translation(30611)
				if not 'live' in title.lower() and not 'nächste' in title.lower():
					position = 3
				COMBI.append([position, name, title, idd])
	if COMBI:
		for position, name, title, idd in sorted(COMBI, key=lambda d:d[0], reverse=False):
			addDir(name, baseURL+"/"+idd, "Clips_Videos", thumb, category=title, background="KEIN HINTERGRUND")
		if not any(x in category.lower() for x in UN_Supported_2) and ffilter != 'no_Additives':
			addDir(translation(30612), url, "Leagues_Overview", thumb, background="KEIN HINTERGRUND")
	if FOUND == 0:
		return xbmcgui.Dialog().notification((translation(30522).format('Ergebnisse')), translation(30524), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def Clips_Videos(url, ffilter="", category=""):
	debug("(Clips_Videos) -------------------------------------------------- START = Clips_Videos --------------------------------------------------")
	debug("(Clips_Videos) ### URL = {0} ### FFILTER = {1} ### CATEGORY = {2} ###".format(url, ffilter, category))
	FOUND = 0
	content = getUrl(url).replace('window.config={', '{')
	startCOMPLETE = False
	startDATE = False
	CHOICE = category
	DATA = json.loads(content, object_pairs_hook=OrderedDict)
	for each in DATA['components']:
		if 'item' in each['props'] and 'title' in each['props']['item'] and each['props']['item']['title'] != "":
			RUBRIK = py2_enc(each['props']['item']['title']).strip()
			if RUBRIK == CHOICE and 'children' in each['props']['item']:
				for d in each['props']['item']['children']:
					debug("(Clips_Videos) ### ENTRY = {0} ###".format(str(d)))
					FOUND = 1
					title = py2_enc(d['title']).strip()
					idd = str(d['id']).strip()+".js?lang=de"
					gender = ""
					if 'gender' in d and d['gender'] != "" and d['gender'] != None:
						sexo = py2_enc(d['gender']).strip()
						if sexo == 'WOMEN': gender = "  [COLOR FFFF5AAA]("+sexo.replace('WOMEN', 'F')+")[/COLOR]"
						if sexo == 'MEN': gender = "  [COLOR deepskyblue]("+sexo.replace('MEN', 'M')+")[/COLOR]"
					if 'date' in d and d['date'] != "" and d['date'] != None:
						relevance = str(d['date']).strip()
						LOCALstart = utc_to_local(datetime(1970, 1, 1) + timedelta(milliseconds=int(relevance)))
						startCOMPLETE = LOCALstart.strftime('%d.%m.%y • %H:%M')
						startDATE = LOCALstart.strftime('%d.%m.%Y')
						startTIME = LOCALstart.strftime('%H:%M')
					plot = ""
					if 'league' in d and 'title' in d['league'] and d['league']['title'] != "" and d['league']['title'] != None:
						plot = py2_enc(d['league']['title']).strip()+" :[CR]"+title
					if plot == "" and 'description' in d and d['description'] != "" and d['description'] != None:
						plot = py2_enc(d['description']).strip()
					fotoBIG = ""
					try: photo = d['image']['cover'][0].strip().replace('ß', '%C3%9F') # -ß- Esszett für Browser-URL deklarieren, damit das Bild angezeigt wird
					except: photo = ""
					if photo == "":
						try: photo = d['image']['thumb'][0].strip().replace('ß', '%C3%9F') # -ß- Esszett für Browser-URL deklarieren, damit das Bild angezeigt wird
						except: photo = ""
					if photo == "":
						fotoBIG = "KEIN HINTERGRUND"
						try: photo = d['teams'][0]['image']['logo'][0].strip().replace('ß', '%C3%9F') # -ß- Esszett für Browser-URL deklarieren, damit das Bild angezeigt wird
						except: photo = ""
					if photo == "":
						fotoBIG = "KEIN HINTERGRUND"
						try: photo = d['image']['logo'][0].strip().replace('ß', '%C3%9F')+"?w=500" # -ß- Esszett für Browser-URL deklarieren, damit das Bild angezeigt wird
						except: photo = ""
					name = title+gender
					if startCOMPLETE:
						name = startDATE+" - "+title+gender
						if 'live' in RUBRIK.lower():
							name = "[COLOR chartreuse][B]~ ~ ~  ( LIVE )[/B][/COLOR]  ["+startTIME+"]  "+title+gender+"  [COLOR chartreuse][B]~ ~ ~[/B][/COLOR]"
						if 'nächste' in RUBRIK.lower():
							name = startCOMPLETE+" - "+title+gender
						addLink(name, baseURL+"/"+idd, "playVideo", photo, plot, SPIEL=name, background=fotoBIG)
					else:
						xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
						addDir(name, baseURL+"/"+idd, "Clips_Categories", photo, plot, ffilter='no_Additives', background=fotoBIG)
	if FOUND == 0:
		return xbmcgui.Dialog().notification((translation(30522).format('Einträge')), (translation(30525).format(CHOICE)), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def Leagues_Overview(url):
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
	debug("(Leagues_Overview) -------------------------------------------------- START = Leagues_Overview --------------------------------------------------")
	debug("(Leagues_Overview) ### URL = {0} ###".format(url))
	FOUND = 0
	content = getUrl(url).replace('window.config={', '{')
	DATA = json.loads(content, object_pairs_hook=OrderedDict)
	for each in DATA['components']:
		if 'filter' in each['props'] and 'options' in each['props']['filter']:
			for d in each['props']['filter']['options']:
				debug("(Leagues_Overview) ### ENTRY = {0} ###".format(str(d)))
				title = py2_enc(d['title']).strip()
				idd = str(d['id']).strip()
				if idd != '*' and idd != None:
					FOUND = 1
					idd = idd+".js?lang=de"
					addDir(title, baseURL+"/"+idd, "Clips_Categories", icon, ffilter='no_Additives')
	if FOUND == 0:
		return xbmcgui.Dialog().notification((translation(30522).format('Ergebnisse')), translation(30524), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url, name=""):
	debug("(playVideo) -------------------------------------------------- START = playVideo --------------------------------------------------")
	debug("(playVideo) ### URL = {0} ### NAME = {1} ###".format(url, name))
	filmList_1 = []
	filmList_2 = []
	fileURL = False
	testURL = False
	content = getUrl(url).replace('window.config={', '{')
	try:
		DATA = json.loads(content, object_pairs_hook=OrderedDict)
		for each in DATA['components']:
			if 'item' in each['props'] and 'video' in each['props']['item']:
				for d in each['props']['item']['video']:
					if 'mp4' in d and d['mp4'] !="":
						mp4 = d['mp4']
						filmList_1.append(mp4)
						fileURL = True
					if 'm3u8' in d and d['m3u8'] !="":
						m3u8 = d['m3u8']
						filmList_2.append(m3u8)
						fileURL = True
					debug("(playVideo) ### VIDEOS_mp4 = {0} ###".format(str(filmList_1)))
					debug("(playVideo) ### VIDEOS_m3u8 = {0} ###".format(str(filmList_2)))
	except: 
		failing("(playVideo) ##### Abspielen des Streams NICHT möglich ##### URL : {0} #####\n   ########## KEINEN Stream-Eintrag auf der Webseite von *sporttotal.tv* gefunden !!! ##########".format(url))
		return xbmcgui.Dialog().notification((translation(30521).format('URL 1')), translation(30526), icon, 8000)
	if not fileURL:
		failing("(playVideo) ##### Abspielen des Streams NICHT möglich ##### URL : {0} #####\n   ########## KEINEN Stream-Eintrag auf der Webseite von *sporttotal.tv* gefunden !!! ##########".format(url))
		return xbmcgui.Dialog().notification((translation(30521).format('URL 1')), translation(30526), icon, 8000)
	if filmList_1 or filmList_2:
		if filmList_1:
			for ite in filmList_1:
				if not 'pano' in ite and ('cloudfront' in ite or 'azureedge' in ite): stream = ite
		if filmList_2:
			for ele in filmList_2:
				if (not 'pano' in ele and not ele.endswith('hd_hls.m3u8')) or (not filmList_1 and filmList_2 and not 'pano' in ele): stream = ele
		standardSTREAM = re.compile(r'(?:/[^/]+?\.mp4|/[^/]+?\.m3u8|/[^/]+?\.ism/manifest)', re.DOTALL).findall(stream)[0]
		correctSTREAM = quote(cleanTitle(standardSTREAM))
		debug("(playVideo) ### standardSTREAM = {0} ### correctSTREAM = {1} ###".format(standardSTREAM, correctSTREAM))
		finalURL = stream.replace(standardSTREAM, correctSTREAM)
		try:
			code = urlopen(finalURL).getcode()
			if str(code) == "200":
				testURL = True
		except: pass
	if fileURL and testURL: # https://d3j8poz04ftomu.cloudfront.net/RECORD/0_hd_hls.m3u8?hlsid=HTTP_ID_1
		log("(playVideo) StreamURL : {0}".format(finalURL))
		listitem = xbmcgui.ListItem(path=finalURL)
		if enableInputstream and 'm3u8' in finalURL:
			try:
				if ADDON_operate('inputstream.adaptive'):
					listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
					listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
					listitem.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
					listitem.setMimeType('application/vnd.apple.mpegurl')
				else:
					addon.setSetting("inputstream", "false")
			except: pass
		xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
		xbmc.sleep(1000)
		if not xbmc.getCondVisibility("Window.IsVisible(fullscreenvideo)") and not xbmc.Player().isPlaying():
			listitem = xbmcgui.ListItem(path=finalURL, label=name)
			xbmc.Player().play(item=finalURL, listitem=listitem)
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

def utc_to_local(dt):
	if time.localtime().tm_isdst: return dt - timedelta(seconds=time.altzone)
	else: return dt - timedelta(seconds=time.timezone)

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
	u = sys.argv[0]+"?url="+quote_plus(url)+"&mode="+str(mode)+"&ffilter="+quote_plus(ffilter)+"&category="+quote_plus(category)+"&image="+image
	liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=image)
	liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": plot})
	if image != icon and background != "KEIN HINTERGRUND":
		liz.setArt({'fanart': image})
	else:
		liz.setArt({'fanart': defaultFanart})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
  
def addLink(name, url, mode, image, plot=None, duration=None, studio=None, genre=None, SPIEL="", background=""):
	u = sys.argv[0]+"?url="+quote_plus(url)+"&mode="+str(mode)+"&SPIEL="+str(SPIEL)
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
SPIEL = unquote_plus(params.get('SPIEL', ''))
ffilter = unquote_plus(params.get('ffilter', ''))
category = unquote_plus(params.get('category', ''))
background = unquote_plus(params.get('background', ''))
referer = unquote_plus(params.get('referer', ''))

if mode == 'aSettings':
	addon.openSettings()
elif mode == 'iSettings':
	xbmcaddon.Addon('inputstream.adaptive').openSettings()
elif mode == 'Clips_Categories':
	Clips_Categories(url, ffilter, category, image)
elif mode == 'Clips_Videos':
	Clips_Videos(url, ffilter, category)
elif mode == 'Leagues_Overview':
	Leagues_Overview(url)
elif mode == 'playVideo':
	playVideo(url, SPIEL)
else:
	index()