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
import base64


global debuging
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath    = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
temp           = xbmc.translatePath(os.path.join(dataPath, 'temp', '')).encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
artpic = os.path.join(addonPath, 'resources', 'media', '').encode('utf-8').decode('utf-8')
NEXT_BEFORE_PAGE = addon.getSetting('NEXT_BEFORE') == 'true'
Zertifikat = addon.getSetting('inetCert')
DEB_LEVEL = (xbmc.LOGNOTICE if addon.getSetting('enableDebug') == 'true' else xbmc.LOGDEBUG)
baseURL = 'http://www.filmstarts.de'

xbmcplugin.setContent(pluginhandle, 'movies')

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)

if Zertifikat == 'false':
	try: _create_unverified_https_context = ssl._create_unverified_context
	except AttributeError: pass
	else: ssl._create_default_https_context = _create_unverified_https_context

if xbmcvfs.exists(temp) and os.path.isdir(temp):
	shutil.rmtree(temp, ignore_errors=True)
	xbmc.sleep(500)
xbmcvfs.mkdirs(temp)
cookie = os.path.join(temp, 'cookie.lwp')
cj = LWPCookieJar()

if xbmcvfs.exists(cookie):
	cj.load(cookie, ignore_discard=True, ignore_expires=True)

if xbmcvfs.exists(cookie):
	cj.load(cookie, ignore_discard=True, ignore_expires=True)

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
	xbmc.log("["+addon.getAddonInfo('id')+"-"+addon.getAddonInfo('version')+"]"+py2_enc(msg), level)

