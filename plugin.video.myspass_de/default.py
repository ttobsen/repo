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
import ssl

try: _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context


global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
temp        = xbmc.translatePath(os.path.join(dataPath, 'temp', '')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
baseURL = "https://www.myspass.de"

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

def getUrl(url, header=None, agent='Dalvik/2.1.0 (Linux; U; Android 7.1.2;)'):
	opener = build_opener()
	opener.addheaders = [('User-Agent', agent), ('Accept-Encoding', 'gzip, identity')]
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
	return content

def index():
	addDir('Home', 'http://m.myspass.de/api/index.php?command=hometeaser', 'listVideos', icon)
	addDir('Ganze Folgen', 'http://m.myspass.de/api/index.php?command=formats', 'listShows', icon)
	addDir('Shows A-Z', 'http://m.myspass.de/api/index.php?command=azformats', 'listShows', icon)
	addDir('Beliebteste', 'http://m.myspass.de/api/index.php?command=favourite', 'listVideos', icon)
	addDir('Neueste', 'http://m.myspass.de/api/index.php?command=latest&length=30', 'listVideos', icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def listShows(url):
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	debug("(listShows) ------------------------------------------------ START = listShows -----------------------------------------------")
	debug("(listShows) ### URL : {0} ###".format(url))
	content = getUrl(url)
	DATA = json.loads(content) 
	for element in DATA['data']:
		name = element['format'].replace('fÃ¼r das JÃ¶rg', 'für das Jörg')
		plot = element['format_description']
		idd = str(element['format_id'])
		logo = 'http:'+element['latestVideo']['original_image'].replace('\/', '/')
		debug("(listShows) XXX TITLE = {0} | IDD = {1} | LOGO = {2} XXX".format(str(name), idd, str(logo)))
		if 'media/images' in logo:
			addDir(name, 'http://m.myspass.de/api/index.php?command=seasonslist&id='+idd, 'listSeasons', logo, plot)
	xbmcplugin.endOfDirectory(pluginhandle)

def listSeasons(url):
	debug("(listSeasons) ------------------------------------------------ START = listSeasons -----------------------------------------------")
	debug("(listSeasons) ### URL : {0} ###".format(url))
	content = getUrl(url)
	DATA = json.loads(content) 
	for element in DATA['data']:
		name = element['season_name']
		if name == '1': name = 'Staffel 1'
		plot = element['season_description']
		idd = str(element['season_id'])
		logo = 'http:'+element['latestVideo']['original_image'].replace('\/', '/')
		debug("(listSeasons) XXX TITLE = {0} | IDD = {1} | LOGO = {2} XXX".format(str(name), idd, str(logo)))
		if name != 'Trailer':
			addDir(name, 'http://m.myspass.de/api/index.php?command=seasonepisodes&id='+idd, 'listVideos', logo, plot)
	xbmcplugin.endOfDirectory(pluginhandle)

def listVideos(url):
	debug("(listVideos) ------------------------------------------------ START = listVideos -----------------------------------------------")
	debug("(listVideos) ### URL : {0} ###".format(url))
	workList = ""
	firstURL = url
	try:
		content = getUrl(url)
		DATA = json.loads(content)
	except: return xbmcgui.Dialog().notification('[COLOR red]Leider gibt es KEINE Einträge :[/COLOR]', '* [COLOR blue]In dieser Rubrik[/COLOR] * bei Myspass.de', icon, 8000)
	for element in DATA['data']:
		seriesname = element['format'].replace('fÃ¼r das JÃ¶rg', 'für das Jörg')
		title = element['title']
		if 'Teil 2' in title or 'Teil 3' in title: continue
		idd = str(element['unique_id'])
		if 'command=hometeaser' in firstURL:
			element = element['video']
		image = 'http:'+element['original_image'].replace('\/', '/')
		duration2 = ""
		vidURL2 = ""
		duration3 = ""
		vidURL3 = ""
		if 'Teil 1' in title:
			try:
				searchURL = element['myspass_url'].replace('\/', '/').replace('/myspass/', '/')
				header = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36'), ('Accept-Encoding', 'gzip, identity')]
				html = getUrl(searchURL, header=header)
				if 'www.myspass.de' in searchURL and '-Teil-' in searchURL: shortURL = searchURL.split('www.myspass.de')[1].split('-Teil-')[0]
				else: shortURL = searchURL
				content_2 = html[html.find('<table class="listView--table">')+1:]
				content_2 = content_2[:content_2.find('</table>')]
				match = re.compile('data-id="(.+?)".*?<a href="(.+?)">', re.DOTALL).findall(content_2)
				for newIDD, url2 in match:
					if shortURL in url2 and 'Teil-2' in url2:
						content_3 = getUrl('http://m.myspass.de/api/index.php?command=video&id='+str(newIDD))
						DATA_2 = json.loads(content_3)
						duration2 = DATA_2['data']['play_length']
						vidURL2 = "@@"+DATA_2['data']['video_url'].replace('\/', '/').replace('http://c11021-osu.p.core.cdn.streamfarm.net/', 'https://cldf-od.r53.cdn.tv1.eu/')
					if shortURL in url2 and 'Teil-3' in url2:
						content_4 = getUrl('http://m.myspass.de/api/index.php?command=video&id='+str(newIDD))
						DATA_3 = json.loads(content_4)
						duration3 = DATA_3['data']['play_length']
						vidURL3 = "@@"+DATA_3['data']['video_url'].replace('\/', '/').replace('http://c11021-osu.p.core.cdn.streamfarm.net/', 'https://cldf-od.r53.cdn.tv1.eu/')
			except: pass
		startDATES = None
		Note_1 = ""
		Note_2 = ""
		if "broadcast_date" in element and element['broadcast_date'] != "" and element['broadcast_date'] != None:
			try:
				airedtime = datetime(*(time.strptime(element['broadcast_date'], '%Y-%m-%d')[0:6])) # 2019-06-13
				startDATES =  airedtime.strftime('%d.%m.%Y')
			except: pass
		if startDATES and not '1970' in startDATES: Note_1 = "Sendung vom "+str(startDATES)+"[CR][CR]"
		if "teaser_text" in element and element['teaser_text'] != "" and element['teaser_text'] != None:
			Note_2 = element['teaser_text']
		plot = Note_1+Note_2
		season = str(element['season_number']).zfill(2)
		episode = str(element['episode_nr'])
		if episode.startswith('00'): episode = episode.replace('00', '0')
		episode = episode.zfill(2)
		vidURL = element['video_url'].replace('\/', '/').replace('http://c11021-osu.p.core.cdn.streamfarm.net/', 'https://cldf-od.r53.cdn.tv1.eu/')
		if vidURL2 != "": vidURL = vidURL+vidURL2
		if vidURL3 != "": vidURL = vidURL+vidURL3
		duration = element['play_length']
		if duration2 != "": duration = int(duration)+int(duration2)
		if duration3 != "": duration = int(duration)+int(duration3)
		name = "[COLOR chartreuse]S"+season+"E"+episode+":[/COLOR]  "+title.split('- Teil')[0].split(' Teil')[0]
		if 'hometeaser' in firstURL or 'favourite' in firstURL or 'latest&length' in firstURL:
			name = "[COLOR chartreuse]S"+season+"E"+episode+":[/COLOR]  "+seriesname+" - "+title.split('- Teil')[0].split(' Teil')[0]
		seq = idd+"###"+vidURL+"###"+seriesname+"###"+name+"###"+image+"###"+plot+"###"+str(duration)+"###"+str(season)+"###"+str(episode)+"###"
		workList = workList+seq.replace('\n', ' ').encode('utf-8')+'\n'
		listitem = xbmcgui.ListItem(path=sys.argv[0]+'?number='+idd+'&mode=play_CODE')
		listitem.setInfo(type='Video', infoLabels={'Tvshowtitle': seriesname, 'Title': name, 'Season': season, 'Episode': episode, 'Plot': plot, 'Duration': duration, 'Studio': 'myspass.de', 'Genre': 'Unterhaltung', 'mediatype': 'episode'})
		listitem.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
		if image != icon:
			listitem.setArt({'fanart': image})
		listitem.addStreamInfo('Video', {'Duration':duration})
		listitem.setProperty('IsPlayable', 'true')
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sys.argv[0]+'?number='+idd+'&mode=play_CODE', listitem=listitem)
	with open(os.path.join(dataPath, 'episode_data.txt'), 'w') as input:
		input.write(workList)
		debug("(listVideos) XXX workList : {0} XXX".format(str(workList)))
	xbmcplugin.endOfDirectory(pluginhandle)
 
def play_CODE(idd):
	debug("(play_CODE) ------------------------------------------------ START = play_CODE -----------------------------------------------")
	debug("(play_CODE) ### IDD : {0} ###".format(str(idd)))
	pos_LISTE = 0
	Special = False
	PL = xbmc.PlayList(1)
	with open(os.path.join(dataPath, 'episode_data.txt'), 'r') as output:
		sequence = output.read().split('\n')
		for seq in sequence:
			field = seq.split('###')
			if field[0]==idd:
				endURL = field[1]
				seriesname = field[2]
				title = field[3]
				try: title = title.split(':[/COLOR]')[1].strip()
				except: pass
				try: title = title.split(seriesname+" -")[1].strip()
				except: pass
				image = field[4]
				plot = field[5] 
				duration = field[6]
				season = field[7]
				episode = field[8]
				if '@@' in endURL:
					Special = True
					videoURL = endURL.split('@@')
					complete = '/2'
					if len(videoURL) == 3:
						complete = '/3'
					for single in videoURL:
						log("(play_CODE) Playlist : {0} ".format(str(single)))
						pos_LISTE += 1
						NRS_title = title+"[COLOR chartreuse]  TEIL "+str(pos_LISTE)+complete+"[/COLOR]"
						listitem = xbmcgui.ListItem(title)
						listitem.setInfo(type='Video', infoLabels={'Tvshowtitle': seriesname, 'Title': NRS_title, 'Season': season, 'Episode': episode, 'Plot': plot, 'Duration': duration, 'Studio': 'myspass.de', 'Genre': 'Unterhaltung', 'mediatype': 'episode'})
						listitem.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': image})
						xbmc.sleep(50)
						PL.add(url=single, listitem=listitem, index=pos_LISTE)
				else:
					log("(play_CODE) Streamurl : {0} ".format(str(endURL)))
					listitem = xbmcgui.ListItem(path=endURL)
					listitem.setInfo(type='Video', infoLabels={'Tvshowtitle': seriesname, 'Title': title, 'Season': season, 'Episode': episode, 'Plot': plot, 'Duration': duration, 'Studio': 'myspass.de', 'Genre': 'Unterhaltung', 'mediatype': 'episode'})
					listitem.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': image})
	if Special:
		return PL
	else:
		xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, plot=None):
	u = sys.argv[0]+'?url='+quote_plus(url)+'&mode='+str(mode)
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if image != icon:
		liz.setArt({'fanart': image})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

params = parameters_string_to_dict(sys.argv[2])
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
number = unquote_plus(params.get('number', ''))

if mode == 'listShows':
	listShows(url)
elif mode == 'listSeasons':
	listSeasons(url)
elif mode == 'listVideos':
	listVideos(url)
elif mode == 'play_CODE':
	play_CODE(number)
else:
	index()