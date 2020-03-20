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
COUNTRY = addon.getSetting('sprache')
prefQUALITY = {'1280x720':720, '720x406':406, '640x360':360, '384x216':216}[addon.getSetting('prefVideoQuality')]
baseURL = "https://www.arte.tv/"
apiURL = "https://api-cdn.arte.tv/api/emac/v3/"+COUNTRY+"/web/"
OPA_token = "AOwImM4EGZ2gjYjRGZzEzYxMTNxMWOjJDO4gDO3UWN3UmN5IjNzAzMlRmMwEWM2I2NhFWN1kjYkJjZ1cjY1czN reraeB"
EMAC_token = "wYxYGNiBjNwQjZzIjMhRDOllDMwEjM2MDN3MjY4U2M1ATYkVWOkZTM5QzM4YzN2ITM0E2MxgDO1EjN5kjZmZWM reraeB"
headerOPA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0', 'Accept-Encoding': 'gzip, deflate', 'Authorization': '{}'.format(OPA_token[::-1])}
headerEMAC = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0', 'Accept-Encoding': 'gzip, deflate', 'Authorization': '{}'.format(EMAC_token[::-1])}
__HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0', 'Accept-Encoding': 'gzip, deflate'}

xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
xbmcplugin.setContent(int(sys.argv[1]), 'movies')

starting = {
    'highlights': apiURL+'data/MANUAL_TEASERS/?code=playlists_HOME&limit=50',
    'magazines': apiURL+'data/MANUAL_TEASERS/?code=magazines_HOME&limit=50',
    'byDate': apiURL+'pages/TV_GUIDE/?day=',
    'duration': apiURL+'data/VIDEO_LISTING/?videoType=',
    'viewed': apiURL+'data/VIDEO_LISTING/?videoType=MOST_VIEWED',
    'recent': apiURL+'data/VIDEO_LISTING/?videoType=MOST_RECENT',
    'chance': apiURL+'data/VIDEO_LISTING/?videoType=LAST_CHANCE',
    'search': apiURL+'data/SEARCH_LISTING/?'
}

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

def getUrl(url, method, allow_redirects=False, verify=False, stream=False, headers="", data="", timeout=30):
	response = requests.Session()
	if method == 'GET':
		content = response.get(url, allow_redirects=allow_redirects, verify=verify, stream=stream, headers=headers, data=data, timeout=timeout).text
	elif method == 'POST':
		content = response.post(url, data=data, allow_redirects=allow_redirects, verify=verify).text
	content = py2_enc(content)
	return content

