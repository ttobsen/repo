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
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath    = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg') or os.path.join(addonPath, 'resources', 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png') or os.path.join(addonPath, 'resources', 'icon.png')
Pagination = int(addon.getSetting('max_pages'))
enableInputstream = addon.getSetting('inputstream') == 'true'
prefSTREAM = addon.getSetting('streamSelection')
prefQUALITY = {0: 1080, 1: 720, 2: 576, 3: 360}[int(addon.getSetting('prefVideoQuality'))]
useThumbAsFanart = addon.getSetting('useThumbAsFanart') == 'true'
enableAdjustment = addon.getSetting('show_settings') == 'true'
DEB_LEVEL = (xbmc.LOGNOTICE if addon.getSetting('enableDebug') == 'true' else xbmc.LOGDEBUG)
baseURL = 'https://www.spiegel.de'
# https://cdn.jwplayer.com/v2/media/Ks1yAFoQ?sources=hls,dash,mp4

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

def convert_duration(duration):
	match = re.match('^(\d+):(\d+)$', duration)
	if match is None: return None
	ret = 0
	for group, factor in enumerate([60, 1], 1):
		ret = factor * (ret+int(match.group(group)))
	return ret

def translation(id):
	return py2_enc(addon.getLocalizedString(id))

def failing(content):
	log(content, xbmc.LOGERROR)

def debug_MS(content):
	log(content, DEB_LEVEL)

def log(msg, level=xbmc.LOGNOTICE):
	xbmc.log('[{0} v.{1}]{2}'.format(addon.getAddonInfo('id'), addon.getAddonInfo('version'), py2_enc(msg)), level)

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

def index():
	addDir(translation(30601), baseURL+'/video/', 'listThemes', icon, nosub=2)
	addDir(translation(30602), baseURL+'/thema/spiegel-tv/', 'listThemes', icon)
	addDir(translation(30603), baseURL+'/panorama/', 'listThemes', icon, nosub=9)
	addDir(translation(30604), baseURL+'/politik/ausland/', 'listThemes', icon, nosub=8)
	addDir(translation(30605), baseURL+'/politik/deutschland/', 'listThemes', icon, nosub=8)
	addDir(translation(30606), 'UU1w6pNGiiLdZgyNpXUnA4Zw', 'listYTcategories', icon)
	addDir(translation(30607), 'PL8B9FDFC553E79FC6', 'listYTcategories', icon)
	addDir(translation(30608), 'PLuiYhcgFTmqDTfN9kw9H3u_lqBymi_kop', 'listYTcategories', icon)
	addDir(translation(30609), 'PL54B134AD9A7A86C8', 'listYTcategories', icon, nosub='lowQ')
	addDir(translation(30610), 'PLuiYhcgFTmqBmHD5Rnvu2IWdW3ZNlyF6N', 'listYTcategories', icon)
	addDir(translation(30611), 'PLuiYhcgFTmqCqURWOR9LfQPAIHkc9mRDv', 'listYTcategories', icon)
	addDir(translation(30612), 'PU1w6pNGiiLdZgyNpXUnA4Zw', 'listYTcategories', icon, nosub='lowQ')
	addDir(translation(30613), 'PLuiYhcgFTmqDB29p4MkEHvt0F148t4GEC', 'listYTcategories', icon, nosub='lowQ')
	addDir(translation(30614), 'PL084070CE355CB92A', 'listYTcategories', icon, nosub='lowQ')
	addDir(translation(30615), 'PLuiYhcgFTmqCpfixek3PcfJTwhGKIAGFq', 'listYTcategories', icon, nosub='lowQ')
	addDir(translation(30616), 'PLuiYhcgFTmqCMQU0Tk7jXA8jp-Z7k1koZ', 'listYTcategories', icon, nosub='lowQ')
	if enableAdjustment:
		addDir(translation(30617), "", "aSettings", icon)
		if enableInputstream:
			if ADDON_operate('inputstream.adaptive'):
				addDir(translation(30618), "", "iSettings", icon)
			else:
				addon.setSetting("inputstream", "false")
	xbmcplugin.endOfDirectory(pluginhandle)

