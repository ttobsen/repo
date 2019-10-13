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
	from urllib import quote_plus, unquote_plus # Python 2.X
	from urlparse import urljoin
	from urllib2 import build_opener # Python 2.X
	from HTMLParser import HTMLParser
	unescape = HTMLParser().unescape
elif PY3:
	from urllib.parse import urljoin, quote_plus, unquote_plus # Python 3+
	from urllib.request import build_opener # Python 3+
	try: from html import unescape
	except ImportError:
		from html.parser import HTMLParser
		unescape = HTMLParser().unescape

from bs4 import BeautifulSoup as origSoup
# Generiert sonst ein UserWarning
BeautifulSoup = lambda x: origSoup(x, 'html.parser')

from datetime import datetime, date, timedelta
import time
import threading
import json
import xbmcvfs
import io
import gzip

baseURL = "https://api.tele5.de/v1/"
NEXX_URL = 'https://api.nexx.cloud/v3/759/'
WEBSITE_URL = 'https://www.tele5.de/'
WEBSITE_AGENT = ('Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0')
AVAILABILITY_NONE = '1'
AVAILABILITY_END = '2'
AVAILABILITY_REMAIN = '0'

KODI_LEIA = xbmc.getInfoLabel('System.BuildVersion') >= '18'

pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
enableInputstream = addon.getSetting('inputstream') == "true"
showRemainingTime = addon.getSetting('showOnlineUntil')
max_rest_warn = 3600 * int(addon.getSetting('maxRestWarn'))
fsk18 = addon.getSetting('fsk18') == "true"
useThumbAsFanart = addon.getSetting('useThumbAsFanart') == "true"
enableAdjustment = addon.getSetting('show_settings') == "true"
DEB_LEVEL = (xbmc.LOGNOTICE if addon.getSetting('enableDebug') == "true" else xbmc.LOGDEBUG)

timeformat = xbmc.getRegion('time').replace('%H%H', '%H').replace('%I%I', '%I').replace(':%S', '')
dateformat = xbmc.getRegion('dateshort')

xbmcplugin.setContent(pluginhandle, 'movies')

if addon.getSetting('enableTitleOrder') == "true":
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)

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

def translation(ID):
	LANGUAGE = addon.getLocalizedString(ID)
	LANGUAGE = py2_enc(LANGUAGE)
	return LANGUAGE

def failing(content):
	log(content, xbmc.LOGERROR)

def notify_err(head, content):
	xbmcgui.Dialog().notification(head, content, icon, 12000)

def debug_MS(content):
	log(content, DEB_LEVEL)

def debug(content):
	log(content, xbmc.LOGDEBUG)

def log(msg, level=xbmc.LOGNOTICE):
	msg = py2_enc(msg)
	xbmc.log("["+addon.getAddonInfo('id')+"-"+addon.getAddonInfo('version')+"]"+msg, level)

def decode_duration(duration):
	match = re.match('^(\d+):(\d+):(\d+)$', duration)
	if match is None: return None
	ret = 0
	for group, factor in enumerate([60, 60, 1], 1):
		ret = factor * (ret + int(match.group(group)))
	return ret

def maybe_explode(s, delim = ','):
	if KODI_LEIA: return explode(s, delim)
	else: return s or None

def explode(s, delim = ','):
	if s: return [item.strip() for item in s.split(delim)]
	return []

def make_thread(func, *args):
	thread = threading.Thread(target = func, args = args)
	# Daemon-Threads werden automatisch gekillt, wenn der Prozess beendet
	# wird. Das könnte helfen, dass KODI beendet werden kann, wenn ein
	# Thread sich aufhängt.
	if hasattr(thread, 'daemon'): thread.daemon = True
	else: thread.setDaemon()
	return thread

