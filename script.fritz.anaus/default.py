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
id=__addon__.getAddonInfo('id')
cj = cookielib.CookieJar()

# inhalt=__addon__.getSetting("inhalt")
profile    = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")




devicenames=[]
allstrings=[]


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
        
def readids(ip,password):
     deviceids=[]     
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
     if nr>=0:
             name=devicenames[nr]
             ids=deviceids[nr]         
             debug("Set Setting :"+    ids)         
             __addon__.setSetting(id="ids", value=ids)                                
         
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
         
def aus():
   global sid
   global ip
   baseurl="http://"+ip    
   sid=getSessionID(baseurl,username,password)
   ids=__addon__.getSetting("ids")
 #            url=baseurl +"/webservices/homeautoswitch.lua?ain="+ids+"&switchcmd=setswitchon&sid="+sid    
   url=baseurl +"/webservices/homeautoswitch.lua?ain="+ids+"&switchcmd=setswitchoff&sid="+sid                            
   content=getUrl(url)                      
def an():
   global sid
   global ip
   baseurl="http://"+ip    
   sid=getSessionID(baseurl,username,password)
   ids=__addon__.getSetting("ids")
   url=baseurl +"/webservices/homeautoswitch.lua?ain="+ids+"&switchcmd=setswitchon&sid="+sid      
   debug("URL EINAUS: "+ url)                
   content=getUrl(url)  
   
def menu():
   Menu1=[]
   Menu1.append("An")
   Menu1.append("Aus")
   dialog = xbmcgui.Dialog()
   nr=dialog.select("Ein/AUS", Menu1)
   if nr>=0:
      if nr==0 :
            an()
      if nr==1 :
           aus()

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
ip=__addon__.getSetting("ip")  
username=__addon__.getSetting("username")  
password=__addon__.getSetting("password")      
ids=__addon__.getSetting("ids")   
if mode=="":
   menu()
if mode=="clear":      
      xbmc.log("Starte Settings")       
      readids(ip,sid)      
if mode=="an":      
      xbmc.log("Starte Settings")   
      sid=getSessionID(baseurl,username,password)       
      an(ids,ip)      
if mode=="aus":      
      xbmc.log("Starte Settings")                                   
      sid=getSessionID(baseurl,username,password) 
      aus()
            
       