def listThemes(url, filter):
	debug_MS("(listThemes) -------------------------------------------------- START = listThemes --------------------------------------------------")
	debug_MS("(listThemes) ### URL = {0} ### FILTER = {1} ### PAGINATION = {2} ###".format(url, filter, str(Pagination)))
	Isolated = set()
	pageNUMBER = 1
	position = 1
	total = 1
	content = getUrl(url)
	while total > 0 and pageNUMBER <= Pagination + int(filter):
		if pageNUMBER > 1:
			newURL = url+'p'+str(pageNUMBER)+'/'
		else: newURL = url
		debug_MS("(listThemes) ### newURL : {0} ###".format(str(newURL)))
		response = getUrl(newURL)
		selection = re.findall(r'(?:<section class="relative flex flex-wrap w-full" data-size="full" data-first="true" data-area="block>topic|<section data-area="article-teaser-list">)(.+?)border-shade-light">Ältere Artikel</span>', response, re.DOTALL)
		for chtml in selection:
			debug_MS("(listThemes) no.1 XXXXX CHTML : {0} XXXXX".format(str(chtml)))
			part = chtml.split('data-block-el="articleTeaser"')
			for i in range(1, len(part), 1):
				element = part[i]
				title = re.compile('<article aria-label="([^"]+?)"', re.DOTALL).findall(element)[0]
				title = _clean(title)
				if title in Isolated:
					continue
				Isolated.add(title)
				link = re.compile('<a href="([^"]+?)" target=', re.DOTALL).findall(element)[0].strip()
				try: photo = re.compile('<img data-image-el="img".*?src="([^"]+?)" srcset=', re.DOTALL).findall(element)[0]#.replace('_w488_', '_w1280_')
				except: photo = ""
				if '_fd' in photo: photo = photo.split('_fd')[0]+'.jpg'
				try:
					tagline = re.compile(r'(?:text-primary-dark font-sansUI font-bold text-base">|text-primary-base font-sansUI font-bold text-base">)([^<]+?)</span>', re.DOTALL).findall(element)[0].strip()
					tagline = _clean(tagline)
				except: tagline = ""
				try: 
					desc = re.compile('class="font-serifUI font-normal text-base leading-loose mr-6">(.+?)</a>', re.DOTALL).findall(element)[0]
					Note_1 = re.sub(r'\<.*?\>', '', desc)
					Note_1 = _clean(Note_1)+'[CR][CR]'
				except: Note_1 = ""
				try: Note_2 = re.compile('<footer class="font-sansUI text-shade-dark text-s">(.+?)</span>', re.DOTALL).findall(element)[0].replace('<span>', '')
				except: Note_2 = ""
				plot = Note_1+translation(30620).format(_clean(Note_2))
				duration = None
				try: duration = convert_duration(re.compile('<span class="text-white font-sansUI text-s font-bold">([^<]+?)</span>', re.DOTALL).findall(element)[0].strip())
				except: pass
				debug_MS("(listThemes) no.2 ### TITLE = {0} || LINK = {1} || DURATION = {2} ###".format(title, link, str(duration)))
				debug_MS("(listThemes) no.2 ### FOTO = {0} || TAGLINE = {1} ###".format(photo, tagline))
				if duration != None:
					addLink(title, link, 'playVideo', photo, duration, plot, tagline)
			position += 1
			debug_MS("(listThemes) ### position : {0} ###".format(str(position)))
		try:
			pageUrl = re.compile('text-base md:text-base sm:text-s leading-normal">\s+Seite.*?<a href="([^"]+?)" class=', re.DOTALL).findall(response)[0]
			debug_MS("(listThemes) ### pageUrl : {0} ###".format(str(pageUrl)))
			total = Pagination
		except: total = 0
		pageNUMBER += 1
	xbmcplugin.endOfDirectory(pluginhandle)
  
