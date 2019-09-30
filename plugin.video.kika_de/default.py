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
import io
import gzip
import hashlib


global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
temp        = xbmc.translatePath(os.path.join(dataPath, 'temp', '')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
artpic = os.path.join(addonPath, 'resources', 'media', '').encode('utf-8').decode('utf-8')
Newest = addon.getSetting("Newest") == 'true'
since00 = addon.getSetting("since00") == 'true'
since03 = addon.getSetting("since03") == 'true'
since06 = addon.getSetting("since06") == 'true'
since10 = addon.getSetting("since10") == 'true'
sinceAll = addon.getSetting("sinceAll") == 'true'
formatToAutoSelect = {0:'1280x720', 1:'960x540', 2:'720x576', 3:'640x360', 4:'512x288', 5:'480x270', 6:'320x180'}[int(addon.getSetting('prefVideoQuality'))]
Dating = addon.getSetting("show_date") == 'true'
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == 'true'
Pagination = int(addon.getSetting("max_pages"))+1
Adjustment = addon.getSetting("show_settings") == 'true'
forceView = addon.getSetting("forceView") == 'true'
viewIDAlphabet = str(addon.getSetting("viewIDAlphabet"))
viewIDShows = str(addon.getSetting("viewIDShows"))
viewIDVideos = str(addon.getSetting("viewIDVideos"))
baseURL = "https://www.kika.de"

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

def convert_duration(duration):
	match = re.match('^(\d+):(\d+)$', duration)
	if match is None: return None
	ret = 0
	for group, factor in enumerate([60, 1], 1):
		ret = factor * (ret+int(match.group(group)))
	return ret

def getUrl(url, header=None, agent='Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0'):
	global cj
	for cook in cj:
		debug("(getUrl) Cookie : {0}".format(str(cook)))
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
	if Newest: addDir(translation(30602), baseURL+"/videos/index.html", 'listEpisodes', icon)
	if since00: addDir(translation(30603), baseURL+"/kikaninchen/sendungen/videos-kikaninchen-100.html", 'listAlphabet', icon)
	if since03: addDir(translation(30604), baseURL+"/videos/abdrei/videos-ab-drei-buendel100.html", 'listAlphabet', icon)
	if since06: addDir(translation(30605), baseURL+"/videos/absechs/videosabsechs-buendel100.html", 'listAlphabet', icon)
	if since10: addDir(translation(30606), baseURL+"/videos/abzehn/videosabzehn-buendel102.html", 'listAlphabet', icon)
	if sinceAll: addDir(translation(30607), baseURL+"/videos/allevideos/allevideos-buendelgruppen100.html", 'listAlphabet', icon)
	addDir(translation(30608), baseURL+"/resources/player/xml/kika/livestream.xml", 'play_LIVE', artpic+'live.png', folder=False)
	if Adjustment: addDir(translation(30609), "", 'aSettings', artpic+'settings.png')
	xbmcplugin.endOfDirectory(pluginhandle)

def listAlphabet(url):
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
	debug("(listAlphabet) ------------------------------------------------ START = listAlphabet -----------------------------------------------")
	debug("(listAlphabet) ### URL : {0} ###".format(url))
	html = getUrl(url)
	content = html[html.find('class="bundleNaviWrapper"')+1:]
	content = content[:content.find('class="modCon"')]
	match = re.compile('<a href="(.+?)" class="pageItem".*?>(.+?)</a>', re.DOTALL).findall(content)
	for endURL, title in match:
		if endURL[:4] != "http": endURL = baseURL+endURL
		if title == '...': title = '#'
		debug("(listAlphabet) XXX TITLE = {0} | endURL = {1} XXX".format(str(title), endURL))
		if '/kikaninchen/' in url:
			addDir(title, endURL, 'listEpisodes', artpic+title.title()+'.png')
		else:
			addDir(title, endURL, 'listShows', artpic+title.title()+'.png')
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceView:
		xbmc.executebuiltin('Container.SetViewMode('+viewIDAlphabet+')')

def listShows(url):
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
	debug("(listShows) ------------------------------------------------ START = listShows -----------------------------------------------")
	debug("(listShows) ### URL : {0} ###".format(url))
	content = getUrl(url)
	part = content.split('class="teaser teaserStandard  teaserMultigroup')
	for i in range(1, len(part), 1):
		entry = part[i]
		image = re.compile("data-ctrl-image=.*?'urlScheme':'(.+?)'}", re.DOTALL).findall(entry)[0].split('-resimage_v-')[0]+"-resimage_v-tlarge169_w-1280.jpg"
		if image[:4] != "http": image = baseURL+image
		url2 = re.compile('<h4 class="headline">.*?href="(.+?)" title=', re.DOTALL).findall(entry)[0]
		if url2[:4] != "http": url2 = baseURL+url2
		title = re.compile('<h4 class="headline">.*?title="">(.+?)</a>', re.DOTALL).findall(entry)[0]
		title = cleanTitle(title)
		if not 'kikaninchen' in title.lower():
			endURL = url2
			if '/sendungen/videos' in url2:
				try:
					shorten = url2.split('/sendungen/videos')[0]+'/index.html'
					debug("(listShows) XXX shortURL = {0} XXX".format(shorten))
					result = getUrl(shorten)
					endURL = re.findall(r'<a href=".+?(/[a-z-]+/buendelgruppe[0-9]+.html)" title="">',result,re.S)[0]
					if endURL[:4] != "http": endURL = baseURL+endURL
				except: pass
			debug("(listShows) XXX TITLE = {0} | endURL = {1} | PHOTO = {2} XXX".format(str(title), endURL, str(image)))
			addDir(title, endURL, 'listEpisodes', image, seriesname=title)
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceView:
		xbmc.executebuiltin('Container.SetViewMode('+viewIDShows+')')

def listEpisodes(url, page=0):
	debug("(listEpisodes) ------------------------------------------------ START = listEpisodes -----------------------------------------------")
	debug("(listEpisodes) ### URL : {0} ###".format(url))
	COMBI_1 = []
	COMBI_2 = []
	workList = ""
	Isolated = set()
	pos = 0
	pos2 = 0
	pos3 = 0
	html = getUrl(url)
	if '<div class="bundleNaviItem' in html and not 'kikaninchen' in url:
		NaviItem = re.findall('<div class="bundleNaviItem.*?href="(.+?)" class="pageItem" title="">(.+?)</a>', html, re.DOTALL)
		for link, name in NaviItem:
			if link in Isolated:
				continue
			Isolated.add(link)
			pos += 1
			url2 = link
			if url2[:4] != "http": url2 = baseURL+url2
			debug("(listEpisodes) FIRST XXX POS = {0} | URL-2 = {1} XXX".format(str(pos), url2))
			if pos == Pagination: break
			COMBI_1.append([pos, url2])
	else:
		pos += 1
		url2 = url
		debug("(listEpisodes) SECOND XXX POS = {0} | URL-2 = {1} XXX".format(str(pos), url2))
		COMBI_1.append([pos, url2])
	for pos, url2 in COMBI_1:
		debug("(listEpisodes) THIRD XXX POS = {0} | URL-2 = {1} XXX".format(str(pos), url2))
		startURL = url2
		result = getUrl(url2)
		if not 'index' in startURL:
			content = result[result.find('<!--Header Area for the Multigroup -->')+1:]
			content = content[:content.find('<!--The bottom navigation -->')]
		else:
			content = result[result.find('<h2 class="conHeadline">Neue Videos</h2>')+1:]
			content = content[:content.find('<span class="linktext">Alle Videos</span>')]
		part = content.split('class="teaser teaserStandard')
		for i in range(1, len(part), 1):
			entry = part[i]
			image = re.compile("data-ctrl-image=.*?'urlScheme':'(.+?)'}", re.DOTALL).findall(entry)[0].split('-resimage_v-')[0]+"-resimage_v-tlarge169_w-1280.jpg"
			if image[:4] != "http": image = baseURL+image
			endURL = re.compile('<h4 class="headline">.*?href="(.+?)" title=', re.DOTALL).findall(entry)[0].replace("sendereihe", "buendelgruppe")
			if endURL[:4] != "http": endURL = baseURL+endURL
			try: duration = convert_duration(re.compile('<span class="icon-duration">(.+?)</span>', re.DOTALL).findall(entry)[0])
			except: duration = 0
			plot = ""
			seriesname = ""
			if not 'index' in startURL:
				if '<meta property="og:title" content=' in result:
					Note_1 = re.compile('<meta property="og:title" content="(.+?)"/>', re.DOTALL).findall(result)[0]
					plot = cleanTitle(Note_1)
					seriesname = cleanTitle(Note_1)
				if '<meta property="og:description" content' in result:
					Note_2 = re.compile('<meta property="og:description" content="(.+?)"/>', re.DOTALL).findall(result)[0]
					plot += '[CR][CR]'+cleanTitle(Note_2)
			first = ""
			second = ""
			text = ""
			if '<h4 class="headline">' in entry: first = re.compile('<h4 class="headline">.*?title="">(.+?)</a>', re.DOTALL).findall(entry)[0]
			if '<p class="dachzeile">' in entry: second = re.compile('<p class="dachzeile">.*?title="">(.+?)</a>', re.DOTALL).findall(entry)[0]
			if '<img title=' in entry: text = re.compile('<img title=.*?alt="([^"]+?)"', re.DOTALL).findall(entry)[0]
			if first.strip() !="" and second.strip() !="" and text.strip() !="":
				title1 = cleanTitle(first)
				if not 'index' in startURL:
					plot += '[CR][CR]'+cleanTitle(text)
					title2 = cleanTitle(first)
					if Dating and ('Folge' in second or 'buendelgruppe' in startURL):
						title2 = cleanTitle(first)+"   [COLOR deepskyblue]("+cleanTitle(second).split(',')[0]+")[/COLOR]"
				else:
					title2 = cleanTitle(second)+' - '+cleanTitle(first)
					plot = cleanTitle(second)+'[CR][CR]'+cleanTitle(text)
					seriesname = cleanTitle(second)
			elif first.strip() !="" and second.strip() =="":
				title1 = cleanTitle(first)
			elif first.strip() =="" and second.strip() !="":
				title1 = cleanTitle(second)
			else:
				title1 = cleanTitle(text)
			pos2 += 1
			episode = 0
			numbers = 0
			if title1[:1].isdigit():
				numbers = re.findall('([0-9]+). ',title1,re.S)[0].strip().zfill(4)
				episode = numbers
				pos3 += 1
			if pos2 == pos3:
				debug("(listEpisodes) FOURTH XXX POS_2 = {0} | POS_3 = {1} XXX".format(str(pos2), str(pos3)))
				COMBI_2.append([numbers, pos2, pos3, title1, title2, endURL, image, plot, duration, seriesname, episode])
				COMBI_2 = sorted(COMBI_2, key=lambda num:num[0], reverse=True)
			else:
				COMBI_2.append([numbers, pos2, pos3, title1, title2, endURL, image, plot, duration, seriesname, episode])
	if COMBI_2:
		for numbers, pos2, pos3, title1, title2, endURL, image, plot, duration, seriesname, episode in COMBI_2:
			hasresult = hashlib.md5(seriesname+'-'+title1).hexdigest()
			seq = hasresult+"###"+endURL+"###"+seriesname+"###"+title2+"###"+image+"###"+plot+"###"+str(duration)+"###"+str(episode)+"###"
			workList = workList+seq.replace("\n"," ").encode('utf-8')+"\n"
			listitem = xbmcgui.ListItem(path=sys.argv[0]+'?number='+hasresult+'&mode=play_CODE')
			listitem.setInfo(type='Video', infoLabels={'Title': title2, 'Tvshowtitle': seriesname, 'Plot': plot, 'Duration': duration, 'Episode': episode, 'Mediatype': 'episode'})
			listitem.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
			if useThumbAsFanart and image != icon and not artpic in image:
				listitem.setArt({'fanart': image})
			listitem.addStreamInfo('Video', {'Duration':duration})
			listitem.setProperty('IsPlayable', 'true')
			xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sys.argv[0]+'?number='+hasresult+'&mode=play_CODE', listitem=listitem)
	with open(os.path.join(dataPath, 'episode_data.txt'), 'w') as input:
		input.write(workList)
		debug("(listEpisodes) XXX workList : {0} XXX".format(str(workList)))
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceView:
		xbmc.executebuiltin('Container.SetViewMode('+viewIDVideos+')')

