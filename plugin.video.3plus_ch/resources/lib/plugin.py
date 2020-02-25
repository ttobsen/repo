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
	from urllib2 import build_opener, Request, urlopen  # Python 2.X
	from urlparse import urljoin, urlparse, urlunparse  # Python 2.X
elif PY3:
	from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode, urljoin, urlparse, urlunparse  # Python 3+
	from urllib.request import build_opener, Request, urlopen  # Python 3+
try: import StorageServer
except: from . import storageserverdummy as StorageServer
import json
import xbmcvfs
import shutil
import socket
import time
from datetime import datetime, timedelta
import io
import gzip


global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
socket.setdefaulttimeout(40)
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
WORKFILE = os.path.join(dataPath, 'episode_data.txt')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
artpic = os.path.join(addonPath, 'resources', 'media', '').encode('utf-8').decode('utf-8')
cachePERIOD = int(addon.getSetting('cacherhythm'))
cache = StorageServer.StorageServer(addon.getAddonInfo('id'), cachePERIOD) # (Your plugin name, Cache time in hours)
enableInputstream = addon.getSetting('inputstream') == 'true'
prefSTREAM = addon.getSetting('streamSelection')
prefQUALITY = {0: 720, 1: 540, 2: 480, 3: 360}[int(addon.getSetting('prefVideoQuality'))]
useThumbAsFanart = addon.getSetting('useThumbAsFanart') == 'true'
enableAdjustment = addon.getSetting('show_settings') == 'true'
DEB_LEVEL = (xbmc.LOGNOTICE if addon.getSetting('enableDebug') == 'true' else xbmc.LOGDEBUG)
baseURL = 'https://www.3plus.tv/'
apiURL = 'https://www.3plus.tv/api/pub/gql/tv3plus/'
PartnerId = '1719221' # für Kaltura-Player

xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

if not xbmcvfs.exists(dataPath):
	xbmcvfs.mkdirs(dataPath)

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

def debug_MS(content):
	log(content, DEB_LEVEL)

def log(msg, level=xbmc.LOGNOTICE):
	xbmc.log('[{0} v.{1}]{2}'.format(addon.getAddonInfo('id'), addon.getAddonInfo('version'), py2_enc(msg)), level)

def makeREQUEST(url):
	return cache.cacheFunction(getUrl, url)