def getUrl(url, header=None, data=None, agent='okhttp/3.3.1', decode=json.loads):
	opener = build_opener()
	opener.addheaders = [('User-Agent', agent), ('Accept-Encoding', 'gzip, identity')]
	try:
		if header: opener.addheaders = header
		response = opener.open(url, data=data, timeout=30)
		content = response.read()
		if response.info().get('Content-Encoding') == 'gzip':
			content = gzip.GzipFile(fileobj=io.BytesIO(content)).read()
	except Exception as e:
		failure = str(e)
		failing("(getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
		xbmcgui.Dialog().notification(translation(30521).format('URL'), "ERROR = [COLOR red]{0}[/COLOR]".format(failure), icon, 15000)
		return sys.exit(0)
	return decode(content)

def ADDON_operate(INPUT_STREAM):
	js_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.GetAddonDetails", "params": {"addonid":"'+INPUT_STREAM+'", "properties": ["enabled"]}, "id":1}')
	if '"enabled":false' in js_query:
		try:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.SetAddonEnabled", "params": {"addonid":"'+INPUT_STREAM+'", "enabled":true}, "id":1}')
			failing("(ADDON_operate) ERROR - ERROR - ERROR :\n##### Das benötigte Addon : *inputstream.adaptive* ist NICHT aktiviert !!! #####\n##### Es wird jetzt versucht die Aktivierung durchzuführen !!! #####")
		except: pass
	if '"error":' in js_query:
		xbmcgui.Dialog().ok(addon.getAddonInfo('id'), translation(30501))
		failing("(ADDON_operate) ERROR - ERROR - ERROR :\n##### Das benötigte Addon : *inputstream.adaptive* ist NICHT installiert !!! #####\n##### Bitte KODI-Krypton (Version 17 oder höher) installieren, Diese enthalten das erforderliche Addon im Setup !!! #####")
		return False
	if '"enabled":true' in js_query:
		return True

class Session:
	def __init__(self):
		try:
			self.json = getUrl(NEXX_URL+"session/init",
			  data = "nxp_devh=1548081216:390&nxp_userh&precid=0&playlicense=0&gateway=html5&adGateway&explicitlanguage=de&supportsAdStreamtypes=1&addTextTemplates=1&addDomainData=1&addAdModel=1")
			self.cid = self.get_prop('result', 'general', 'cid')
		except ValueError:
			failing("(init_session) ERROR: Can't get cid")
			notify_err("ERROR fetching Video URL", "Can't get CID")
			sys.exit(0)
	def fetch(self, url, *args, **kwargs):
		self.json = getUrl(NEXX_URL+url, *args, 
		  header = [
		    ('X-Request-CID', self.cid),
		    ('X-Request-Token', 'cc044bba23acddecbe83e60a7e8ffb16')
		  ],
		  **kwargs
		)
		return self.json
	def get_prop(self, *args):
		data = self.json
		for prop in args:
			if not isinstance(data, dict): raise ValueError
			try:
				if isinstance(prop, tuple):
					data = data.get(*prop)
				else:
					data = data[prop]
			except KeyError:
				raise ValueError
		return data

def dict_get(d, *keys):
	for key in keys:
		try: d = d[key]
		except KeyError: return None
	return d

def index():
	addDir(translation(30601), 'listOverview')
	listSections()
	if enableAdjustment:
		addDir(translation(30602), 'aSettings')
		if enableInputstream:
			if ADDON_operate('inputstream.adaptive'):
				addDir(translation(30603), 'iSettings')
			else: addon.setSetting('inputstream', 'false')
	xbmcplugin.endOfDirectory(pluginhandle)

def listOverview():
	data = getUrl(baseURL+'overview/all')
	for i, item in enumerate(data['result']):
		if item['items']:
			addDir(unescape(item['title']), 'listType',
			  ','.join(str(series['id']) for series in item['items']))
		elif item['type'] == 'Filme':
			addDir(unescape(item['title']), 'listMovies')
	xbmcplugin.endOfDirectory(pluginhandle)

def get_fsk18_movies(data):
	if not fsk18: return
	IDs = set()
	ID_lock = threading.Lock()
	domain_paths = set(movie['domain_path'] for movie in data)
	# General information, needed by all threads
	threads = []
	std_info = (
	  # 0: All found IDs, by movie they come after
	  [[] for _ in range(len(data)+1)],
	  # 1: All known links
	  dict((urljoin(WEBSITE_URL, movie['slug']).rstrip('/'), i)
	       for i, movie in enumerate(data, 1)),
	  # 2: Synchronisation for 0 and 1
	  threading.Lock(),
	  # 3: All previously known IDs (only for reading)
	  set(movie['general']['ID'] for movie in data),
	  # 4: All started threads. list.append is atomic, so no lock needed
	  threads,
	)
	threads.extend(make_thread(get_domain_path, path,
	  set(urljoin(WEBSITE_URL, movie['slug'])
	    for movie in data if movie['domain_path'] == path),
	  std_info
	) for path in domain_paths)
	my_thread = threads.pop()
	for thread in threads: thread.start()
	# Andere threads dürfen maximal doppelt so lang wie dieser hier brauchen.
	start_time = time.time()
	# Ein Thread wird nicht gestartet, sondern hier ausgeführt.
	# Falls da ein Fehler drin ist, lässt er sich killen!
	my_thread.run()
	end_time = max(2 * time.time() - start_time, start_time + 30)
	for thread in threads:
		thread.join(end_time - time.time())
		if thread.isAlive():
			# Threads können nicht gekillt werden => Die Kacke ist am Dampfen
			notify_err("THREADING ERROR!", "A thread doesn't finish!")
			break
	byid = {}
	IDs = [ID for sub in std_info[0] for ID in sub if ID is not None]
	# Nichts gefunden?
	if not IDs: return
	for movie in getUrl(baseURL+'nexx/videos/multi?videos='+
	  ','.join(IDs))['result']:
		byid[str(movie['general']['ID'])] = movie
	add = 0
	for i, IDs in enumerate(std_info[0]):
		for ID in IDs:
			try:
				movie = byid[ID]
			except KeyError: pass
			else:
				# Wir wollen nur Filme
				if movie['general']['videotype'] != 'movie': continue
				data.insert(i + add, movie)
				add += 1

def get_domain_path(path, slugs, std_info):
	abs_path = urljoin(WEBSITE_URL, path)
	debug_MS("(get_domain_path) Fetching : "+abs_path)
	data = getUrl(abs_path, agent = WEBSITE_AGENT, decode = BeautifulSoup)
	links = {}
	for link in data('a',
	  href = lambda h: urljoin(abs_path, h).rstrip('/') in slugs):
		links.setdefault(urljoin(abs_path, link['href']), []).append(link)
		debug_MS("(get_domain_path) Found link : "+link['href'])
	if not links: return
	links = links.values()
	variants = [
	  (elem, dict((attr, set(value) if isinstance(value, list) else value)
		for attr, value in elem.attrs.items()))
	  for elem in links.pop()
	]
	for link in links:
		next_variants = []
		for elem in link:
			for parent, attr in variants:
				new_variant = (get_common_parent(parent, elem),
				               attr_intersect_elem(attr, elem))
				for i, old_variant in enumerate(next_variants):
					if is_better_test(new_variant, old_variant):
						next_variants.pop(i)
					elif is_better_test(old_variant, new_variant):
						# Die obere Bedingung wird auch nicht mehr passieren
						break
				else:
					next_variants.append(new_variant)
		variants = next_variants
		debug_MS("(get_domain_path) variants = "+repr(variants))
	if not variants:
		# Das dürfte auf keinen Fall passieren
		failing("(get_domain_path) Keine Kriterien gefunden : "+domain_path)
		return
	attr = variants[0][1]
	debug_MS("(get_domain_path) Common parent tag : "+variants[0][0].name+
	  '; attributes = '+repr(attr))
	links = variants[0][0].find_all(
	  lambda tag: tag.name == 'a' and attr_subset_elem(attr, tag)
	)
	idx = 0
	thread = None
	with std_info[2]:
		for link in links:
			link = urljoin(abs_path, link['href'])
			slink = link.rstrip('/')
			try: n_idx = std_info[1][slink]
			except KeyError:
				debug_MS("(get_domain_path) Found unknown movie : "+link)
				std_info[1][slink] = None
				l = len(std_info[0][idx])
				std_info[0][idx].append(None)
				if thread is not None:
					std_info[4].append(thread)
					thread.start()
				thread = make_thread(extract_id, link, idx, l, std_info)
			else:
				if n_idx is not None: idx = n_idx
	# Anzahl der threads minimieren
	if thread is not None: thread.run()

player_regex = re.compile('^player_(\d+)$', re.ASCII if PY3 else 0)
def extract_id(link, i, j, std_info):
	soup = getUrl(link, agent = WEBSITE_AGENT, decode = BeautifulSoup)
	elem = soup.find(attr = {'data-id': True})
	if elem is None:
		elem = soup.find(id = player_regex)
		if elem is None:
			# Keine ID rauszufinden
			debug_MS("(extract_id) Keine ID gefunden : "+link)
			return
		ID = player_regex.match(elem['id']).group(1)
	else:
		ID = elem['data-id']
	debug_MS("(extract_id) link = "+link+" (ID = "+str(ID)+")")
	if int(ID) in std_info[3]: return
	with std_info[2]:
		if ID not in (ID for group in std_info[0] for ID in group):
			std_info[0][i][j] = ID

def get_common_parent(a, b):
	ids = set(map(id, b.parents))
	if id(a) in ids: return a
	for parent_a in a.parents:
		if id(parent_a) in ids: return parent_a

def attr_intersect_elem(a, b):
	return dict(
	  (attr, value.intersection(b[attr]) if isinstance(value, set) else value)
	  for attr, value in a.items()
	  if b.has_attr(attr) and
	  (isinstance(value, list) or value == b[attr])
	)

def attr_subset_elem(a, b):
	return all(b.has_attr(attr) and (va.issubset(b[attr])
	    if isinstance(va, set) else va == b[attr])
	  for attr, va in a.items())

def attr_subset(a, b):
	return all(attr in b and (va <= b[attr] if isinstance(va, set)
	  else va == b[attr]) for attr, va in a.items())

def is_parent(a, b):
	return a is b or id(a) in map(id, b.parents)

def is_better_test((pa, aa), (pb, ab)):
	return is_parent(pb, pa) and attr_subset(ab, aa)

def listMovies():
	debug_MS("(listMovies) BEGIN")
	data = getUrl(baseURL+'nexx/videos/movies/all')['result']
	get_fsk18_movies(data) # Verändert data
	for movie in data: listVideo(movie)
	xbmcplugin.endOfDirectory(pluginhandle)

def listSchlefaz():
	data = getUrl(baseURL+'nexx/videos/all?type=movie&channel=29864')['result']
	debug_MS('(listSchlefaz) 1: '+str(next((m for m in data if m['general']['ID'] == '1554421'), None)))
	get_fsk18_movies(data)
	debug_MS('(listSchlefaz) 2: '+str(next((m for m in data if m['general']['ID'] == 1554421), None)))
	for movie in data: listVideo(movie)
	xbmcplugin.endOfDirectory(pluginhandle)

series_cache = {}
def get_series(ID):
	try: cached = series_cache[int(ID)]
	except KeyError: pass
	else: return cached
	series_cache[int(ID)] = info = getUrl(baseURL+'nexx/series/byid/'+str(ID))
	return info

remove_irrelevant = re.compile('[^A-Za-z0-9]')
def get_teaser_desc(info):
	debug_MS("(get_teaser_desc) teaser = "+repr(info['teaser'])+
	  '; description = '+repr(info['description']))
	desc = remove_irrelevant.sub('', info['description'])
	teaser = remove_irrelevant.sub('', info['teaser'])
	if not desc or desc in teaser: return info['teaser']
	if not teaser or teaser in desc: return info['description']
	return info['teaser']+'\n\n'+info['description']

def listType(ID):
	debug_MS("(listType) BEGIN "+ID)
	items = getUrl(baseURL+'nexx/series/multi?series='+ID)['result']
	for item in items:
		if item['available_episodes']:
			addDir(unescape(item['result']['general']['title']), 'listSeries',
			  item['result']['general']['ID'],
			  item['result']['imagedata']['thumb'],
			  unescape(get_teaser_desc(item['result']['general'])),
			  'tvshow'
			)
	xbmcplugin.endOfDirectory(pluginhandle)

def listSeries(ID):
	data = get_series(int(ID))
	available = [str(season) for season in sorted(data['available_seasons'])]
	if not available:
		failing("(listSeries) No seasons found (ID = "+ID+")")
		return
	if (len(available) <= 2 if data['available_episodes'] <= 6 else
	  len(available) == 1):
		for season in available:
			listSeasonPart(ID, season)
	else:
		for season in available:
			addDir(translation(30604).format(season), 'listSeason',
			  ID, data['result']['imagedata']['thumb'], season = season)
	xbmcplugin.endOfDirectory(pluginhandle)

def listSeason(ID, season):
	listSeasonPart(ID, season)
	xbmcplugin.endOfDirectory(pluginhandle)

def listSeasonPart(ID, season):
	data = getUrl(baseURL+'nexx/series/byid/'+ID+'?season='+season)
	series_cache[int(ID)] = data
	episodes = data['episodes']
	episodes.sort(key=lambda video: video['episodedata']['episode'])
	for video in episodes: listVideo(video)

def listPlaylist(ID):
	listPlaylistPart(getUrl(baseURL+'nexx/playlists/byid/'+ID))
	xbmcplugin.endOfDirectory(pluginhandle)

def listPlaylistPart(data):
	videos = data['videos']
	"""
	if not videos:
		seasondata = data['result']['seasondata']
		series = seasondata['series']
		season = seasondata['season']
		videos = [episode for episode
			in get_series(series)['episodes']
			if episode['episodedata']['season'] == season
		]
	"""
	for video in videos: listVideo(video)

def listSections():
	for idx, section in enumerate(getUrl(baseURL+'sections/published/all')
	  ['sections']):
		if 'items' in section:
			addDir(unescape(section['title']), 'listSection', idx)
		else:
			try: pl_type = section['playlistType']
			except KeyError: continue
			if pl_type == 'all movies': mode = 'listMovies'
			elif pl_type == 'schlefaz': mode = 'listSchleFaZ'
			elif pl_type == 'custom':
				addDir(unescape(section['title']), 'listPlaylist',
				  section['playlistId'])
				continue
			else: continue
			addDir(unescape(section['title']), mode)

def listSection(idx):
	idx = int(idx)
	arr = { "video": [], "playlist": [], "series": [] }
	info = getUrl(baseURL+'sections/published/all')['sections'][idx]['items']
	for item in info:
		try: arr[item['mediaType']].append(str(item['id']))
		except KeyError: pass
	debug_MS(repr(arr))
	fetched = { 'video': {}, 'playlist': {}, 'series': series_cache }
	for t, l in arr.items():
		if not l: continue
		if t == 'series': u = t
		else: u = t+'s'
		for item in \
		  getUrl(baseURL+'nexx/'+u+'/multi?'+u+'='+','.join(l))['result']:
			fetched[t][(item if t == 'video' else item['result'])
			  ['general']['ID']] = item
	for item in info:
		try: data = fetched[item['mediaType']][item['id']]
		except KeyError: continue
		if item['mediaType'] == 'video': listVideo(data)
		elif item['mediaType'] == 'series' and not data['available_episodes']:
			pass
		else:
			addDir(unescape(data['result']['general']['title']),
			  'listSeries' if item['mediaType']=='series' else 'listPlaylist',
			  data['result']['general']['ID'],
			  data['result']['imagedata']['thumb'],
			  unescape(get_teaser_desc(data['result']['general'])))
	xbmcplugin.endOfDirectory(pluginhandle)

def makeListItem(info):
	thumb = info['imagedata']['thumb']
	poster = info['imagedata']['thumb_alt']
	if 'nodata' in poster: poster = thumb
	title = unescape(info['general']['title'])
	try: episodedata = info['episodedata']
	except KeyError:
		episodedata = {}
		series = None
	else:
		if 'Folge '+str(episodedata['episode']) not in title:
			title = ('[COLOR chartreuse]'+episodedata['episodeIndex']+
			  ':[/COLOR] '+title)
		series = unescape(get_series(episodedata['series'])
		  ['result']['general']['title'])

	if info['restrictiondata']['validUntil']:
		expiry_date = datetime.fromtimestamp(
		  info['restrictiondata']['validUntil'])
		diff = expiry_date - datetime.now()
		if diff.days < 0: return None
		if showRemainingTime == AVAILABILITY_END:
			note = translation(30605).format(expiry_date.strftime(
			  dateformat if diff.days else timeformat))
		elif showRemainingTime == AVAILABILITY_REMAIN:
			if diff.days: left = str(diff.days)+'d'
			elif diff.seconds >= 3600: left = str(diff.seconds // 3600)+'h'
			else: left = str(diff.seconds // 60)+'min'
			note = translation(30606).format(left)
		else: note = ''
		if note:
			if 86400 * diff.days + diff.seconds < max_rest_warn:
				title += '  [COLOR orangered]('+note+')[/COLOR]'
				note = ''
			else: note = note.capitalize()+'\n'
	else: note = ''
	duration = decode_duration(info['general']['runtime'])
	mediatype = info['general']['videotype']
	if mediatype not in ['movie', 'episode', 'musicvideo']: mediatype = 'video'
	liz = xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=thumb)
	released = info['general']['releasedate']
	if released:
		try: year = time.gmtime(released).tm_year
		except ValueError: # cannot handle value before YEAR=1970
			published = datetime(1970, 1, 1) + timedelta(seconds=int(released))
			year = published.strftime('%Y')
	else: year = None
	fsk = info['general']['ages']
	if fsk:
		mpaa = 'Ab '+str(fsk)+' Jahren'
		if fsk == 18: note += mpaa+'\n'
	else: mpaa = None
	if note: note += '\n'
	liz.setInfo(type="Video", infoLabels = {
		'episode': episodedata.get('episode', None),
		'season': episodedata.get('season', None),
		'tvshowtitle': series,
		'cast': explode(unescape(info['general']['persons'])),
		'director': unescape(info['general']['director']) or None,
		'writer': unescape(info['general']['scriptby']) or None,
		'credits': maybe_explode(unescape(info['general']['producer'])),
		'studio': unescape(info['general']['studio'] or '') or None,
		'plot': note+unescape(get_teaser_desc(info['general'])),
		'mpaa': mpaa,
		'title': title,
		'duration': duration,
		'mediatype': mediatype,
		'year': year,
		'genre': maybe_explode(unescape(info['general']['genre']))
	})
	liz.setArt({'poster': poster})
	if useThumbAsFanart: liz.setArt({'fanart': thumb})
	else: liz.setArt({'fanart': defaultFanart})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	return liz

def listVideo(info):
	liz = makeListItem(info)
	if liz is None: return
	u = sys.argv[0]+"?mode=play&id="+str(info['general']['ID'])
	liz.addContextMenuItems([(translation(30651), 'RunPlugin(plugin://{0}?mode=addVideoList&id={1})'.format(addon.getAddonInfo('id'), info['general']['ID']))])
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

def play(ID):
	debug_MS("(play) ------ START --------")
	session = Session()
	try:
		session.fetch("videos/byid/"+ID,
		  data = 'additionalfields=language,channel,format,persons,studio,licenseby,slug,fileversion,contentModerationAspects&addInteractionOptions=1&addStatusDetails=1&addStreamDetails=1&addFeatures=1&addCaptions=1&addScenes=1&addHotSpots=1&addBumpers=1&captionFormat=data')
		result = session.get_prop('result')
		if isinstance(result, list):
			result = next(r for r in result if str(r['general']['ID']) == ID)
		locator = result['streamdata']['azureLocator']
	except (ValueError, StopIteration):
		failing("(play) ERROR: Can't get locator")
		notify_err("Error finding Video URL", "Bad response")
		return
	path = ('https://tele5nexx.akamaized.net/'+
	  locator+'/'+ID+'_src.ism/Manifest(format=m3u8-aapl)')
	debug_MS(path)
	listitem = xbmcgui.ListItem(path = path)
	if enableInputstream:
		if ADDON_operate('inputstream.adaptive'):
			listitem.setMimeType('application/vnd.apple.mpegurl')
			listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
			listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
		else:
			addon.setSetting("inputstream", "false")
	listitem.setContentLookup(False)
	xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def addVideoList(ID):
	PL = xbmc.PlayList(1)
	info = getUrl(baseURL+'nexx/videos/byid/'+ID)['result']
	liz = makeListItem(info)
	if liz is None: return
	liz.setContentLookup(False)
	PL.add(sys.argv[0]+"?mode=play&id="+str(info['general']['ID']), liz)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, mode, ID=None, image=icon, plot=None, mediatype=None, season=None):
	debug_MS('(addDir) ID = '+str(ID))
	u = (sys.argv[0]+"?mode="+mode+
	  ("" if ID is None else "&id="+str(ID))+
	  ("" if season is None else "&season="+str(season))
	)
	debug_MS('(addDir) URL = '+u)
	liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=image)
	liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": plot})
	liz.setArt({'poster': image})
	if useThumbAsFanart and image != icon:
		liz.setArt({'fanart': image})
	else:
		liz.setArt({'fanart': defaultFanart})
	return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)

params = parameters_string_to_dict(sys.argv[2])
ID = unquote_plus(params.get('id', '0'))
mode = unquote_plus(params.get('mode', ''))

if mode == 'aSettings':
	addon.openSettings()
elif mode == 'iSettings':
	xbmcaddon.Addon('inputstream.adaptive').openSettings()
elif mode == 'listMovies':
	listMovies()
elif mode == 'listSchleFaZ':
	listSchlefaz()
elif mode == 'listType':
	listType(ID)
elif mode == 'listSeries':
	listSeries(ID)
elif mode == 'listSeason':
	listSeason(ID, unquote_plus(params['season']))
elif mode == 'listPlaylist':
	listPlaylist(ID)
elif mode == 'listSections':
	listSections()
elif mode == 'listSection':
	listSection(ID)
elif mode == 'listOverview':
	listOverview()
elif mode == 'play':
	play(ID)
elif mode == 'addVideoList':
	addVideoList(ID)
else:
	index()