def getXmlUrlForEpisode(url):
	xmlUrl = "0"
	try:
		content = getUrl(url)
		xmlUrl = re.compile('dataURL:\'([^\']*)\'', re.DOTALL).findall(content)[0]
	except: pass
	return xmlUrl

def getStreamEntry(entry):
	TITLE = ""
	stream = ""
	TITLE = py2_enc(re.compile('<profileName>(.+?)</profileName>', re.DOTALL).findall(entry)[0])
	try: stream = re.compile('<progressiveDownloadUrl>(.+?)</progressive', re.DOTALL).findall(entry)[0]
	except: pass
	if stream == "":
		try:
			matches = re.compile('<flashMediaServerURL>(.+?)</flash', re.DOTALL).findall(entry)
			for match2 in matches:
				url = match2.split(":") #url was mp4:mp4dyn/1/FCMS-[HASH].mp4
				if len(url) > 1:
					url = url[1]
				else:
					url = url[0]
				appMatch = re.compile('<flashMediaServerApplicationURL>(.+?)</flash', re.DOTALL).findall(entry)
				stream = appMatch[0]+"/"+url
		except: pass
	return TITLE,stream

def play_CODE(idd):
	debug("(play_CODE) ------------------------------------------------ START = play_CODE -----------------------------------------------")
	debug("(play_CODE) ### IDD : {0} ###".format(str(idd)))
	QUALITIES = ['1280x720', '960x540', '720x576', '640x360', '512x288', '480x270', '320x180']
	DATA = {}
	DATA['media'] = []
	finalURL = False
	with open(os.path.join(dataPath, 'episode_data.txt'), 'r') as output:
		sequence = output.read().split('\n')
		for seq in sequence:
			field = seq.split('###')
			if field[0]==idd:
				endURL = field[1]
				seriesname = field[2]
				title2 = field[3]
				image = field[4]
				plot = field[5] 
				duration = field[6] 
				episode = field[7]
	xmlUrl = getXmlUrlForEpisode(endURL)
	debug("(play_CODE) ### xmlUrl : {0} ###".format(xmlUrl))
	if xmlUrl != "0":
		content = getUrl(xmlUrl)
		part = content.split('<asset>')
		for i in range(1, len(part), 1):
			entry = part[i]
			TITLE,stream = getStreamEntry(entry)
			if formatToAutoSelect in TITLE:
				debug("(play_CODE) XXX TITLE = {0} | Bevorzugte-URL = {1} XXX".format(str(TITLE), stream))
				finalURL = stream
		if not finalURL:
			for found in QUALITIES:
				for i in range(1, len(part), 1):
					entry = part[i]
					TITLE,stream = getStreamEntry(entry)
					if found in TITLE:
						DATA['media'].append({'url': stream, 'quality': found, 'mimeType': 'mp4'})
			debug("(play_CODE) XXX  Stream-URLs : {0} XXX".format(str(DATA['media'])))
			finalURL = DATA['media'][0]['url']
	if finalURL:
		log("(playVideo) Streamurl : {0}".format(finalURL))
		listitem = xbmcgui.ListItem(path=finalURL)
		xbmcplugin.setResolvedUrl(pluginhandle,True, listitem)
	else:
		failing("(playVideo) ##### Abspielen des Streams NICHT möglich ##### URL : {0} #####\n   ########## KEINEN Stream-Eintrag auf der Webseite von *kika.de* gefunden !!! ##########".format(url))
		return xbmcgui.Dialog().notification(translation(30521).format('STREAM'), translation(30523), icon, 8000)

