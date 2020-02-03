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
	from urllib import quote, unquote, quote_plus, unquote_plus, urlencode, urlretrieve  # Python 2.X
	from urllib2 import Request, urlopen  # Python 2.X
elif PY3:
	from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode  # Python 3+
	from urllib.request import Request, urlopen, urlretrieve  # Python 3+
import json
import xbmcvfs
import shutil
import socket
import time
import io
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
dataPath = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
targetDir = xbmc.translatePath(os.path.join(addon.getSetting('download_path')))
useThumbAsFanart = addon.getSetting('useThumbAsFanart') == 'true'
baseYT = 'https://www.youtube.com/list_ajax?style=json&action_get_list=1&list='
baseURL = 'https://massengeschmack.tv'

__HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0','Accept-Encoding': 'gzip, deflate'}
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

def convert_duration(SECS):
	match = re.match('^(\d+):(\d+):(\d+)$', SECS)
	if match is None: return None
	ret = 0
	for group, factor in enumerate([60, 60, 1], 1):
		ret = factor * (ret + int(match.group(group)))
	return ret

def failing(content):
	log(content, xbmc.LOGERROR)

def debug(content):
	log(content, xbmc.LOGDEBUG)

def log(msg, level=xbmc.LOGNOTICE):
	xbmc.log("["+addon.getAddonInfo('id')+"-"+addon.getAddonInfo('version')+"]"+py2_enc(str(msg)), level)

def getUrl(url, method, allow_redirects=False, verify=False, stream=False, headers="", data="", timeout=40):
	response = requests.Session()
	if method == 'GET':
		content = response.get(url, allow_redirects=allow_redirects, verify=verify, stream=stream, headers=headers, data=data, timeout=timeout)
	elif method == 'POST':
		content = response.post(url, data=data, allow_redirects=allow_redirects, verify=verify).text
	return content

