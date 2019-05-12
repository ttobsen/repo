#!/usr/bin/python
# -*- coding: utf-8 -*-

import time, sys, os, urlparse
import xbmc ,xbmcgui, xbmcaddon,xbmcvfs
import urllib2,urllib, zlib,json
import shutil
import re
from xml.dom.minidom import parseString
import md5
import hashlib
import cookielib

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__addondir__    = xbmc.translatePath( __addon__.getAddonInfo('path') )
idname=__addon__.getAddonInfo('id')
cj = cookielib.CookieJar()

# inhalt=__addon__.getSetting("inhalt")
profile    = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")

def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
    


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
        

def getUrl(url,data="X"):
        print("Get Url: " +url)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        userAgent = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0"
        opener.addheaders = [('User-Agent', userAgent)]
        content=""
        try:
          if data!="x" :
             content=opener.open(url,data=data).read()
          else:
             content=opener.open(url).read()
        except urllib2.HTTPError as e:
             print e
        opener.close()
        return content
        
def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict
  
def getSessionID(baseuri, username, password, sid = None):
  debug("GetSessionId")
  debug("baseuri : "+ baseuri )
  debug("username : "+ username)
  debug("password : "+ password)
  if sid == None:
    uri = baseuri + "/login_sid.lua"
  else:
    uri = baseuri + "/login_sid.lua?sid="+sid
  debug("uri : "+ uri)
  req = urllib2.urlopen(uri)
  data = req.read()
  #print "data from checking sid:"
  #print data
  
  xml = parseString(data)
  sid = xml.getElementsByTagName("SID").item(0).firstChild.data
  debug("SID ist :"+ sid)
  #print "sid",sid
  if sid != "0000000000000000":
    return sid
  else:
    challenge = xml.getElementsByTagName("Challenge").item(0).firstChild.data
    debug("Challange :"+ challenge)
    #print "challenge",challenge
    uri = baseuri + "/login_sid.lua"
    post_data = urllib.urlencode({'username' : username, 'response' : createResponse(challenge,password), 'page' : ''})
    #print "req uri:",uri, post_data
    debug("getSessionID url :"+ uri)
    debug("Post Data :" + post_data)
    req = urllib2.urlopen(uri, post_data)
    data = req.read()    
    debug ("data from login:")
    debug (req.info())
    debug(data)
    xml = parseString(data)
    sid = xml.getElementsByTagName("SID").item(0).firstChild.data
    debug("Nach Login SID :"+ sid)
    if sid == "0000000000000000": 
       debug("Login Failed")
    else:
       debug("Sid : "+ sid)
    return sid

def createResponse(challenge, password):
  text = "%s-%s" % (challenge, password)
  text = text.encode("utf-16le")
  res = "%s-%s" % (challenge, hashlib.md5(text).hexdigest())
  #print "md5: [%s]" % res
  return res

def getdevices():
    global sid
    global baseurl
    global ip
    baseurl="http://"+ip             
    sid=getSessionID(baseurl,username,password)
    debug("SID : "+sid)
    url=baseurl +"/webservices/homeautoswitch.lua?switchcmd=getdevicelistinfos&sid="+sid
    content=getUrl(url)
    debug("+++getdevices CONTENT+++")
    debug(content)
    debug("---getdevices CONTENT---")
    xml = parseString(content)
    devices = xml.getElementsByTagName("device")
    return devices 
        
