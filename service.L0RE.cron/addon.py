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
	from urllib import quote, unquote, quote_plus, unquote_plus, urlencode, urlopen  # Python 2.X
elif PY3:
	from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode  # Python 3+
	from urllib.request import urlopen  # Python 3+
import xbmcvfs
import shutil
import time
from datetime import datetime
import sqlite3
import traceback


global debuging
pluginhandle = int(sys.argv[1])
__addon__ = xbmcaddon.Addon()  
addonPath = xbmc.translatePath(__addon__.getAddonInfo('path')).encode('utf-8').decode('utf-8')
profile    = xbmc.translatePath(__addon__.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
temp       = xbmc.translatePath(os.path.join(profile, 'temp', '')).encode('utf-8').decode('utf-8')
icon = os.path.join(addonPath ,'icon.png')
forceTrash = __addon__.getSetting("forceErasing") == 'true'

if not xbmcvfs.exists(temp):
	xbmcvfs.mkdirs(temp)

def py2_enc(s, encoding='utf-8'):
	if PY2 and isinstance(s, unicode):
		s = s.encode(encoding)
	return s

def py2_uni(s, encoding='utf-8'):
	if PY2 and isinstance(s, str):
		s = unicode(s, encoding)
	return s

def translation(id):
	LANGUAGE = __addon__.getLocalizedString(id)
	LANGUAGE = py2_enc(LANGUAGE)
	return LANGUAGE

def debug(content):
	log(content, xbmc.LOGDEBUG)

def failing(content):
	log(content, xbmc.LOGERROR)

def log(msg, level=xbmc.LOGNOTICE):
	msg = py2_enc(msg)
	xbmc.log("["+__addon__.getAddonInfo('id')+"-"+__addon__.getAddonInfo('version')+"](addon.py) "+msg, level)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, source=None):
	u = sys.argv[0]+"?url="+quote_plus(url)+"&mode="+str(mode)+"&name="+quote_plus(name)+"&source="+quote_plus(source)
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type="Video", infoLabels={"Title": name})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image})
	xbmcplugin.setContent(int(sys.argv[1]), 'movies')
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
stunden = unquote_plus(params.get('stunden', ''))
source = unquote_plus(params.get('source', ''))

def createtable():
	conn = sqlite3.connect(temp+'/cron.db')
	cur = conn.cursor()
	try:
		cur.execute('CREATE TABLE IF NOT EXISTS cron (stunden INTEGER, url TEXT PRIMARY KEY, name TEXT, last DATETIME)')
		try:
			cur.execute('ALTER TABLE cron ADD COLUMN source TEXT')
		except sqlite3.OperationalError: pass
	except :
		var = traceback.format_exc()
		debug(var)
	conn.commit()#Do not forget this !
	cur.close()
	conn.close()

def insert(name, url, stunden, last, source=""):
	try:
		conn = sqlite3.connect(temp+'/cron.db')
		cur = conn.cursor()
		cur.execute('INSERT OR REPLACE INTO cron VALUES ({0}, "{1}", "{2}", {3}, "{4}")'.format(int(stunden), url, name, last, source))
		conn.commit()
	except:
		conn.rollback()
		var = traceback.format_exc()
		debug(var)
	cur.close()
	conn.close()

def delete(name, url, source=""):
	REM_text = py2_enc(name).replace('[COLOR orangered]Eintrag+Ordner löschen: [/COLOR]', '').replace('[COLOR orangered]Nur Eintrag löschen: [/COLOR]', '').strip()
	if source.startswith("special://"):
		source = xbmc.translatePath(os.path.join('source', ''))
	source = py2_uni(source)
	try:
		conn = sqlite3.connect(temp+'/cron.db')
		cur = conn.cursor()
		cur.execute('DELETE FROM cron WHERE url="{0}"'.format(url))
		conn.commit()
		if source != "" and os.path.isdir(source) and forceTrash:
			shutil.rmtree(source, ignore_errors=True)
			log("########## DELETING from Crontab and System - TITLE = "+REM_text+" ##########")
		elif source == "" or not forceTrash:
			xbmcgui.Dialog().ok(__addon__.getAddonInfo('id'), translation(30501))
			log("########## DELETING only from Crontab - TITLE = "+REM_text+" ##########")
	except:
		conn.rollback()# Roll back any change if something goes wrong
		var = traceback.format_exc()
		failing("ERROR - ERROR - ERROR : ########## ({0}) received... ({1}) ...Delete Name in List failed ##########".format(REM_text, var))
	cur.close()
	conn.close()

def list_entries():
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
	try:
		conn = sqlite3.connect(temp+'/cron.db')
		cur = conn.cursor()
		cur.execute('SELECT * FROM cron')
		r = list(cur)
		for member in r:
			std = member[0]
			url = member[1]
			name = member[2]
			last = member[3]
			source = member[4] if member[4] != None else ""
			debug("##### stunden= "+str(std)+" / url= "+url+" / name= "+name+" / last= "+str(last)+" / source= "+source+" #####")
			if forceTrash:
				addDir("[COLOR orangered]Eintrag+Ordner löschen: [/COLOR]"+py2_enc(name), py2_enc(url), "delete", "", py2_enc(source))
			else:
				addDir("[COLOR orangered]Nur Eintrag löschen: [/COLOR]"+py2_enc(name), py2_enc(url), "delete", "", py2_enc(source))
	except:
		var = traceback.format_exc()
		debug(var)
	conn.commit()
	cur.close()
	conn.close()
	xbmcplugin.endOfDirectory(pluginhandle) 

if mode == 'adddata':
	debug("########## URL-1 = "+url+" ##########")
	createtable()
	debug("########## START INSTERT ##########")
	insert(name, url, stunden, "datetime('now','localtime')", source)
	debug("########## AFTER INSTERT ##########")
	debug("########## URL-2 = "+url+" ##########")
	xbmc.executebuiltin('RunPlugin('+url+')')
elif mode == 'delete':
	delete(name, url, source)
else:
	xbmc.sleep(500)
	list_entries()