def index():
	if targetDir != '': addDir(translation(30621), '', 'listing', icon)
	addDir(translation(30601), baseURL+'/mag/1', "shows", icon)
	addDir(translation(30602), baseYT+'UUj089h5WsDdh1q8t54K3ZCw', 'YOUT_channel', icon)
	addDir(translation(30603), baseYT+'PLqh6lroBRtJ2s-Qchjp4Th4UdjeUnvZEZ', 'YOUT_channel', icon)
	addDir(translation(30604), baseYT+'PLqh6lroBRtJ3hsqfybfFBwA9Q34er0cqq', 'YOUT_channel', icon)
	addDir(translation(30605), baseYT+'PLqh6lroBRtJ1IMXNJphxxrng9cDc9I52S', 'YOUT_channel', icon)
	addDir(translation(30606), baseYT+'PLqh6lroBRtJ1MCHW4qv6jI0tvcJ9KWRaa', 'YOUT_channel', icon)
	addDir(translation(30607), baseYT+'PLqh6lroBRtJ0QXyvHlCc2Q-7rB5E0tNjS', 'YOUT_channel', icon)
	addDir(translation(30608), baseYT+'PLqh6lroBRtJ1b6at_tZBLWX5mgQZfwH9x', 'YOUT_channel', icon)
	addDir(translation(30609), baseYT+'PLqh6lroBRtJ2s7TYjZvf_Pzo0BkRRaRyO', 'YOUT_channel', icon)
	addDir(translation(30610), baseYT+'PLqh6lroBRtJ3TGilJSiLloC_sb75Taeq7', 'YOUT_channel', icon)
	addDir(translation(30611), baseYT+'PLqh6lroBRtJ0VtaJKNb8RBW0EIC0AAaVz', 'YOUT_channel', icon)
	addDir(translation(30612), baseYT+'PLqh6lroBRtJ2zjUQe3He-qkIk6oHL-AVT', 'YOUT_channel', icon)
	addDir(translation(30613), baseYT+'PLqh6lroBRtJ37ha_85phsaNuqleodCUK7', 'YOUT_channel', icon)
	addDir(translation(30614), baseYT+'PLqh6lroBRtJ3yp06m-JJ2Hgc_mL4n86Hm', 'YOUT_channel', icon)
	addDir(translation(30615), baseYT+'PLqh6lroBRtJ0Ew2inhQE7OEPdUirdYsNH', 'YOUT_channel', icon)
	addDir(translation(30616), baseYT+'PLqh6lroBRtJ1XWSjrAmVX1hAmWqYY4VCn', 'YOUT_channel', icon)
	addDir(translation(30617), baseYT+'PLqh6lroBRtJ2LoCcoJ3lGzLorDVQFo5_t', 'YOUT_channel', icon)
	addDir(translation(30618), baseYT+'PLqh6lroBRtJ2kUtgvYWQoJwKcgWqIT49-', 'YOUT_channel', icon)
	addDir(translation(30619), baseYT+'PLqh6lroBRtJ1zvG4KPm0edK78s8aLsDRh', 'YOUT_channel', icon)
	addDir(translation(30620), baseYT+'PLqh6lroBRtJ22STc80jUwywSwhLiqY7po', 'YOUT_channel', icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def shows(url):
	debug("(shows) -------------------------------------------------- START = shows --------------------------------------------------")
	html = getUrl(url, 'GET', False, False, False, __HEADERS).text
	content = html[html.find('<ul class="nav navbar-nav">')+1:]
	content = content[:content.find('<li><a href="https://forum.massengeschmack.tv/">Forum</a>')]
	spl = content.split('<li')
	for i in range(1, len(spl), 1):
		entry = spl[i]
		selection = re.findall(r'<a href="([^"]+?)">([^<]+?)</a></li>', entry, re.S)
		for endURL, name in selection:
			endURL = py2_enc(baseURL+endURL)
			name = _clean(name)
			debug("(shows) ### endURL : {0} ### NAME : {1} ###".format(str(url), str(name)))
			if not 'Live' in name:
				addDir(name, endURL, "episodes", icon, origSERIE=name)
	xbmcplugin.endOfDirectory(pluginhandle)

def episodes(url ,origSERIE):
	debug("(episodes) -------------------------------------------------- START = episodes --------------------------------------------------")
	COMBI = []
	content = getUrl(url, 'GET', False, False, False, __HEADERS).text
	PID = re.compile('MAG_PID = ([0-9]+?);', re.DOTALL).findall(content)[0]
	SID = re.compile('MAG_SPID = ([0-9]+?);', re.DOTALL).findall(content)[0]   
	pageNUMBER = 1
	total = 1
	maximum = 100
	while (total > 0):
		JS_url = baseURL+'/api/api_p.php?action=getFeed&from=[{0}]&contentType=[{1}]&limit={2}&page={3}'.format(str(PID), str(SID), str(maximum), str(pageNUMBER))
		response = getUrl(JS_url, 'GET', False, False, False, __HEADERS).text
		DATA = json.loads(response)
		for item in DATA['eps']:
			debug("(episodes) ##### FOLGE : {0} #####".format(str(item)))
			video = baseURL+'/play/'+item['identifier']
			title = _clean(item['title'])
			episode = ""
			if 'enum' in item and item['enum'] != "" and item['enum'] != None:
				episode = item['enum']
			if 'img' in item and item['img'] != "" and item['img'] != None:
				logo = item['img']
			plot = origSERIE+'[CR][CR]'
			if 'desc' in item and item['desc'] != "" and item['desc'] != None:
				plot += _clean(item['desc'])
			duration = ""
			if 'duration' in item and item['duration'] != "" and item['duration'] != None:
				duration = convert_duration(item['duration'])
			subscribed = item['subscribed']
			COMBI.append([episode, video, logo, title, plot, duration, origSERIE, subscribed])
			if episode != "": COMBI = sorted(COMBI, key=lambda num:num[0], reverse=True)
		try:
			total = DATA['pages'] - pageNUMBER
		except: total = 0
		pageNUMBER += 1
		xbmc.sleep(2000)
	if COMBI and total == 0:
		for episode, video, logo, title, plot, duration, origSERIE, subscribed in COMBI:
			if subscribed == True:
				addLink(title, video, 'playVideo', logo, plot, duration, episode, origSERIE=origSERIE, nosub='DIRECTstream')
	xbmcplugin.endOfDirectory(pluginhandle)

def YOUT_channel(url):
	debug("(YOUT_channel) -------------------------------------------------- START = YOUT_channel --------------------------------------------------")
	debug("(YOUT_channel) ### URL = {0} ###".format(url))
	response = getUrl(url, 'GET', False, False, False, __HEADERS).text
	DATA = json.loads(response)
	for item in DATA['video']:
		debug("(YOUT_channel) ##### FOLGE : {0} #####".format(str(item)))
		title = _clean(item['title'])
		plot =""
		if 'added' in item and item['added'] !="" and item['added'] != None:
			plot = '[COLOR yellow]'+str(item['added'])+'[/COLOR][CR]'
		if 'description' in item and item['description'] !="" and item['description'] != None:
			plot += _clean(item['description'])
		try: photo = item['thumbnail'].replace('/default.jpg', '/maxresdefault.jpg')
		except: photo = ""
		videoId = ""
		if 'encrypted_id' in item and item['encrypted_id'] !="" and item['encrypted_id'] != None:
			videoId = str(item['encrypted_id'])
		duration = ""
		if 'length_seconds' in item and item['length_seconds'] !="" and item['length_seconds'] != None:
			duration = item['length_seconds']
		rating = ""
		if 'rating' in item and item['rating'] !="" and item['rating'] != None:
			rating = str(item['rating'])
		votes = ""
		if 'likes' in item and item['likes'] !="" and item['likes'] != None:
			votes = str(item['likes'])
		addLink(title, videoId, 'playVideo', photo, plot, duration, rating, votes, nosub='YTstream')
	xbmcplugin.endOfDirectory(pluginhandle)

def getVideo(url):
	debug("(getVideo) -------------------------------------------------- START = getVideo --------------------------------------------------")
	content = getUrl(url, 'GET', False, False, False, __HEADERS).text
	debug("++++++++++++++++++++++++")
	debug("(getVideo) XXXXX CONTENT : {0} XXXXX".format(str(content)))
	debug("++++++++++++++++++++++++")
	match1 = re.findall('<li><a href="(//massengeschmack.+?)"><span class="glyphicon glyphicon-film"', content, re.S)
	match2 = re.findall('type: "video/mp4", src: "([^"]+)"', content, re.S)
	if match1:
		return 'http:'+match1[0]
	elif match2:
		return match2[0]
	else:
		return xbmcgui.Dialog().notification(translation(30521).format('PLAY'), translation(30522), icon, 8000)

def MULTI_download(*args):
	from threading import Thread
	threads = []
	thread = Thread(target=getDownload, args=args)
	if hasattr(thread, 'daemon'): thread.daemon = True
	else: thread.setDaemon()
	threads.append(thread)
	for thread in threads: thread.start()

def getDownload(param):
	debug("(getDownload) -------------------------------------------------- START = getDownload --------------------------------------------------")
	now = str(time.strftime ('%d-%m-%Y'))
	LIB_entry = param[param.find('###START'):]
	LIB_entry = LIB_entry[:LIB_entry.find('END###')]
	url = LIB_entry.split('###')[2]
	name = LIB_entry.split('###')[3]
	type = LIB_entry.split('###')[4]
	debug("(getDownload) ### URL : {0} || Name : {1} || Type : {2} ###".format(url, name, type))
	if targetDir is None or targetDir is '':
		xbmcgui.Dialog().notification(translation(30521).format('DOWNLOAD'), translation(30523), icon, 8000)
		return addon.openSettings(sys.argv[0])
	xbmcgui.Dialog().notification(translation(30524), translation(30526).format(name), icon, 8000)
	from youtube_dl import YoutubeDL
	fields = {'forceurl': True, 'forcetitle': True, 'quiet': True, 'no_warnings': True, 'noplaylist': True, 'format': 'best', 'outtmpl': os.path.join(targetDir, '%(title)s ['+now+'].%(ext)s')}
	with YoutubeDL(fields) as ydl:
		meta = ydl.extract_info(url, download=True)
		try:
			if 'entries' in meta: Vinfo = meta['entries'][0]
			else:
				Vinfo = meta
			if 'url' in Vinfo: media = Vinfo['url']
			else:
				if 'formats' in Vinfo and len(Vinfo['formats']) > 0:
					media = Vinfo['formats'][-1]['url']
			log("(getDownload) DOWNLOAD-VIDEO : {0}".format(media))
		except: pass
	xbmc.sleep(2000)
	xbmcgui.Dialog().notification(translation(30525), translation(30526).format(name), icon, 12000)

def listing():
	debug("(listing) -------------------------------------------------- START = listing --------------------------------------------------")
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
	for elem in os.listdir(targetDir):
		filePath = '{0}/{1}'.format(_edit(targetDir), _edit(elem))
		name = '{0}'.format(_edit(elem).replace('.mp4', '').replace('_', ' '))
		addLink(name, filePath, 'playVideo', icon, nosub='DOWNstream')
	xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url, type):
	debug("(playVideo) -------------------------------------------------- START = playVideo --------------------------------------------------")
	if type == 'YTstream':
		finalURL = 'plugin://plugin.video.youtube/play/?video_id='+url
	elif type == 'DIRECTstream':
		finalURL = getVideo(url)
	else:
		finalURL = url
	log("(playVideo) Streamurl : {0}".format(finalURL))
	listitem=xbmcgui.ListItem(path=finalURL)
	xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def _clean(text):
	text = py2_enc(text)
	for n in (('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'), ('&apos;', "'"), ("&#x27;", "'"), ('&#34;', '"'), ('&#39;', '\''), ('&#039;', '\''), ('►', '>')
		, ('&#x00c4', 'Ä'), ('&#x00e4', 'ä'), ('&#x00d6', 'Ö'), ('&#x00f6', 'ö'), ('&#x00dc', 'Ü'), ('&#x00fc', 'ü'), ('&#x00df', 'ß'), ('&#xD;', ''), ('\xc2\xb7', '-')
		, ('&quot;', '"'), ('&szlig;', 'ß'), ('&ndash;', '-'), ('&Auml;', 'Ä'), ('&Ouml;', 'Ö'), ('&Uuml;', 'Ü'), ('&auml;', 'ä'), ('&ouml;', 'ö'), ('&uuml;', 'ü')
		, ('&agrave;', 'à'), ('&aacute;', 'á'), ('&acirc;', 'â'), ('&egrave;', 'è'), ('&eacute;', 'é'), ('&ecirc;', 'ê'), ('&igrave;', 'ì'), ('&iacute;', 'í'), ('&icirc;', 'î')
		, ('&ograve;', 'ò'), ('&oacute;', 'ó'), ('&ocirc;', 'ô'), ('&ugrave;', 'ù'), ('&uacute;', 'ú'), ('&ucirc;', 'û'), ("\\'", "'")):
		text = text.replace(*n)
	return text.strip()