def index():
	if COUNTRY=="de":
		addDir("Besondere Highlights", starting['highlights'], "listMagazines", icon)
		addDir("Themen", 'https://api.arte.tv/api/opa/v3/', "listThemes", icon)
		addDir("Sendungen A-Z", starting['magazines'], "listMagazines", icon)
		addDir("Programm sortiert nach Datum", "", "listSelection", icon)
		addDir("Videos sortiert nach Laufzeit", starting['duration'], "listRunTime", icon)
		addDir("Meistgesehen", starting['viewed'], "videos_AbisZ", icon)
		addDir("Neueste Videos", starting['recent'], "videos_AbisZ", icon)
		addDir("Letzte Chance", starting['chance'], "videos_AbisZ", icon)
		addDir("Suche ...", "", "SearchArte", icon)
		addDir("Live & Event TV", "", "liveTV", icon)
		addDir("ARTE Einstellungen", "", "aSettings", icon)
	elif COUNTRY=="fr":
		addDir("Faits saillants spéciaux", starting['highlights'], "listMagazines", icon)
		addDir("Sujets", 'https://api.arte.tv/api/opa/v3/', "listThemes", icon)
		addDir("Émissions A-Z", starting['magazines'], "listMagazines", icon)
		addDir("Programme trié par date", "", "listSelection", icon)
		addDir("Vidéos triées par durée", starting['duration'], "listRunTime", icon)
		addDir("Les plus vues", starting['viewed'], "videos_AbisZ", icon)
		addDir("Les plus récentes", starting['recent'], "videos_AbisZ", icon)
		addDir("Dernière chance", starting['chance'], "videos_AbisZ", icon)
		addDir("Recherche ...", "", "SearchArte", icon)
		addDir("ARTE Paramètres", "", "aSettings", icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def listThemes(url):
	debug("(listThemes) ------------------------------------------------ START = listThemes -----------------------------------------------")
	result = getUrl(url+'categories?language='+COUNTRY+'&limit=50', 'GET', False, False, False, headerOPA)
	debug("++++++++++++++++++++++++")
	debug("(listThemes) RESULT : {0}".format(str(result)))
	debug("++++++++++++++++++++++++")
	DATA = json.loads(result)
	for themeITEM in DATA['categories']:
		Cat = str(themeITEM['code'])
		title = py2_enc(themeITEM['label']).strip()
		tagline = ""
		if 'description' in themeITEM and themeITEM['description']:
			tagline = py2_enc(themeITEM['description']).strip()
		if title.lower() != 'andere':
			sublist = json.dumps(themeITEM['subcategories'])
			debug("(listThemes) ### NAME = {0} || CATEGORY = {1} ###".format(title, Cat))
			addDir(title, sublist, "listSubThemes", icon, tagline, query=Cat)
	xbmcplugin.endOfDirectory(pluginhandle)

def listSubThemes(Xurl, nomCat):
	debug("(listSubThemes) ------------------------------------------------ START = listSubThemes -----------------------------------------------")
	subcategories = json.loads(Xurl)
	debug("++++++++++++++++++++++++")
	debug("(listSubThemes) CONTENT : {0}".format(str(subcategories)))
	debug("++++++++++++++++++++++++")
	if nomCat == "ARS":
		addDir("* Alle Genres *", "Nothing", "videos_Themes", icon, query="VIDEO_LISTING/?category="+nomCat+"@videoType=MOST_RECENT")
	for subITEM in subcategories:
		subCat = str(subITEM['code'])
		title = py2_enc(subITEM['label']).strip()
		tagline = ""
		if 'description' in subITEM and subITEM['description']:
			tagline = py2_enc(subITEM['description']).strip()
		debug("(listSubThemes) ### CAT = {0} || subCAT = {1} || NAME = {2} ###".format(nomCat, subCat, title))
		# https://api-cdn.arte.tv/api/emac/v3/de/web/data/MOST_RECENT_SUBCATEGORY?subCategoryCode=AJO&page=2&limit=10
		addDir(title, "Nothing", "videos_Themes", icon, tagline, query="MOST_RECENT_SUBCATEGORY/?subCategoryCode="+subCat)
	xbmcplugin.endOfDirectory(pluginhandle) 

def listMagazines(url):
	debug("(listMagazines) ------------------------------------------------ START = listMagazines -----------------------------------------------")
	result = getUrl(url, 'GET', False, False, False, headerEMAC)
	debug("++++++++++++++++++++++++")
	debug("(listMagazines) RESULT : {0}".format(str(result)))
	debug("++++++++++++++++++++++++")
	DATA = json.loads(result)
	for magITEM in DATA['data']:
		if 'kind' in magITEM and 'isCollection' in magITEM['kind'] and magITEM['kind']['isCollection'] == False:
			duration = magITEM['duration']
			if duration and duration != "" and duration != "0":
				listVideo(magITEM, "", nosub='(listMagazines)')
		else:
			idd = str(magITEM['programId'])
			title = py2_enc(magITEM['title']).strip()
			plot = str(get_desc(magITEM))
			max_res = max(magITEM['images']['landscape']['resolutions'], key=lambda item: item['w'])
			thumb = max_res['url']
			newURL = magITEM['url']
			addDir(title, url, 'listCollections', thumb, plot=plot, query=idd)
			debug("(listMagazines) ready ### NAME = {0} || IDD = {1} ###".format(title, idd))
	xbmcplugin.endOfDirectory(pluginhandle)

def listCollections(Xurl, query, photo):
	COMBI = []
	prefer = ['collection_videos', 'collection_subcollection']
	result = getUrl(apiURL+query, 'GET', False, False, False, headerEMAC)
	debug("++++++++++++++++++++++++")
	debug("(listCollections) CONTENT : {0}".format(str(result)))
	debug("++++++++++++++++++++++++")
	DATA = json.loads(result)
	FOUND = 0
	FILTER = filter(lambda item: item['data'] and item['title'] != None and any(x in item['code']['name'].lower() for x in prefer), DATA['zones'])
	for zone in FILTER:
		title = py2_enc(zone['title']).strip()
		collection = zone['code']['name'].upper()
		idd = str(zone['code']['id'])
		text = "/?collectionId="+idd
		if collection == 'COLLECTION_SUBCOLLECTION': # ?collectionId=RC-014035&subCollectionId=RC-017486&page=2
			text = "/?collectionId="+idd.split('_')[0]+"@subCollectionId="+idd.split('_')[1]
		debug("(listCollections) ### NAME = {0} || COLLECTION = {1} || IDD = {2} ###".format(title, collection, idd))
		FOUND += 1
		COMBI.append([title, collection, text])
	if FOUND < 2:
		videos_Themes("Nothing", query=collection+text)
		debug("(listCollections) ----- Nothing FOUND - goto = videos_Themes -----")
	else:
		for title, collection, text in COMBI:
			addDir(title, "Nothing", "videos_Themes", photo, query=collection+text)
	xbmcplugin.endOfDirectory(pluginhandle) 

def videos_Themes(url, query, page="1"):
	debug("(videos_Themes) ------------------------------------------------ START = videos_Themes -----------------------------------------------")
	debug("(videos_Themes) ### URL : {0} || QUERY : {1} ###".format(url, query))
	FOUND = 0
	if int(page) == 1 and query != "":
		url = apiURL+'data/'+query.replace('@', '&')
	js_URL = url+'&page='+page+'&limit=50'
	debug("(videos_Themes) complete JSON-URL : {0}".format(js_URL))
	result = getUrl(js_URL, 'GET', False, False, False, headerEMAC)
	DATA = json.loads(result)
	for movie in DATA['data']:
		duration = movie['duration']
		if duration and duration != "" and duration != "0":
			FOUND += 1
			listVideo(movie, "", nosub='(videos_Themes)')
	# NEXTPAGE = https://api-cdn.arte.tv/api/emac/v3/de/web/data/COLLECTION_SUBCOLLECTION/?collectionId=RC-014035&subCollectionId=RC-015171&page=2&limit=20
	if ('MOST_RECENT' in query and FOUND > 49) or ('collectionId' in query and int(page) == 1 and FOUND > 11) or ('collectionId' in query and int(page) > 1 and FOUND > 9):
		debug("(videos_Themes) Now show NextPage ...")
		addDir("[COLOR lime]Nächste Seite  >>>[/COLOR]", url, "videos_Themes", icon, page=int(page)+1, query=query)
	xbmcplugin.endOfDirectory(pluginhandle)

def listSelection():
	i = -20
	while i <= 20:
		WU = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
		WT = (datetime.now() - timedelta(days=i)).strftime('%a~%d.%m.%Y')
		if COUNTRY=="de":
			MD = WT.split('~')[0].replace('Mon', 'Montag').replace('Tue', 'Dienstag').replace('Wed', 'Mittwoch').replace('Thu', 'Donnerstag').replace('Fri', 'Freitag').replace('Sat', 'Samstag').replace('Sun', 'Sonntag')
		elif COUNTRY=="fr":
			MD = WT.split('~')[0].replace('Mon', 'Lundi').replace('Tue', 'Mardi').replace('Wed', 'Mercredi').replace('Thu', 'Jeudi').replace('Fri', 'Vendredi').replace('Sat', 'Samedi').replace('Sun', 'Dimanche')
		if i == 0: addDir("[COLOR lime]"+WT.split('~')[1]+" | "+MD+"[/COLOR]", WU, 'videos_Datum', icon)
		else: addDir(WT.split('~')[1]+" | "+MD, WU, 'videos_Datum', icon)
		i += 1
	xbmcplugin.endOfDirectory(pluginhandle)

def videos_Datum(tag):
	debug("(videos_Datum) ------------------------------------------------ START = videos_Datum -----------------------------------------------")
	url = starting['byDate']+tag # URL-Tag = https://api-cdn.arte.tv/api/emac/v3/de/web/pages/TV_GUIDE/?day=2019-12-08
	debug("(videos_Datum) URL : {0}".format(url))
	result = getUrl(url, 'GET', False, False, False, headerEMAC)
	DATA = json.loads(result)
	for movie in DATA['zones'][-1]['data']:
		stickers = str(movie['stickers'])
		if "FULL_VIDEO" in stickers:
			listVideo(movie, "", nosub='(videos_Datum)')
	xbmcplugin.endOfDirectory(pluginhandle)

def listRunTime(url):
	debug("(listRunTime) ------------------------------------------------ START = listRunTime -----------------------------------------------")
	if COUNTRY=="de":
		addDir("Videos 0 bis 5 Min.", url, "videos_AbisZ", icon, query="SHORT_DURATION")
		addDir("Videos 5 bis 15 Min.", url, "videos_AbisZ", icon, query="MEDIUM_DURATION")
		addDir("Videos 15 bis 60 Min.", url, "videos_AbisZ", icon, query="LONG_DURATION")
		addDir("Videos > 60 Min.", url, "videos_AbisZ", icon, query="LONGER_DURATION")
	elif COUNTRY=="fr":
		addDir("Vidéos 0 à 5 min.", url, "videos_AbisZ", icon, query="SHORT_DURATION")
		addDir("Vidéos 5 à 15 min.", url, "videos_AbisZ", icon, query="MEDIUM_DURATION")
		addDir("Vidéos 15 à 60 min.", url, "videos_AbisZ", icon, query="LONG_DURATION")
		addDir("Vidéos > 60 min.", url, "videos_AbisZ", icon, query="LONGER_DURATION")
	xbmcplugin.endOfDirectory(pluginhandle)

def SearchArte():
	debug("(SearchArte) ------------------------------------------------ START = SearchArte -----------------------------------------------")
	word = xbmcgui.Dialog().input("Search ARTE ...", type=xbmcgui.INPUT_ALPHANUM)
	word = quote_plus(word, safe='') # SEARCH = https://api-cdn.arte.tv/api/emac/v3/de/web/data/SEARCH_LISTING/?query=b%C3%A4ren&page=1&limit=50
	if word == "": return
	videos_AbisZ(starting['search'], query='query='+word)
	xbmcplugin.endOfDirectory(pluginhandle)

def videos_AbisZ(url, query, page="1"):
	debug("(videos_AbisZ) ------------------------------------------------ START = videos_AbisZ -----------------------------------------------")
	debug("(videos_AbisZ) ### URL : {0} || QUERY : {1} ###".format(url, query))
	FOUND = 0
	if int(page) == 1 and (query != "" or '_LISTING' in url):
		url = url+query.replace('@', '&').replace(' ', '+')+'&page='+page+'&limit=50'
	# DURATION = https://api-cdn.arte.tv/api/emac/v3/de/web/data/VIDEO_LISTING/?videoType=LONGER_DURATION&page=2&limit=20 || SEARCH = https://api-cdn.arte.tv/api/emac/v3/de/web/data/SEARCH_LISTING/?query=europe&page=2&limit=20
	# STANDARD =  https://api-cdn.arte.tv/api/emac/v3/de/web/data/VIDEO_LISTING/?videoType=MOST_VIEWED&page=1&limit=20
	debug("(videos_AbisZ) complete JSON-URL : {0}".format(url))
	result = getUrl(url, 'GET', False, False, False, headerEMAC)
	DATA = json.loads(result)
	for movie in DATA['data']:
		duration = movie['duration']
		if duration and duration != "" and duration != "0":
			FOUND += 1
			listVideo(movie, "", nosub='(videos_AbisZ)')
	try: # NEXTPAGE = https://api-cdn.arte.tv/api/emac/v3/de/web/data/VIDEO_LISTING?videoType=LAST_CHANCE&page=2&limit=20
		nextpage = DATA["nextPage"]
		debug("(videos_AbisZ) This is NextPage : {0}".format(nextpage))
		if nextpage[:4] == "http":
			debug("(videos_AbisZ) Now show NextPage ...")
			addDir("[COLOR lime]Nächste Seite  >>>[/COLOR]", nextpage, "videos_AbisZ", icon, page=int(page)+1, query=query)
	except: pass
	xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url):
	debug("(playVideo) ------------------------------------------------ START = playVideo -----------------------------------------------")
	# Übergabe des Abspiellinks von anderem Video-ADDON: plugin://plugin.video.tyl0re.arte/?mode=playVideo&url=048256-000-A oder: plugin://plugin.video.tyl0re.arte/?mode=playVideo&url=https://www.arte.tv/de/videos/048256-000-A/wir-waren-koenige/
	DATA = {}
	DATA['media'] = []
	finalURL = False
	try:
		if url[:4] == "http": idd = re.compile('/videos/(.+?)/', re.DOTALL).findall(url)[0]
		else: idd = url
		debug("----->")
		debug("(playVideo) ### IDD : {0} ###".format(str(idd)))
		if COUNTRY=="de":
			SHORTCUTS = ['DE', 'OmU', 'OV', 'VO'] # "DE" = Original deutsch | "OmU" = Original mit deutschen Untertiteln | "OV" = Stumm oder Originalversion
		elif COUNTRY=="fr":
			SHORTCUTS = ['VOF', 'VF', 'VOSTF', 'VO'] # "VOF" = Original französisch | "VF" = französisch vertont | "VOSTF" = Stumm oder Original mit französischen Untertiteln
		content = getUrl('https://api.arte.tv/api/player/v1/config/'+COUNTRY+'/'+str(idd)+'?autostart=0&lifeCycle=1', 'GET', False, False, False, __HEADERS)
		stream = json.loads(content)['videoJsonPlayer']
		stream_offer = stream['VSR']
		for element in stream_offer:
			if int(stream['VSR'][element]['versionProg']) == 1 and stream['VSR'][element]['mediaType'].lower() == "mp4":
				debug("(playVideo) ### Stream-Element : {0} ###".format(str(stream['VSR'][element])))
				for found in SHORTCUTS:
					if stream['VSR'][element]['versionShortLibelle'] == found and stream['VSR'][element]['height'] == prefQUALITY:
						DATA['media'].append({'streamURL': stream['VSR'][element]['url']})
						finalURL = DATA['media'][0]['streamURL']
				if not finalURL:
					if stream['VSR'][element]['height'] == prefQUALITY:
						finalURL = stream['VSR'][element]['url']
		debug("(playVideo) ### Quality-Setting : {0} ###".format(str(prefQUALITY)))
		log("(playVideo) StreamURL : {0}".format(str(finalURL)))
		debug("<-----")
		if finalURL: 
			listitem = xbmcgui.ListItem(path=finalURL)
			listitem.setContentLookup(False)
			xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
		else: xbmcgui.Dialog().notification(addon.getAddonInfo('id')+" : [COLOR red]!!! STREAM - URL - ERROR !!![/COLOR]", "ERROR = [COLOR red]KEINE passende *Stream-Url* auf ARTE gefunden ![/COLOR]", xbmcgui.NOTIFICATION_ERROR, 6000)
	except: xbmcgui.Dialog().notification(addon.getAddonInfo('id')+" : [COLOR red]!!! VIDEO - URL - ERROR !!![/COLOR]", "ERROR = [COLOR red]Der übertragene *Video-Abspiel-Link* ist FEHLERHAFT ![/COLOR]", xbmcgui.NOTIFICATION_ERROR, 6000)

