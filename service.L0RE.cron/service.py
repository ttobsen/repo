# -*- coding: utf-8 -*-

import sys
import os
import xbmc
import xbmcaddon
import xbmcvfs
import time
from datetime import datetime,timedelta
import sqlite3


global debuging
PY2 = sys.version_info[0] == 2
__addon__ = xbmcaddon.Addon()  
profile    = xbmc.translatePath(__addon__.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
temp       = xbmc.translatePath(os.path.join(profile, 'temp', '')).encode('utf-8').decode('utf-8')

wait_time = 180  # 180 seconds = 3 minutes - wait at KODI start
loop_time = 3600  # 3600 seconds = 1 hour - time when the process started again

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

def special(msg, level=xbmc.LOGNOTICE):
	xbmc.log(msg, level)

def debug(content):
	log(content, xbmc.LOGDEBUG)

def failing(content):
	log(content, xbmc.LOGERROR)

def log(msg, level=xbmc.LOGNOTICE):
	msg = py2_enc(msg)
	xbmc.log("["+__addon__.getAddonInfo('id')+"-"+__addon__.getAddonInfo('version')+"](service.py) "+msg, level)

def fixtime(date_string, format):
	debug("fixtime ##### date_string : "+str(date_string)+" ##### format :" +str(format)+" #####")
	try:
		object = datetime.strptime(date_string, format)
	except TypeError:
		object = datetime(*(time.strptime(date_string, format)[0:6]))
	return object

if __name__ == '__main__':
	special("#######################################################################################")
	special("########## RUNNING: "+__addon__.getAddonInfo('id')+" PLUGIN VERSION "+__addon__.getAddonInfo('version')+" / ON PLATFORM: "+sys.platform+" ##########")
	special("################# Start the Service in 3 minutes - wait for other Instances to close #################")
	special("#######################################################################################")
	time.sleep(wait_time)
	log("########## START SERVICE ##########")
	MAX_ERRORS = 10
	errors = 0
	monitor = xbmc.Monitor()
	while not monitor.abortRequested():
		if not xbmc.getCondVisibility('Library.IsScanningVideo'):
			debug("########## START LOOP ... ##########")
			try:
				conn = sqlite3.connect(temp+'/cron.db')
				cur = conn.cursor()
				cur.execute('SELECT * FROM cron')
				r = list(cur)
				conn.commit()
				cur.close()
				conn.close()
				for member in r:
					std = member[0]
					url = member[1]
					name = member[2]
					last = member[3]
					debug("###### Control-Session for TITLE = "+py2_uni(name)+" / LASTUPDATE: "+last+" ##########")
					now = datetime.now()
					previous = fixtime(last, "%Y-%m-%d %H:%M:%S")
					if now > previous + timedelta(hours=std):
						log("########## start ACTION for TITLE = "+py2_uni(name)+" / LASTUPDATE = "+last+" ##########")
						conn = sqlite3.connect(temp+'/cron.db')
						cur = conn.cursor()
						cur.execute('UPDATE cron SET last={0} WHERE url="{1}"'.format("datetime('now','localtime')", py2_enc(url)))
						conn.commit()
						cur.close()
						conn.close()
						xbmc.executebuiltin('RunPlugin('+py2_enc(url)+')')
			except Exception as e:
				failure = str(e)
				errors += 1
				if errors >= MAX_ERRORS:
					failing("ERROR - ERROR - ERROR : ########## ({0}) received... (Number: {1}/{2}) ...Ending Service ##########".format(failure, errors, MAX_ERRORS))
					break
				else:
					failing("ERROR - ERROR - ERROR : ########## ({0}) received... (Number: {1}/{2}) ...Continuing Service ##########".format(failure, errors, MAX_ERRORS))
			else:
				errors = 0
			debug("########## ... END LOOP ##########")
			if monitor.waitForAbort(loop_time):
				break
