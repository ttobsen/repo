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
from datetime import datetime, date, timedelta


global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath    = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
temp           = xbmc.translatePath(os.path.join(dataPath, 'temp', '')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
COUNTRY = addon.getSetting('sprache')
prefQUALITY = {'1280x720':720, '720x406':406, '640x360':360, '384x216':216}[addon.getSetting('prefVideoQuality')]
baseURL = "https://www.arte.tv/"
apiURL = "https://www.arte.tv/guide/api/api"

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)

xbmcplugin.setContent(int(sys.argv[1]), 'movies')

if xbmcvfs.exists(temp) and os.path.isdir(temp):
	shutil.rmtree(temp, ignore_errors=True)
	xbmc.sleep(500)
xbmcvfs.mkdirs(temp)
cookie = os.path.join(temp, 'cookie.lwp')
cj = LWPCookieJar()

if xbmcvfs.exists(cookie):
	cj.load(cookie, ignore_discard=True, ignore_expires=True)

starting = {
    'selection': apiURL+'/zones/'+COUNTRY+'/playlists_HOME?limit=50',
    'byDate': apiURL+'/pages/'+COUNTRY+'/TV_GUIDE/?day=',
    'duration': apiURL+'/zones/'+COUNTRY+'/listing_DURATION',
    'magazines': apiURL+'/zones/'+COUNTRY+'/listing_MAGAZINES?page=1&limit=50',
    'viewed': apiURL+'/zones/'+COUNTRY+'/listing_MOST_VIEWED',
    'recent': apiURL+'/zones/'+COUNTRY+'/listing_MOST_RECENT',
    'chance': apiURL+'/zones/'+COUNTRY+'/listing_LAST_CHANCE',
    'search': apiURL+'/zones/'+COUNTRY+'/listing_SEARCH'
}

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

def debug(content):
	log(content, xbmc.LOGDEBUG)

def log(msg, level=xbmc.LOGNOTICE):
	msg = py2_enc(msg)
	xbmc.log("["+addon.getAddonInfo('id')+"-"+addon.getAddonInfo('version')+"]"+msg, level)

