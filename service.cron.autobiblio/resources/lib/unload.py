# -*- coding: utf-8 -*-
# 12.08.2018 - ©realvito

import sys
import os
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import shutil


PY2 = sys.version_info[0] == 2
__addon__ = xbmcaddon.Addon('service.cron.autobiblio')
addonPath = xbmc.translatePath(__addon__.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath    = xbmc.translatePath(__addon__.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
temp           = xbmc.translatePath(os.path.join(dataPath, 'temp', '')).encode('utf-8').decode('utf-8')
Database = os.path.join(temp, 'MyTimeOrders.db')
icon = os.path.join(addonPath, 'icon.png')


class Unload:
	def __init__(self, *args, **kwargs):
		if sys.argv[1] == 'loeschen':
			if os.path.isdir(temp) and xbmcvfs.exists(Database):
				if xbmcgui.Dialog().yesno(heading=__addon__.getAddonInfo('id'), line1=translation(30502), line2=translation(30503), nolabel=translation(30504), yeslabel=translation(30505)):
					shutil.rmtree(temp, ignore_errors=True)
					xbmc.sleep(1000)
					xbmcgui.Dialog().notification(translation(30521), translation(30522), icon, 8000)
					xbmc.log("["+__addon__.getAddonInfo('id')+"](unload.py) ########## DELETING complete DATABASE ... "+Database+" ... success ##########", xbmc.LOGNOTICE)
				else:
					return# they clicked no, we just have to exit the gui here
			else:
				xbmcgui.Dialog().ok(__addon__.getAddonInfo('id'), translation(30506))

def py2_enc(s, encoding='utf-8'):
	if PY2:
		if not isinstance(s, basestring):
			s = str(s)
		s = s.encode(encoding) if isinstance(s, unicode) else s
	return s

def translation(id):
	return py2_enc(__addon__.getLocalizedString(id))

def Main():
	Unload()

if __name__ == '__main__':
	Main()