def readids():
     deviceids=[]
     deviceids.append("")
     devicenames=[]
     devicenames.append("Keine Aktion")
     allstrings=[]
     allstrings.append("Keine Aktion")
     atkion=""
     aktion_id=""
     global ip 
     global password
     if ip and password:
       Menu1=[]
       Menu1.append("TV is Running")
       Menu1.append("TV is not Running")
       Menu1.append("TV is Paused")
       Menu1.append("Video is Running")
       Menu1.append("Video is not Running")
       Menu1.append("Video is Paused")
       dialog = xbmcgui.Dialog()
       nr=dialog.select("Select Action", Menu1)
       if nr>=0:
         if nr==0 :
            aktion="tvon"
            aktionid="idtvon"
         if nr==1 :
            aktion="tvoff"
            aktionid="idtvoff"
         if nr==2 :
            aktion="pausetv"
            aktionid="idpausetv"            
         if nr==3 :
            aktion="videoon"
            aktionid="idvideoon"
         if nr==4 :
            aktion="videooff"
            aktionid="idvideooff"
         if nr==5 :
            aktion="pausevideo"
            aktionid="idpausevideo"
         devices=getdevices()         
         
         for device in devices:
          namexml=device.getElementsByTagName("name")[0]
          name=namexml.firstChild.data
          devid=device.getAttribute('identifier')
          devicenames.append(name)
          deviceids.append(devid)
          allstrings.append(name + "( "+ devid +" )")        
         dialog = xbmcgui.Dialog()
         nr=dialog.select("Menu", allstrings)
         if nr>=1:
             name=devicenames[nr]
             ids=deviceids[nr]           
             Menu3=[]
             Menu3.append("Einschalten")
             Menu3.append("Auschalten")
             dialog = xbmcgui.Dialog()
             nr=dialog.select("Select Strom", Menu3)
             if nr >=0:
                if nr==0 :
                  zustand="setswitchon"
                if nr==1 :
                  zustand="setswitchoff"
                __addon__.setSetting(id=aktion, value=zustand)                
                __addon__.setSetting(id=aktionid, value=ids)                                
         else:
                __addon__.setSetting(id=aktion, value="")                
                __addon__.setSetting(id=aktionid, value="")         

def login(oldip,oldusername,oldpassword):
  global ip
  global username
  global password
  global sid
  global baseurl
  ip=__addon__.getSetting("ip")  
  username=__addon__.getSetting("username")  
  password=__addon__.getSetting("password") 
  baseurl="http://"+ip       
  if oldpassword!=password or oldusername!=username or oldip!=ip:
         debug("Es hat sich was geändert")
         if password!="" and ip!="" :
           debug ("Authentifiziere")           
           sid=getSessionID(baseurl,username,password)                      
         oldpassword=password
         oldusername=username
         oldip=ip  
  yield oldip
  yield oldusername
  yield oldpassword
         
def einausschalten()  :
   deviceids=[]
   deviceids.append("")
   devicenames=[]
   allstrings=[]   
   oldpassword=""
   oldusername=""
   oldip=""
   oldurl=""
   global sid
   allstrings.append("Keine Aktion")
   devicenames.append("Keine Aktion")
   devices=getdevices()      
   for device in devices:
      namexml=device.getElementsByTagName("name")[0]
      name=namexml.firstChild.data
      devid=device.getAttribute('identifier')
      devicenames.append(name)
      deviceids.append(devid)
      allstrings.append(name + "( "+ devid +" )")        
      dialog = xbmcgui.Dialog()
      nr=dialog.select("Menu", allstrings)
      if nr>=1:
        name=devicenames[nr]
        ids=deviceids[nr]           
        Menu3=[]
        Menu3.append("Einschalten")
        Menu3.append("Auschalten")
        dialog = xbmcgui.Dialog()
        nr=dialog.select("Select Strom", Menu3)  
        login(oldip,oldusername,oldpassword)        
        if nr==0:
             url=baseurl +"/webservices/homeautoswitch.lua?ain="+ids+"&switchcmd=setswitchon&sid="+sid    
             debug("URL EINAUS: "+ url)             
             content=getUrl(url)    
        if nr==1:
             url=baseurl +"/webservices/homeautoswitch.lua?ain="+ids+"&switchcmd=setswitchoff&sid="+sid             
             debug("URL EINAUS: "+ url)             
             content=getUrl(url)                      
                
if len(sys.argv) > 1:
    params = parameters_string_to_dict(sys.argv[2])
    mode = urllib.unquote_plus(params.get('mode', ''))
    ip=__addon__.getSetting("ip")  
    username=__addon__.getSetting("username")  
    password=__addon__.getSetting("password")  
    tvon=__addon__.getSetting("tvon")        
    tvon_id=__addon__.getSetting("idtvon")         
    tvoff=__addon__.getSetting("tvoff")   
    tvoff_id=__addon__.getSetting("idtvoff")
    videoon=__addon__.getSetting("videoon")        
    videoon_id=__addon__.getSetting("idvideovon")         
    videooff=__addon__.getSetting("videooff")   
    videooff_id=__addon__.getSetting("idvideooff")               
    pausetv=__addon__.getSetting("pausetv")     
    pausetv_id=__addon__.getSetting("idpausetv")     
    pausevideo=__addon__.getSetting("pausevideo")     
    pausevideo_id=__addon__.getSetting("idpausevideo")   
    if mode=="clear":      
      xbmc.log("Starte Settings")                                   
      readids()
      exit(0)
    else: 
       einausschalten()
       exit(0)
       
    
       