def getUrl(url, header=None, referer=None):
	global cj
	for cook in cj:
		debug("(getUrl) Cookie : "+str(cook))
	opener = build_opener(HTTPCookieProcessor(cj))
	try:
		if header:
			opener.addheaders = header
		else:
			opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36')]
		if referer:
			opener.addheaders = [('Referer', referer)]
		response = opener.open(url, timeout=30)
		content = py3_dec(response.read())
	except Exception as e:
		failure = str(e)
		if hasattr(e, 'code'):
			failing("(getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
		elif hasattr(e, 'reason'):
			failing("(getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
		content = ""
		return sys.exit(0)
	opener.close()
	try: cj.save(cookie, ignore_discard=True, ignore_expires=True)
	except: pass
	return content

def index():
	if COUNTRY=="de":
		addDir("Besondere Highlights", starting['selection'], "listMagazines", icon)
		addDir("Themen", baseURL+COUNTRY+"/", "listThemes", icon)
		addDir("Sendungen A-Z", starting['magazines'], "listMagazines", icon)
		addDir("Programm sortiert nach Datum", "", "listDatum", icon)
		addDir("Videos sortiert nach Laufzeit", starting['duration'], "listRunTime", icon)
		addDir("Meistgesehen", starting['viewed'], "videos_AbisZ", icon)
		addDir("Neueste Videos", starting['recent'], "videos_AbisZ", icon)
		addDir("Letzte Chance", starting['chance'], "videos_AbisZ", icon)
		addDir("Suche ...", "", "SearchArte", icon)
		addDir("Live & Event TV", "", "liveTV", icon)
		addDir("ARTE Einstellungen", "", "Settings", icon)
	elif COUNTRY=="fr":
		addDir("Faits saillants spéciaux", starting['selection'], "listMagazines", icon)
		addDir("Sujets", baseURL+COUNTRY+"/", "listThemes", icon)
		addDir("Émissions A-Z", starting['magazines'], "listMagazines", icon)
		addDir("Programme trié par date", "", "listDatum", icon)
		addDir("Vidéos triées par durée", starting['duration'], "listRunTime", icon)
		addDir("Les plus vues", starting['viewed'], "videos_AbisZ", icon)
		addDir("Les plus récentes", starting['recent'], "videos_AbisZ", icon)
		addDir("Dernière chance", starting['chance'], "videos_AbisZ", icon)
		addDir("Recherche ...", "", "SearchArte", icon)
		addDir("ARTE Paramètres", "", "Settings", icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def listMagazines(url):
	debug("(listMagazines) ------------------------------------------------ START = listMagazines -----------------------------------------------")
	result = getUrl(url)
	DATA = json.loads(result)
	for movie in DATA['data']:
		listVideo(movie, 'listCollections', nosub='(listMagazines)', query="collection_videos/?collectionId="+movie['programId'], ISF=True)
	xbmcplugin.endOfDirectory(pluginhandle)

def listThemes(url):
	debug("(listThemes) ------------------------------------------------ START = listThemes -----------------------------------------------")
	UN_Supported = ['360', 'Accue', 'Direct', 'Digitale', 'Edition', 'Guide', 'Home', 'Live', 'Magazin', 'productions', 'Programm', 'VOD/DVD']
	content = getUrl(url)
	content = re.compile(' window.__INITIAL_STATE__ = (.+?)window.__CLASS_IDS__ =', re.DOTALL).findall(content)[0].strip()[:-1]
	debug("++++++++++++++++++++++++")
	debug("(listSubThemes) CONTENT : "+str(content))
	debug("++++++++++++++++++++++++")
	DATA = json.loads(content)
	for themeITEM in DATA['categories']:
		Cat = str(themeITEM['code'])
		title = py2_enc(themeITEM['label'])
		newURL = themeITEM['url']
		tagline = ""
		if 'description' in themeITEM and themeITEM['description']:
			tagline = py2_enc(themeITEM['description'])
		if not any(x in title for x in UN_Supported):
			debug("(listThemes) filtered ### Name = {0} || Url = {1} ###".format(title, newURL))
			addDir(title, newURL, "listSubThemes", icon, tagline)
	xbmcplugin.endOfDirectory(pluginhandle)

def listSubThemes(Xurl):
	debug("(listSubThemes) ------------------------------------------------ START = listSubThemes -----------------------------------------------")
	COMBI = []
	content = getUrl(Xurl)
	content = re.compile(' window.__INITIAL_STATE__ = (.+?)window.__CLASS_IDS__ =', re.DOTALL).findall(content)[0].strip()[:-1]
	debug("++++++++++++++++++++++++")
	debug("(listSubThemes) CONTENT : "+str(content))
	debug("++++++++++++++++++++++++")
	DATA = json.loads(content)
	FOUND = 0
	for d in DATA['categories']:
		for subITEM in d['subcategories']:
			nomCat = str(d['code'])
			subCat = str(subITEM['code'])
			title = py2_enc(subITEM['label'])
			debug("(listSubThemes) ready ### CAT = {0} || subCAT = {1} || NAME = {2} ###".format(nomCat, subCat, title))
			newURL = subITEM['url']
			tagline = ""
			if 'description' in subITEM and subITEM['description']:
				tagline = py2_enc(subITEM['description'])
			if Xurl in newURL:
				debug("(listSubThemes) ready ### Name = {0} || Url = {1} ###".format(title, newURL))
				FOUND = 1
				COMBI.append([title, nomCat, subCat, newURL, tagline])
	if FOUND == 0:
		videos_Themes(Xurl)
		debug("(listSubThemes) ----- Nothing FOUND - goto = videos_Themes -----")
	else: # https://api-cdn.arte.tv/api/emac/v3/de/web/data/MOST_RECENT_SUBCATEGORY?mainZonePage=2&authorizedAreas=DE_FR%2CEUR_DE_FR%2CSAT%2CALL&subCategoryCode=AJO&page=2&limit=10
		for title, nomCat, subCat, newURL, tagline in COMBI: # listing_MOST_RECENT?page=2&limit=20&category=ARS&subcategories=MET
			if nomCat == "ARS" and FOUND == 1:
				FOUND += 1
				addDir("* Alle Genres *", "Nothing", "videos_Themes", icon, query="listing_MOST_RECENT/?category="+nomCat)
				addDir("Saison ARTE Opera", baseURL+COUNTRY+"/videos/RC-016485/saison-arte-opera/", "listCollections", icon, tagline, query="listing_MOST_RECENT/?category="+nomCat+"@subcategories="+subCat)
			addDir(title, "Nothing", "videos_Themes", icon, tagline, query="listing_MOST_RECENT/?category="+nomCat+"@subcategories="+subCat)
	xbmcplugin.endOfDirectory(pluginhandle) 

def listCollections(Xurl, query=""):
	COMBI = []
	content = getUrl(Xurl)
	content = re.compile(' window.__INITIAL_STATE__ = (.+?)window.__CLASS_IDS__ =', re.DOTALL).findall(content)[0].strip()[:-1]
	debug("++++++++++++++++++++++++")
	debug("(listSubThemes) CONTENT : "+str(content))
	debug("++++++++++++++++++++++++")
	subelement = json.loads(content)['pages']['list']
	FOUND = 0
	if PY2: makeITEMS = subelement.iteritems
	elif PY3: makeITEMS = subelement.items
	for key, value in makeITEMS():
		for zone in value['zones']:
			title = zone['title']
			collection = zone['code']['name']
			idd = str(zone['code']['id'])
			text = "/?collectionId="+idd
			if collection == 'collection_subcollection': # ?collectionId=RC-014035&subCollectionId=RC-017486&page=2
				text = "/?collectionId="+idd.split('_')[0]+"@subCollectionId="+idd.split('_')[1]
			debug("(listCollections) ### NAME = {0} || COLLECTION = {1} || IDD = {2} ###".format(title, collection, idd))
			if title != None and (collection == 'collection_videos' or collection == 'collection_subcollection'):
				FOUND += 1
				COMBI.append([title, collection, text])
	if FOUND < 2:
		videos_Themes("Nothing", query=query)
		debug("(listCollections) ----- Nothing FOUND - goto = videos_Themes -----")
	else:
		for title, collection, text in COMBI:
			addDir(title, "Nothing", "videos_Themes", icon, query=collection+text)
	xbmcplugin.endOfDirectory(pluginhandle) 

def videos_Themes(url, page="1", query=""):
	debug("(videos_Themes) ------------------------------------------------ START = videos_Themes -----------------------------------------------")
	debug("(videos_Themes) URL : "+url)
	SUPPORTED = ['Ausschnitt', 'Bonus', 'Live', 'Programm', 'Programme']
	category = False
	FOUND = 0
	if int(page) == 1:
		if url == "Nothing" and query != "":
			url = apiURL+"/zones/"+COUNTRY+"/"+query.replace('@', '&')
		else:
			content = getUrl(url)
			content = re.compile(' window.__INITIAL_STATE__ = (.+?)window.__CLASS_IDS__ =', re.DOTALL).findall(content)[0].strip()[:-1]
			debug("++++++++++++++++++++++++")
			debug("(videos_Themes) CONTENT : "+str(content))
			debug("++++++++++++++++++++++++")
			struktur = json.loads(content)
			sub1 = struktur["pages"]["list"]
			key = list(sub1)[0]
			sub2 = sub1[key]["zones"]
			for zone in sub2:
				try:
					debug("(videos_Themes) <ZONE-Supported> : "+zone["data"][0]["kind"]["label"])
					if any(x in zone["data"][0]["kind"]["label"] for x in SUPPORTED):
						debug("(videos_Themes) <ZONE-Category> : "+zone["code"]["name"])
						category = zone["code"]["name"].replace('highlights_subcategory', 'videos_subcategory').replace('collection_sublights', 'collection_videos')
						debug("(videos_Themes) <ZONE-ID> : "+zone["code"]["id"])
						idd = zone["code"]["id"]
						break
				except: pass
			# URL = https://www.arte.tv/guide/api/api/zones/de/videos_subcategory/?id=AJO&page=2&limit=10
			if category and query == "":
				url = apiURL+"/zones/"+COUNTRY+"/"+category+"/?id="+str(idd)
			else: return sys.exit(0)
	jsonurl = url+"&page="+page+"&limit=50"
	debug("(videos_Themes) complete JSON-URL : "+jsonurl)
	result = getUrl(jsonurl)
	DATA = json.loads(result)
	for movie in DATA['data']:
		duration = movie['duration']
		if duration and duration != "" and duration != "0":
			FOUND += 1
			listVideo(movie, "", nosub='(videos_Themes)')
	# NEXTPAGE = https://api-cdn.arte.tv/api/emac/v3/de/web/data/collection_subcollection/?collectionId=RC-014035&subCollectionId=RC-017486&page=2&limit=20
	if ('MOST_RECENT' in query and FOUND > 49) or ('collectionId' in query and int(page) == 1 and FOUND > 11) or ('collectionId' in query and int(page) > 1 and FOUND > 9):
		debug("(videos_Themes) Now show NextPage ...")
		addDir("[COLOR lime]Nächste Seite  >>>[/COLOR]", url, "videos_Themes", icon, page=int(page)+1, query=query)
	xbmcplugin.endOfDirectory(pluginhandle)

def listDatum():
	debug("(listDatum) ------------------------------------------------ START = listDatum -----------------------------------------------")
	if COUNTRY=="de":
		addDir("Zukunft", "-22", "datumSelect", icon)
		addDir("Vergangenheit", "22", "datumSelect", icon)
	elif COUNTRY=="fr":
		addDir("Avenir", "-22", "datumSelect", icon)
		addDir("Passé", "22", "datumSelect", icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def datumSelect(wert):
	debug("(datumSelect) ------------------------------------------------ START = datumSelect -----------------------------------------------")
	if int(wert) < 0:
		start = 0
		end = int(wert)
		sprung = -1
	elif int(wert) > 0:
		start = 0
		end = int(wert)
		sprung = 1
	for i in range(start, end, sprung):
		title = (date.today()-timedelta(days=i)).strftime('%d-%m-%Y')
		suche = (date.today()-timedelta(days=i)).strftime('%Y-%m-%d')
		addDir(title, suche, "videos_Datum", icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def videos_Datum(tag):
	debug("(videos_Datum) ------------------------------------------------ START = videos_Datum -----------------------------------------------")
	url = starting['byDate']+tag # URL-Tag = https://www.arte.tv/guide/api/api/pages/de/TV_GUIDE/?day=2018-08-14
	debug("(videos_Datum) URL : "+url)
	result = getUrl(url)
	DATA = json.loads(result)
	for movie in DATA['zones'][-1]['data']:
		stickers = str(movie['stickers'])
		if "FULL_VIDEO" in stickers:
			listVideo(movie, "", nosub='(videos_Datum)')
	xbmcplugin.endOfDirectory(pluginhandle)

def listRunTime(url):
	debug("(listRunTime) ------------------------------------------------ START = listRunTime -----------------------------------------------")
	if COUNTRY=="de":
		addDir("Videos 0 bis 5 Min.", url, "videos_AbisZ", icon, query="@maxDuration=5@minDuration=0")
		addDir("Videos 5 bis 15 Min.", url, "videos_AbisZ", icon, query="@maxDuration=15@minDuration=5")
		addDir("Videos 15 bis 60 Min.", url, "videos_AbisZ", icon, query="@maxDuration=60@minDuration=15")
		addDir("Videos > 60 Min.", url, "videos_AbisZ", icon, query="@minDuration=60")
	elif COUNTRY=="fr":
		addDir("Vidéos 0 à 5 min.", url, "videos_AbisZ", icon, query="@maxDuration=5@minDuration=0")
		addDir("Vidéos 5 à 15 min.", url, "videos_AbisZ", icon, query="@maxDuration=15@minDuration=5")
		addDir("Vidéos 15 à 60 min.", url, "videos_AbisZ", icon, query="@maxDuration=60@minDuration=15")
		addDir("Vidéos > 60 min.", url, "videos_AbisZ", icon, query="@minDuration=60")
	xbmcplugin.endOfDirectory(pluginhandle)

def SearchArte():
	debug("(SearchArte) ------------------------------------------------ START = SearchArte -----------------------------------------------")
	word = xbmcgui.Dialog().input("Search ARTE ...", type=xbmcgui.INPUT_ALPHANUM)
	word = quote_plus(word, safe='') #SEARCH = https://www.arte.tv/guide/api/api/zones/de/listing_SEARCH?page=1&limit=20&query=filme
	if word == "": return
	videos_AbisZ(starting['search'], query='@query='+word)
	xbmcplugin.endOfDirectory(pluginhandle)

def videos_AbisZ(url, page="1", query=""):
	debug("(videos_AbisZ) ------------------------------------------------ START = videos_AbisZ -----------------------------------------------")
	debug("(videos_AbisZ) URL : "+url+" || QUERY : "+query)
	FOUND = 0
	if query != "": # DURATION = https://www.arte.tv/guide/api/api/zones/de/listing_DURATION/?page=2&limit=20&maxDuration=5&minDuration=0 || SEARCH = https://www.arte.tv/guide/api/api/zones/de/listing_SEARCH/?page=2&limit=20&query=concert
		jsonurl = url+"?page="+page+"&limit=50"+query.replace("@", "&").replace(" ", "+")
	else: # STANDARD =  https://www.arte.tv/guide/api/api/zones/de/listing_MOST_VIEWED/?page=2&limit=20
		jsonurl = url+"?page="+page+"&limit=50"
	debug("(videos_AbisZ) complete JSON-URL : "+jsonurl)
	result = getUrl(jsonurl)
	DATA = json.loads(result)
	for movie in DATA['data']:
		duration = movie['duration']
		if duration and duration != "" and duration != "0":
			FOUND += 1
			listVideo(movie, "", nosub='(videos_AbisZ)')
	 # NEXTPAGE = https://api-cdn.arte.tv/api/emac/v3/de/web/data/VIDEO_LISTING?videoType=LAST_CHANCE&page=2&limit=20
	if FOUND > 49:
		debug("(videos_AbisZ) Now show NextPage ...")
		addDir("[COLOR lime]Nächste Seite  >>>[/COLOR]", url, "videos_AbisZ", icon, page=int(page)+1, query=query)
	xbmcplugin.endOfDirectory(pluginhandle)

def playvideo(url):
	debug("(playvideo) ------------------------------------------------ START = playvideo -----------------------------------------------")
	# Übergabe des Abspiellinks von anderem Video-ADDON: plugin://plugin.video.L0RE.arte/?mode=playvideo&url=048256-000-A oder: plugin://plugin.video.L0RE.arte/?mode=playvideo&url=https://www.arte.tv/de/videos/048256-000-A/wir-waren-koenige/
	DATA = {}
	DATA['media'] = []
	finalURL = False
	try:
		if url[:4] == "http": idd = re.compile('/videos/(.+?)/', re.DOTALL).findall(url)[0]
		else: idd = url
		debug("----->")
		debug("(playvideo) IDD : "+idd)
		if COUNTRY=="de":
			SHORTCUTS = ['DE', 'OmU', 'OV', 'VO'] # "DE" = Original deutsch | "OmU" = Original mit deutschen Untertiteln | "OV" = Stumm oder Originalversion
		elif COUNTRY=="fr":
			SHORTCUTS = ['VOF', 'VF', 'VOSTF', 'VO'] # "VOF" = Original französisch | "VF" = französisch vertont | "VOSTF" = Stumm oder Original mit französischen Untertiteln
		content = getUrl("https://api.arte.tv/api/player/v1/config/"+COUNTRY+"/"+idd+"?autostart=0&lifeCycle=1")
		stream = json.loads(content)['videoJsonPlayer']
		stream_offer = stream['VSR']
		for element in stream_offer:
			if int(stream['VSR'][element]['versionProg']) == 1 and stream['VSR'][element]['mediaType'].lower() == "mp4":
				debug("(playvideo) Stream-Element : "+str(stream['VSR'][element]))
				for found in SHORTCUTS:
					if stream['VSR'][element]['versionShortLibelle'] == found and stream['VSR'][element]['height'] == prefQUALITY:
						DATA['media'].append({'streamURL': stream['VSR'][element]['url']})
						finalURL = DATA['media'][0]['streamURL']
				if not finalURL:
					if stream['VSR'][element]['height'] == prefQUALITY:
						finalURL = stream['VSR'][element]['url']
		debug("(playvideo) Quality-Setting : "+str(prefQUALITY))
		log("(playvideo) StreamURL : "+str(finalURL))
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
	items.append(("ARTE-TV HD", "https://artelive-lh.akamaihd.net/i/artelive_de@393591/index_1_av-p.m3u8", icon))
	items.append(("ARTE Event 1", "https://arteevent01-lh.akamaihd.net/i/arte_event01@395110/index_1_av-p.m3u8", icon))
	items.append(("ARTE Event 2", "https://arteevent02-lh.akamaihd.net/i/arte_event02@308866/index_1_av-p.m3u8", icon))
	items.append(("ARTE Event 3", "https://arteevent03-lh.akamaihd.net/i/arte_event03@305298/index_1_av-p.m3u8", icon))
	items.append(("ARTE Event 4", "https://arteevent04-lh.akamaihd.net/i/arte_event04@308879/index_1_av-p.m3u8", icon))
	for item in items:
		listitem = xbmcgui.ListItem(path=item[1], label=item[0], iconImage=item[2], thumbnailImage=item[2])
		listitem.setArt({'fanart': defaultFanart})
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sys.argv[0]+"?mode=playLive&url="+quote_plus(item[1])+"&name="+item[0], listitem=listitem)  
	xbmcplugin.endOfDirectory(pluginhandle)

def utc_to_local(dt):
	if time.localtime().tm_isdst: return dt - timedelta(seconds=time.altzone)
	else: return dt - timedelta(seconds=time.timezone)

def get_desc(info):
	if 'fullDescription' in info and info['fullDescription'] is not None: return py2_enc(info['fullDescription'])
	elif 'description' in info and info['description'] is not None: return py2_enc(info['description'])
	elif 'shortDescription' in info and info['shortDescription'] is not None: return py2_enc(info['shortDescription'])
	return ""

def get_ListItem(info, nosub, ISF):
	seriesname = None
	tagline = None
	duration = None
	goDATE = None
	startTIMES = ""
	endTIMES = ""
	Note_1 = ""
	Note_2 = ""
	title = py2_enc(info['title'])
	if 'subtitle' in info and info['subtitle']:
		subtitle = py2_enc(info['subtitle'])
		title += " - "+subtitle
	if 'teaserText' in info and info['teaserText'] != None:
		tagline = py2_enc(info['teaserText'])
	max_res = max(info['images']['landscape']['resolutions'], key=lambda item: item['w'])
	thumb = max_res['url']
	duration = info['duration']
	if 'broadcastDates' in info and info['broadcastDates'][0] != None:
		airedtime = datetime(*(time.strptime(info['broadcastDates'][0], '%Y-%m-%dT%H:%M:%SZ')[0:6])) # 2019-06-13T13:30:00Z
		LOCALTIME = utc_to_local(airedtime)
		title = "[COLOR orangered]"+LOCALTIME.strftime('%H:%M')+"[/COLOR]  "+title
	if 'availability' in info and info['availability'] != None:
		if 'start' in info['availability'] and info['availability']['start'] != None:
			startDates = datetime(*(time.strptime(info['availability']['start'], '%Y-%m-%dT%H:%M:%SZ')[0:6])) # 2019-06-13T13:30:00Z
			LOCALstart = utc_to_local(startDates)
			startTIMES = LOCALstart.strftime('%d.%m.%y • %H:%M')
			goDATE =  LOCALstart.strftime('%d.%m.%Y')
		if 'end' in info['availability'] and info['availability']['end'] != None:
			endDates = datetime(*(time.strptime(info['availability']['end'], '%Y-%m-%dT%H:%M:%SZ')[0:6])) # 2020-05-30T21:59:00Z
			LOCALend = utc_to_local(endDates)
			endTIMES = LOCALend.strftime('%d.%m.%y • %H:%M')
	if startTIMES != "": Note_1 = "Vom [COLOR chartreuse]"+str(startTIMES)+"[/COLOR] "
	if endTIMES != "": Note_2 = "bis [COLOR orangered]"+str(endTIMES)+"[/COLOR][CR][CR]"
	if ISF == False and goDATE: xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
	if duration: xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DURATION)
	liz = xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=thumb)
	liz.setInfo(type='Video', infoLabels = {
		'Episode': None,
		'Season': None,
		'Tvshowtitle': seriesname,
		'Title': title,
		'Tagline': tagline,
		'Plot': Note_1+Note_2+str(get_desc(info)),
		'Duration': duration,
		'Date': goDATE,
		'Year': None,
		'Genre': None,
		'Director': None,
		'Writer': None,
		'Studio': 'ARTE',
		'Mpaa': None,
		'Mediatype': 'video'
	})
	liz.setArt({'poster': thumb, 'fanart': thumb})
	if ISF == False:
		liz.addStreamInfo('Video', {'Duration': duration})
		liz.setProperty('IsPlayable', 'true')
	if nosub !=  "":
		debug(nosub+" ### Title = {0} ###".format(title))
		debug(nosub+" ### vidURL = {0} ###".format(info['url']))
		debug(nosub+" ### Duration = {0} ###".format(duration))
		debug(nosub+" ### Thumb = {0} ###".format(thumb))
	return liz

def listVideo(info, mode=None, page=1, nosub="", query="", ISF=False):
	if ISF == False:
		u = sys.argv[0]+"?mode=playvideo&url="+quote_plus(info['url'])
	else:
		u = sys.argv[0]+"?url="+quote_plus(info['url'])+"&mode="+str(mode)+"&page="+str(page)+"&query="+str(query)
	liz = get_ListItem(info, nosub, ISF)
	if liz is None: return
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=ISF)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, tagline=None, page=1, query=""):   
	u = sys.argv[0]+"?url="+quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)+"&query="+str(query)
	liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=image)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Tagline': tagline})
	liz.setArt({'fanart': defaultFanart})
	if image != icon: liz.setArt({'fanart': image})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
page = unquote_plus(params.get('page', ''))
nosub = unquote_plus(params.get('nosub', ''))
query = unquote_plus(params.get('query', ''))
referer = unquote_plus(params.get('referer', ''))

if mode == 'listThemes':
	listThemes(url)
elif mode == 'listSubThemes':
	listSubThemes(url)
elif mode == 'listMagazines':
	listMagazines(url)
elif mode == 'listCollections':
	listCollections(url, query)
elif mode == 'videos_Themes':
	videos_Themes(url, page, query)
elif mode == 'listDatum':
	listDatum()
elif mode == 'datumSelect':
	datumSelect(url)
elif mode == 'videos_Datum':
	videos_Datum(url)
elif mode == 'listRunTime':
	listRunTime(url)
elif mode == 'SearchArte':
	SearchArte()
elif mode == 'videos_AbisZ':
	videos_AbisZ(url, page, query)
elif mode == 'playvideo':
	playvideo(url)
elif mode == 'playLive':
	playLive(url, name)
elif mode == 'liveTV':
	liveTV()
elif mode == 'Settings':
	addon.openSettings()
else:
	index()