def getUrl(url, header=None, referer=None, agent='Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0'):
	opener = build_opener()
	opener.addheaders = [('User-Agent', agent), ('Accept-Encoding', 'gzip, deflate')]
	try:
		if header: opener.addheaders = header
		if referer: opener.addheaders = [('Referer', referer)]
		response = opener.open(url, timeout=30)
		if response.info().get('Content-Encoding') == 'gzip':
			content = py3_dec(gzip.GzipFile(fileobj=io.BytesIO(response.read())).read())
		else:
			content = py3_dec(response.read())
	except Exception as e:
		failure = str(e)
		failing("(getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
		if 'cdnapisec.kaltura.com' in url and '404' in failure:
			KPid = url.split('entryId/')[1].split('/format')[0]
			xbmcgui.Dialog().notification(translation(30527), translation(30528).format(KPid), icon, 15000)
		else:
			xbmcgui.Dialog().notification(translation(30521).format('URL'), "ERROR = [COLOR red]{0}[/COLOR]".format(failure), icon, 15000)
		content = ""
		return sys.exit(0)
	opener.close()
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

def clearCache():
	debug_MS("(clearCache) -------------------------------------------------- START = clearCache --------------------------------------------------")
	debug_MS("(clearCache) ========== Lösche jetzt den Addon-Cache ==========")
	cache.delete('%')
	xbmc.sleep(1000)
	xbmcgui.Dialog().ok(addon.getAddonInfo('id'), translation(30502))

def index():
	addDir(translation(30601), 'sendungen', 'listProductions', icon)
	addDir(translation(30602), 'videos', 'listVideos', icon)
	addDir(translation(30603), 'the-voice-of-switzerland', 'listVideos', icon)
	addDir(translation(30604), 'adieu-heimat', 'listVideos', icon)
	addDir(translation(30608), "0", 'getSearch', icon, limit=1)
	addDir(translation(30609).format(str(cachePERIOD)), "", 'clearCache', icon)
	if enableAdjustment:
		addDir(translation(30610), "", 'aSettings', icon)
		if enableInputstream and ADDON_operate('inputstream.adaptive'):
			addDir(translation(30611), "", 'iSettings', icon)
		else:
			addon.setSetting('inputstream', 'false')
	xbmcplugin.endOfDirectory(pluginhandle)

def listProductions(idd):  # https://www.3plus.tv/api/pub/gql/tv3plus/NewsArticleTeaser/2d5925defbf8ae31f3604f3dd6a5e44783a46a11?variables=%7B%22contextId%22%3A%22NewsArticle%3A136264072%22%7D
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
	debug_MS("(listProductions) ------------------------------------------------ START = listProductions -----------------------------------------------")
	debug_MS("(listProductions) ### IDD : {0} ###".format(str(idd)))
	url = apiURL+'Page/296171194de3453b2934d396f36a7309f255bbf5?variables=%7B%22prefix%22%3A%22pwa%22%2C%22ogUrlForCurrentSkin%22%3Atrue%2C%22path%22%3A%22%2F{0}%22%2C%22ressort%22%3A%22{0}%22%7D'.format(idd)
	debug_MS("(listProductions) ### URL : {0} ###".format(str(url)))
	UN_Supported = ['dokumentationen', 'filme', 'serien'] # these lists are empty or not compatible
	content = makeREQUEST(url)
	COMBI_FIRST = []
	Isolated = set()
	title = '00'
	contextType = '00'
	contextId = '00'
	response = json.loads(content)['data']['page']['layout']['content']['content'][0]['content'][0]['content']
	for item in response:
		if 'type' in item and item['type'] == 'FramedContent':
			title = _clean(item['header']['title'])
		if 'content' in item and 'contextType' in item['content'] and item['content']['contextType'] != "" and item['content']['contextType'] != None:
			contextType =  item['content']['contextType']
		if 'content' in item and 'contextId' in item['content'] and item['content']['contextId'] != "" and item['content']['contextId'] != None:
			contextId = item['content']['contextId']
		group = '00'
		if 'content' in item and 'group' in item['content'] and item['content']['group'] != "" and item['content']['group'] != None:
			group =  item['content']['group']
		if contextId in Isolated or contextId == '00' or any(x in group for x in UN_Supported):
			continue
		Isolated.add(contextId)
		debug_MS("(listProductions) no.1 ### TITLE = {0} || contextId = {1} || Group = {2} ###".format(title, str(contextId), group))
		COMBI_FIRST.append([title, contextId, group, contextType])
	if COMBI_FIRST:
		for title, contextId, group, contextType in COMBI_FIRST:
			link = apiURL+'NewsArticleTeaser/2d5925defbf8ae31f3604f3dd6a5e44783a46a11?variables=%7B%22contextId%22%3A%22{0}%22%7D'.format(quote(contextId))
			result = makeREQUEST(link)
			debug_MS("(listProductions) ### LINK : {0} ###".format(str(link)))
			short = json.loads(result)['data']['context']
			title = _clean(short['title'])
			plot = ""
			if 'lead' in short and short['lead'] != "" and short['lead'] != None:
				plot = _clean(short['lead'])
			# grösste Auflösung = https://static.az-cdn.ch/__ip/9w9PsDp2QzKB3vvT_4ZFEPzztfQ/8a0585a3041972617a5abe010d3c6407a2901bbd/n-ch12_2x-16x9-far
			try: image = short['teaserImage']['image']['url']+'n-ch12_2x-16x9-far'
			except: image = ""
			PRO_link = '00'
			if 'headRessort' in short and 'urls' in short['headRessort'] and 'relative' in short['headRessort']['urls'] and short['headRessort']['urls']['relative'] != "" and short['headRessort']['urls']['relative'] != None:
				PRO_link = _clean(short['headRessort']['urls']['relative']).replace('/', '')
			debug_MS("(listProductions) no.2 ### TITLE = {0} || FOTO = {1} || PRO_link = {2} ###".format(title, str(image), str(PRO_link)))
			if PRO_link != '00':
				addDir(title, PRO_link, 'listVideos', image)
	xbmcplugin.endOfDirectory(pluginhandle)

def getSearch(url, limit, default="", heading="Suche nach...", hidden=False):
	debug_MS("(getSearch) ------------------------------------------------ START = getSearch -----------------------------------------------")
	debug_MS("(getSearch) ### LIMIT : {0} ###".format(str(limit)))
	limit = int(limit)
	if limit == 1:
		keyboard = xbmc.Keyboard(default, heading, hidden)
		keyboard.doModal()
		if keyboard.isConfirmed() and keyboard.getText():
			limit += 1
			word = py2_enc(keyboard.getText())
			return listVideos('Searchterm@@'+word, limit)
		else: return default
	return default

def listVideos(idd, limit):  # https://www.3plus.tv/api/pub/gql/tv3plus/NewsArticleTeaser/2d5925defbf8ae31f3604f3dd6a5e44783a46a11?variables=%7B%22contextId%22%3A%22NewsArticle%3A136264072%22%7D
	debug_MS("(listVideos) ------------------------------------------------ START = listVideos -----------------------------------------------")
	debug_MS("(listVideos) ### IDD : {0} ### LIMIT : {1} ###".format(idd, str(limit)))
	UN_Supported = ['dokumentationen', 'filme', 'serien', 'Eigenproduktionen'] # these lists are empty or not compatible
	COMBI_FIRST = []
	COMBI_SEASON = []
	COMBI_EPISODE = []
	sea_LIST = []
	uno_LIST = []
	Isolated = set()
	pos1 = 0
	pos2 = 0
	FOUND = 1
	limit = int(limit)
	title = '00'
	contextType = '00'
	contextId = '00'
	if 'Searchterm' in idd and limit <= 2:
		# SEARCH = https://www.3plus.tv/api/pub/gql/tv3plus/Search/8edd5397e0fd160310524073f04d8200325310ed?variables=%7B%22fulltext%22%3A%22bauer%20sucht%22%2C%22assetType%22%3Anull%2C%22functionScore%22%3A%22%22%2C%22offset%22%3A0%7D
		url = apiURL+'Search/8edd5397e0fd160310524073f04d8200325310ed?variables=%7B%22fulltext%22%3A%22{0}%22%2C%22assetType%22%3Anull%2C%22functionScore%22%3A%22%22%2C%22offset%22%3A0%7D'.format(idd.split('@@')[1].replace(' ', '%20'))
		limit += 1
		try:
			content = makeREQUEST(url)
			response = json.loads(content)['data']['search']['fulltext']['newsarticles']['data']
			for item in response:
				if 'baseType' in item and item['baseType'] == 'NewsArticle':
					contextType = item['baseType']
				if 'id' in item and item['id'] != "" and item['id'] != None:
					contextId = item['id']
				if contextId in Isolated or contextId == '00':
					continue
				Isolated.add(contextId)
				debug_MS("(Searching) no.1 ### baseType = {0} || contextId = {1} ###".format(contextType, str(contextId)))
				COMBI_FIRST.append([title, contextId, contextType])
		except: return xbmcgui.Dialog().notification(translation(30522).format('Ergebnisse'), translation(30524), icon, 8000)
	elif not 'Searchterm' in idd:
		limit += 1
		url = apiURL+'Page/296171194de3453b2934d396f36a7309f255bbf5?variables=%7B%22prefix%22%3A%22pwa%22%2C%22ogUrlForCurrentSkin%22%3Atrue%2C%22path%22%3A%22%2F{0}%22%2C%22ressort%22%3A%22{0}%22%7D'.format(idd)
		content = makeREQUEST(url)
		response = json.loads(content)['data']['page']['layout']['content']['content'][0]['content'][0]['content']
		for item in response:
			if 'type' in item and item['type'] == 'FramedContent':
				title = _clean(item['header']['title'])
			if 'content' in item and 'contextType' in item['content'] and item['content']['contextType'] != "" and item['content']['contextType'] != None:
				contextType =  item['content']['contextType']
			if 'content' in item and 'contextId' in item['content'] and item['content']['contextId'] != "" and item['content']['contextId'] != None:
				contextId = item['content']['contextId']
			group = '00'
			if 'content' in item and 'group' in item['content'] and item['content']['group'] != "" and item['content']['group'] != None:
				group =  item['content']['group']
			if contextId in Isolated or contextId == '00' or any(x in group for x in UN_Supported) or any(x in title for x in UN_Supported):
				continue
			Isolated.add(contextId)
			debug_MS("(listVideos) no.1 ### TITLE = {0} || contextId = {1} || Group = {2} ###".format(title, str(contextId), group))
			COMBI_FIRST.append([title, contextId, contextType])
	if COMBI_FIRST:
		for title, contextId, contextType in COMBI_FIRST:
			link = apiURL+'NewsArticleTeaser/2d5925defbf8ae31f3604f3dd6a5e44783a46a11?variables=%7B%22contextId%22%3A%22{0}%22%7D'.format(quote(contextId))
			result = makeREQUEST(link)
			debug_MS("(listVideos) ### LINK : {0} ###".format(str(link)))
			short = json.loads(result)['data']['context']
			try: title = _clean(short['mainAsset']['title'])
			except: title = _clean(short['title'])
			origSERIE = ""
			origSERIE = title.replace('|', '').replace('ST', 'Staffel ').split('Staffel')[0].strip()
			Note_1 =""
			Note_2 =""
			Note_3 =""
			season = 0
			episode = 0
			if 'Staffel ' in title or 'ST ' in title:
				try: season = re.findall('(?:Staffel|ST) ([0-9]+)', title, re.S)[0].strip().zfill(4)
				except: pass
			if title[:2].isdigit() or 'Folge ' in title or 'Episode ' in title:
				try:
					episode = re.findall('(?:Folge|Episode) ([0-9]+)', title, re.S)[0].strip().zfill(4)
					pos1 += 1
				except: pass
			else: pos2 += 1
			if origSERIE != "": Note_1 = translation(30620).format(str(origSERIE))
			startTIMES = None
			try:
				startDates = datetime(*(time.strptime(short['displayDate'][:19], '%Y{0}%m{0}%dT%H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2020-01-22T10:33:11+01:00
				LOCALstart = utc_to_local(startDates)
				startTIMES = LOCALstart.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
			except: pass
			if startTIMES: Note_2 = translation(30621).format(str(startTIMES))
			if 'lead' in short and short['lead'] != "" and short['lead'] != None:
				Note_3 = _clean(short['lead'])
			plot = Note_1+Note_2+Note_3
			try: duration = short['mainAsset']['video']['kaltura']['meta']['duration']
			except: duration = ""
			try: kalturaId = str(short['mainAsset']['video']['kaltura']['kalturaId'])
			except: kalturaId = '00'
			# grösste Auflösung = https://static.az-cdn.ch/__ip/9w9PsDp2QzKB3vvT_4ZFEPzztfQ/8a0585a3041972617a5abe010d3c6407a2901bbd/n-ch12_2x-16x9-far
			try: image = short['teaserImage']['image']['url']+'n-ch12_2x-16x9-far'
			except: image = ""
			SE_num = ""
			if 'contextLabel' in short and short['contextLabel'] != "" and short['contextLabel'] != None:
				SE_num = _clean(short['contextLabel'])
			SE_link = ""
			if 'headRessort' in short and 'urls' in short['headRessort'] and 'relative' in short['headRessort']['urls'] and short['headRessort']['urls']['relative'] != "" and short['headRessort']['urls']['relative'] != None:
				SE_link = _clean(short['headRessort']['urls']['relative']).replace('/', '')
			debug_MS("(listVideos) no.2 ### TITLE = {0} || SEASON = {1} || EPISODE = {2} || startTIMES = {3} ###".format(title, str(season), str(episode), str(startTIMES)))
			debug_MS("(listVideos) no.2 ### SERIE = {0} || kalturaId = {1} || FOTO = {2} || DURATION = {3} ###".format(origSERIE, kalturaId, str(image), str(duration)))
			if SE_num != "" and 'staffel' in SE_num.lower():
				COMBI_SEASON.append([SE_num, SE_link, image, plot])
			else:
				COMBI_EPISODE.append([episode, pos1, pos2, kalturaId, image, title, plot, duration, origSERIE, season])
	else:
		return xbmcgui.Dialog().notification(translation(30522).format('Einträge'), translation(30525).format(idd), icon, 10000)
	if COMBI_SEASON:
		for SE_num, SE_link, image, plot in COMBI_SEASON:
			if 'staffel' in SE_num.lower():
				try:
					NUMBER = SE_num.lower().replace('staffel', '').strip()
					sea_LIST.append(NUMBER)
					newSE = int(max(sea_LIST))+1
					newLINK = SE_link.split('-staffel-')[0]+'-staffel-'+str(newSE)
					if FOUND == 1:
						FOUND += 1
						addDir('Staffel '+str(newSE), newLINK, 'listVideos', image, limit=limit)
				except: pass
				addDir(SE_num, SE_link, 'listVideos', image, limit=limit)
	if COMBI_EPISODE and not COMBI_SEASON:
		if pos2 <= 5 and not 'Notruf' in title:
			COMBI_EPISODE = sorted(COMBI_EPISODE, key=lambda num:num[0], reverse=True)
		for episode, pos1, pos2, kalturaId, image, title, plot, duration, origSERIE, season in COMBI_EPISODE:
			EP_entry = py2_enc(kalturaId+'@@'+str(origSERIE)+'@@'+str(title)+'@@'+str(image)+'@@'+str(plot)+'@@'+str(duration)+'@@'+str(season)+'@@'+str(episode)+'@@')
			if kalturaId != '00':
				if EP_entry not in uno_LIST:
					uno_LIST.append(EP_entry)
				listitem = xbmcgui.ListItem(path=sys.argv[0]+'?IDENTiTY='+kalturaId+'&mode=playCODE')
				ilabels = {}
				ilabels['Season'] = season
				ilabels['Episode'] = episode
				ilabels['Tvshowtitle'] = origSERIE
				ilabels['Title'] = title
				ilabels['Tagline'] = None
				ilabels['Plot'] = plot
				ilabels['Duration'] = duration
				ilabels['Year'] = None
				ilabels['Genre'] = 'Eigenproduktion'
				ilabels['Director'] = None
				ilabels['Writer'] = None
				ilabels['Studio'] = '3plus.tv'
				ilabels['Mpaa'] = None
				ilabels['Mediatype'] = 'episode'
				listitem.setInfo(type='Video', infoLabels=ilabels)
				listitem.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
				if useThumbAsFanart and image != icon and not artpic in image:
					listitem.setArt({'fanart': image})
				listitem.addStreamInfo('Video', {'Duration':duration})
				listitem.setProperty('IsPlayable', 'true')
				playInfos = '###START###{0}?IDENTiTY={1}&mode=playCODE###{2}###{3}###END###'.format(sys.argv[0], kalturaId, title, image)
				listitem.addContextMenuItems([(translation(30654), 'RunPlugin('+sys.argv[0]+'?mode=addQueue&url='+quote_plus(playInfos)+')')])
				xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sys.argv[0]+'?IDENTiTY='+kalturaId+'&mode=playCODE', listitem=listitem)
		with open(WORKFILE, 'w') as input:
			input.write('\n'.join(uno_LIST))
	xbmcplugin.endOfDirectory(pluginhandle)

def playCODE(IDD):
	debug_MS("(playCODE) ------------------------------------------------ START = playCODE -----------------------------------------------")
	debug_MS("(playCODE) ### IDD : {0} ###".format(str(IDD)))
	# try .mpd = https://cdnapisec.kaltura.com/p/1719221/sp/1719221/playManifest/entryId/1_p6l6ymw0/flavorIds/0_wi9evyfh,0_om5ckrkd,0_vnrmio95,0_68g0date/deliveryProfileId/10182/protocol/https/format/mpegdash/manifest.mpd
	# all of .m3u8 = https://cdnapisec.kaltura.com/p/1719221/sp/171922100/playManifest/entryId/1_p1giw45o/format/applehttp/protocol/https/a.m3u8?responseFormat=json
	# .m3u8 = https://cfvod.kaltura.com/hls/p/1719221/sp/171922100/serveFlavor/entryId/1_6hrjp75i/v/1/ev/7/flavorId/1_fbhvz56l/name/a.mp4/index.m3u8
	# .mp4 = https://cfvod.kaltura.com/p/1719221/sp/171922100/serveFlavor/entryId/1_6hrjp75i/v/1/ev/7/flavorId/1_fbhvz56l/name/a.mp4
	DATA = {}
	DATA['media'] = []
	finalURL = False
	streamTYPE = False
	with open(WORKFILE, 'r') as output:
		lines = output.readlines()
		for line in lines:
			field = line.split('@@')
			if field[0]==IDD:
				entryId = field[0]
				origSERIE = field[1]
				title = field[2]
				image = field[3]
				plot = field[4] 
				duration = field[5] 
				season = field[6]
				episode = field[7]
	if IDD != '00' and entryId != '00':
		firstUrl = 'https://cdnapisec.kaltura.com/p/{0}/sp/{0}00/playManifest/entryId/{1}/format/applehttp/protocol/https/a.m3u8?responseFormat=json'.format(PartnerId, entryId)
		ref = 'https://license.theoplayer.com/'
		content = getUrl(firstUrl, referer=ref)
		debug_MS("(playCODE) ### firstUrl : {0} ###".format(str(firstUrl)))
		result = json.loads(content)
		for elem in result['flavors']:
			vid = elem['url']
			ext = elem['ext']
			height = elem['height']
			if (ext == 'vnd.apple.mpegURL' or ext == 'x-mpegurl' or ext== 'mp4'):
				DATA['media'].append({'url': vid, 'mimeType': ext, 'height': height})
				DATA['media'] = sorted(DATA['media'], key=lambda b:b['height'], reverse=True)
				debug_MS("(playCODE) listing_1_DATA[media] ### height : "+str(height)+" ### url : "+vid+" ### mimeType : "+ext+" ###")
		if DATA['media']:
			for item in DATA['media']:
				if enableInputstream:
					if ADDON_operate('inputstream.adaptive') and '/hls' and '.m3u8' in item['url']:
						finalURL = DATA['media'][0]['url']
						streamTYPE = 'HLS'
					else:
						addon.setSetting('inputstream', 'false')
				elif not enableInputstream and prefSTREAM == "0" and '.m3u8' in item['url'] and item['height'] == prefQUALITY:
					finalURL = item['url']
					streamTYPE = 'M3U8'
					debug_MS("(playCODE) listing_2_Standard ### height : "+str(item['height'])+" ### finalURL : "+finalURL+" ### mimeType : "+str(item['mimeType'])+" ### streamTYPE : "+streamTYPE+" ###")
				elif not enableInputstream and prefSTREAM == "1" and '.mp4' in item['url'] and item['height'] == prefQUALITY:
					finalURL = item['url'].replace('/hls', '').replace('/index.m3u8', '')
					streamTYPE = 'MP4'
					debug_MS("(playCODE) listing_2_Standard ### height : "+str(item['height'])+" ### finalURL : "+finalURL+" ### mimeType : "+str(item['mimeType'])+" ### streamTYPE : "+streamTYPE+" ###")
		if not finalURL and DATA['media']:
			for item in DATA['media']:
				if item['mimeType'].lower() == 'mp4':
					finalURL = DATA['media'][0]['url'].replace('/hls', '').replace('/index.m3u8', '')
					streamTYPE = 'MP4'
			log("(playCODE) !!!!! KEINEN passenden Stream gefunden --- nehme jetzt den Reserve-Stream-MP4 !!!!!")
			debug_MS("(playCODE) listing_2_Standard ### height : "+str(DATA['media'][0]['height'])+" ### finalURL : "+finalURL+" ### mimeType : "+str(DATA['media'][0]['mimeType'])+" ### streamTYPE : "+streamTYPE+" ###")
	if finalURL and streamTYPE:
		if streamTYPE == 'M3U8':
			log("(playCODE) M3U8_stream : {0}".format(finalURL))
		if streamTYPE == 'MP4':
			log("(playCODE) MP4_stream : {0}".format(finalURL))
		listitem = xbmcgui.ListItem(path=finalURL)
		if streamTYPE == 'HLS':
			debug_MS("(playCODE) listing_2_Standard ### height : "+str(DATA['media'][0]['height'])+" ### finalURL : "+finalURL+" ### mimeType : "+str(DATA['media'][0]['mimeType'])+" ### streamTYPE : "+streamTYPE+" ###")
			log("(playCODE) HLS_stream : {0}".format(finalURL))
			listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
			listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
			listitem.setMimeType('application/vnd.apple.mpegurl')
		xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
	else: 
		failing("(playCODE) ##### Die angeforderte Video-Url wurde leider NICHT gefunden !!! #####")
		return xbmcgui.Dialog().notification(translation(30521).format('PLAY'), translation(30526), icon, 8000)

def utc_to_local(dt):
	if time.localtime().tm_isdst: return dt - timedelta(seconds=time.altzone)
	else: return dt - timedelta(seconds=time.timezone)

def _clean(text):
	text = py2_enc(text)
	for n in (('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'), ('&apos;', "'"), ("&#x27;", "'"), ('&#34;', '"'), ('&#39;', '\''), ('&#039;', '\''), ('►', '>'), ('3+ ', '')
		, ('&#x00c4', 'Ä'), ('&#x00e4', 'ä'), ('&#x00d6', 'Ö'), ('&#x00f6', 'ö'), ('&#x00dc', 'Ü'), ('&#x00fc', 'ü'), ('&#x00df', 'ß'), ('&#xD;', ''), ('\xc2\xb7', '-')
		, ('&quot;', '"'), ('&szlig;', 'ß'), ('&ndash;', '-'), ('&Auml;', 'Ä'), ('&Ouml;', 'Ö'), ('&Uuml;', 'Ü'), ('&auml;', 'ä'), ('&ouml;', 'ö'), ('&uuml;', 'ü')
		, ('&agrave;', 'à'), ('&aacute;', 'á'), ('&acirc;', 'â'), ('&egrave;', 'è'), ('&eacute;', 'é'), ('&ecirc;', 'ê'), ('&igrave;', 'ì'), ('&iacute;', 'í'), ('&icirc;', 'î')
		, ('&ograve;', 'ò'), ('&oacute;', 'ó'), ('&ocirc;', 'ô'), ('&ugrave;', 'ù'), ('&uacute;', 'ú'), ('&ucirc;', 'û'), ('_', ' ')):
		text = text.replace(*n)
	return text.strip()

def addQueue(vid):
	PL = xbmc.PlayList(1)
	STREAMe = vid[vid.find('###START'):]
	STREAMe = STREAMe[:STREAMe.find('END###')]
	url = STREAMe.split('###')[2]
	name = STREAMe.split('###')[3]
	image = STREAMe.split('###')[4]
	listitem = xbmcgui.ListItem(name)
	listitem.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	listitem.setProperty('IsPlayable', 'true')
	PL.add(url, listitem)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, plot=None, limit=1):
	u = '{0}?url={1}&mode={2}&limit={3}'.format(sys.argv[0], quote_plus(url), str(mode), str(limit))
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon and not artpic in image:
		liz.setArt({'fanart': image})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
limit = unquote_plus(params.get('limit', ''))
origSERIE = unquote_plus(params.get('origSERIE', ''))
IDENTiTY = unquote_plus(params.get('IDENTiTY', ''))
referer = unquote_plus(params.get('referer', ''))

if mode == 'aSettings':
	addon.openSettings()
elif mode == 'iSettings':
	xbmcaddon.Addon('inputstream.adaptive').openSettings()
elif mode == 'clearCache':
	clearCache()
elif mode == 'listProductions':
	listProductions(url)
elif mode == 'getSearch':
	getSearch(url, limit)
elif mode == 'listVideos':
	listVideos(url, limit)
elif mode == 'playCODE':
	playCODE(IDENTiTY)
elif mode == 'addQueue':
	addQueue(url)
else:
	index()