def _edit(input, nom='utf-8', esc='unicode_escape', ign='ignore'):
	if PY2 and  isinstance(input, str):
		input = input.decode(esc, ign).encode(nom) #UnicodeDecodeError: 'utf8' codec can't decode byte 0x9c
	elif PY2 and isinstance(input, bytes):
		input = input.decode(esc, ign).encode(nom)
	return input

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, plot=None, origSERIE=""):
	u = '{0}?url={1}&mode={2}&origSERIE={3}'.format(sys.argv[0], quote_plus(url), str(mode), str(origSERIE))
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Tvshowtitle': origSERIE, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon:
		liz.setArt({'fanart': image})
	return xbmcplugin.addDirectoryItem(pluginhandle, url=u, listitem=liz, isFolder=True)

def addLink(name, url, mode, image, plot=None, duration=None, episode=None, rating=None, votes=None, origSERIE="", nosub='00'):
	u = '{0}?url={1}&mode={2}&origSERIE={3}&nosub={4}'.format(sys.argv[0], quote_plus(url), str(mode), str(origSERIE), str(nosub))
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Tvshowtitle': origSERIE, 'Plot': plot, 'Duration': duration, 'Episode': episode, 'Rating': rating, 'Votes': votes, 'Mediatype': 'episode'})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon:
		liz.setArt({'fanart': image})
	liz.setProperty('IsPlayable', 'true')
	liz.setContentLookup(False)
	if nosub == 'DIRECTstream' or nosub == 'YTstream':
		liz.addContextMenuItems([(translation(30655), 'RunPlugin({0}?mode=MULTI_download&url=###START###{1}###{2}###{3}###END###)'.format(sys.argv[0], url, name, nosub))])
	if nosub == 'DOWNstream':
		liz.addContextMenuItems([(translation(30656), 'RunPlugin({0}?mode=trashcan&url={1})'.format(sys.argv[0], url))])
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

params = parameters_string_to_dict(sys.argv[2])
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
origSERIE = unquote_plus(params.get('origSERIE', ''))
nosub = unquote_plus(params.get('nosub', ''))

if mode == 'shows':
	shows(url)
elif mode == 'episodes':
	episodes(url, origSERIE)
elif mode == 'YOUT_channel':
	YOUT_channel(url)
elif mode == 'listing':
	listing()
elif mode == 'MULTI_download':
	MULTI_download(url)
elif mode == 'trashcan':
	xbmcvfs.delete(url)
	xbmc.sleep(1000)
	xbmc.executebuiltin('Container.Refresh')
elif mode == 'playVideo':
	playVideo(url, nosub)
else:
	index()