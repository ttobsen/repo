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
	from HTMLParser import HTMLParser  # Python 2.X
	try: import StorageServer
	except: from resources.lib import storageserverdummy as StorageServer
elif PY3:
	from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode  # Python 3+
	from html.parser import HTMLParser  # Python 3+
import json
import xbmcvfs
import shutil
import socket
import time
import random
import requests
try:
	from requests.packages.urllib3.exceptions import InsecureRequestWarning
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except: pass


global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
socket.setdefaulttimeout(40)
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
artpic = os.path.join(addonPath, 'resources', 'media', '').encode('utf-8').decode('utf-8')
preferredStreamType = addon.getSetting('streamSelection')
preferPlayTechnique = addon.getSetting('play_technique')
showCompleteEPISODES = addon.getSetting('show.all_episodes') == 'true'
showStreamMESSAGE = addon.getSetting('show.stream_message') == 'true'
if PY2:
	cachePERIOD = int(addon.getSetting('cacherhythm'))
	cache = StorageServer.StorageServer(addon.getAddonInfo('id'), cachePERIOD) # (Your plugin name, Cache time in hours)
baseURL = "https://www.atv.at"
startURL = "https://www.atv.at/"

__HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0','Accept-Encoding': 'gzip, deflate'}
headerFIELDS = "User-Agent=Mozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F67.0.3396.62%20Safari%2F537.36"

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

def cleanTEXT(s, encoding='utf-8'):
	parser = HTMLParser()
	s = s.replace("  ", " ").encode(encoding).decode(encoding)
	return parser.unescape(s)

def translation(id):
	return py2_enc(addon.getLocalizedString(id))

def failing(content):
	log(content, xbmc.LOGERROR)

def debug(content):
	log(content, xbmc.LOGDEBUG)

def log(msg, level=xbmc.LOGNOTICE):
	xbmc.log("["+addon.getAddonInfo('id')+"-"+addon.getAddonInfo('version')+"]"+py2_enc(msg), level)

def makeREQUEST(url):
	if PY2:
		INQUIRE = cache.cacheFunction(getUrl, url, 'GET', False, False, __HEADERS)
	elif PY3:
		INQUIRE = getUrl(url, 'GET', False, False, __HEADERS)
	return INQUIRE

def getUrl(url, method, allow_redirects=False, verify=False, headers="", data="", timeout=40):
	response = requests.Session()
	if method == 'GET':
		content = response.get(url, allow_redirects=allow_redirects, verify=verify, headers=headers, data=data, timeout=timeout).text
	elif method == 'POST':
		content = response.post(url, data=data, allow_redirects=allow_redirects, verify=verify).text
	return content

def clearCache():
	debug("(clearCache) -------------------------------------------------- START = clearCache --------------------------------------------------")
	if PY2:
		debug("(clearCache) ========== Lösche jetzt den Addon-Cache ==========")
		cache.delete('%')
		xbmc.sleep(1000)
		xbmcgui.Dialog().ok(addon.getAddonInfo('id'), translation(30501))
	elif PY3:
		Python_Version = str(sys.version).split(')')[0].strip()+')'
		failing("(clearCache) ACHTUNG : ... Die installierte PYTHONVERSION : *** "+str(Python_Version)+" *** ist nicht kompatibel !!!\n##### Das Löschen des Cache wird ABGEBROCHEN und Die Cachefunktion wird DEAKTIVIERT !!! #####")
		xbmcgui.Dialog().ok(addon.getAddonInfo('id'), translation(30502).format(Python_Version))