#      dialog2 = xbmcgui.Dialog()      
 #     ok = xbmcgui.Dialog().ok( "Neu Configuration", "Nach verlassen des Einstellungen wird Twitter neu Configuriert" )   
 #     exit()            
def is_playback_paused():
   try:
    start_time = xbmc.Player().getTime()
    time.sleep(1)
    if xbmc.Player().getTime() != start_time:
        return False
    else:
        return True
   except:
        return False

         
if __name__ == '__main__':
    xbmc.log("Twitter:  Starte Plugin")    
    oldip=""
    oldusername=""
    oldpassword=""    
    oldurl=""
    sid=""
    baseurl=""
    
    # Starte Service
    monitor = xbmc.Monitor()    
    # Solange der Service läuft
    while not monitor.abortRequested():  
    
      oldip,oldusername,oldpassword=login(oldip,oldusername,oldpassword)        
      if monitor.waitForAbort(5):
        break            
      tvon=__addon__.getSetting("tvon")        
      tvon_id=__addon__.getSetting("idtvon")         
      tvoff=__addon__.getSetting("tvoff")   
      tvoff_id=__addon__.getSetting("idtvoff") 
      videoon=__addon__.getSetting("videoon")        
      videoon_id=__addon__.getSetting("idvideoon")         
      videooff=__addon__.getSetting("videooff")   
      videooff_id=__addon__.getSetting("idvideooff")          
      pausetv=__addon__.getSetting("pausetv")     
      pausetv_id=__addon__.getSetting("idpausetv")     
      pausevideo=__addon__.getSetting("pausevideo")     
      pausevideo_id=__addon__.getSetting("idpausevideo")     
      # Nur wenn ein Fernsehnder an ist      
      if sid == "":
        break
      if xbmc.Player().isPlaying() :
         pause=is_playback_paused()
      else: 
         pause=False
         
      url=""
      # Video läuft nicht 
      if not xbmc.Player().isPlaying() : 
         if videooff_id!="" and videooff!="":                         
             url=baseurl +"/webservices/homeautoswitch.lua?ain="+videooff_id+"&switchcmd="+ videooff +"&sid="+sid               
      # TV läuft nicht              
      if not xbmc.getCondVisibility('Pvr.IsPlayingTv') : 
         if tvoff_id!="" and tvoff!="":                         
             url=baseurl +"/webservices/homeautoswitch.lua?ain="+tvoff_id+"&switchcmd="+ tvoff +"&sid="+sid                      
      #        
      if xbmc.Player().isPlaying() :
          if videoon_id!="" and videoon!="":       
             url=baseurl +"/webservices/homeautoswitch.lua?ain="+videoon_id+"&switchcmd="+ videoon +"&sid="+sid       
      if xbmc.getCondVisibility('Pvr.IsPlayingTv'):
          if tvon_id!="" and tvon!="": 
             url=baseurl +"/webservices/homeautoswitch.lua?ain="+tvon_id+"&switchcmd="+ tvon +"&sid="+sid                    
      
      if xbmc.Player().isPlaying() and pause:
          if pausevideo_id!="" and pausevideo!="": 
             url=baseurl +"/webservices/homeautoswitch.lua?ain="+pausevideo_id+"&switchcmd="+ pausevideo +"&sid="+sid          
      if xbmc.getCondVisibility('Pvr.IsPlayingTv') and pause:
          if pausetv_id!="" and pausetv!="": 
             url=baseurl +"/webservices/homeautoswitch.lua?ain="+pausetv_id+"&switchcmd="+ pausetv +"&sid="+sid                       
             
      if not oldurl==url:
         content=getUrl(url)             
         oldurl=url
         debug("Schalte Um URL:" + url)
             
     
      
      