def play_LIVE(url):
	debug("(play_LIVE) ------------------------------------------------ START = play_LIVE -----------------------------------------------")
	live_url = False
	try:
		content =  getUrl(url)
		part = content.split('<asset>')
		for i in range(1, len(part), 1):
			entry = part[i]
			if '<geoZone>DE</geoZone>' in entry:
				live_url = re.compile('<adaptiveHttpStreamingRedirectorUrl>(.+?)</adaptive', re.DOTALL).findall(entry)[0]
	except: pass
	if live_url:
		debug("(play_LIVE) ### LIVEurl : {0} ###".format(live_url))
		listitem = xbmcgui.ListItem(path=live_url, label=translation(30608))
		listitem.setMimeType('application/vnd.apple.mpegurl')
		xbmc.Player().play(item=live_url, listitem=listitem)
	else:
		failing("(liveTV) ##### Abspielen des Live-Streams NICHT möglich ##### URL : {0} #####\n   ########## KEINEN Live-Stream-Eintrag auf der Webseite von *kika.de* gefunden !!! ##########".format(url))
		return xbmcgui.Dialog().notification(translation(30521).format('LIVE'), translation(30524), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def cleanTitle(title):
	title = py2_enc(title)
	title = title.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', '\'').replace('&#039;', '\'').replace('&szlig;', 'ß').replace('&ndash;', '-')
	title = title.replace('&#x00c4', 'Ä').replace('&#x00e4', 'ä').replace('&#x00d6', 'Ö').replace('&#x00f6', 'ö').replace('&#x00dc', 'Ü').replace('&#x00fc', 'ü').replace('&#x00df', 'ß')
	title = title.replace('&Auml;', 'Ä').replace('&Ouml;', 'Ö').replace('&Uuml;', 'Ü').replace('&auml;', 'ä').replace('&ouml;', 'ö').replace('&uuml;', 'ü')
	title = title.replace('&agrave;', 'à').replace('&aacute;', 'á').replace('&egrave;', 'è').replace('&eacute;', 'é').replace('&igrave;', 'ì').replace('&iacute;', 'í')
	title = title.replace('&ograve;', 'ò').replace('&oacute;', 'ó').replace('&ugrave;', 'ù').replace('&uacute;', 'ú')
	if 'Rechte:' in title: title=title.split('Rechte:')[0]
	title = title.replace('KIKA - ', '').replace('KiKA - ', '').replace('Folgenübersicht', '').replace('Folge vom ', '').replace('| ', '')
	return title.strip()

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, plot=None, seriesname="", page=0, folder=True):
	u = sys.argv[0]+'?url='+quote_plus(url)+'&mode='+str(mode)+'&page='+str(page)
	liz = liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Tvshowtitle': seriesname, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon and not artpic in image:
		liz.setArt({'fanart': image})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=folder)

params = parameters_string_to_dict(sys.argv[2])
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
page = unquote_plus(params.get('page', ''))
number = unquote_plus(params.get('number', ''))

if mode == 'aSettings':
	addon.openSettings()
elif mode == 'listAlphabet':
	listAlphabet(url)
elif mode == 'listShows':
	listShows(url)
elif mode == 'listEpisodes':
	listEpisodes(url, page)
elif mode == 'play_CODE':
	play_CODE(number)
elif mode == 'play_LIVE':
	play_LIVE(url)
else:
	index()