def listYTcategories(url, filter):
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_UNSORTED)
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_DURATION)
	debug_MS("(listYTcategories) -------------------------------------------------- START = listYTcategories --------------------------------------------------")
	debug_MS("(listYTcategories) ### URL = {0} ### FILTER = {1} ###".format(url, filter))
	response = getUrl('https://www.youtube.com/list_ajax?style=json&action_get_list=1&list='+url)
	DATA = json.loads(response)
	for item in DATA['video']:
		debug_MS("(listYTcategories) no.1 XXXXX FOLGE : {0} XXXXX".format(str(item)))
		title = _clean(item['title'])
		startTIMES = None
		year = None
		begins = None
		Note_1 = ""
		Note_2 = ""
		if 'time_created' in item and item['time_created'] !="" and item['time_created'] != None:
			startDATES = datetime(1970, 1, 1) + timedelta(seconds=int(item['time_created']))
			startTIMES = startDATES.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
			year = startDATES.strftime('%Y')
			begins =  startDATES.strftime('%d{0}%m{0}%Y').format('.')
		if startTIMES: Note_1 = translation(30621).format(str(startTIMES))
		if 'description' in item and item['description'] !="" and item['description'] != None:
			if 'Mehr Infos über' in item['description']: item['description'] = item['description'].split('Mehr Infos über')[0].strip()
			Note_2 = _clean(item['description'])
		plot = Note_1+Note_2
		if begins: xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_DATE)
		try: 
			if filter == 'lowQ':
				photo = item['thumbnail'].replace('/default.jpg', '/hqdefault.jpg')
			else: photo = item['thumbnail'].replace('/default.jpg', '/maxresdefault.jpg')
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
		debug_MS("(listYTcategories) no.2 ### TITLE = {0} || videoID = {1} || DURATION = {2} ###".format(title, videoId, str(duration)))
		debug_MS("(listYTcategories) no.2 ### FOTO = {0} || startTIMES = {1} || VOTES = {2} ###".format(photo, str(startTIMES), votes))
		addLink(title, videoId, 'playVideo', photo, duration, plot, rating=rating, votes=votes, nosub='YTstream', year=year, begins=begins)
	xbmcplugin.endOfDirectory(pluginhandle)  

