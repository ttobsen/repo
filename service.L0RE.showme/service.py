#!/usr/bin/python
# -*- coding: utf-8 -*-

import time, sys, os, urlparse
import xbmc ,xbmcgui, xbmcaddon,xbmcvfs
import urllib2,urllib,json
import re,md5,shutil
import socket, cookielib
from datetime import datetime
import post


__addon__ = xbmcaddon.Addon()


profile    = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")
translation = __addon__.getLocalizedString
  

base_url = sys.argv[0]
addon = xbmcaddon.Addon()

profile    = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")
translation = __addon__.getLocalizedString

cj = cookielib.LWPCookieJar();
  
try:
  if xbmcvfs.exists(temp):
    shutil.rmtree(temp)
  xbmcvfs.mkdirs(temp)
except:
  pass
       
# Einlesen von Parametern, Notwendig für Reset der Twitter API
def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGDEBUG):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
    

        
if __name__ == '__main__':
    notice("START")
    temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")
    monitor = xbmc.Monitor()         
    while not monitor.abortRequested():  
      notice("LOOP")    
      username=addon.getSetting("username") 
      password=addon.getSetting("password") 
      community=addon.getSetting("community") 
      communitypassword=addon.getSetting("communitypassword")  
      service=addon.getSetting("service")  
      if service=="false":
         break      
      debug("username :"+username)
      debug("password :"+password)
      debug("community :"+community)
      debug("communitypassword :"+communitypassword)      
      if username=="" or password=="" or community=="" or communitypassword=="":
        sleep=60
        if monitor.waitForAbort(sleep):       
           break            
        continue
      else:
        sleep=86400
    
      reg,msg=post.postdb()
      if reg=="1":
        dialog = xbmcgui.Dialog()
        nr=dialog.ok("Fehler", msg)
        sleep=60

      if monitor.waitForAbort(sleep):       
        break            
           

