#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
	reload(sys)
	sys.setdefaultencoding('utf8')
	from urllib import quote, unquote, quote_plus, unquote_plus, urlencode  # Python 2.X
	from urllib2 import Request, urlopen  # Python 2.X
elif PY3:
	from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode  # Python 3+
	from urllib.request import Request, urlopen  # Python 3+
import time

tickerADDON = xbmcaddon.Addon()
tickerA_Path  = xbmc.translatePath(tickerADDON.getAddonInfo('path')).encode('utf-8').decode('utf-8')
icon = os.path.join(tickerA_Path, 'icon.png')
defaultFanart = os.path.join(tickerA_Path, 'fanart.jpg')

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
	LANGUAGE = tickerADDON.getLocalizedString(id)
	LANGUAGE = py2_enc(LANGUAGE)
	return LANGUAGE

def special(msg, level=xbmc.LOGNOTICE):
	xbmc.log(msg, level)

def debug(content):
	log(content, xbmc.LOGDEBUG)

def failing(content):
	log(content, xbmc.LOGERROR)

def log(msg, level=xbmc.LOGNOTICE):
	msg = py2_enc(msg)
	xbmc.log("["+tickerADDON.getAddonInfo('id')+"-"+tickerADDON.getAddonInfo('version')+"]"+msg, level)

def getUrl(url, headers=False, referer=False):
	req = Request(url)
	if headers:
		for key in headers:
			req.add_header(key, headers[key])
	else:
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0')
	if referer:
		req.add_header('Referer', referer)
	try:
		response = urlopen(req, timeout=40)
		link = py3_dec(response.read())
	except Exception as e:
		failure = str(e)
		if hasattr(e, 'code'):
			failing("(getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
		elif hasattr(e, 'reason'):
			failing("(getUrl) ERROR - ERROR - ERROR : ########## {0} === {1} ##########".format(url, failure))
		link = ""
		return sys.exit(0)
	response.close()
	return link

def validLOCATION(photo):
	try:
		code = urlopen(photo).getcode()
		if str(code) == "200":
			return True
	except: pass
	return False

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, iconimage, desc=None, sortname=""):
	u = sys.argv[0]+"?url="+quote_plus(url)+"&mode="+str(mode)+"&name="+quote_plus(name)
	liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=iconimage)
	liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "TrackNumber": sortname})
	liz.setArt({'fanart': defaultFanart})
	xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