def playVideo(url, filter):
	debug_MS("(playVideo) -------------------------------------------------- START = playVideo --------------------------------------------------")
	debug_MS("(playVideo) ### URL = {0} ### FILTER = {1} ###".format(url, filter))
	if filter == 'YTstream':
		finalURL = 'plugin://plugin.video.youtube/play/?video_id='+url
		listitem = xbmcgui.ListItem(path=finalURL)
		xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
	else:
		DATA = {}
		DATA['media'] = []
		finalURL = False
		streamTYPE = False
		try:
			content1 = getUrl(url)
			content1 = content1.replace('&#34;', '"')
			IDD = re.compile('"mediaId":"(.+?)",', re.DOTALL).findall(content1)[0].strip()
		except:
			failing("(playVideo) ##### Abspielen des Streams NICHT möglich ##### URL : {0} #####\n   ########## KEINEN Stream-Eintrag auf der Webseite von *spiegel.de* gefunden !!! ##########".format(url))
			return xbmcgui.Dialog().notification(translation(30521).format('Play 1'), translation(30526), icon, 8000)
		content2 = getUrl('https://vcdn01.spiegel.de/v2/media/'+str(IDD)+'?sources=hls,dash,mp4')
		result = json.loads(content2)
		for elem in result['playlist'][0]['sources']:
			type = elem['type']
			vid = elem['file']
			if type.lower() == 'video/mp4':
				height = elem['height']
				DATA['media'].append({'url': vid, 'mimeType': type.lower(), 'height': height})
				DATA['media'] = sorted(DATA['media'], key=lambda b:b['height'], reverse=True)
				debug_MS("(playVideo) listing_1_DATA[media] ### height : "+str(height)+" ### url : "+vid+" ### mimeType : "+str(type)+" ###")
			if enableInputstream and type.lower() == 'application/vnd.apple.mpegurl':
				if ADDON_operate('inputstream.adaptive'):
					finalURL = vid
					streamTYPE = 'HLS'
					debug_MS("(playVideo) listing_2_Standard ### finalURL : "+finalURL+" ### mimeType : "+str(type)+" ### streamTYPE : "+streamTYPE+" ###")
				else:
					addon.setSetting('inputstream', 'false')
			elif not enableInputstream and type.lower() == 'application/vnd.apple.mpegurl' and prefSTREAM == '0':
				finalURL = vid
				streamTYPE = 'M3U8'
				debug_MS("(playVideo) listing_2_Standard ### finalURL : "+finalURL+" ### mimeType : "+str(type)+" ### streamTYPE : "+streamTYPE+" ###")
		if not finalURL and DATA['media'] and prefSTREAM == '1':
			for item in DATA['media']:
				if item['mimeType'].lower() == 'video/mp4' and item['height'] == prefQUALITY:
					finalURL = item['url']
					streamTYPE = 'MP4'
					debug_MS("(playVideo) listing_2_Standard ### height : "+str(item['height'])+" ### finalURL : "+finalURL+" ### mimeType : "+str(item['mimeType'])+" ### streamTYPE : "+streamTYPE+" ###")
		if not finalURL and DATA['media']:
			for item in DATA['media']:
				if item['mimeType'].lower() == 'video/mp4':
					finalURL = DATA['media'][0]['url']
					streamTYPE = 'MP4'
			log("(playVideo) !!!!! KEINEN passenden Stream gefunden --- nehme jetzt den Reserve-Stream-MP4 !!!!!")
			debug_MS("(playVideo) listing_2_Standard ### height : "+str(DATA['media'][0]['height'])+" ### finalURL : "+finalURL+" ### mimeType : "+str(DATA['media'][0]['mimeType'])+" ### streamTYPE : "+streamTYPE+" ###")
		if finalURL and streamTYPE:
			if streamTYPE == 'M3U8':
				log("(playVideo) M3U8_stream : {0}".format(finalURL))
			if streamTYPE == 'MP4':
				log("(playVideo) MP4_stream : {0}".format(finalURL))
			listitem = xbmcgui.ListItem(path=finalURL)
			if streamTYPE == 'HLS':
				log("(playVideo) HLS_stream : {0}".format(finalURL))
				listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
				listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
				listitem.setMimeType('application/vnd.apple.mpegurl')
			xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
		else: 
			failing("(playVideo) ##### Die angeforderte Video-Url wurde leider NICHT gefunden !!! #####")
			return xbmcgui.Dialog().notification(translation(30521).format('PLAY 2'), translation(30526), icon, 8000)