def getUrl(url, header=None, referer=None, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36'):
	global cj
	opener = build_opener(HTTPCookieProcessor(cj))
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
	try: cj.save(cookie, ignore_discard=True, ignore_expires=True)
	except: pass
	return content

def index():
	addDir(translation(30601), "", 'trailer', icon)
	addDir(translation(30602), "", 'kino', icon)
	addDir(translation(30603), "", 'series', icon)
	addDir(translation(30604), "", 'news', icon)
	addDir(translation(30608), "", 'aSettings', artpic+'settings.png')
	xbmcplugin.endOfDirectory(pluginhandle)

def trailer():
	addDir(translation(30620), baseURL+"/trailer/beliebteste.html", 'listTrailer', icon)
	addDir(translation(30621), baseURL+"/trailer/imkino/", 'listTrailer', icon)
	addDir(translation(30622), baseURL+"/trailer/bald/", 'listTrailer', icon)
	addDir(translation(30623), baseURL+"/trailer/neu/", 'listTrailer', icon)
	addDir(translation(30624), baseURL+"/trailer/archiv/", 'filtertrailer', icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def kino():
	addDir(translation(30630), baseURL+"/filme-imkino/vorpremiere/", 'listKino_small', icon)
	addDir(translation(30631), baseURL+"/filme-imkino/kinostart/", 'listKino_big', icon, datum="N")
	addDir(translation(30632), baseURL+"/filme-imkino/neu/", 'listKino_big', icon, datum="J")
	addDir(translation(30633), baseURL+"/filme-imkino/besten-filme/user-wertung/", 'listKino_big', icon, datum="N")
	addDir(translation(30634), baseURL+"/filme-vorschau/de/", 'selectionWeek', icon)
	addDir(translation(30635), baseURL+"/filme/besten/user-wertung/", 'filterkino', icon)
	addDir(translation(30636), baseURL+"/filme/schlechtesten/user-wertung/", 'filterkino', icon)
	addDir(translation(30637), baseURL+"/filme/kinderfilme/", 'filterkino', icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def series():
	addDir(translation(30650), baseURL+"/serien/top/", 'listSeries_big', icon, datum="N")
	addDir(translation(30651), baseURL+"/serien/beste/", 'filterserien', icon)
	addDir(translation(30652), baseURL+"/serien/top/populaerste/", 'listSeries_big', icon, datum="N")
	addDir(translation(30653), baseURL+"/serien/kommende-staffeln/meisterwartete/", 'listSeries_big', icon, datum="N")
	addDir(translation(30654), baseURL+"/serien/kommende-staffeln/", 'listSeries_big', icon, datum="N")
	addDir(translation(30655), baseURL+"/serien/kommende-staffeln/demnaechst/", 'listSeries_big', icon, datum="N")
	addDir(translation(30656), baseURL+"/serien/neue/", 'listSeries_big', icon, datum="N")
	addDir(translation(30657), baseURL+"/trailer/serien/neueste/", 'listSpecial_Series_Trailer', icon)
	addDir(translation(30658), baseURL+"/serien-archiv/", 'filterserien', icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def news():
	addDir(translation(30670), baseURL+"/videos/shows/funf-sterne/", 'listNews', icon)
	addDir(translation(30671), baseURL+"/videos/shows/filmstarts-fehlerteufel/", 'listNews', icon)
	addDir(translation(30672), baseURL+"/trailer/interviews/", 'listNews', icon)
	addDir(translation(30673), baseURL+"/videos/shows/meine-lieblings-filmszene/", 'listNews', icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def filtertrailer(url):
	debug_MS("(filtertrailer) -------------------------------------------------- START = filtertrailer --------------------------------------------------")
	debug_MS("(filtertrailer) ##### URL={0} #####".format(url))
	if not "genre-" in url:
		addDir(translation(30801), url, 'selectionCategories', icon, type="filtertrailer", CAT_text="Nach Genre")
	if not "sprache-" in url:
		addDir(translation(30802), url, 'selectionCategories', icon, type="filtertrailer", CAT_text="Nach Sprache")
	if not "format-" in url:
		addDir(translation(30803), url, 'selectionCategories', icon, type="filtertrailer", CAT_text="Nach Typ")
	addDir(translation(30810), url, 'listSpecial_Series_Trailer', icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def filterkino(url):
	debug_MS("(filterkino) -------------------------------------------------- START = filterkino --------------------------------------------------")
	debug_MS("(filterkino) ##### URL={0} #####".format(url))
	if not "genre-" in url:
		addDir(translation(30801), url, 'selectionCategories', icon, type="filterkino", CAT_text="Alle Genres")
	if not "jahrzehnt" in url:
		addDir(translation(30804), url, 'selectionCategories', icon, type="filterkino", CAT_text="Alle Jahre")
	if not "produktionsland-" in url:
		addDir(translation(30805), url, 'selectionCategories', icon, type="filterkino", CAT_text="Alle Länder")
	addDir(translation(30810), url, 'listKino_small', icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def filterserien(url):
	debug_MS("(filterserien) -------------------------------------------------- START = filterserien --------------------------------------------------")
	debug_MS("(filterserien) ##### URL={0} #####".format(url))
	if not "genre-" in url:
		if "serien-archiv" in url: CAT_text = "Nach Genre"
		else: CAT_text="Alle Genres"
		addDir(translation(30801), url, 'selectionCategories', icon, type="filterserien", CAT_text=CAT_text)
	if not "jahrzehnt" in url:
		if "serien-archiv" in url: CAT_text = "Nach Produktionsjahr"
		else: CAT_text="Alle Jahre"
		addDir(translation(30804), url, 'selectionCategories', icon, type="filterserien", CAT_text=CAT_text)
	if not "produktionsland-" in url:
		if "serien-archiv" in url: CAT_text = "Nach Land"
		else: CAT_text="Alle Länder"
		addDir(translation(30805), url, 'selectionCategories', icon, type="filterserien", CAT_text=CAT_text)
	if "serien-archiv" in url:
		addDir(translation(30810), url, 'listSeries_big', icon, datum="N")
	else:
		addDir(translation(30810), url, 'listSeries_small', icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def selectionCategories(url, type="", CAT_text=""):
	debug_MS("(selectionCategories) -------------------------------------------------- START = selectionCategories --------------------------------------------------")
	debug_MS("(selectionCategories) ##### URL={0} ##### TYPE={1} ##### TEXT={2} #####".format(url, type, CAT_text))
	content = getUrl(url)
	if "archiv/" in url:
		result = content[content.find('data-name="'+CAT_text+'"')+1:]
		result = result[:result.find('</ul>')]
		part = result.split('class="filter-entity-item"')
	else:
		result = content[content.find(CAT_text+'</span>')+1:]
		result = result[:result.find('</li></ul>')]
		part = result.split('</li><li')
	for i in range(1,len(part),1):  
		element=part[i]
		element = element.replace('<strong>', '').replace('</strong>', '')
		try:
			try: number = re.compile(r'<span class=["\'](?:light|lighten)["\']>\(([^<]+?)\)</span>', re.DOTALL).findall(element)[0].strip() 
			except: number = ""
			if 'href=' in element:
				matchUN = re.compile(r'href=["\']([^"]+)["\'](?: title=.+?["\']>|>)([^<]+?)</a>', re.DOTALL).findall(element)
				link = matchUN[0][0]
				name = matchUN[0][1].strip()
			else:
				try:
					matchUN = re.compile(r'<span class=["\']ACr([^"]+) item-content["\'] title=.+?["\']>([^<]+?)</span>', re.DOTALL).findall(element)
					oldURL = matchUN[0][0].replace('ACr', '')
					link = base64.b64decode(oldURL).decode('utf-8', 'ignore')
					name = matchUN[0][1].strip()
				except:
					matchUN = re.compile(r'<span class=["\']acLnk ([^"]+)["\']>([^<]+?)</span>', re.DOTALL).findall(element)  
					link = decodeURL(matchUN[0][0])
					name = matchUN[0][1].strip()
			if number != "": name += "   ("+str(number)+")"
			addDir(name, baseURL+link, type, icon)
			debug_MS("(selectionCategories) Name : {0}".format(name))
			debug_MS("(selectionCategories) Link : {0}".format(baseURL+link))
		except:
			failing("..... exception .....")
			failing("(selectionCategories) Fehler-Eintrag : {0} #####".format(str(element)))
	xbmcplugin.endOfDirectory(pluginhandle)

def selectionWeek(url):
	debug_MS("(selectionWeek) -------------------------------------------------- START = selectionWeek --------------------------------------------------")
	debug_MS("(selectionWeek) ##### URL={0} #####".format(url))
	content = getUrl(url)
	result = content[content.find('<div class="pagination pagination-select">')+1:]
	result = result[:result.find('<span class="txt">Nächste</span><i class="icon icon-right icon-arrow-right-a">')]
	matchUN = re.compile(r'<option value=["\']ACr([^"]+)["\']([^<]+)</option>', re.DOTALL).findall(result)
	for oldURL, title in matchUN:
		oldURL = oldURL.replace('ACr', '')
		link = base64.b64decode(oldURL).decode('utf-8', 'ignore')
		datum = str(link.replace('filme-vorschau/de/week-', '').replace('/', ''))
		title = title.replace('>', '')
		if "selected" in title:
			title = title.replace('selected', '')
			name = "[I][COLOR lime]"+cleanTitle(title)+translation(30831)+"[/COLOR][/I]"
		else: name = cleanTitle(title)
		debug_MS("(selectionWeek) Name : {0}".format(name))
		debug_MS("(selectionWeek) Datum : {0}".format(datum))
		addDir(name, baseURL+"/filme-vorschau/de/week-", 'listKino_big', icon, datum=datum)
	xbmcplugin.endOfDirectory(pluginhandle)

def listTrailer(url, page=1):
	debug_MS("(listTrailer) -------------------------------------------------- START = listTrailer --------------------------------------------------")
	page = int(page)
	if page > 1:
		PGurl = url+"?page="+str(page)
	else: PGurl = url
	debug_MS("(listTrailer) ##### URL={0} ##### PAGE={1} #####".format(PGurl, str(page)))
	content = getUrl(PGurl)
	selection = re.findall('<div class="card video-card-trailer(.+?)<span class="thumbnail-count">', content, re.DOTALL)
	for chtml in selection:
		try:
			image = re.compile(r'src=["\'](https?://.+?(?:[0-9]+\.png|[a-z]+\.png|[0-9]+\.jpg|[a-z]+\.jpg|[0-9]+\.gif|[a-z]+\.gif))["\'\?]', re.DOTALL|re.IGNORECASE).findall(chtml)[0]
			photo = enlargeIMG(image)
			matchUN = re.compile('<a href=["\']([^"]+)["\'] class=["\']layer-link["\']>([^<]+)</a>', re.DOTALL).findall(chtml)
			link = matchUN[0][0]
			title = matchUN[0][1]
			name = cleanTitle(title)
			debug_MS("(listTrailer) Name : {0}".format(name))
			debug_MS("(listTrailer) Link : {0}".format(baseURL+link))
			debug_MS("(listTrailer) Icon : {0}".format(photo))
			addLink(name, baseURL+link, 'playVideo', photo, extraURL=url)
		except:
			failing("..... exception .....")
			failing("(listTrailer) Fehler-Eintrag : {0} #####".format(str(chtml)))
	try:
		nextP = re.compile(r'class=["\']((?:ACr[^<]+</span></div></nav>    </section>|button button-md item["\'] href=[^<]+</a></div></nav>    </section>))', re.DOTALL).findall(content)[0]
		debug_MS("(listTrailer) Now show NextPage ...")
		addDir(translation(30832), url, 'listTrailer', artpic+"nextpage.png", page=page+1)
	except: pass
	xbmcplugin.endOfDirectory(pluginhandle)

def listSpecial_Series_Trailer(url, page=1, position=0):
	debug_MS("(listSpecial_Series_Trailer) -------------------------------------------------- START = listSpecial_Series_Trailer --------------------------------------------------")
	page = int(page)
	NEPVurl = url
	if page > 1:
		PGurl = url+"?page="+str(page)
	else: PGurl = url
	debug_MS("(listSpecial_Series_Trailer) ##### URL={0} ##### PAGE={1} #####".format(PGurl, str(page)))
	content = getUrl(PGurl)
	if int(position) == 0:
		try:
			position = re.compile('<a class=["\']button button-md item["\'] href=.+?page=[0-9]+["\']>([0-9]+)</a></div></nav>', re.DOTALL).findall(content)[0]
			debug_MS("(listSpecial_Series_Trailer) *FOUND-1* Pages-Maximum : {0}".format(str(position)))
		except:
			try:
				position = re.compile('<span class=["\']ACr.+?button-md item["\']>([0-9]+)</span></div></nav>', re.DOTALL).findall(content)[0]
				debug_MS("(listSpecial_Series_Trailer) *FOUND-2* Pages-Maximum : {0}".format(str(position)))
			except: pass
	result = content[content.find('<main id="content-layout" class="content-layout cf">')+1:]
	result = result[:result.find('<div class="rc-content">')]
	part = result.split('<figure class="thumbnail ">')
	for i in range(1,len(part),1):
		element = part[i]
		element = element.replace('<strong>', '').replace('</strong>', '')
		try:
			try:
				image = re.compile(r'src=["\'](https?://.+?(?:[0-9]+\.png|[a-z]+\.png|[0-9]+\.jpg|[a-z]+\.jpg|[0-9]+\.gif|[a-z]+\.gif))["\'\?]', re.DOTALL|re.IGNORECASE).findall(element)[0]
			except:
				image = re.compile(r'["\']src["\']:["\'](https?://.+?(?:[0-9]+\.png|[a-z]+\.png|[0-9]+\.jpg|[a-z]+\.jpg|[0-9]+\.gif|[a-z]+\.gif))["\'\?]', re.DOTALL|re.IGNORECASE).findall(element)[0]
			photo = enlargeIMG(image)
			try:
				RuTi = re.compile('class=["\']thumbnail-count["\']>(.+?)</span>', re.DOTALL).findall(element)[0].strip()
				if ":" in RuTi:
					running = re.compile('([0-9]+):([0-9]+)', re.DOTALL).findall(RuTi)
					duration = int(running[0][0])*60+int(running[0][1])
				elif not ":" in RuTi:
					duration = int(RuTi)
			except: duration =""
			matchUN = re.compile(r'class=["\']meta-title-link["\'] href=["\']([^"]+?)["\']([^<]+)</a>', re.DOTALL).findall(element)
			link = matchUN[0][0]
			name = matchUN[0][1].replace(' >', '').replace('>', '')
			name = cleanTitle(name)
			debug_MS("(listSpecial_Series_Trailer) Name : {0}".format(name))
			debug_MS("(listSpecial_Series_Trailer) Link : {0}".format(baseURL+link))
			debug_MS("(listSpecial_Series_Trailer) Icon : {0}".format(photo))
			if link !="" and not "En savoir plus" in name:
				addLink(name, baseURL+link, 'playVideo', photo, duration=duration, extraURL=url)
		except:
			failing("..... exception .....")
			failing("(listSpecial_Series_Trailer) Fehler-Eintrag : {0} #####".format(str(element)))
	if int(position) > page:
		debug_MS("(listSpecial_Series_Trailer) Now show NextPage ...")
		addDir(translation(30832), NEPVurl, 'listSpecial_Series_Trailer', artpic+"nextpage.png", page=page+1, position=position)
	xbmcplugin.endOfDirectory(pluginhandle)

def listKino_big(url, page=1, datum="N", position=0):
	debug_MS("(listKino_big) -------------------------------------------------- START = listKino_big --------------------------------------------------")
	page = int(page)
	FOUND = False
	NEPVurl = url
	if page > 1:
		PGurl = url+"?page="+str(page)
	else: PGurl = url
	if datum !="" and datum !="J" and datum !="N":
		PGurl = PGurl+datum+"/"
	debug_MS("(listKino_big) ##### URL={0} ##### PAGE={1} #####".format(PGurl, str(page)))
	content = getUrl(PGurl)
	if int(position) == 0:
		try:
			position = re.compile('<a class=["\']button button-md item["\'] href=.+?page=[0-9]+["\']>([0-9]+)</a></div></nav>', re.DOTALL).findall(content)[0]
			debug_MS("(listKino_big) *FOUND-1* Pages-Maximum : {0}".format(str(position)))
		except:
			try:
				position = re.compile('<span class=["\']ACr.+?button-md item["\']>([0-9]+)</span></div></nav>', re.DOTALL).findall(content)[0]
				debug_MS("(listKino_big) *FOUND-2* Pages-Maximum : {0}".format(str(position)))
			except: pass
	result = content[content.find('<main id="content-layout" class="content-layout cf">')+1:]
	result = result[:result.find('<div class="rc-content">')]
	part = result.split('<figure class="thumbnail ">')
	for i in range(1,len(part),1):
		element=part[i]
		try:
			matchUN = re.compile('class=["\']ACr([^ "]+) thumbnail-container thumbnail-link["\'] title=["\'](.+?)["\']>', re.DOTALL).findall(element)
			oldURL = matchUN[0][0].replace('ACr', '')
			newURL = base64.b64decode(oldURL).decode('utf-8', 'ignore')
			title = matchUN[0][1]
			name = cleanTitle(title)
			image = re.compile(r'src=["\'](https?://.+?(?:[0-9]+\.png|[a-z]+\.png|[0-9]+\.jpg|[a-z]+\.jpg|[0-9]+\.gif|[a-z]+\.gif))["\'\?]', re.DOTALL|re.IGNORECASE).findall(element)[0]
			photo = enlargeIMG(image)
			if "/serien" in PGurl:
				try: movieDATE = re.compile('<div class=["\']meta-body-item meta-body-info["\']>([^<]+?)<span class=["\']spacer["\']>/</span>', re.DOTALL).findall(element)[0]
				except: movieDATE =""
			else:
				try: movieDATE = re.compile('<span class=["\']date["\']>.*?([a-zA-Z]+ [0-9]+)</span>', re.DOTALL).findall(element)[0]
				except: movieDATE =""
			if movieDATE != "" and "/serien" in PGurl:
				name = name+"   ("+str(movieDATE.replace('\n', '').replace(' - ', '~').replace('läuft seit', 'ab').strip())+")"
			elif movieDATE != "" and "besten-filme/user-wertung" in PGurl:
				newDATE = cleanMonth(movieDATE.lower())
				name = name+"   ("+str(newDATE)+")"
			try: # Grab - Genres
				result_1 = re.compile('<span class=["\']spacer["\']>/</span>(.+?)</div>', re.DOTALL).findall(element)[-1]
				matchG = re.compile('<span class=["\']ACr.*?["\']>(.+?)</span>', re.DOTALL).findall(result_1)
				genres = []
				for gNames in matchG:
					gNames = cleanTitle(gNames)
					genres.append(gNames)
				gGenre =", ".join(genres)
			except: gGenre =""
			try: # Grab - Directors
				result_2 = re.compile('<div class=["\']meta-body-item meta-body-direction light["\']>(.+?)</div>', re.DOTALL).findall(element)[-1]
				matchD = re.compile('<span class=["\']ACr.*?["\']>(.+?)</span>', re.DOTALL).findall(result_2)
				directors = []
				for dNames in matchD:
					dNames = cleanTitle(dNames)
					directors.append(dNames)
				dDirector =", ".join(directors)
			except: dDirector =""
			try: # Grab - Plot
				desc = re.compile('<div class=["\']synopsis["\']>(.+?)</div>', re.DOTALL).findall(element)[0]
				plot = re.sub(r'\<.*?\>', '', desc)
				plot = cleanTitle(plot)
			except: plot=""
			try: # Grab - Rating
				result_3 = element[element.find('User-Wertung')+1:]
				rRating = re.compile('class=["\']stareval-note["\']>([^<]+?)</span></div>', re.DOTALL).findall(result_3)[0].strip().replace(',', '.')
			except:
				try:
					result_3 = element[element.find('Pressekritiken')+1:]
					rRating = re.compile('class=["\']stareval-note["\']>([^<]+?)</span></div>', re.DOTALL).findall(result_3)[0].strip().replace(',', '.')
				except: rRating =""
			video = re.compile('<div class=["\']buttons-holder["\']>(.+?)</div>', re.DOTALL).findall(element)
			debug_MS("(listKino_big) Name : {0}".format(name))
			debug_MS("(listKino_big) Link : {0}".format(baseURL+newURL))
			debug_MS("(listKino_big) Icon : {0}".format(photo))
			debug_MS("(listKino_big) Regie : {0}".format(dDirector))
			debug_MS("(listKino_big) Genre : {0}".format(gGenre))
			if video and ("Trailer" in video[0] or "Teaser" in video[0]) and not 'button btn-disabled' in element:
				FOUND = True
				addLink(name, baseURL+newURL, 'playVideo', photo, plot, gGenre, dDirector, rRating, extraURL=url)
			else:
				FOUND = True
				addDir(name+translation(30835), "", 'listKino_big', photo, plot, gGenre, dDirector, rRating)
		except:
			failing("..... exception .....")
			failing("(listKino_big) Fehler-Eintrag : {0} #####".format(str(element)))
	if not FOUND:
		return xbmcgui.Dialog().notification(translation(30523), translation(30524), icon, 8000)
	if NEXT_BEFORE_PAGE and datum !="" and datum !="J" and datum !="N":
		try:
			LEFT = re.compile(r'<span class=["\']ACr([^ "]+) button button-md button-primary-full button-left["\']>.*?span class=["\']txt["\']>Vorherige</span>', re.DOTALL).findall(result)[0]
			OLD_L = LEFT.replace('ACr', '')
			LINK_L = base64.b64decode(OLD_L).decode('utf-8', 'ignore')
			BeforeDAY = str(LINK_L.replace('filme-vorschau/de/week-', '').replace('/', ''))
			before = datetime(*(time.strptime(BeforeDAY, '%Y-%m-%d')[0:6]))
			bxORG = before.strftime('%Y-%m-%d')
			bxNEW = before.strftime('%d.%m.%Y')
			RIGHT = re.compile(r'<span class=["\']ACr([^ "]+) button button-md button-primary-full button-right["\']>.*?span class=["\']txt["\']>Nächste</span>', re.DOTALL).findall(result)[0]
			OLD_R = RIGHT.replace('ACr', '')
			LINK_R = base64.b64decode(OLD_R).decode('utf-8', 'ignore')
			NextDAY = str(LINK_R.replace('filme-vorschau/de/week-', '').replace('/', ''))
			next = datetime(*(time.strptime(NextDAY, '%Y-%m-%d')[0:6]))
			nxORG = next.strftime('%Y-%m-%d')
			nxNEW = next.strftime('%d.%m.%Y')
			addDir(translation(30833).format(str(nxNEW)), NEPVurl, 'listKino_big', icon, datum=nxORG)
			addDir(translation(30834).format(str(bxNEW)), NEPVurl, 'listKino_big', icon, datum=bxORG)
		except: pass
	if int(position) > page and datum =="N":
		debug_MS("(listKino_big) Now show NextPage ...")
		addDir(translation(30832), NEPVurl, 'listKino_big', artpic+"nextpage.png", page=page+1, datum=datum, position=position)
	xbmcplugin.endOfDirectory(pluginhandle)

def listKino_small(url, page=1):
	debug_MS("(listKino_small) -------------------------------------------------- START = listKino_small --------------------------------------------------")
	page = int(page)
	FOUND = False
	if page > 1:
		PGurl = url+"?page="+str(page)
	else: PGurl = url
	debug_MS("(listKino_small) ##### URL={0} ##### PAGE={1} #####".format(PGurl, str(page)))
	content = getUrl(PGurl)
	part = content.split('<div class="data_box">')
	for i in range(1,len(part),1):
		element = part[i]
		try:
			try:
				newURL = re.compile('button btn-primary ["\'] href=["\']([^"]+?)["\']', re.DOTALL).findall(element)[0]
			except:
				try:
					matchU = re.compile('class=["\']acLnk ([^ ]+?) button btn-primary', re.DOTALL).findall(element)[0]
					newURL = decodeURL(matchU)
				except: newURL =""
			image = re.compile(r'src=["\'](https?://.+?(?:[0-9]+\.png|[a-z]+\.png|[0-9]+\.jpg|[a-z]+\.jpg|[0-9]+\.gif|[a-z]+\.gif))["\'\?]', re.DOTALL|re.IGNORECASE).findall(element)[0]
			photo = enlargeIMG(image)
			title = re.compile('alt=["\'](.+?)["\'\" \' ]\s+title=', re.DOTALL).findall(element)[0]
			name = cleanTitle(title)
			try:
				movieDATE = re.compile('<span class=["\']film_info lighten fl["\']>Starttermin(.+?)</div>', re.DOTALL).findall(element)[0]
				newDATE = re.sub(r'\<.*?\>', '', movieDATE)
			except: newDATE =""
			if newDATE != "" and not "unbekannt" in newDATE.lower():
				name = name+"   ("+newDATE.replace('\n', '').replace('.', '-').strip()[0:10]+")"
			try: # Grab - Directors
				result_1 = re.compile('<span class=["\']film_info lighten fl["\']>Von </span>(.+?)</div>', re.DOTALL).findall(element)[-1]
				matchD = re.compile(r'(?:<span title=|<a title=)["\'](.+?)["\'] (?:class=|href=)', re.DOTALL).findall(result_1)
				directors = []
				for dNames in matchD:
					dNames = cleanTitle(dNames)
					directors.append(dNames)
				dDirector =", ".join(directors)
			except: dDirector =""
			try: # Grab - Genres
				result_2 = re.compile('<span class=["\']film_info lighten fl["\']>Genre</span>(.+?)</div>', re.DOTALL).findall(element)[-1]
				matchG = re.compile('<span itemprop=["\']genre["\']>([^<]+?)</span>', re.DOTALL).findall(result_2)
				genres = []
				for gNames in matchG:
					gNames = cleanTitle(gNames)
					genres.append(gNames)
				gGenre =", ".join(genres)
			except: gGenre =""
			try: # Grab - Plot
				desc = re.compile("<p[^>]*>([^<]+)<", re.DOTALL).findall(element)[0]
				plot = desc.replace('&nbsp;', '')
				plot = cleanTitle(plot)
			except: plot=""
			try: # Grab - Rating
				result_3 = element[element.find('User-Wertung')+1:]
				result_3 = result_3[:result_3.find('</TrueTemplate>')]
				rRating = re.compile('<span class=["\']note["\']>([^<]+?)</span></span>', re.DOTALL).findall(result_3)[0].strip().replace(',', '.')
			except:
				try:
					result_3 = element[element.find('Pressekritiken')+1:]
					result_3 = result_3[:result_3.find('User-Wertung')]
					rRating = re.compile('<span class=["\']note["\']>([^<]+?)</span></span>', re.DOTALL).findall(result_3)[0].strip().replace(',', '.')
				except: rRating=""
			debug_MS("(listKino_small) Name : {0}".format(name))
			debug_MS("(listKino_small) Link : {0}".format(baseURL+newURL))
			debug_MS("(listKino_small) Icon : {0}".format(photo))
			debug_MS("(listKino_small) Regie : {0}".format(dDirector))
			debug_MS("(listKino_small) Genre : {0}".format(gGenre))
			if newURL !="" and not 'button btn-disabled' in element:
				FOUND = True
				addLink(name, baseURL+newURL, 'playVideo', photo, plot, gGenre, dDirector, rRating, extraURL=url)
			else:
				FOUND = True
				addDir(name+translation(30835), "", 'listKino_small', photo, plot, gGenre, dDirector, rRating)
		except:
			failing("..... exception .....")
			failing("(listKino_small) Fehler-Eintrag : {0} #####".format(str(element)))
	if not FOUND:
		return xbmcgui.Dialog().notification(translation(30523), translation(30524), icon, 8000)
	if 'fr">Nächste<i class="icon-arrow-right">' in content:
		debug_MS("(listKino_small) Now show NextPage ...")
		addDir(translation(30832), url, 'listKino_small', artpic+"nextpage.png", page=page+1)
	xbmcplugin.endOfDirectory(pluginhandle)

def listSeries_small(url, page=1):
	debug_MS("(listSeries_small) -------------------------------------------------- START = listSeries_small --------------------------------------------------")
	page = int(page)
	FOUND = False
	if page > 1:
		PGurl = url+"?page="+str(page)
	else: PGurl = url
	debug_MS("(listSeries_small) ##### URL={0} ##### PAGE={1} #####".format(PGurl, str(page)))
	content = getUrl(PGurl)
	part = content.split('<div class="data_box">')
	for i in range(1,len(part),1):
		element = part[i]
		try:
			try:
				newURL = re.compile('button btn-primary ["\'] href=["\']([^"]+?)["\']', re.DOTALL).findall(element)[0]
			except:
				try:
					matchU = re.compile('class=["\']acLnk ([^ ]+?) button btn-primary', re.DOTALL).findall(element)[0]
					newURL = decodeURL(matchU)
				except: newURL =""
			image = re.compile(r'src=["\'](https?://.+?(?:[0-9]+\.png|[a-z]+\.png|[0-9]+\.jpg|[a-z]+\.jpg|[0-9]+\.gif|[a-z]+\.gif))["\'\?]', re.DOTALL|re.IGNORECASE).findall(element)[0]
			photo = enlargeIMG(image)
			title =re.compile('<h2 class=["\']tt_18 d_inlin[^>]*>(.+?)</h2>', re.DOTALL).findall(element)[0]
			name = re.sub(r'\<.*?\>', '', title)
			name = cleanTitle(name)
			try:
				movieDATE = re.compile('<span class=["\']lighten(?:\">|\'>)\s+Produktionszeitraum(.+?)</tr>', re.DOTALL).findall(element)[0]
				newDATE = re.sub(r'\<.*?\>', '', movieDATE)
			except: newDATE =""
			if newDATE != "" and not "unbekannt" in newDATE:
				name = name+'   ('+newDATE.replace('\n', '').replace(' ', '').replace('-', '~').strip()+')'
			try: # Grab - Directors
				result_1 = re.compile('<span class=["\']lighten["\']>mit</span>(.+?)</tr>', re.DOTALL).findall(element)[-1]
				matchD = re.compile(r'(?:<span title=|<a title=)["\'](.+?)["\'] (?:class=|href=)', re.DOTALL).findall(result_1)
				directors = []
				for dNames in matchD:
					dNames = cleanTitle(dNames)
					directors.append(dNames)
				dDirector =", ".join(directors)
			except: dDirector =""
			try: # Grab - Genres
				result_2 = re.compile('<span class=["\']lighten["\']>Genre(.+?)</tr>', re.DOTALL).findall(element)[-1]
				matchG = re.compile('<span itemprop=["\']genre["\']>([^<]+?)</span>', re.DOTALL).findall(result_2)
				genres = []
				for gNames in matchG:
					gNames = cleanTitle(gNames)
					genres.append(gNames)
				gGenre =", ".join(genres)
			except: gGenre =""
			try: # Grab - Plot
				desc = re.compile("<p[^>]*>([^<]+)<", re.DOTALL).findall(element)[0]
				plot = desc.replace('&nbsp;', '')
				plot = cleanTitle(plot)
			except: plot=""
			try: # Grab - Rating
				rRating = re.compile('<span class=["\']note["\']><span class=["\']acLnk.*?["\']>([^<]+?)</span></span>', re.DOTALL).findall(element)[0].strip().replace(',', '.')
			except: rRating=""
			debug_MS("(listSeries_small) Name : {0}".format(name))
			debug_MS("(listSeries_small) Link : {0}".format(baseURL+newURL))
			debug_MS("(listSeries_small) Icon : {0}".format(photo))
			debug_MS("(listSeries_small) Regie : {0}".format(dDirector))
			debug_MS("(listSeries_small) Genre : {0}".format(gGenre))
			if newURL !="" and not 'button btn-disabled' in element:
				FOUND = True
				addLink(name, baseURL+newURL, 'playVideo', photo, plot, gGenre, dDirector, rRating, extraURL=url)
			else:
				FOUND = True
				addDir(name+translation(30835), "", 'listSeries_small', photo, plot, gGenre, dDirector, rRating)
		except:
			failing("..... exception .....")
			failing("(listSeries_small) Fehler-Eintrag : {0} #####".format(str(element)))
	if not FOUND:
		return xbmcgui.Dialog().notification(translation(30523), translation(30524), icon, 8000)
	if 'fr">Nächste<i class="icon-arrow-right">' in content:
		debug_MS("(listSeries_small) Now show NextPage ...")
		addDir(translation(30832), url, 'listSeries_small', artpic+"nextpage.png", page=page+1)
	xbmcplugin.endOfDirectory(pluginhandle)

def listNews(url, page=1):
	debug_MS("(listNews) -------------------------------------------------- START = listNews --------------------------------------------------")
	page = int(page)
	if page > 1:
		PGurl = url+"?page="+str(page)
	else: PGurl = url
	debug_MS("(listNews) ##### URL={0} ##### PAGE={1} #####".format(PGurl, str(page)))
	content = getUrl(PGurl)
	result = content[content.find('<div class="colcontent">')+1:]
	result = result[:result.find('class="centeringtable">')]
	part = result.split('<div class="datablock')
	for i in range(1,len(part),1):
		element = part[i]
		try:
			image = re.compile(r'src=["\'](https?://.+?(?:[0-9]+\.png|[a-z]+\.png|[0-9]+\.jpg|[a-z]+\.jpg|[0-9]+\.gif|[a-z]+\.gif))["\'\?]', re.DOTALL|re.IGNORECASE).findall(element)[0]
			photo = enlargeIMG(image)
			try:
				matchUN = re.compile('href=["\'](.+?)["\'] class=.*?</strong>([^<]+?)</', re.DOTALL).findall(element)
				link = matchUN[0][0]
				title = matchUN[0][1]
			except:
				matchUN = re.compile('href=["\'](.+?)["\']>(.+?)</a>', re.DOTALL).findall(element)
				link = matchUN[0][0]
				title = matchUN[0][1].replace('\n', '')
				title = re.sub(r'\<.*?\>', '', title)
			name = cleanTitle(title)
			try: # Grab - Plot
				desc = re.compile('class=["\']fs11 purehtml["\']>(.+?)<div class=["\']spacer["\']></div>', re.DOTALL).findall(element)[0]
				plot = re.sub(r'\<.*?\>', '', desc)
				plot = cleanTitle(plot)
			except: plot =""
			debug_MS("(listNews) Name : {0}".format(name))
			debug_MS("(listNews) Link : {0}".format(baseURL+link))
			debug_MS("(listNews) Icon : {0}".format(photo))
			addLink(name, baseURL+link, 'playVideo', photo, plot, extraURL=url)
		except:
			failing("..... exception .....")
			failing("(listNews) Fehler-Eintrag : {0} #####".format(str(element)))
	try:
		nextP = re.compile('(<li class="navnextbtn">[^<]+<span class="acLnk)', re.DOTALL).findall(content)[0]
		debug_MS("(listNews) Now show NextPage ...")
		addDir(translation(30832), url, 'listNews', artpic+"nextpage.png", page=page+1)
	except: pass
	xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url, extraURL=""):
	debug_MS("(playVideo) -------------------------------------------------- START = playVideo --------------------------------------------------")
	debug_MS("(playVideo) ##### URL={0} ##### REFERER={1} ##### ".format(url, extraURL))
	finalURL = False
	content = getUrl(url, referer=extraURL)
	try:
		LINK = re.compile("<iframe[^>]+?src=['\"](.+?)['\"]", re.DOTALL).findall(content)
		debug_MS("(playVideo) *FOUND-1* Extra-Content : {0}".format(LINK))
		if  "_video" in LINK[1]:
			newURL = baseURL+LINK[1]
			content = getUrl(newURL, referer=url)
		elif "youtube.com" in LINK[0]:
			youtubeID = LINK[0].split('/')[-1].strip()
			debug_MS("(playVideo) *FOUND-2* Extern-Video auf Youtube [ID] : {0}".format(youtubeID))
			finalURL = 'plugin://plugin.video.youtube/play/?video_id='+youtubeID
	except: pass
	if not finalURL:
		DATA = {}
		DATA['media'] = []
		mp4_QUALITIES = ['high', 'medium']
		try:
			response = re.compile(r'(?:class=["\']player  js-player["\']|class=["\']player player-auto-play js-player["\']|<div id=["\']btn-export-player["\'].*?) data-model=["\'](.+?),&quot;disablePostroll&quot;:false', re.DOTALL).findall(content)[0].replace('&quot;', '"')+"}"
			debug_MS("(playVideo) ##### Extraction of Stream-Links : {0} #####".format(response))
			jsonObject = json.loads(response)
			for item in jsonObject['videos']:
				vidQualities = item['sources']
				for found in mp4_QUALITIES:
					for quality in vidQualities:
						if quality == found:
							DATA['media'].append({'url': vidQualities[quality], 'quality': quality, 'mimeType': 'video/mp4'})
				finalURL = DATA['media'][0]['url']
		except: pass
	if finalURL:
		finalURL = finalURL.replace(' ', '%20')
		if not "youtube" in finalURL and finalURL[:4] != "http":
			finalURL ="http:"+finalURL
		log("(playVideo) StreamURL : {0}".format(finalURL))
		listitem = xbmcgui.ListItem(path=finalURL)
		xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
	else:
		failing("(playVideo) ##### Abspielen des Streams NICHT möglich #####\n   ##### URL : {0} #####".format(url))
		return xbmcgui.Dialog().notification(translation(30521).format('URL'), translation(30522), icon, 8000)

def cleanTitle(text):
	text = py2_enc(text)
	for n in (('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'), ('&Amp;', '&'), ('&nbsp;', ' '), ("&quot;", "\""), ("&Quot;", "\""), ('&reg;', ''), ('&szlig;', 'ß'), ('&mdash;', '-'), ('&ndash;', '-'), ('–', '-'), ('&sup2;', '²')
		, ('&#x00c4', 'Ä'), ('&#x00e4', 'ä'), ('&#x00d6', 'Ö'), ('&#x00f6', 'ö'), ('&#x00dc', 'Ü'), ('&#x00fc', 'ü'), ('&#x00df', 'ß')
		, ('&Auml;', 'Ä'), ('Ä', 'Ä'), ('&auml;', 'ä'), ('ä', 'ä'), ('&Euml;', 'Ë'), ('&euml;', 'ë'), ('&Iuml;', 'Ï'), ('&iuml;', 'ï'), ('&Ouml;', 'Ö'), ('Ö', 'Ö'), ('&ouml;', 'ö'), ('ö', 'ö'), ('&Uuml;', 'Ü'), ('Ü', 'Ü'), ('&uuml;', 'ü'), ('ü', 'ü'), ('&yuml;', 'ÿ')
		, ('&agrave;', 'à'), ('&Agrave;', 'À'), ('&aacute;', 'á'), ('&Aacute;', 'Á'), ('&egrave;', 'è'), ('&Egrave;', 'È'), ('&eacute;', 'é'), ('&Eacute;', 'É'), ('&igrave;', 'ì'), ('&Igrave;', 'Ì'), ('&iacute;', 'í'), ('&Iacute;', 'Í')
		, ('&ograve;', 'ò'), ('&Ograve;', 'Ò'), ('&oacute;', 'ó'), ('&Oacute;', 'ó'), ('&ugrave;', 'ù'), ('&Ugrave;', 'Ù'), ('&uacute;', 'ú'), ('&Uacute;', 'Ú'), ('&yacute;', 'ý'), ('&Yacute;', 'Ý')
		, ('&atilde;', 'ã'), ('&Atilde;', 'Ã'), ('&ntilde;', 'ñ'), ('&Ntilde;', 'Ñ'), ('&otilde;', 'õ'), ('&Otilde;', 'Õ'), ('&Scaron;', 'Š'), ('&scaron;', 'š')
		, ('&acirc;', 'â'), ('&Acirc;', 'Â'), ('&ccedil;', 'ç'), ('&Ccedil;', 'Ç'), ('&ecirc;', 'ê'), ('&Ecirc;', 'Ê'), ('&icirc;', 'î'), ('&Icirc;', 'Î'), ('&ocirc;', 'ô'), ('&Ocirc;', 'Ô'), ('&ucirc;', 'û'), ('&Ucirc;', 'Û')
		, ('&alpha;', 'a'), ('&Alpha;', 'A'), ('&aring;', 'å'), ('&Aring;', 'Å'), ('&aelig;', 'æ'), ('&AElig;', 'Æ'), ('&epsilon;', 'e'), ('&Epsilon;', 'Ε'), ('&eth;', 'ð'), ('&ETH;', 'Ð'), ('&gamma;', 'g'), ('&Gamma;', 'G')
		, ('&oslash;', 'ø'), ('&Oslash;', 'Ø'), ('&theta;', 'θ'), ('&thorn;', 'þ'), ('&THORN;', 'Þ')
		, ("\\'", "'"), ('&iexcl;', '¡'), ('&iquest;', '¿'), ('&rsquo;', '’'), ('&lsquo;', '‘'), ('&sbquo;', '’'), ('&rdquo;', '”'), ('&ldquo;', '“'), ('&bdquo;', '”'), ('&rsaquo;', '›'), ('lsaquo;', '‹'), ('&raquo;', '»'), ('&laquo;', '«')
		, ("&#x27;", "'"), ('&#34;', '"'), ('&#39;', '\''), ('&#039;', '\''), ('&#196;', 'Ä'), ('&#214;', 'Ö'), ('&#220;', 'Ü'), ('&#228;', 'ä'), ('&#246;', 'ö'), ('&#252;', 'ü'), ('&#223;', 'ß'), ('&#160;', ' ')
		, ('&#192;', 'À'), ('&#193;', 'Á'), ('&#194;', 'Â'), ('&#195;', 'Ã'), ('&#197;', 'Å'), ('&#199;', 'Ç'), ('&#200;', 'È'), ('&#201;', 'É'), ('&#202;', 'Ê')
		, ('&#203;', 'Ë'), ('&#204;', 'Ì'), ('&#205;', 'Í'), ('&#206;', 'Î'), ('&#207;', 'Ï'), ('&#209;', 'Ñ'), ('&#210;', 'Ò'), ('&#211;', 'Ó'), ('&#212;', 'Ô')
		, ('&#213;', 'Õ'), ('&#215;', '×'), ('&#216;', 'Ø'), ('&#217;', 'Ù'), ('&#218;', 'Ú'), ('&#219;', 'Û'), ('&#221;', 'Ý'), ('&#222;', 'Þ'), ('&#224;', 'à')
		, ('&#225;', 'á'), ('&#226;', 'â'), ('&#227;', 'ã'), ('&#229;', 'å'), ('&#231;', 'ç'), ('&#232;', 'è'), ('&#233;', 'é'), ('&#234;', 'ê'), ('&#235;', 'ë')
		, ('&#236;', 'ì'), ('&#237;', 'í'), ('&#238;', 'î'), ('&#239;', 'ï'), ('&#240;', 'ð'), ('&#241;', 'ñ'), ('&#242;', 'ò'), ('&#243;', 'ó'), ('&#244;', 'ô')
		, ('&#245;', 'õ'), ('&#247;', '÷'), ('&#248;', 'ø'), ('&#249;', 'ù'), ('&#250;', 'ú'), ('&#251;', 'û'), ('&#253;', 'ý'), ('&#254;', 'þ'), ('&#255;', 'ÿ'), ('&#287;', 'ğ')
		, ('&#304;', 'İ'), ('&#305;', 'ı'), ('&#350;', 'Ş'), ('&#351;', 'ş'), ('&#352;', 'Š'), ('&#353;', 'š'), ('&#376;', 'Ÿ'), ('&#402;', 'ƒ')
		, ('&#8211;', '–'), ('&#8212;', '—'), ('&#8226;', '•'), ('&#8230;', '…'), ('&#8240;', '‰'), ('&#8364;', '€'), ('&#8482;', '™'), ('&#169;', '©'), ('&#174;', '®'), ('&#183;', '·')):
		text = text.replace(*n)
	return text.strip()

def cleanMonth(month):
	for m in (('januar ', '01-'), ('februar ', '02-'), ('märz ', '03-'), ('april ', '04-'), ('mai ', '05-'), ('juni ', '06-'), ('juli ', '07-'), ('august ', '08-'), ('september ', '09-'), ('oktober ', '10-'), ('november ', '11-'), ('dezember ', '12-')):
		month = month.replace(*m)
	return month.strip()

def enlargeIMG(cover):
	debug_MS("(enlargeIMG) -------------------------------------------------- START = enlargeIMG --------------------------------------------------")
	debug_MS("(enlargeIMG) 1.Original-COVER : {0}".format(cover))
	imgCode = ['commons/', 'medias', 'pictures', 'seriesposter', 'videothumbnails']
	for XL in imgCode:
		if XL in cover:
			try: cover = cover.split('.net/')[0]+'.net/'+XL+cover.split(XL)[1]
			except: pass
	debug_MS("(enlargeIMG) 2.Converted-COVER : {0}".format(cover))
	return cover

def decodeURL(url):
	debug_MS("(decodeURL) -------------------------------------------------- START = decodeURL --------------------------------------------------")
	debug_MS("(decodeURL) ## URL-Original={0} ##".format(url))
	normalstring = ['3F','2D','13', '1E', '19', '1F', '20', '2A', '21', '22', '2B', '23', '24', '2C', '25', '26', 'BA', 'B1', 'B2', 'BB', 'B3', 'B4', 'BC', 'B5', 'B6', 'BD', 'B7', 'B8', 'BE', 'B9', 'BF', '30', '31', '32', '3B', '33', '34', '3C', '35', '3D', '4A', '41', '42', '4B', '43', '44', '4C', '45', '46', '4D', '47', '48', '4E', '49', '4F', 'C0', 'C1', 'C2', 'CB', 'C3', 'C4', 'CC', 'C5', 'C6', 'CD']
	decodestring = ['_',':','%', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
	result =""
	for i in range(0,len(url),2):
		signs = url[i:i+2]
		ind = normalstring.index(signs)
		dec = decodestring[ind]
		result = result+dec
	debug_MS("(decodeURL) ## URL-Decoded={0} ##".format(result))
	return result

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, plot=None, genre=None, director=None, rating=None, page=1, type="", CAT_text="", datum="", position=0):  
	u = sys.argv[0]+'?url='+quote_plus(url)+'&mode='+str(mode)+'&page='+str(page)+'&type='+str(type)+'&CAT_text='+str(CAT_text)+'&datum='+str(datum)+'&position='+str(position)
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot, 'Genre': genre, 'Director': director, 'Rating': rating})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

def addLink(name, url, mode, image, plot=None, genre=None, director=None, rating=None, duration=None, extraURL=""):
	u = sys.argv[0]+'?url='+quote_plus(url)+'&mode='+str(mode)+'&extraURL='+quote_plus(extraURL)
	liz = xbmcgui.ListItem(name)
	ilabels = {}
	ilabels['Season'] = None
	ilabels['Episode'] = None
	ilabels['Tvshowtitle'] = None
	ilabels['Title'] = name
	ilabels['Tagline'] = None
	ilabels['Plot'] = plot
	ilabels['Duration'] = duration
	ilabels['Year'] = None
	ilabels['Genre'] = genre
	ilabels['Director'] = director
	ilabels['Writer'] = None
	ilabels['Rating'] = rating
	ilabels['Mpaa'] = None
	ilabels['Mediatype'] = 'video'
	liz.setInfo(type='Video', infoLabels=ilabels)
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	liz.setContentLookup(False)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
page = unquote_plus(params.get('page', ''))
type = unquote_plus(params.get('type', ''))
CAT_text = unquote_plus(params.get('CAT_text', ''))
datum = unquote_plus(params.get('datum', ''))
position = unquote_plus(params.get('position', ''))
extraURL = unquote_plus(params.get('extraURL', ''))
referer = unquote_plus(params.get('referer', ''))

if mode == 'aSettings':
	addon.openSettings()
elif mode == 'trailer':
	trailer()
elif mode == 'series':
	series()
elif mode == 'kino':
	kino()
elif mode == 'news':
	news()
elif mode == 'filtertrailer':
	filtertrailer(url)
elif mode == 'filterkino':
	filterkino(url)
elif mode == 'filterserien':
	filterserien(url)
elif mode == 'selectionCategories':
	selectionCategories(url, type, CAT_text)
elif mode == 'selectionWeek':
	selectionWeek(url)
elif mode == 'listTrailer':
	listTrailer(url, page)
elif mode == 'listSpecial_Series_Trailer':
	listSpecial_Series_Trailer(url, page, position)
elif mode == 'listKino_big':
	listKino_big(url, page, datum, position)
elif mode == 'listSeries_big':
	listKino_big(url, page, datum ,position)
elif mode == 'listKino_small':
	listKino_small(url, page)
elif mode == 'listSeries_small':
	listSeries_small(url, page)
elif mode == 'listNews':
	listNews(url, page)
elif mode == 'playVideo':
	playVideo(url, extraURL)
else:
	index()