def index():
	addDir(translation(30601), baseURL+"/mediathek/", 'listSeries', icon)
	if PY2: addDir(translation(30602).format(str(cachePERIOD)), "", 'clearCache', icon)
	addDir(translation(30603), "", 'aSettings', icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def USER_from_austria():
	try:
		return 'window.is_not_geo_ip_blocked = true' in requests.get('https://videos.atv.cdn.tvnext.tv/blocked/detect.js', headers=__HEADERS, verify=True, timeout=30).text
	except:
		return False

def listSeries(url):
	count = 0
	pos1 = 0
	html = makeREQUEST(url)
	clusters = re.findall('<li class="program">(.*?)</li>', html, re.DOTALL)
	for cluster in clusters:
		if '<div class="video_indicator">' in cluster:
			try:
				url2 = re.compile('href="([^"]+?)"', re.DOTALL).findall(cluster)[0]
				img = re.compile('<img src="(.*?)teaser_image_file(.*?)" alt=', re.DOTALL).findall(cluster)
				pic1 = img[0][0]
				pic2 = img[0][1]
				if (pic1.startswith('https://static.atv.cdn.tvnext.tv/dynamic/get_asset_resized.php') or pic1.startswith('https://atv.at/dynamic/get_asset_resized.php') or pic1.startswith('https://www.atv.at/dynamic/get_asset_resized.php')) and 'path=format_pages%252F' in pic1:
					thumb = baseURL+"/static/assets/cms/format_pages/teaser_image_file"+pic2.split('&amp;percent')[0].replace('%252F', '/')
				else:
					thumb = artpic+"empty.jpg"
				title = re.compile('<h3 class="program_title">([^<]+?)</h3>', re.DOTALL).findall(cluster)[0]
				title = cleanTEXT(title)
				debug("(listSeries) ##### Url2 : "+url2+" ##### Titel : "+title+" #####")
				addDir(title, url2, "listCluster", thumb)
			except:
				pos1 += 1
				failing("(listSeries) Error-in-Series : "+str(cluster))
				if pos1 > 1 and count == 0:
					count += 1
					xbmcgui.Dialog().notification(translation(30521).format('DISPLAY'), translation(30522), icon, 8000)
	xbmcplugin.endOfDirectory(pluginhandle)

def listCluster(url, photo):
	if url[:4] != "http":
		url = baseURL+url
	html = makeREQUEST(url)
	if not listSeasons(html, photo):
		listVideos(html)
	xbmcplugin.endOfDirectory(pluginhandle)

def listSeasons(html, photo):
	index_seasons = html.find('<select class="select jsb_ jsb_Select" data-jsb=')
	if index_seasons != -1:
		seasons_block = html[index_seasons:html.find('</select>', index_seasons)]
		seasons = re.findall('<option.*?value="(.*?)">(.*?)</option>', seasons_block, re.DOTALL)
		for url2, title in seasons:
			title = cleanTEXT(title)
			debug("(listSeasons) ##### Url2 : "+url2+" ##### Titel : "+title+" #####")
			addDir(title, url2, "listEpisodes", photo)
		return True
	return False

def listEpisodes(url):
	if url[:4] != "http":
		url = baseURL+url
	html = makeREQUEST(url)
	listVideos(html)
	xbmcplugin.endOfDirectory(pluginhandle)

def listVideos(html):
	videoIsolated_List1 = set()
	videoIsolated_List2 = set()
	count = 0
	pos1 = 0
	pos2 = 0
	videos_2 = re.findall('<li class="teaser">(.*?)</li>', html, re.DOTALL)
	try:
		tvshowtitle = re.compile('<h3 class="title uppercase one_line">.+?">(.*?)</a></h3>', re.DOTALL).findall(html)[0].strip()
		seriesname = cleanTEXT(tvshowtitle)
	except: seriesname = ""
	try: 
		desc = re.compile('<h2 class="title">(.*?)<div class="mod_teasers four all_rows jsb_ jsb_ExpandableTeaser"', re.DOTALL).findall(html)[0]
		desc = "- "+desc.split('</h2>')[0]+' -\n'+desc.split('</h2>')[1].split('</div>')[0]
		plot = re.sub('\<.*?\>', '', desc)
		plot = cleanTEXT(plot)
	except: plot = ""
	idNumber = "##### Alle Episoden auf einer Seite - Nicht eingeschaltet ! #####"
	if showCompleteEPISODES:
		index_VideoID = html.find('<div class="more jsb_ jsb_MoreTeasersButton" data-jsb="')
		if index_VideoID != -1:
			url_get_ID = html[index_VideoID + 55:html.find('"', index_VideoID + 55)]
			if url_get_ID.startswith('url='):
				url_get_ID = url_get_ID[4:]
			idNumber = url_get_ID.replace('%3A', ':').replace('%2F', '/').replace('%3F', '?').replace('%3D', '=').replace(baseURL+'/uri/fepe/', '').split('/')[0].strip()
		else: idNumber = "##### ID - Nicht gefunden ! #####"
	debug("(listVideos[1]) idNumber : "+str(idNumber))
	pageNumber = int(1)
	if not "#####" in idNumber:
		while pageNumber < int(13):
			urlVideos_1 = baseURL+"/uri/fepe/"+idNumber+"/?page="+str(pageNumber)
			content = makeREQUEST(urlVideos_1)
			debug("(listVideos[1]) ##### urlVideos_1 : "+urlVideos_1+" #####")
			if '<div class="more jsb_ jsb_MoreTeasersButton" data-jsb="' in content:
				pageNumber += int(1)
			else:
				pageNumber += int(12)
			videos_1 = re.findall('<li class="teaser">(.*?)</li>', content, re.DOTALL)
			for video in videos_1:
				if '<div class="video_indicator">' in video:
					try:
						url = re.compile('href="([^"]+?)" ', re.DOTALL).findall(video)[0]
						img = re.compile('<img src="(.*?)teaser_image_file(.*?)" width=', re.DOTALL).findall(video)
						pic1 = img[0][0]
						pic2 = img[0][1]
						if (pic1.startswith('https://static.atv.cdn.tvnext.tv/dynamic/get_asset_resized.php') or pic1.startswith('https://atv.at/dynamic/get_asset_resized.php') or pic1.startswith('https://www.atv.at/dynamic/get_asset_resized.php')):
							if 'path=detail_pages%252F' in pic1:
								thumb = baseURL+"/static/assets/cms/detail_pages/teaser_image_file"+pic2.split('&amp;percent')[0].replace('%252F', '/')
							elif 'path=media_items%252F' in pic1:
								thumb = baseURL+"/static/assets/cms/media_items/teaser_image_file"+pic2.split('&amp;percent')[0].replace('%252F', '/')
						else:
							thumb = pic1+'teaser_image_file'+pic2.split('?cb=')[0]
						title = re.compile('class="title">([^<]+?)</', re.DOTALL).findall(video)[0]
						title = cleanTEXT(title)
						season = ""
						episode = ""
						if "staffel-" in url:
							try: season = url.split(startURL)[1].split('staffel-')[-1].split('/')[0].strip() # https://www.atv.at/bauer-sucht-frau-staffel-14/die-hofwochen-folge-12/d1958945/
							except: season = ""
						if "folge-" in url:
							try: episode = url.split(startURL)[1].split('folge-')[-1].split('/')[0].split('-')[0].strip() # https://www.atv.at/bauer-sucht-frau-staffel-2/folge-13/v1642204/
							except: episode = ""
						if "episode-" in url and episode=="":
							try: episode = url.split(startURL)[1].split('episode-')[-1].split('/')[0].split('-')[0].strip() # https://www.atv.at/bauer-sucht-frau-staffel-3/episode-14-event-teil-1/v1640552/
							except: episode = ""
						if url in videoIsolated_List1:
							continue
						videoIsolated_List1.add(url)
						debug("(listVideos[1]) ##### Serie : "+seriesname+" #####")
						debug("(listVideos[1]) ##### Titel : "+title+" #####")
						debug("(listVideos[1]) ##### Season : "+str(season)+" / Episode : "+str(episode)+" #####")
						debug("(listVideos[1]) ##### Thumb : "+thumb+" #####")
						addLink(title, url, "playVideo", thumb, plot, seriesname, season, episode)
					except:
						pos1 += 1
						failing("(listVideos[1]) Error-in-Video-1 : "+str(video))
						if pos1 > 1 and count == 0:
							count += 1
							xbmcgui.Dialog().notification(translation(30521).format('DISPLAY'), translation(30522), icon, 8000)
	if videos_2 !="":
		for video in videos_2:
			if '<div class="video_indicator">' in video:
				try:
					url = re.compile('href="([^"]+?)" ', re.DOTALL).findall(video)[0]
					img = re.compile('<img src="(.*?)teaser_image_file(.*?)" width=', re.DOTALL).findall(video)
					pic1 = img[0][0]
					pic2 = img[0][1]
					if (pic1.startswith('https://static.atv.cdn.tvnext.tv/dynamic/get_asset_resized.php') or pic1.startswith('https://atv.at/dynamic/get_asset_resized.php') or pic1.startswith('https://www.atv.at/dynamic/get_asset_resized.php')):
						if 'path=detail_pages%252F' in pic1:
							thumb = baseURL+"/static/assets/cms/detail_pages/teaser_image_file"+pic2.split('&amp;percent')[0].replace('%252F', '/')
						elif 'path=media_items%252F' in pic1:
							thumb = baseURL+"/static/assets/cms/media_items/teaser_image_file"+pic2.split('&amp;percent')[0].replace('%252F', '/')
					else:
						thumb = pic1+'teaser_image_file'+pic2.split('?cb=')[0]
					title = re.compile('class="title">([^<]+?)</', re.DOTALL).findall(video)[0]
					title = cleanTEXT(title)
					season = ""
					episode = ""
					if "staffel-" in url:
						try: season = url.split(startURL)[1].split('staffel-')[-1].split('/')[0].strip() # https://www.atv.at/bauer-sucht-frau-staffel-14/die-hofwochen-folge-12/d1958945/
						except: season = ""
					if "folge-" in url:
						try: episode = url.split(startURL)[1].split('folge-')[-1].split('/')[0].split('-')[0].strip() # https://www.atv.at/bauer-sucht-frau-staffel-2/folge-13/v1642204/
						except: episode = ""
					if "episode-" in url and episode=="":
						try: episode = url.split(startURL)[1].split('episode-')[-1].split('/')[0].split('-')[0].strip() # https://www.atv.at/bauer-sucht-frau-staffel-3/episode-14-event-teil-1/v1640552/
						except: episode = ""
					Wanted = url.split(startURL)[1].split('/')[0][:6]
					debug("(list_videos[2]) ##### Wanted-URL : "+Wanted+" #####")
					if (url in videoIsolated_List1 or 'aufruf' in url.lower() or not Wanted in url):
						continue
					if url in videoIsolated_List2:
						continue
					videoIsolated_List2.add(url)
					debug("(listVideos[2]) ##### Serie : "+seriesname+" #####")
					debug("(listVideos[2]) ##### Titel : "+title+" #####")
					debug("(listVideos[2]) ##### Season : "+str(season)+" / Episode : "+str(episode)+" #####")
					debug("(listVideos[2]) ##### Thumb : "+thumb+" #####")
					addLink(title, url, "playVideo", thumb, plot, seriesname, season, episode)
				except:
					pos2 += 1
					failing("(listVideos[2]) Error-in-Video-2 : "+str(video))
					if pos2 > 1 and count == 0:
						count += 1
						xbmcgui.Dialog().notification(translation(30521).format('DISPLAY'), translation(30522), icon, 8000)
	# now look for more videos button
	if "#####" in idNumber:
		index_more_videos = html.find('<div class="more jsb_ jsb_MoreTeasersButton" data-jsb="')
		if index_more_videos != -1:
			url_more_videos = html[index_more_videos + 55:html.find('"', index_more_videos + 55)]
			if url_more_videos.startswith('url='):
				url_more_videos = url_more_videos[4:]
			url_more_videos = unquote_plus(url_more_videos)
			debug("(listVideos[3]) ##### url_more_videos : "+url_more_videos+" #####")
			addDir(translation(30604), url_more_videos, "listEpisodes", artpic+"nextpage.png")

def playVideo(url, photo):
	videoIsolated_M3U8 = set()
	videoIsolated_MP4 = set()
	book = []
	COMBINATION_1 = []
	COMBINATION_2 = []
	ASSEMBLY = []
	firstURL = ""
	found_M3U8 = 0
	found_MP4 = 0
	number_M3U8 = 0
	number_MP4 = 0
	pos_M3U8 = ""
	pos_MP4 = ""
	M3U8_Url = ""
	MP4_Old = ""
	ENDnum_MP4 = ""
	MP4_Url = ""
	count1 = 0
	count2 = 0
	pos2 = 0
	lastCODE = ('_2.mp4', '_3.mp4', '_4.mp4', '_5.mp4', '_6.mp4', '_7.mp4', '_8.mp4', '_9.mp4')
	html = getUrl(url, 'GET', False, False, __HEADERS)
	try: 
		desc = re.compile('<div class="js_expandable">.+?<p[^>]*>(.*?)</p>', re.DOTALL).findall(html)[0]
		plot = re.sub('\<.*?\>', '', desc)
		plot = cleanTEXT(plot)
	except: plot = ""
	match = re.search('class="jsb_video/VideoPlaylist" data-jsb="(.*?)">', html)
	if match:
		content = cleanTEXT(match.group(1))
		DATA = json.loads(content)
		parts = DATA['videos'][0]['parts']
		geoblocked_parts = 0
		single_videoURL = False
		for part in parts:
			videotitle = part['tracking']['nurago']['videotitle'].replace('_', ' ').strip() # Bauer sucht Frau Die Hofwochen - Folge 5
			tvshowtitle = part['tracking']['nurago']['programname'].strip() # Bauer sucht Frau
			title = part['tracking']['nurago']['episodename'].strip() # Folge 14 - Die Hofwochen
			NRS_title = part['title'].strip() # Die Hofwochen - Folge 5 1/7
			season = ""
			episode = ""
			if part['tracking']['nurago']['seasonid'] and part['tracking']['nurago']['seasonid'] !="":
				try: season = part['tracking']['nurago']['seasonid'].strip() # 14
				except: season = ""
			if part['tracking']['nurago']['clipreferer'] and "staffel-" in part['tracking']['nurago']['clipreferer'] and season=="":
				try: season = part['tracking']['nurago']['clipreferer'].split(startURL)[1].split('staffel-')[-1].split('/')[0].strip() # https://www.atv.at/bauer-sucht-frau-staffel-14/die-hofwochen-folge-12/d1958945/
				except: season = ""
			if part['tracking']['nurago']['episodename'] and "Folge " in part['tracking']['nurago']['episodename']:
				try: episode = part['tracking']['nurago']['episodename'].split('Folge')[1].split('-')[0].split(':')[0].strip() # Folge 14 - Die Hofwochen
				except: episode = ""
			if part['tracking']['nurago']['episodename'] and "Episode " in part['tracking']['nurago']['episodename'] and episode=="":
				try: episode = part['tracking']['nurago']['episodename'].split('Episode')[1].split('-')[0].split(',')[0].strip() # Episode 2
				except: episode = ""
			if part['tracking']['nurago']['clipreferer'] and ("folge-" in part['tracking']['nurago']['clipreferer'] or "episode-" in part['tracking']['nurago']['clipreferer']) and episode=="":
				try: episode = part['tracking']['nurago']['clipreferer'].split(startURL)[1].split('folge-')[-1].split('episode-')[-1].split('/')[0].strip() # https://www.atv.at/bauer-sucht-frau-staffel-14/die-hofwochen-folge-12/d1958945/
				except: episode = ""
			duration = int(part['tracking']['nurago']['videoduration']) # 1250
			thumb = part['preview_image_url'].split('?cb=')[0].strip() # https://static.atv.cdn.tvnext.tv/static/assets/cms/media_items/teaser_image_file/1930300.jpg
			if not videotitle in book and count1 < 1:
				count1 += 1
				log("(playVideo[1]) -------------------- VideoTitel : "+videotitle+" --------------------")
			debug("(playVideo[1]) ##### Serie : "+tvshowtitle+" #####")
			debug("(playVideo[1]) ##### Titel : "+title+" #####")
			debug("(playVideo[1]) ##### Season : "+str(season)+" / Episode : "+str(episode)+" #####")
			debug("(playVideo[1]) ##### Dauer (seconds) : "+str(duration)+" #####")
			debug("(playVideo[1]) ##### Thumb : "+thumb+" #####")
			if part['is_geo_ip_blocked'] and part['is_geo_ip_blocked'] == True:
				geoblocked_parts += 1
			M3U8_Part = part['sources'][0]['src']
			if not M3U8_Part:
				continue
			if M3U8_Part:
				if M3U8_Part in videoIsolated_M3U8:
					continue
				videoIsolated_M3U8.add(M3U8_Part)
				number_M3U8 += 1
				pos_M3U8 = str(number_M3U8)+': '
				debug("(playVideo[1]) ##### M3U8_Part : "+M3U8_Part+" #####")
				if not "chunklist" in M3U8_Part:
					try:
						bestQuality = getUrl(M3U8_Part, "GET", False, False, __HEADERS)
						newM3U8 = re.compile('(https?://.*?.m3u8)', re.DOTALL).findall(bestQuality)[0].replace('blocked-', '')
						M3U8_Url = newM3U8
						found_M3U8 += 1
					except: pass
				else:
					M3U8_Url = M3U8_Part
					found_M3U8 += 1
			else:
				number_M3U8 += 1
				pos_M3U8 = str(number_M3U8)+': '
				debug("(playVideo[1]) -------------------- M3U8_Url : KEINE passende ~m3u8~ gefunden !!! --------------------")
			MP4_Part = part['sources'][1]['src'].replace('blocked-', '')
			if not MP4_Part:
				continue
			if MP4_Part:
				if any(x in MP4_Part for x in lastCODE):
					firstURL = MP4_Part[:-6]
				elif MP4_Part.startswith('https://multiscreen.atv.cdn.tvnext.tv'):
					firstURL = MP4_Part.split('.mp4')[0]
				if MP4_Part in videoIsolated_MP4:
					continue
				videoIsolated_MP4.add(MP4_Part)
				number_MP4 += 1
				pos_MP4 = str(number_MP4)+': '
				MP4_Old = str(pos_MP4)+MP4_Part
				ENDnum_MP4 = str(pos_MP4).split(':')[0]
				debug("(playVideo[1]) ##### MP4_Part : "+MP4_Part+" #####")
			else:
				number_MP4 += 1
				pos_MP4 = str(number_MP4)+': '
				debug("(playVideo[1]) -------------------- MP4_Url : KEINE passende ~mp4~ gefunden !!! --------------------")
			COMBINATION_1.append([pos_MP4, MP4_Old, ENDnum_MP4, pos_M3U8, M3U8_Url, videotitle, tvshowtitle, title, NRS_title, season, episode, photo, thumb, duration])
		for pos_MP4, MP4_Old, ENDnum_MP4, pos_M3U8, M3U8_Url, videotitle, tvshowtitle, title, NRS_title, season, episode, photo, thumb, duration in COMBINATION_1:
			if MP4_Old[:8] == "1: rtsp:" and "https://multiscreen.atv.cdn.tvnext.tv" in firstURL:
				debug("(playVideo[2]) ##### MP4_Old-1 [1: rtsp:] : "+MP4_Old+" #####")
				MP4_Url = firstURL+".mp4"
				found_MP4 += 1
			elif MP4_Old[:8] != "1: rtsp:" and "rtsp://" in MP4_Old and "https://multiscreen.atv.cdn.tvnext.tv" in firstURL:
				debug("(playVideo[2]) ##### MP4_Old-2 [rtsp://] : "+MP4_Old+" #####")
				MP4_Url = firstURL+"_"+ENDnum_MP4+".mp4"
				found_MP4 += 1
			elif not "rtsp:" in MP4_Old and "https://multiscreen.atv.cdn.tvnext.tv" in firstURL:
				MP4_Url = MP4_Old.split(': ')[1]
				found_MP4 += 1
			COMBINATION_2.append([pos_MP4, MP4_Url, pos_M3U8, M3U8_Url, videotitle, tvshowtitle, title, NRS_title, season, episode, photo, thumb, duration])
		for pos_MP4, MP4_Url, pos_M3U8, M3U8_Url, videotitle, tvshowtitle, title, NRS_title, season, episode, photo, thumb, duration in COMBINATION_2:
			MP4_Video = str(pos_MP4)+MP4_Url
			M3U8_Video = str(pos_M3U8)+M3U8_Url
			#log("(playVideo[3]) Video  -  MP4 = "+MP4_Video)
			#log("(playVideo[3]) Video - M3U8 = "+M3U8_Video)
			if (firstURL == ""  or preferredStreamType == "1" or found_MP4 != len(parts)) and M3U8_Url != "" and found_M3U8 == len(parts):
				single_videoURL = M3U8_Url
			elif (M3U8_Url == "" or preferredStreamType == "0" or found_M3U8 != len(parts)) and MP4_Url != "" and found_MP4 == len(parts):
				single_videoURL = MP4_Url
			ASSEMBLY.append([single_videoURL, tvshowtitle, title, NRS_title, season, episode, plot, photo, thumb, duration])
		if geoblocked_parts == len(parts) and not USER_from_austria():
			log("(playVideo[3]) Falsche IP ##### DIESE STREAMS SIND LEIDER NUR MIT EINER IP-ADRESSE IN ÖSTERREICH VERFÜGBAR #####")
			return xbmcgui.Dialog().notification(translation(30523), translation(30524), icon, 10000)
		log("(playVideo[3]) FIND  -   MP4 = "+str(found_MP4)+" - Streams")
		log("(playVideo[3]) FIND -  M3U8 = "+str(found_M3U8)+" - Streams")
		if single_videoURL and (found_M3U8 == len(parts) or found_MP4 == len(parts)):
			PL = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
			combined_videoURL = ""
			pos_LISTE = 0
			if preferPlayTechnique == "1" and showStreamMESSAGE:
				xbmcgui.Dialog().notification(translation(30527), translation(30528).format(title), icon, 5000)
				xbmc.sleep(500)
			for single_videoURL, tvshowtitle, title, NRS_title, season, episode, plot, photo, thumb, duration in ASSEMBLY:
				pos_LISTE += 1
				combined_videoURL += single_videoURL+" , "
				if preferPlayTechnique == "0" or preferPlayTechnique == "1":
					stacked_videoURL = 'stack://'+combined_videoURL[:-3]
					listitem = xbmcgui.ListItem(path=stacked_videoURL)
					listitem.setInfo(type="Video", infoLabels={'TVShowTitle': tvshowtitle, 'Title': title, 'Season': season, 'Episode': episode, 'Plot': plot, 'Duration': duration, 'Studio': 'ATV.at', 'Genre': 'Unterhaltung', 'mediatype': 'episode'})
					listitem.setArt({'thumb': photo, 'poster': photo, 'fanart': photo})
					listitem.setMimeType("mime/x-type")
				if preferPlayTechnique == "2":
					NRS_title = '[COLOR chartreuse]'+NRS_title+'[/COLOR]' # Die Hofwochen - Folge 5 1/7
					listitem = xbmcgui.ListItem(title)
					listitem.setInfo(type="Video", infoLabels={'TVShowTitle': tvshowtitle, 'Title': NRS_title, 'Season': season, 'Episode': episode, 'Plot': plot, 'Duration': duration, 'Studio': 'ATV.at', 'Genre': 'Unterhaltung', 'mediatype': 'episode'})
					listitem.setArt({'thumb': thumb, 'poster': thumb, 'fanart': thumb}) # Episode-Bild = wechselnd für jeden Videopart
					xbmc.sleep(50)
					PL.add(url=single_videoURL, listitem=listitem, index=pos_LISTE)
			if preferPlayTechnique == "0":
				log("(playSTANDARD-1) combined_videoURL : "+combined_videoURL)
				log("(playSTANDARD-1) -------------------- Meldung: *Standard-Abspielen [1]* in den Settings eingestellt --------------------")
				xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
			if preferPlayTechnique == "1":
				log("(playSTANDARD-2) combined_videoURL : "+combined_videoURL)
				log("(playSTANDARD-2) -------------------- Meldung: *Standard-Abspielen [2]* in den Settings eingestellt --------------------")
				xbmc.Player().play(item=stacked_videoURL, listitem=listitem)
			if preferPlayTechnique == "2":
				log("(playPLAYLIST-3) combined_videoURL : "+combined_videoURL)
				log("(playPLAYLIST-3) -------------------- Meldung: Nur *Playliste-Abspielen [3]* in den Settings eingestellt --------------------")
				return PL
		else:
			return xbmcgui.Dialog().notification(translation(30525), translation(30526), icon, 10000)
	else:
		return xbmcgui.Dialog().notification(translation(30525), translation(30526), icon, 10000)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addLink(name, url, mode, image, plot=None, seriesname=None, season=None, episode=None, duration=None, genre=None, year=None, begins=None):
	u = sys.argv[0]+'?url='+quote_plus(url)+'&image='+quote_plus(image)+'&mode='+str(mode)
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
	ilabels['Genre'] = 'Unterhaltung'
	ilabels['Director'] = None
	ilabels['Writer'] = None
	ilabels['Studio'] = 'ATV.at'
	ilabels['Mpaa'] = None
	ilabels['Mediatype'] = 'episode'
	liz.setInfo(type='Video', infoLabels=ilabels)
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if image != icon and not artpic in image:
		liz.setArt({'fanart': image})
	liz.addStreamInfo('Video', {'Duration': duration})
	if preferPlayTechnique == "0" or preferPlayTechnique == "2":
		liz.setProperty('IsPlayable', 'true')
		liz.setContentLookup(False)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

def addDir(name, url, mode, image, plot=None):
	u = sys.argv[0]+'?url='+quote_plus(url)+'&image='+quote_plus(image)+'&mode='+str(mode)
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if image != icon and not artpic in image:
		liz.setArt({'fanart': image})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))

if mode == 'aSettings':
	addon.openSettings()
elif mode == 'clearCache':
	clearCache()
elif mode == 'listSeries':
	listSeries(url)
elif mode == 'listCluster':
	listCluster(url, image)
elif mode == 'listEpisodes':
	listEpisodes(url)
elif mode == 'playVideo':
	playVideo(url, image)
else:
	index()