def _clean(text):
	text = py2_enc(text)
	for n in (('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'), ('&Amp;', '&'), ('&nbsp;', ' '), ("&quot;", "\""), ("&Quot;", "\""), ('&szlig;', 'ß'), ('&mdash;', '-'), ('&ndash;', '-'), ('&apos;', "'"), ("&#x27;", "'"), ('&#34;', '"'), ('&#39;', '\''), ('&#039;', '\'')
		, ('&#x00c4', 'Ä'), ('&#x00e4', 'ä'), ('&#x00d6', 'Ö'), ('&#x00f6', 'ö'), ('&#x00dc', 'Ü'), ('&#x00fc', 'ü'), ('&#x00df', 'ß'), ('&#xD;', ''), ('\xc2\xb7', '-')
		, ('&#xC4;', 'Ä'), ('&#xE4;', 'ä'), ('&#xD6;', 'Ö'), ('&#xF6;', 'ö'), ('&#xDC;', 'Ü'), ('&#xFC;', 'ü'), ('&#xDF;', 'ß'), ('&#x201E;', '„'), ('&#xB4;', '´'), ('&#x2013;', '-'), ('&#xA0;', ' ')
		, ('\\xC4', 'Ä'), ('\\xE4', 'ä'), ('\\xD6', 'Ö'), ('\\xF6', 'ö'), ('\\xDC', 'Ü'), ('\\xFC', 'ü'), ('\\xDF', 'ß'), ('\\x201E', '„'), ('\\x28', '('), ('\\x29', ')'), ('\\x2F', '/'), ('\\x2D', '-'), ('\\x20', ' '), ('\\x3A', ':'), ('\\"', '"')
		, ('&Auml;', 'Ä'), ('Ä', 'Ä'), ('&auml;', 'ä'), ('ä', 'ä'), ('&Euml;', 'Ë'), ('&euml;', 'ë'), ('&Iuml;', 'Ï'), ('&iuml;', 'ï'), ('&Ouml;', 'Ö'), ('Ö', 'Ö'), ('&ouml;', 'ö'), ('ö', 'ö'), ('&Uuml;', 'Ü'), ('Ü', 'Ü'), ('&uuml;', 'ü'), ('ü', 'ü'), ('&yuml;', 'ÿ')
		, ('&agrave;', 'à'), ('&Agrave;', 'À'), ('&aacute;', 'á'), ('&Aacute;', 'Á'), ('&acirc;', 'â'), ('&Acirc;', 'Â'), ('&egrave;', 'è'), ('&Egrave;', 'È'), ('&eacute;', 'é'), ('&Eacute;', 'É'), ('&ecirc;', 'ê'), ('&Ecirc;', 'Ê')
		, ('&igrave;', 'ì'), ('&Igrave;', 'Ì'), ('&iacute;', 'í'), ('&Iacute;', 'Í'), ('&icirc;', 'î'), ('&Icirc;', 'Î'), ('&ograve;', 'ò'), ('&Ograve;', 'Ò'), ('&oacute;', 'ó'), ('&Oacute;', 'ó'), ('&ocirc;', 'ô'), ('&Ocirc;', 'Ô')
		, ('&ugrave;', 'ù'), ('&Ugrave;', 'Ù'), ('&uacute;', 'ú'), ('&Uacute;', 'Ú'), ('&ucirc;', 'û'), ('&Ucirc;', 'Û'), ('&yacute;', 'ý'), ('&Yacute;', 'Ý')):
		text = text.replace(*n)
	return text.strip()

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, plot=None, nosub=0, origSERIE=None):   
	u = '{0}?url={1}&mode={2}&nosub={3}&origSERIE={4}'.format(sys.argv[0], quote_plus(url), str(mode), str(nosub), str(origSERIE))
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Tvshowtitle': origSERIE, 'Title': name, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon:
		liz.setArt({'fanart': image})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

def addLink(name, url, mode, image, duration=None, plot=None, tagline=None, rating=None, votes=None, nosub=0, genre=None, year=None, begins=None):
	u = '{0}?url={1}&mode={2}&nosub={3}'.format(sys.argv[0], quote_plus(url), str(mode), str(nosub))
	liz = xbmcgui.ListItem(name)
	ilabels = {}
	ilabels['Season'] = None
	ilabels['Episode'] = None
	ilabels['Tvshowtitle'] = None
	ilabels['Title'] = name
	ilabels['Tagline'] = tagline
	ilabels['Plot'] = plot
	ilabels['Duration'] = duration
	if begins != None:
		ilabels['Date'] = begins
	ilabels['Year'] = year
	ilabels['Genre'] = 'News'
	ilabels['Rating'] = rating
	ilabels['Votes'] = votes
	ilabels['Studio'] = 'Der Spiegel'
	ilabels['Mpaa'] = None
	ilabels['Mediatype'] = 'video'
	liz.setInfo(type='Video', infoLabels=ilabels)
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon:
		liz.setArt({'fanart': image})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

params = parameters_string_to_dict(sys.argv[2])
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
nosub = unquote_plus(params.get('nosub', ''))
origSERIE = unquote_plus(params.get('origSERIE', ''))
referer = unquote_plus(params.get('referer', ''))

if mode == 'aSettings':
	addon.openSettings()
elif mode == 'iSettings':
	xbmcaddon.Addon('inputstream.adaptive').openSettings()
elif mode == 'listThemes':
	listThemes(url, nosub)  
elif mode == 'listYTcategories':
	listYTcategories(url, nosub)
elif mode == 'playVideo':
	playVideo(url, nosub)
else:
	index()
