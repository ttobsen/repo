#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    This Plugin is compatible between Python 2.X and Python 3+
    without using any extra extern Plugins from XBMC (KODI)
    Copyright (C) 2018 by realvito
    Released under GPL(v3)
"""

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

#token = 'ffc9a283b511b7e11b326fdc3d76c5559b50544e reraeB'
#getheader = {'Api-Auth': 'reraeB '+token[::-1]} = Gespiegelt
#getheader = {'Api-Auth': 'Bearer '+token} = Original

pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
temp        = xbmc.translatePath(os.path.join(dataPath, 'temp', '')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
artpic = os.path.join(addonPath, 'resources', 'media', '').encode('utf-8').decode('utf-8')
preferredStreamType = addon.getSetting("streamSelection")
showTVchannel = addon.getSetting("enableChannelID") == 'true'
showNOW = addon.getSetting("enableTVnow")
enableDebug = addon.getSetting("enableDebug") == 'true'
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == 'true'
baseURL = "https://www.tvtoday.de"
dateURL = "/mediathek/nach-datum/"
ZDFapiUrl = "https://api.zdf.de"

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
	if PY2 and isinstance(s, unicode):
		s = s.encode(encoding)
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

def debug_MS(content):
	if enableDebug:
		log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
	msg = py2_enc(msg)
	xbmc.log("["+addon.getAddonInfo('id')+"-"+addon.getAddonInfo('version')+"]"+msg, level)

def getUrl(url, header=None, agent='Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0'):
	global cj
	for cook in cj:
		debug_MS("(getUrl) Cookie : {0}".format(str(cook)))
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
		content = ""
		return sys.exit(0)
	opener.close()
	try: cj.save(cookie, ignore_discard=True, ignore_expires=True)
	except: pass
	return content

def index():
	i = 1
	while i <= 5:
		WU = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
		WT = (datetime.now() - timedelta(days=i)).strftime('%a~%d.%m.%Y')
		MD = WT.split('~')[0].replace('Mon', translation(30601)).replace('Tue', translation(30602)).replace('Wed', translation(30603)).replace('Thu', translation(30604)).replace('Fri', translation(30605)).replace('Sat', translation(30606)).replace('Sun', translation(30607))
		addDir(translation(30608).format(MD, WT.split('~')[1]), baseURL+dateURL+WU+".html", 'listVideos_Day_Channel', icon)
		i += 1
	addDir(translation(30609), baseURL+"/mediathek/nach-sender/", 'listChannel', icon)
	addDir(translation(30611), "Spielfilm", 'listVideosGenre', icon)
	addDir(translation(30612), "Serie", 'listVideosGenre', icon)
	addDir(translation(30613), "Reportage", 'listVideosGenre', icon)
	addDir(translation(30614), "Unterhaltung", 'listVideosGenre', icon)
	addDir(translation(30615), "Kinder", 'listVideosGenre', icon)
	addDir(translation(30616), "Sport", 'listVideosGenre', icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def listChannel(url):
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
	html = getUrl(url)
	debug_MS("(listChannel) SENDER-SORTIERUNG : Alle Sender in TV-Today")
	if showNOW == 'true':
		debug_MS("(listChannel) --- NowTV - Sender EINGEBLENDET ---")
	else:
		debug_MS("(listChannel) --- NowTV - Sender AUSGEBLENDET ---")
	content = html[html.find('<ul class="channels-listing">'):]
	content = content[:content.find('<aside class="module" data-style=')]
	spl = content.split('<li>')
	for i in range(1, len(spl), 1):
		entry = spl[i]
		try:
			fullUrl = re.compile(r'href=["\'](.*?.html)["\']>', re.DOTALL).findall(entry)[0]
			channelID = fullUrl.split('nach-sender/')[1].split('.html')[0].strip()
			channelID = cleanStation(channelID.strip())
			title = channelID.replace('(', '').replace(')', '').replace('  ', '')
			if not baseURL in fullUrl:
				fullUrl = baseURL+fullUrl
			if showNOW == 'false':
				if ("RTL" in channelID or "VOX" in channelID or "SUPER" in channelID):
					continue
			debug_MS("(listChannel) Link : {0}{1}".format(fullUrl, channelID))
			addDir('[COLOR lime]'+title+'[/COLOR]', fullUrl, 'listVideos_Day_Channel', artpic+title.lower().replace(' ', '')+'.png', studio=title)
		except:
			failing("(listChannel) Fehler-Eintrag : {0}".format(str(entry)))
	xbmcplugin.endOfDirectory(pluginhandle)

def listVideos_Day_Channel(url):
	html = getUrl(url)
	debug_MS("(listVideos_Day_Channel) MEDIATHEK : {0}".format(url))
	if showNOW == 'true':
		debug_MS("(listVideos_Day_Channel) --- NowTV - Sender EINGEBLENDET ---")
	else:
		debug_MS("(listVideos_Day_Channel) --- NowTV - Sender AUSGEBLENDET ---")
	content = html[html.find('<section data-style="modules/movie-starts"')+1:]
	content = content[:content.find('<aside class="module" data-style="modules/marginal')]
	spl = content.split('<div data-style="elements/teaser/teaser-l"')
	for i in range(1, len(spl), 1):
		entry = spl[i]
		try:
			name1 = re.compile(r'<img alt=["\'](.*?)["\']', re.DOTALL).findall(entry)[0]
			try:
				name2_1 = re.compile(r'<p class=["\']h2["\']>(.*?)</p>', re.DOTALL).findall(entry)[0]
				name2_2 = re.compile(r'<span class=["\']date["\']>(.*?)/span>', re.DOTALL).findall(entry)[0].replace(", <", " ").replace(",<", " ").replace("<", "")
				if name2_1 and name2_2:
					title = cleanTitle(name2_1)+" - "+cleanTitle(name2_2)
			except:
				title = cleanTitle(name1)
			fullUrl = re.compile(r'<a class=["\']img-box["\'] href=["\'](.*?.html)["\']>', re.DOTALL).findall(entry)[0]
			if not baseURL in fullUrl:
				fullUrl = baseURL+fullUrl
			photo = re.compile(r'src=["\'](https?://.*?.jpg)["\']', re.DOTALL).findall(entry)[0]
			if ',' in photo:
				photo = photo.split(',')[0].rstrip()+'.jpg'
			if not '/mediathek/nach-sender' in url:
				channel = re.compile(r'data-credit=["\'](.*?)["\']>', re.DOTALL).findall(entry)[0]
				channelID = cleanTitle(channel)
				channelID = cleanStation(channelID.strip())
				studio = ""
			else:
				channelID = cleanTitle(url.split('/')[-1].replace('.html', '').strip())
				channelID = cleanStation(channelID.strip())
				studio = channelID.replace('(', '').replace(')', '').replace('  ', '')
			desc = re.compile(r'<p class=["\']short-copy["\']>(.*?)</p>', re.DOTALL).findall(entry)[0]
			plot = cleanTitle(desc)
			if showTVchannel and channelID != "":
				title += channelID
			if showNOW == 'false' and channelID != "":
				if ("RTL" in channelID or "VOX" in channelID or "SUPER" in channelID):
					continue
			debug_MS("(listVideos_Day_Channel) Name : {0}".format(title))
			debug_MS("(listVideos_Day_Channel) Link : {0}".format(fullUrl))
			debug_MS("(listVideos_Day_Channel) Icon : {0}".format(photo))
			addLink(title, fullUrl, 'playVideo', photo, plot, studio)
		except:
			failing("(listVideos_Day_Channel) Fehler-Eintrag : {0}".format(str(entry)))
	xbmcplugin.endOfDirectory(pluginhandle)

def listVideosGenre(category):
	html = getUrl(baseURL+"/mediathek/")
	debug_MS("(listVideosGenre) MEDIATHEK : {0}/mediathek/ - Genre = *{1}*".format(baseURL, category.upper()))
	if showNOW == 'true':
		debug_MS("(listVideosGenre) --- NowTV - Sender EINGEBLENDET ---")
	else:
		debug_MS("(listVideosGenre) --- NowTV - Sender AUSGEBLENDET ---")
	content = html[html.find('<h3 class="h3 uppercase category-headline">'+category+'</h3>')+1:]
	content = content[:content.find('<div class="banner-container">')]
	spl = content.split('<div class="slide js-slide">')
	for i in range(1, len(spl), 1):
		entry = spl[i]
		try:
			name1 = re.compile(r'alt=["\'](.*?)["\']', re.DOTALL).findall(entry)
			name2 = re.compile(r'<p class=["\']h7 name["\']>(.*?)</p>', re.DOTALL).findall(entry)
			if name2 != "":
				title = cleanTitle(name2[0])
			else:
				title = cleanTitle(name1[0])
			channel = re.compile(r'<span class=["\']h6 text["\']>(.*?)</span>', re.DOTALL).findall(entry)[0]
			channelID = cleanTitle(channel)
			channelID = cleanStation(channelID.strip())
			studio = channelID.replace('(', '').replace(')', '').replace('  ', '')
			fullUrl = re.compile(r'<a href=["\']([0-9a-zA-Z-_/.]+html)["\'] class=["\']element js-hover', re.DOTALL).findall(entry)[0]
			if not baseURL in fullUrl:
				fullUrl = baseURL+fullUrl
			photo = re.compile(r'(?:data|img).+?src=["\'](https?://.*?.jpg)["\']', re.DOTALL).findall(entry)[0]
			if ',' in photo:
				photo = photo.split(',')[0].rstrip()+'.jpg'
			desc = re.compile(r'<p class=["\']small-meta description["\']>(.*?)</p>', re.DOTALL).findall(entry)[0]
			plot = cleanTitle(desc)
			if showTVchannel and channelID != "":
				title += channelID
			if showNOW == 'false' and channelID != "":
				if ("RTL" in channelID or "VOX" in channelID or "SUPER" in channelID):
					continue
			debug_MS("(listVideosGenre) Name : {0}".format(title))
			debug_MS("(listVideosGenre) Link : {0}".format(fullUrl))
			debug_MS("(listVideosGenre) Icon : {0}".format(photo))
			addLink(title, fullUrl, 'playVideo', photo, plot, studio)
		except:
			failing("(listVideosGenre) Fehler-Eintrag : {0}".format(str(entry)))
	xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url):
	finalURL = False
	ARD_SCHEMES = ('http://www.ardmediathek.de', 'https://www.ardmediathek.de', 'http://mediathek.daserste.de', 'https://mediathek.daserste.de')
	RTL_SCHEMES = ('http://www.nowtv.de', 'https://www.nowtv.de', 'http://www.tvnow.de', 'https://www.tvnow.de')
	log("(playVideo) --- START WIEDERGABE ANFORDERUNG ---")
	log("(playVideo) frei")
	try:
		content = getUrl(url)
		LINK = re.compile('<div class="img-wrapper stage">\s*<a href=\"([^"]+)" target=', re.DOTALL).findall(content)[0]
		log("(playVideo) AbspielLink (Original) : {0}".format(LINK))
	except:
		log("(playVideo) MediathekLink-00 : MediathekLink der Sendung in TV-Today NICHT gefunden !!!")
		xbmcgui.Dialog().notification(translation(30521), translation(30522), icon, 8000)
		LINK = ""
	log("(playVideo) frei")
	if LINK.startswith("https://www.arte.tv"):
		videoID = re.compile("arte.tv/de/videos/([^/]+?)/", re.DOTALL).findall(LINK)[0]
		try:
			finalURL = 'plugin://plugin.video.L0RE.arte/?mode=playvideo&url='+str(videoID)
			log("(playVideo) AbspielLink-1 (ARTE-TV) : {0}".format(finalURL))
		except:
			try:
				finalURL = 'plugin://plugin.video.arteplussept/play/SHOW/'+str(videoID)
				log("(playVideo) AbspielLink-2 (ARTE-plussept) : {0}".format(finalURL))
			except:
				if finalURL:
					log("(playVideo) AbspielLink-00 (ARTE) : *ARTE-Plugin* Der angeforderte -VideoLink- existiert NICHT !!!")
					xbmcgui.Dialog().notification(translation(30523).format('ARTE - Plugin'), translation(30525), icon, 8000)
				else:
					log("(playVideo) AbspielLink-00 (ARTE) : KEIN *ARTE-Addon* zur Wiedergabe vorhanden !!!")
					xbmcgui.Dialog().notification(translation(30523).format('ARTE - Addon'), translation(30524).format('ARTE-Addon'), icon, 8000)
	elif LINK.startswith(ARD_SCHEMES):
		videoURL = LINK
		return ArdGetVideo(videoURL)
	elif LINK.startswith("https://www.zdf.de"):
		cleanURL = LINK[:LINK.find('.html')]
		videoURL = unquote_plus(cleanURL)+".html"
		return ZdfGetVideo(videoURL)
	elif LINK.startswith(RTL_SCHEMES):
		LINK = LINK.replace('http://', 'https://').replace('www.nowtv.de/', 'www.tvnow.de/').replace('list/aktuell/', '').replace('/player', '')
		videoSE = LINK.split('/')[4].strip()
		videoEP = LINK.split('/')[-1].strip()
		log("(playVideo) --- RTL-Daten : ### Serie [{0}] ### Episode [{1}] ### ---".format(videoSE, videoEP))
		return RtlGetVideo(videoSE, videoEP, LINK)
	if finalURL:
		listitem = xbmcgui.ListItem(name, path=finalURL)
		xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
	log("(playVideo) --- ENDE WIEDERGABE ANFORDERUNG ---")

def ArdGetVideo(videoURL):
	finalURL = False
	m3u8_List = []
	ARD_Url = ""
	try:
		if 'documentId=' in videoURL:
			videoID = videoURL.split('documentId=')[1]
		else:
			secondURL = getUrl(videoURL)
			videoID = re.compile(r'["\']contentId["\']:([^,]+?),["\']metadataId["\']:', re.DOTALL).findall(secondURL)[0].replace('"', '').replace("'", "")
		debug_MS("(ArdGetVideo) ***** Extracted-videoID : {0} *****".format(videoID))
		# evtl. NEW = https://appdata.ardmediathek.de/appdata/servlet/play/media/66597424 #
		content = getUrl('https://classic.ardmediathek.de/play/media/'+videoID)
		debug_MS("(ArdGetVideo) ##### CONTENT : {0} #####".format(str(content)))
		result = json.loads(content)
		allLinks = result["_mediaArray"][0]["_mediaStreamArray"]
		linkQuality = 2 # Verfügbare mp4-Qualität in der ARD-Mediathek = 2 (Standard)
		if preferredStreamType == "0" and allLinks:
			for item in allLinks:
				if item["_quality"] != 'auto':
					# Nicht gewollte Qualität überspringen
					continue
				video = item["_stream"]
				if video and 'mil/master.m3u8' in video:
					m3u8_List.append(video)
				else:
					for vids in video:
						if 'mil/master.m3u8' in vids:
							m3u8_List.append(vids)
			if m3u8_List:
				if len(m3u8_List) > 1:
					log("(ArdGetVideo) Wir haben 2 *m3u8-Streams* (ARD+3) - wähle den Ersten : {0}".format(str(m3u8_List[0])))
				else:
					log("(ArdGetVideo) Wir haben 1 *m3u8-Stream* (ARD+3) - wähle Diesen : {0}".format(str(m3u8_List[0])))
				finalURL = m3u8_List[0]
				if finalURL[:4] != "http":
					finalURL = "https:"+finalURL
		if not finalURL and allLinks:
			for quality in allLinks:
				# Überprüfen, ob noch höhere mp4-Qualitäten verfügbar sind und die höchste verfügbare Qualitätsstufe festlegen
				if quality["_quality"] != 'auto' and quality["_quality"] > linkQuality and '_stream' in quality:
					if quality["_quality"] > 2 and not quality["_quality"] > 3:
						linkQuality = 3
					elif quality["_quality"] > 3 and not quality["_quality"] > 4:
						linkQuality = 4
			log("(ArdGetVideo) ##### LINK-Qualität (ARD+3) = {0} ##### [4=höchste|3=beste|2=mittlere|1=schlechteste]".format(str(linkQuality)))
			for element in allLinks:
				if linkQuality != element["_quality"]:
					# Nicht gewollte Qualität überspringen
					continue
				stream = element["_stream"]
				if type(stream) is list or type(stream) is tuple:
					# Überprüfen, ob der ausgewählte mp4-Stream zwei Streams enthält
					if len(stream) > 1:
						if linkQuality > 2 and not "podcast" in stream[0]: 
							ARD_Url = stream[0]
							log("(ArdGetVideo) Wir haben mehrere *mp4-Streams* in der Liste (ARD+3) - wähle den Ersten : {0}".format(ARD_Url))
						else:
							ARD_Url = stream[1]
							log("(ArdGetVideo) Wir haben mehrere *mp4-Streams* in der Liste (ARD+3) - wähle den Zweiten : {0}".format(ARD_Url))
					else:
						ARD_Url = stream[0]
						log("(ArdGetVideo) Wir haben 1 *mp4-Stream* in der Liste (ARD+3) wähle Diesen : {0}".format(ARD_Url))
				else:
					ARD_Url = stream
					log("(ArdGetVideo) Wir haben nur 1 *mp4-Stream* (ARD+3) - wähle Diesen : {0}".format(ARD_Url))
			if ARD_Url != "":
				if ARD_Url[:4] != "http":
					ARD_Url = "https:"+ARD_Url
				finalURL = VideoBEST(ARD_Url, improve='ard-YES') # *mp4URL* Qualität nachbessern, überprüfen, danach abspielen
		if not finalURL:
			log("(ArdGetVideo) AbspielLink-00 (ARD+3) : *ARD-Intern* Der angeforderte -VideoLink- existiert NICHT !!!")
			xbmcgui.Dialog().notification(translation(30523).format('ARD - Intern'), translation(30525), icon, 8000)
		else:
			listitem = xbmcgui.ListItem(name, path=finalURL)
			xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
			log("(ArdGetVideo) END-Qualität (ARD+3) : {0}".format(finalURL))
	except:
		failing("(ArdGetVideo) AbspielLink-00 (ARD+3) : *ARD-Intern* Der angeforderte -VideoLink- existiert NICHT !!!")
		xbmcgui.Dialog().notification(translation(30523).format('ARD - Intern'), translation(30525), icon, 8000)
	log("(playVideo) --- ENDE WIEDERGABE ANFORDERUNG ---")

def RtlGetVideo(SERIES, EPISODE, REFERER):
	j_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.GetAddonDetails", "params": {"addonid":"plugin.video.rtlnow", "properties": ["enabled"]}, "id":1}')
	if '"enabled":false' in j_query:
		try: xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.SetAddonEnabled", "params": {"addonid":"plugin.video.rtlnow", "enabled":true}, "id":1}')
		except: pass
	if xbmc.getCondVisibility('System.HasAddon(plugin.video.rtlnow)'):
		#http://api.tvnow.de/v3/movies/shopping-queen/2361-lisa-marie-nuernberg-flower-power-praesentiere-dich-in-deinem-neuen-bluetenkleid?fields=manifest,isDrm,free
		try: # https://apigw.tvnow.de/module/player/%d" % int(assetID)
			content = getUrl('http://api.tvnow.de/v3/movies/{0}/{1}?fields=manifest,isDrm,free'.format(SERIES, EPISODE))
			response = json.loads(content)
			drm = response["isDrm"]
			free = response["free"]
			log("(RtlGetVideo) --- RTL-Optionen : ### DRM = {0} ### FREE = {1} ### ---".format(drm, free))
			videoFREE = response["manifest"]["dash"].strip().replace('vodnowusodash.secure.footprint.net', 'vodnowusodash-a.akamaihd.net').split('.mpd')[0]+'.mpd'
			debug_MS("(RtlGetVideo) videoFREE : {0}".format(videoFREE))
			protected = "0"
			try: videoHD = response["manifest"]["dashhd"].strip()
			except: videoHD = ""
			if videoHD != "":
				if drm == True:
					protected = "1"
					log("(RtlGetVideo) ~~~ Video ist DRM - geschützt ~~~")
				else: protected = "2"
				videoHD = videoHD.replace('vodnowusodash.secure.footprint.net', 'vodnowusodash-a.akamaihd.net').split('.mpd')[0]+'.mpd'
				debug_MS("(RtlGetVideo) videoHD : {0}".format(videoHD))
			listitem = xbmcgui.ListItem(path='plugin://plugin.video.rtlnow/?mode=playDash&xnormSD='+str(videoFREE)+'&xhighHD='+str(videoHD)+'&xlink='+REFERER+'&xdrm='+protected)
			xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
		except:
			failing("(RtlGetVideo) AbspielLink-00 (TV-Now) : *TVNow-Plugin* Der angeforderte -VideoLink- existiert NICHT !!!")
			xbmcgui.Dialog().notification(translation(30523).format('TVNow - Plugin'), translation(30525), icon, 8000)
	else:
		log("(RtlGetVideo) AbspielLink-00 (TV-Now) : KEIN *TVNow-Addon* zur Wiedergabe vorhanden !!!")
		xbmcgui.Dialog().notification(translation(30523).format('TVNow - Addon'), translation(30524).format('TVNow-Addon'), icon, 8000)
	log("(playVideo) --- ENDE WIEDERGABE ANFORDERUNG ---")

def ZdfGetVideo(videoURL):
	videoFOUND = False
	try: 
		content = getUrl(videoURL)
		response = re.compile(r'data-zdfplayer-jsb=["\']({.+?})["\']', re.DOTALL).findall(content)[0]
		firstURL = json.loads(response)
		if firstURL:
			teaser = firstURL['content']
			secret = firstURL['apiToken']
			headerfields = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0'), ('Api-Auth', 'Bearer '+secret)]
			log("(ZdfGetVideo) SECRET gefunden (ZDF+3) : ***** {0} *****".format(str(secret)))
			if teaser[:4] != "http":
				teaser = ZDFapiUrl+teaser
			debug_MS("(ZdfGetVideo) ##### TEASER : {0} #####".format(teaser))
			secondURL = getUrl(teaser, header=headerfields)
			element = json.loads(secondURL)
			if element['profile'] == "http://zdf.de/rels/not-found":
				return False
			if element['contentType'] == "clip":
				component = element['mainVideoContent']['http://zdf.de/rels/target']
				#videoFOUND1 = ZDFapiUrl+element['mainVideoContent']['http://zdf.de/rels/target']['http://zdf.de/rels/streams/ptmd']
				#videoFOUND2 = ZDFapiUrl+element['mainVideoContent']['http://zdf.de/rels/target']['http://zdf.de/rels/streams/ptmd-template'].replace('{playerId}', 'ngplayer_2_3')
			elif element['contentType'] == "episode":
				if "mainVideoContent" in element:
					component = element['mainVideoContent']['http://zdf.de/rels/target']
				elif "mainContent" in element:
					component = element['mainContent'][0]['videoContent'][0]['http://zdf.de/rels/target']
			if "http://zdf.de/rels/streams/ptmd-template" in component and component['http://zdf.de/rels/streams/ptmd-template'] != "":
				videoFOUND = ZDFapiUrl+component['http://zdf.de/rels/streams/ptmd-template'].replace('{playerId}', 'ngplayer_2_3').replace('\/', '/')
			if videoFOUND:
				debug_MS("(ZdfGetVideo) ##### videoFOUND : {0} #####".format(videoFOUND))
				thirdURL = getUrl(videoFOUND, header=headerfields)
				return ZdfExtractQuality(thirdURL)
	except:
		failing("(ZdfGetVideo) AbspielLink-00 (ZDF+3) : *ZDF-Intern* Der angeforderte -VideoLink- existiert NICHT !!!")
		log("(playVideo) --- ENDE WIEDERGABE ANFORDERUNG ---")
		xbmcgui.Dialog().notification(translation(30523).format('ZDF - Intern'), translation(30525), icon, 8000)

def ZdfExtractQuality(thirdURL):
	jsonObject = json.loads(thirdURL)
	DATA = {}
	DATA['media'] = []
	m3u8_QUALITIES = ['auto', 'veryhigh', 'high', 'med']
	mp4_QUALITIES = ['hd', 'veryhigh', 'high', 'low']
	finalURL = False
	try:
		for each in jsonObject['priorityList']:
			vidType = each['formitaeten'][0]['mimeType'].lower()
			vidQuality = each['formitaeten'][0]['qualities']
			vidForm = each['formitaeten'][0]['type']
			vidMode = each['formitaeten'][0]['facets']
			if preferredStreamType == "0" and vidForm == "h264_aac_ts_http_m3u8_http" and vidType == "application/x-mpegurl":
				for found in m3u8_QUALITIES:
					for quality in vidQuality:
						if quality['quality'] == found and "mil/master.m3u8" in quality['audio']['tracks'][0]['uri']:
							DATA['media'].append({'url': quality['audio']['tracks'][0]['uri'], 'type': 'video', 'mimeType': vidType})
				finalURL = DATA['media'][0]['url']
				log("(ZdfExtractQuality) m3u8-Stream (ZDF+3) : {0}".format(finalURL))
			if not finalURL and vidForm == "h264_aac_mp4_http_na_na" and "progressive" in vidMode and vidType == "video/mp4":
				for found in mp4_QUALITIES:
					for quality in vidQuality:
						if quality['quality'] == found:
							DATA['media'].append({'url': quality['audio']['tracks'][0]['uri'], 'type': 'video', 'mimeType': vidType})
				log("(ZdfExtractQuality) ZDF-STANDARDurl : {0}".format(DATA['media'][0]['url']))
				finalURL = VideoBEST(DATA['media'][0]['url'], improve='zdf-YES') # *mp4URL* Qualität nachbessern, überprüfen, danach abspielen
		if not finalURL:
			log("(ZdfExtractQuality) AbspielLink-00 (ZDF+3) : *ZDF-Intern* VIDEO konnte NICHT abgespielt werden !!!")
		else:
			listitem = xbmcgui.ListItem(name, path=finalURL)
			xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
			log("(ZdfExtractQuality) END-Qualität (ZDF+3) : {0}".format(finalURL))
	except:
		failing("(ZdfExtractQuality) AbspielLink-00 (ZDF+3) : *ZDF-Intern* Fehler bei Anforderung des AbspielLinks !!!")
	log("(playVideo) --- ENDE WIEDERGABE ANFORDERUNG ---")

def VideoBEST(best_url, improve=False):
	# *mp4URL* Qualität nachbessern, überprüfen, danach abspielen
	standards = [best_url,"",""]
	if improve == "ard-YES":
		standards[1] = standards[0].replace('/960', '/1280').replace('.hq.mp4', '.hd.mp4').replace('.l.mp4', '.xl.mp4').replace('_C.mp4', '_X.mp4')
		standards[2] = standards[1].replace('/1280', '/1920').replace('.xl.mp4', '.xxl.mp4')
	elif improve == "zdf-YES":
		standards[1] = standards[0].replace('1456k_p13v11', '2328k_p35v11').replace('1456k_p13v12', '2328k_p35v12').replace('1496k_p13v13', '2328k_p35v13').replace('1496k_p13v14', '2328k_p35v14').replace('2256k_p14v11', '2328k_p35v11').replace('2256k_p14v12', '2328k_p35v12').replace('2296k_p14v13', '2328k_p35v13').replace('2296k_p14v14', '2328k_p35v14')
		standards[2] = standards[1].replace('2328k_p35v12', '3328k_p36v12').replace('2328k_p35v13', '3328k_p36v13').replace('2328k_p35v14', '3328k_p36v14')
	for element in reversed(standards):
		if len(element) > 0:
			try:
				code = urlopen(element).getcode()
				if str(code) == "200":
					return element
			except: pass
	return best_url

def cleanTitle(title):
	title = py2_enc(title)
	title = title.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('amp;', '').replace('&#39;', '\'').replace('&#039;', '\'').replace('&quot;', '"').replace('&szlig;', 'ß').replace('&ndash;', '-')
	title = title.replace('&#x00c4', 'Ä').replace('&#x00e4', 'ä').replace('&#x00d6', 'Ö').replace('&#x00f6', 'ö').replace('&#x00dc', 'Ü').replace('&#x00fc', 'ü').replace('&#x00df', 'ß')
	title = title.replace('&Auml;', 'Ä').replace('&Ouml;', 'Ö').replace('&Uuml;', 'Ü').replace('&auml;', 'ä').replace('&ouml;', 'ö').replace('&uuml;', 'ü')
	title = title.replace('&agrave;', 'à').replace('&aacute;', 'á').replace('&acirc;', 'â').replace('&egrave;', 'è').replace('&eacute;', 'é').replace('&ecirc;', 'ê').replace('&igrave;', 'ì').replace('&iacute;', 'í').replace('&icirc;', 'î')
	title = title.replace('&ograve;', 'ò').replace('&oacute;', 'ó').replace('&ocirc;', 'ô').replace('&ugrave;', 'ù').replace('&uacute;', 'ú').replace('&ucirc;', 'û')
	title = title.replace("\\'", "'").replace('<wbr/>', '').replace('<br />', ' -').replace(" ", ".").replace('Ã¶', 'ö')
	title = title.strip()
	return title

def cleanStation(channelID):
	ChannelCode = ('ARD','Das Erste','ONE','FES','ZDF','2NEO','ZNEO','2INFO','ZINFO','3SAT','Arte','ARTE','BR','HR','KIKA','MDR','NDR','N3','ORF','PHOEN','RBB','SR','SWR','SWR/SR','WDR','RTL','RTL2','VOX','SRTL','SUPER')
	if channelID in ChannelCode and channelID != "":
		try:
			channelID = channelID.replace(' ', '')
			if 'ARD' in channelID or 'DasErste' in channelID:
				channelID = '  (Das Erste)'
			elif 'ONE' in channelID or 'FES' in channelID:
				channelID = '  (ONE)'
			elif 'Arte' in channelID or 'ARTE' in channelID:
				channelID = '  (ARTE)'
			elif '2INFO' in channelID or 'ZINFO' in channelID:
				channelID = '  (ZDFinfo)'
			elif '2NEO' in channelID or 'ZNEO' in channelID:
				channelID = '  (ZDFneo)'
			elif '3SAT' in channelID:
				channelID = '  (3sat)'
			elif 'NDR' in channelID or 'N3' in channelID:
				channelID = '  (NDR)'
			elif 'PHOEN' in channelID:
				channelID = '  (PHOENIX)'
			elif ('SR' in channelID or 'SWR' in channelID) and not 'SRTL' in channelID:
				channelID = '  (SWR)'
			elif 'SRTL' in channelID or 'SUPER' in channelID:
				channelID = '  (SRTL)'
			else:
				channelID = '  ('+channelID+')'
		except: pass
	elif not channelID in ChannelCode and channelID != "":
		channelID = '  ('+channelID+')'
	else:
		channelID = ""
	return channelID

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addQueue(url, name, image, studio):
	PL = xbmc.PlayList(1)
	listitem = xbmcgui.ListItem(name)
	listitem.setInfo(type="Video", infoLabels={"Title": name, "Studio": studio, "mediatype": "video"})
	listitem.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	listitem.setProperty('IsPlayable', 'true')
	listitem.setContentLookup(False)
	PL.add(url, listitem)

def addDir(name, url, mode, image, plot=None, studio=None):
	u = sys.argv[0]+"?url="+quote_plus(url)+"&mode="+str(mode)
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": plot, "Studio": studio})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon and not artpic in image:
		liz.setArt({'fanart': image})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

def addLink(name, url, mode, image, plot=None, studio=None, duration=None, seriesname=None, season=None, episode=None, genre=None, year=None, begins=None):
	u = sys.argv[0]+"?url="+quote_plus(url)+"&mode="+str(mode)
	liz = xbmcgui.ListItem(name)
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
	ilabels['Year'] = year
	ilabels['Genre'] = genre
	ilabels['Director'] = None
	ilabels['Writer'] = None
	ilabels['Studio'] = studio
	ilabels['Mpaa'] = None
	ilabels['Mediatype'] = 'video'
	liz.setInfo(type='Video', infoLabels=ilabels)
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon and not artpic in image:
		liz.setArt({'fanart': image})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	liz.setContentLookup(False)
	liz.addContextMenuItems([(translation(30653), 'RunPlugin({0}?mode=addQueue&url={1}&name={2}&image={3}&studio={4})'.format(sys.argv[0], quote_plus(u), quote_plus(name), quote_plus(image), quote_plus(studio)))])
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
studio = unquote_plus(params.get('studio', ''))

if mode == 'listChannel':
	listChannel(url)
elif mode == 'listVideos_Day_Channel':
	listVideos_Day_Channel(url)
elif mode == 'listVideosGenre':
	listVideosGenre(url)
elif mode == 'playVideo':
	playVideo(url)
elif mode == 'addQueue':
	addQueue(url, name, image, studio)
else:
	index()