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
enableInputstream = addon.getSetting('inputstream') == 'true'
enableAdjustment = addon.getSetting('show_settings') == 'true'
baseURL = 'https://www.sporttotal.tv'

xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

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
	req = Request(url)
	try:
		if header: req.add_header(*header)
		else:
			req.add_header('User-Agent', agent)
			req.add_header('Accept-Encoding', 'gzip, deflate')
		response = urlopen(req, timeout=30)
		if response.info().get('Content-Encoding') == 'gzip':
			content = py3_dec(gzip.GzipFile(fileobj=io.BytesIO(response.read())).read())
		else:
			content = py3_dec(response.read())
	except Exception as e:
		failure = str(e)
		failing("(getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
		xbmcgui.Dialog().notification(translation(30521).format('URL'), "ERROR = [COLOR red]{0}[/COLOR]".format(failure), icon, 12000)
		content = ""
		return sys.exit(0)
	response.close()
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
	debug("(index) -------------------------------------------------- START = index --------------------------------------------------")
	content = getUrl(baseURL+'/root.js?lang=de').replace('window.config={', '{')
	DATA = json.loads(content, object_pairs_hook=OrderedDict)
	for each in DATA['navbar']:
		debug("(index) ### ENTRY = {0} ###".format(str(each)))
		title = ""
		if 'title' in each and each['title'] != "" and each['title'] != None:
			title = cleanTitle(each['title'])
		idd = ""
		if 'id' in each and each['id'] != "" and each['id'] != None:
			idd = str(each['id']).strip()+'.js?lang=de'
		type = ""
		if 'type' in each and each['type'] != "" and each['type'] != None:
			type = cleanTitle(each['type'])
		if type.lower() == 'sport' or title.lower() == 'amator':
			addDir(title, baseURL+'/'+idd, 'Clips_Categories', icon, category=title)
		if type.lower() == 'event' or type.lower() == 'region':
			if type.lower() == 'region': title = '[COLOR yellow]'+title+'[/COLOR]'
			addDir(title, baseURL+'/'+idd, 'Clips_Categories', icon, category=type.lower())
	if enableAdjustment:
		addDir(translation(30608), "", 'aSettings', icon)
		if enableInputstream:
			if ADDON_operate('inputstream.adaptive'):
				addDir(translation(30609), "", 'iSettings', icon)
			else:
				addon.setSetting('inputstream', 'false')
	xbmcplugin.endOfDirectory(pluginhandle)
                                                                                            # https://api.sporttotal.tv/v2/vod?sporttypeuuid=6294114c-5400-4978-bc6a-b3fe75d03fdf&channeluuid=00365d04-ad90-4ef7-b9b3-ef1e72890908
def Clips_Categories(url, ffilter, category, thumb): # https://api.sporttotal.tv/v2/live?sporttypeuuid=6294114c-5400-4978-bc6a-b3fe75d03fdf&channeluuid=00365d04-ad90-4ef7-b9b3-ef1e72890908
	debug("(Clips_Categories) -------------------------------------------------- START = Clips_Categories --------------------------------------------------")
	debug("(Clips_Categories) ### URL = {0} ### FFILTER = {1} ### CATEGORY = {2} ###".format(url, ffilter, category))
	UN_Supported_1 = ['agb', 'component']
	UN_Supported_2 = ['adac', 'amator', 'event', 'motorsport', 'region']
	COMBI = []
	FOUND = 0
	position = 0
	content = getUrl(url).replace('window.config={', '{')
	DATA = json.loads(content, object_pairs_hook=OrderedDict)
	for each in DATA['components']:
		if each['component'] != 'Description' and 'item' in each['props'] and 'title' in each['props']['item'] and each['props']['item']['title'] != "":
			title = cleanTitle(each['props']['item']['title'])
			idd_1 = str(each['props']['item']['id']).strip()
			idd_2 = str(each['id']).strip()+'.js?lang=de'
			debug("(Clips_Categories) ### NAME = {0} ### IDD_1 = {1} ### IDD_2 = {2} ###".format(title, idd_1, idd_2))
			if not any(x in title.lower() for x in UN_Supported_1):
				FOUND = 1
				name = title
				if 'live' in title.lower():
					position = 1
					name = translation(30610).format(title)
				elif 'nächste' in title.lower():
					position = 2
					name = translation(30611)
				else:
					position = 3
				COMBI.append([position, name, title, idd_1, idd_2])
	if COMBI:
		for position, name, title, idd_1, idd_2 in sorted(COMBI, key=lambda d:d[0], reverse=False):
			addDir(name, baseURL+'/'+idd_1+'/'+idd_2, 'Clips_Videos', thumb, category=title, background='KEIN HINTERGRUND')
		if not any(x in category.lower() for x in UN_Supported_2) and ffilter != 'no_Additives':
			addDir(translation(30612), url, 'Leagues_Overview', thumb, background='KEIN HINTERGRUND')
	if FOUND == 0:
		return xbmcgui.Dialog().notification(translation(30522).format('Ergebnisse'), translation(30524), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def Clips_Videos(url, ffilter, category):
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
			RUBRIK = cleanTitle(each['props']['item']['title'])
			if RUBRIK == CHOICE and 'children' in each['props']['item']:
				for d in each['props']['item']['children']:
					debug("(Clips_Videos) ### ENTRY = {0} ###".format(str(d)))
					FOUND = 1
					title = cleanTitle(d['title'])
					idd = str(d['id']).strip()+'.js?lang=de'
					gender = ""
					if 'gender' in d and d['gender'] != "" and d['gender'] != None:
						sexo = cleanTitle(d['gender'])
						if sexo == 'WOMEN': gender = "[COLOR FFFF5AAA]  ({0})[/COLOR]".format(sexo.replace('WOMEN', 'F'))
						if sexo == 'MEN': gender = "[COLOR deepskyblue]  ({0})[/COLOR]".format(sexo.replace('MEN', 'M'))
					if 'date' in d and d['date'] != "" and d['date'] != None:
						relevance = str(d['date']).strip()
						LOCALstart = utc_to_local(datetime(1970, 1, 1) + timedelta(milliseconds=int(relevance)))
						startCOMPLETE = LOCALstart.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
						startDATE = LOCALstart.strftime('%d{0}%m{0}%Y').format('.')
						startTIME = LOCALstart.strftime('%H{0}%M').format(':')
					plot = ""
					if 'league' in d and 'title' in d['league'] and d['league']['title'] != "" and d['league']['title'] != None:
						plot = cleanTitle(d['league']['title'])+" :[CR]"+title
					if plot == "" and 'description' in d and d['description'] != "" and d['description'] != None:
						plot = cleanTitle(d['description'])
					fotoBIG = ""
					photo = icon
					if 'cover' in d['image'] and d['image']['cover'] != "" and d['image']['cover'] != None:
						photo = cleanPhoto(d['image']['cover'][0])
					if photo == icon and 'thumb' in d['image'] and d['image']['thumb'] != "" and d['image']['thumb'] != None:
						photo = cleanPhoto(d['image']['thumb'][0])
					for p in d['teams']:
						if photo == icon and 'image' in p and 'logo' in p['image'] and p['image']['logo'] != "" and p['image']['logo'] != None:
							fotoBIG = 'KEIN HINTERGRUND'
							photo = cleanPhoto(p['image']['logo'][0])
					if photo == icon and 'logo' in d['image'] and d['image']['logo'] != "" and d['image']['logo'] != None:
						fotoBIG = 'KEIN HINTERGRUND'
						photo = cleanPhoto(d['image']['logo'][0])
					name = title+gender
					type = ""
					if 'type' in d and d['type'] != "" and d['type'] != None:
						type = cleanTitle(d['type'])
					if startCOMPLETE and type.lower() != 'league':
						name = startDATE+" - "+title+gender
						if 'live' in RUBRIK.lower():
							name = "[COLOR chartreuse][B]~ ~ ~  ( LIVE )[/B][/COLOR]  [{0}]  {1}  [COLOR chartreuse][B]~ ~ ~[/B][/COLOR]".format(startTIME, title+gender)
						if 'nächste' in RUBRIK.lower() or 'kommende' in RUBRIK.lower():
							name = startCOMPLETE+" - "+title+gender
						addLink(name, baseURL+'/'+idd, 'playVideo', photo, plot, SPIEL=name, background=fotoBIG)
					else:
						xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
						addDir(name, baseURL+'/'+idd, 'Clips_Categories', photo, plot, ffilter='no_Additives', background=fotoBIG)
	if FOUND == 0:
		return xbmcgui.Dialog().notification(translation(30522).format('Einträge'), translation(30525).format(CHOICE), icon, 8000)
	xbmcplugin.endOfDirectory(handle=pluginhandle, cacheToDisc=False)

def Leagues_Overview(url):
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
	debug("(Leagues_Overview) -------------------------------------------------- START = Leagues_Overview --------------------------------------------------")
	debug("(Leagues_Overview) ### URL = {0} ###".format(url))
	ISOLATED = set()
	FOUND = 0
	content = getUrl(url).replace('window.config={', '{')
	DATA = json.loads(content, object_pairs_hook=OrderedDict)
	for each in DATA['components']:
		if 'filter' in each['props'] and 'options' in each['props']['filter']:
			for d in each['props']['filter']['options']:
				debug("(Leagues_Overview) ### ENTRY = {0} ###".format(str(d)))
				title = cleanTitle(d['title'])
				idd = str(d['id']).strip()
				if idd != '*' and idd != None:
					if idd in ISOLATED:
						continue
					ISOLATED.add(idd)
					FOUND = 1
					idd = idd+'.js?lang=de'
					addDir(title, baseURL+'/'+idd, 'Clips_Categories', icon, ffilter='no_Additives')
	if FOUND == 0:
		return xbmcgui.Dialog().notification(translation(30522).format('Ergebnisse'), translation(30524), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url, name):
	debug("(playVideo) -------------------------------------------------- START = playVideo --------------------------------------------------")
	debug("(playVideo) ### URL = {0} ### NAME = {1} ###".format(url, name))
	filmList_1 = []
	filmList_2 = []
	stream = False
	fileURL = False
	testURL = False
	content = getUrl(url).replace('window.config={', '{')
	try:
		DATA = json.loads(content, object_pairs_hook=OrderedDict)
		for each in DATA['components']:
			if 'item' in each['props'] and 'video' in each['props']['item']:
				for d in each['props']['item']['video']:
					if 'm3u8' in d and d['m3u8'] !="":
						m3u8 = d['m3u8']
						filmList_1.append(m3u8)
						fileURL = True
					if 'mp4' in d and d['mp4'] !="":
						mp4 = d['mp4']
						filmList_2.append(mp4)
						fileURL = True
					debug("(playVideo) ### VIDEOS_m3u8 = {0} ###".format(str(filmList_1)))
					debug("(playVideo) ### VIDEOS_mp4 = {0} ###".format(str(filmList_2)))
	except: 
		failing("(playVideo) ##### Abspielen des Streams NICHT möglich ##### URL : {0} #####\n   ########## KEINEN Stream-Eintrag auf der Webseite von *sporttotal.tv* gefunden !!! ##########".format(url))
		return xbmcgui.Dialog().notification(translation(30521).format('URL 1'), translation(30526), icon, 8000)
	if filmList_1:
		for ele in filmList_1:
			if not 'pano' in ele and (not ele.endswith('hd_hls.m3u8') or not filmList_2): stream = ele
	if filmList_2 and not stream:
		for ite in filmList_2:
			if not 'pano' in ite: stream = ite
	if not stream:
		failing("(playVideo) ##### Abspielen des Streams NICHT möglich ##### URL : {0} #####\n   ########## KEINEN Stream-Eintrag auf der Webseite von *sporttotal.tv* gefunden !!! ##########".format(url))
		return xbmcgui.Dialog().notification(translation(30521).format('URL 1'), translation(30526), icon, 8000)
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
					listitem.setMimeType('application/vnd.apple.mpegurl')
				else:
					addon.setSetting('inputstream', 'false')
			except: pass
		xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
		xbmc.sleep(1000)
		if not xbmc.getCondVisibility('Window.IsVisible(fullscreenvideo)') and not xbmc.Player().isPlaying():
			listitem = xbmcgui.ListItem(path=finalURL, label=name)
			xbmc.Player().play(item=finalURL, listitem=listitem)
	else:
		failing("(playVideo) ##### Abspielen des Streams NICHT möglich ##### URL : {0} #####\n   ########## Die Stream-Url auf der Webseite von *sporttotal.tv* ist OFFLINE !!! ##########".format(finalURL))
		xbmcgui.Dialog().notification(translation(30521).format('URL 2'), translation(30527), icon, 8000)

def cleanPhoto(img): # UNICODE-Zeichen für Browser übersetzen - damit Fotos angezeigt werden
	img = py2_enc(img)
	for p in ((' ', '%20'), ('ß', '%C3%9F'), ('ä', '%C3%A4'), ('ö', '%C3%B6'), ('ü', '%C3%BC')
		, ('à', '%C3%A0'), ('á', '%C3%A1'), ('â', '%C3%A2'), ('è', '%C3%A8'), ('é', '%C3%A9'), ('ê', '%C3%AA'), ('ì', '%C3%AC'), ('í', '%C3%AD'), ('î', '%C3%AE')
		, ('ò', '%C3%B2'), ('ó', '%C3%B3'), ('ô', '%C3%B4'), ('ù', '%C3%B9'), ('ú', '%C3%BA'), ('û', '%C3%BB')):
		img = img.replace(*p)
	return img.strip()

def cleanTitle(text):
	text = py2_enc(text)
	for n in (("&#39;", "'"), ('&#196;', 'Ä'), ('&#214;', 'Ö'), ('&#220;', 'Ü'), ('&#228;', 'ä'), ('&#246;', 'ö'), ('&#252;', 'ü'), ('&#223;', 'ß'), ('&#160;', ' ')
		, ('&#192;', 'À'), ('&#193;', 'Á'), ('&#194;', 'Â'), ('&#195;', 'Ã'), ('&#197;', 'Å'), ('&#199;', 'Ç'), ('&#200;', 'È'), ('&#201;', 'É'), ('&#202;', 'Ê')
		, ('&#203;', 'Ë'), ('&#204;', 'Ì'), ('&#205;', 'Í'), ('&#206;', 'Î'), ('&#207;', 'Ï'), ('&#209;', 'Ñ'), ('&#210;', 'Ò'), ('&#211;', 'Ó'), ('&#212;', 'Ô')
		, ('&#213;', 'Õ'), ('&#215;', '×'), ('&#216;', 'Ø'), ('&#217;', 'Ù'), ('&#218;', 'Ú'), ('&#219;', 'Û'), ('&#221;', 'Ý'), ('&#222;', 'Þ'), ('&#224;', 'à')
		, ('&#225;', 'á'), ('&#226;', 'â'), ('&#227;', 'ã'), ('&#229;', 'å'), ('&#231;', 'ç'), ('&#232;', 'è'), ('&#233;', 'é'), ('&#234;', 'ê'), ('&#235;', 'ë')
		, ('&#236;', 'ì'), ('&#237;', 'í'), ('&#238;', 'î'), ('&#239;', 'ï'), ('&#240;', 'ð'), ('&#241;', 'ñ'), ('&#242;', 'ò'), ('&#243;', 'ó'), ('&#244;', 'ô')
		, ('&#245;', 'õ'), ('&#247;', '÷'), ('&#248;', 'ø'), ('&#249;', 'ù'), ('&#250;', 'ú'), ('&#251;', 'û'), ('&#253;', 'ý'), ('&#254;', 'þ'), ('&#255;', 'ÿ')
		, ('&#352;', 'Š'), ('&#353;', 'š'), ('&#376;', 'Ÿ'), ('&#402;', 'ƒ')
		, ('&#8211;', '–'), ('&#8212;', '—'), ('&#8226;', '•'), ('&#8230;', '…'), ('&#8240;', '‰'), ('&#8364;', '€'), ('&#8482;', '™'), ('&#169;', '©'), ('&#174;', '®')
		, ("&Auml;", "Ä"), ("&Uuml;", "Ü"), ("&Ouml;", "Ö"), ("&auml;", "ä"), ("&uuml;", "ü"), ("&ouml;", "ö"), ('&quot;', '"'), ('&szlig;', 'ß'), ('&ndash;', '-')):
		text = text.replace(*n)
	return text.strip()

def utc_to_local(dt):
	if time.localtime().tm_isdst: return dt - timedelta(seconds=time.altzone)
	else: return dt - timedelta(seconds=time.timezone)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, plot=None, ffilter="", category="", background=""):
	u = sys.argv[0]+'?url='+quote_plus(url)+'&mode='+str(mode)+'&ffilter='+quote_plus(ffilter)+'&category='+quote_plus(category)+'&image='+image
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if image != icon and background != 'KEIN HINTERGRUND':
		liz.setArt({'fanart': image})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
  
def addLink(name, url, mode, image, plot=None, duration=None, studio=None, genre=None, SPIEL="", background=""):
	u = sys.argv[0]+'?url='+quote_plus(url)+'&mode='+str(mode)+'&SPIEL='+str(SPIEL)
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot, 'Duration': duration, 'Studio': 'Sporttotal.tv', 'Genre': 'Sport', 'mediatype': 'video'})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if image != icon and background != 'KEIN HINTERGRUND':
		liz.setArt({'fanart': image})
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