def playLive(url, name):
	listitem = xbmcgui.ListItem(path=url, label=name)  
	listitem.setMimeType('application/vnd.apple.mpegurl')
	xbmc.Player().play(item=url, listitem=listitem)

def liveTV():
	debug("(liveTV) ------------------------------------------------ START = liveTV -----------------------------------------------")
	items = []
	items.append(["ARTE-TV HD", "https://artelive-lh.akamaihd.net/i/artelive_de@393591/index_1_av-b.m3u8", icon])
	items.append(["ARTE Event 1", "https://arteevent01-lh.akamaihd.net/i/arte_event01@395110/index_1_av-b.m3u8", icon])
	items.append(["ARTE Event 2", "https://arteevent02-lh.akamaihd.net/i/arte_event02@308866/index_1_av-b.m3u8", icon])
	items.append(["ARTE Event 3", "https://arteevent03-lh.akamaihd.net/i/arte_event03@305298/index_1_av-b.m3u8", icon])
	items.append(["ARTE Event 4", "https://arteevent04-lh.akamaihd.net/i/arte_event04@308879/index_1_av-b.m3u8", icon])
	items.append(["ARTE Event 5", "https://arteevent05-lh.akamaihd.net/i/arte_event05@391593/index_1_av-b.m3u8", icon])
	for item in items:
		listitem = xbmcgui.ListItem(path=item[1], label=item[0])
		listitem.setArt({'icon': icon, 'thumb': item[2], 'poster': item[2], 'fanart': defaultFanart})
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sys.argv[0]+"?mode=playLive&url="+quote_plus(item[1])+"&name="+item[0], listitem=listitem)  
	xbmcplugin.endOfDirectory(pluginhandle)

