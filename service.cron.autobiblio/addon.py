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
	from urllib import quote, unquote, quote_plus, unquote_plus, urlencode  # Python 2.X
elif PY3:
	from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode  # Python 3+
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
dataPath    = xbmc.translatePath(__addon__.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
temp           = xbmc.translatePath(os.path.join(dataPath, 'temp', '')).encode('utf-8').decode('utf-8')
Database = os.path.join(temp, 'MyTimeOrders.db')
icon = os.path.join(addonPath, 'icon.png')
forceTrash = __addon__.getSetting('forceErasing') == 'true'

if not xbmcvfs.exists(temp):
	xbmcvfs.mkdirs(temp)

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

def translation(id):
	return py2_enc(__addon__.getLocalizedString(id))

def failing(content):
	log(content, xbmc.LOGERROR)

def debug(content):
	log(content, xbmc.LOGDEBUG)

def log(msg, level=xbmc.LOGNOTICE):
	xbmc.log('[{0} v.{1}](addon.py) {2}'.format(__addon__.getAddonInfo('id'), __addon__.getAddonInfo('version'), py2_enc(msg)), level)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, source=None, shortENTRY=""):
	u = '{0}?url={1}&mode={2}&name={3}&source={4}&shortENTRY={5}'.format(sys.argv[0], quote_plus(url), str(mode), quote_plus(name), quote_plus(source), quote_plus(shortENTRY))
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type="Video", infoLabels={"Title": name})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image})
	xbmcplugin.setContent(int(sys.argv[1]), 'movies')
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
shortENTRY = unquote_plus(params.get('shortENTRY', ''))
stunden = unquote_plus(params.get('stunden', ''))
source = unquote_plus(params.get('source', ''))

def createtable():
	conn = sqlite3.connect(Database)
	cur = conn.cursor()
	try:
		cur.execute('CREATE TABLE IF NOT EXISTS stocks (stunden INTEGER, url TEXT PRIMARY KEY, name TEXT, last DATETIME)')
		try:
			cur.execute('ALTER TABLE stocks ADD COLUMN source TEXT')
		except sqlite3.OperationalError: pass
	except :
		var = traceback.format_exc()
		debug(var)
	finally:
		conn.commit() #Do not forget this !
		cur.close()
		conn.close()

def insert(name, stunden, url, source):
	last = "datetime('now', 'localtime')"
	try:
		conn = sqlite3.connect(Database)
		cur = conn.cursor()
		cur.execute('INSERT OR REPLACE INTO stocks VALUES ({0}, \'{1}\', \'{2}\', {3}, \'{4}\')'.format(int(stunden), url, name, last, source))
		conn.commit()
	except:
		conn.rollback()
		var = traceback.format_exc()
		debug(var)
	finally:
		cur.close()
		conn.close()

def delete(shortENTRY, url, source):
	if source.startswith("special://"):
		source = xbmc.translatePath(os.path.join('source', ''))
	source = py2_uni(source)
	first_BASE = False
	if '@@' in url and source != "" :
		first_BASE = os.sep.join(source.split(os.sep)[:-1])
	try:
		conn = sqlite3.connect(Database)
		cur = conn.cursor()
		cur.execute('DELETE FROM stocks WHERE url = \'{0}\''.format(url))
		cur.execute('VACUUM')
		conn.commit()
		if source != "" and os.path.isdir(source) and forceTrash:
			shutil.rmtree(source, ignore_errors=True)
			log("########## DELETING from Crontab and System || FOLDER = "+str(source)+" || TITLE = "+shortENTRY+" || ##########")
			if first_BASE:
				if len([f for f in os.listdir(first_BASE)]) == 1:
					shutil.rmtree(first_BASE, ignore_errors=True)
					log("########## LAST TURN - DELETING from System || BASE-FOLDER = "+str(first_BASE)+" || ##########")
		elif source == "" or not forceTrash:
			xbmcgui.Dialog().ok(__addon__.getAddonInfo('id'), translation(30501))
			log("########## DELETING only from Crontab - TITLE = "+shortENTRY+" ##########")
	except:
		conn.rollback()# Roll back any change if something goes wrong
		var = traceback.format_exc()
		failing("ERROR - ERROR - ERROR : ########## ({0}) received... ({1}) ...Delete Name in List failed ##########".format(shortENTRY, var))
	finally:
		cur.close()
		conn.close()

def list_entries():
	xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
	try:
		conn = sqlite3.connect(Database)
		cur = conn.cursor()
		cur.execute('SELECT * FROM stocks')
		r = list(cur)
		conn.commit()
		for member in r:
			std = member[0]
			url = member[1]
			name= member[2]
			shortENTRY= member[2]
			if '@@' in url:
				name += translation(30601).format(url.split('@@')[1])
				shortENTRY += '  ('+url.split('@@')[1]+')'
			else:
				name += translation(30602)
				shortENTRY += '  (Serie)'
			updated = member[3]
			source = member[4] if member[4] != None else ""
			debug("##### stunden= "+str(std)+" || url= "+url+" || shortENTRY= "+shortENTRY+" || last= "+updated+" || source= "+source+" #####")
			if source != "" and os.path.isdir(source) and forceTrash:
				addDir(translation(30603).format(py2_enc(name)), py2_enc(url), "delete", "", py2_enc(source), py2_enc(shortENTRY))
			elif source == "" or not forceTrash:
				addDir(translation(30604).format(py2_enc(name)), py2_enc(url), "delete", "", py2_enc(source), py2_enc(shortENTRY))
	except:
		var = traceback.format_exc()
		debug(var)
	finally:
		cur.close()
		conn.close()
	xbmcplugin.endOfDirectory(pluginhandle) 

if mode == 'adddata':
	createtable()
	debug("########## START INSTERT ##########")
	debug("### Name = "+name+" || Stunden = "+str(stunden)+" || URL-1 = "+url+" || Source = "+source+" ###")
	insert(name, stunden, url, source)
	debug("########## AFTER INSTERT ##########")
	xbmc.executebuiltin('RunPlugin('+url+')')
elif mode == 'delete':
	delete(shortENTRY, url, source)
else:
	xbmc.sleep(500)
	list_entries()