def utc_to_local(dt):
	if time.localtime().tm_isdst: return dt - timedelta(seconds=time.altzone)
	else: return dt - timedelta(seconds=time.timezone)

def get_desc(info):
	if 'fullDescription' in info and info['fullDescription'] is not None: return py2_enc(info['fullDescription']).strip()
	elif 'description' in info and info['description'] is not None: return py2_enc(info['description']).strip()
	elif 'shortDescription' in info and info['shortDescription'] is not None: return py2_enc(info['shortDescription']).strip()
	return ""

def get_ListItem(info, nosub):
	seriesname = None
	tagline = None
	duration = None
	begins = None
	startTIMES = None
	endTIMES = None
	Note_1 = ""
	Note_2 = ""
	title = py2_enc(info['title']).strip()
	if 'subtitle' in info and info['subtitle']:
		title += " - {0}".format(py2_enc(info['subtitle']).strip())
	if 'teaserText' in info and info['teaserText']:
		tagline = py2_enc(info['teaserText']).strip()
	max_res = max(info['images']['landscape']['resolutions'], key=lambda item: item['w'])
	thumb = max_res['url']
	duration = info['duration']
	if 'broadcastDates' in info and info['broadcastDates']:
		airedtime = datetime(*(time.strptime(info['broadcastDates'][0], '%Y{0}%m{0}%dT%H{1}%M{1}%SZ'.format('-', ':'))[0:6])) # 2019-06-13T13:30:00Z
		LOCALTIME = utc_to_local(airedtime)
		title = "[COLOR orangered]{0}[/COLOR]  {1}".format(LOCALTIME.strftime('%H:%M'), title)
	if 'availability' in info and info['availability'] != None:
		if 'start' in info['availability'] and info['availability']['start']:
			startDates = datetime(*(time.strptime(info['availability']['start'][:19], '%Y{0}%m{0}%dT%H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2019-06-13T13:30:00Z
			LOCALstart = utc_to_local(startDates)
			startTIMES = LOCALstart.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
			begins =  LOCALstart.strftime('%d{0}%m{0}%Y').format('.')
		if 'end' in info['availability'] and info['availability']['end']:
			endDates = datetime(*(time.strptime(info['availability']['end'][:19], '%Y{0}%m{0}%dT%H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2020-05-30T21:59:00Z
			LOCALend = utc_to_local(endDates)
			endTIMES =  LOCALend.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
	if startTIMES: Note_1 = "Vom [COLOR chartreuse]{0}[/COLOR] ".format(str(startTIMES))
	if endTIMES: Note_2 = "bis [COLOR orangered]{0}[/COLOR][CR][CR]".format(str(endTIMES))
	if begins: xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_DATE)
	if duration: xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_DURATION)
	liz = xbmcgui.ListItem(title)
	ilabels = {}
	ilabels['Episode'] = None
	ilabels['Season'] = None
	ilabels['Tvshowtitle'] = seriesname
	ilabels['Title'] = title
	ilabels['Tagline'] = tagline
	ilabels['Plot'] = Note_1+Note_2+str(get_desc(info))
	ilabels['Duration'] = duration
	if begins != None:
		ilabels['Date'] = begins
	ilabels['Year'] = None
	ilabels['Genre'] = None
	ilabels['Director'] = None
	ilabels['Writer'] = None
	ilabels['Studio'] = 'ARTE'
	ilabels['Mpaa'] = None
	ilabels['Mediatype'] = 'video'
	liz.setInfo(type='Video', infoLabels=ilabels)
	liz.setArt({'icon': icon, 'thumb': thumb, 'poster': thumb, 'fanart': thumb})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	if nosub:
		debug(nosub+" ### Title = {0} ###".format(title))
		debug(nosub+" ### vidURL = {0} ###".format(info['url']))
		debug(nosub+" ### Duration = {0} ###".format(str(duration)))
		debug(nosub+" ### Thumb = {0} ###".format(thumb))
	return liz

def listVideo(info, mode=None, nosub=None):
	u = sys.argv[0]+"?mode=playVideo&url="+quote_plus(info['url'])
	liz = get_ListItem(info, nosub)
	if liz is None: return
	return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, tagline=None, plot=None, page=1, query=""):   
	u = '{0}?url={1}&mode={2}&query={3}&page={4}&image={5}'.format(sys.argv[0], quote_plus(url), str(mode), str(query), str(page), quote_plus(image))
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot, 'Tagline': tagline})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if image != icon: liz.setArt({'fanart': image})
	return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
page = unquote_plus(params.get('page', ''))
nosub = unquote_plus(params.get('nosub', ''))
query = unquote_plus(params.get('query', ''))

if mode == 'listThemes':
	listThemes(url)
elif mode == 'listSubThemes':
	listSubThemes(url, query)
elif mode == 'listMagazines':
	listMagazines(url)
elif mode == 'listCollections':
	listCollections(url, query, image)
elif mode == 'videos_Themes':
	videos_Themes(url, query, page)
elif mode == 'listSelection':
	listSelection()
elif mode == 'videos_Datum':
	videos_Datum(url)
elif mode == 'listRunTime':
	listRunTime(url)
elif mode == 'SearchArte':
	SearchArte()
elif mode == 'videos_AbisZ':
	videos_AbisZ(url, query, page)
elif mode == 'playVideo':
	playVideo(url)
elif mode == 'playLive':
	playLive(url, name)
elif mode == 'liveTV':
	liveTV()
elif mode == 'aSettings':
	addon.openSettings()
else:
	index()
