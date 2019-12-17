# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from kodi_six.utils import py2_encode
import socket
import sys
import os
import re
import xbmcplugin
import xbmcaddon,xbmc
import xbmcgui, json
import requests,xbmcvfs

try:
    from urllib.parse import quote_plus, unquote_plus
    from http import cookiejar as cookielib
except:
    from urllib import quote_plus, unquote_plus
    import cookielib

addon = xbmcaddon.Addon()
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addonID = addon.getAddonInfo('id')
translation = addon.getLocalizedString

cj = cookielib.LWPCookieJar();
language = addon.getSetting("language")

try:
   import StorageServer
except:
   import storageserverdummy as StorageServer

cachezeit = addon.getSetting("cachetime")
cache = StorageServer.StorageServer(py2_encode("plugin.video.L0RE.cinetrailer"), cachezeit)


def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 

debug("Start Addon")

def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, duration="", desc="", genre='',text=""):
    u = '{0}?url={1}&mode={2}&name{3}&text={4}&bild={5}'.format(sys.argv[0], quote_plus(url), mode, quote_plus(py2_encode(name)), quote_plus(text), iconimage)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Genre": genre})
    liz.setArt({'icon': iconimage, 'thumb': iconimage, 'fanart': iconimage})
    liz.setProperty('IsPlayable', 'true')
    liz.addStreamInfo('video', { 'duration' : duration })
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok

def addDir(name, url, mode, iconimage, desc="",text="",page="",addtype=0,stunden=""):
    u = '{0}?url={1}&mode={2}&text={3}&page={4}&name{5}'.format(sys.argv[0], quote_plus(url), mode, text, page, name)
    ok = True
    liz = xbmcgui.ListItem(name)
    if addtype==1:
      commands = []  
      updatestd=addon.getSetting("updatestd")
      debug("UPDATETIME :"+str(updatestd))
      link = "plugin://plugin.video.L0RE.cinetrailer/?mode=tolibrary&url=%s&name=%s&stunden=%s" % (quote_plus(url), name, str(updatestd))
      #debug("LINK :"+link)
      commands.append(( "Add to library", 'XBMC.RunPlugin('+ link +')'))
      liz.addContextMenuItems( commands )
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    liz.setArt({'thumb': iconimage})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = unquote_plus(params.get('mode', ''))
url = unquote_plus(params.get('url', ''))
page = unquote_plus(params.get('page', ''))
name = unquote_plus(params.get('name', ''))
stunden = unquote_plus(params.get('stunden', ''))


def index():  
  addDir("Neueste Trailer","https://res.cinetrailer.tv/api/v1/"+language+"/movies/newest?pageSize=20&isDebug=false","newlist","",page=1,addtype=1)
  addDir("Demnächst im Kino","https://res.cinetrailer.tv/api/v1/"+language+"/movies/comingsoon?pageSize=20&isDebug=false","newlist","",page=1,addtype=1)
  addDir("Home Video","https://res.cinetrailer.tv/api/v1/"+language+"/movies/homevideo?pageSize=20&isDebug=false","newlist","",page=1,addtype=1)
  addDir("Im Kino","https://res.cinetrailer.tv/api/v1/"+language+"/movies/incinemas?orderBy=&pageSize=20&isDebug=false","newlist","",page=1,addtype=1)
  addDir("Genres","","genres","")
  addDir("Settings", "", 'Settings', "")
  xbmcplugin.endOfDirectory(pluginhandle)   


def getUrl(url,method,allow_redirects=False,verify=False,cookies="",headers="",data=""):
   if method=="GET":
     content = requests.get(url,allow_redirects=allow_redirects,verify=verify,cookies=cookies,headers=headers,data=data).text.encode('utf-8')
   if method=="POST":
     content = requests.post(url,data=data, allow_redirects=allow_redirects,verify=verify,cookies=cookies).text.encode('utf-8')
   return content
   
def genres():
  url="https://res.cinetrailer.tv/api/v1/"+language+"/categories"
  token=getsession()
  values = {
      'Model' : 'Huawei MLA-TL10',
      'AppVersion' : '3.3.15',
      'OsVersion': '4.4.4',
      'OsName': 'android',
      'Market': 'android',   
      'Authorization': 'Bearer '+token,
      #'TimeStamp': '2017-09-04 11:04:45'
  }  
  content = cache.cacheFunction(getUrl,url,"GET",False,False,cj,values)
  struktur = json.loads(content)
  for genre in struktur["categories"]:
    idd=genre["id"]
    title=genre["title"].encode('utf-8')
    url="https://res.cinetrailer.tv/api/v1/"+language+"/movies/search?pageSize=20&desc=true&orderBy=date&categoryId="+str(idd)
    addDir(title,url,"newlist","",page=1)
  xbmcplugin.endOfDirectory(pluginhandle)     
  
def getsession():
  url="https://res.cinetrailer.tv/Token"
  values = {
      'client_id' : 'cinetrailer_android',
      'client_secret' : 'pKQvtSL9FdpB3u38GMHtNMA3',
      'grant_type': 'client_credentials',
    } 
  content = cache.cacheFunction(getUrl,url,"POST",False,False,cj,"",values)    
  struktur = json.loads(content)
  return struktur["access_token"]
def Play(url):
    token=getsession()
    values = {
      'Model' : 'Huawei MLA-TL10',
      'AppVersion' : '3.3.15',
      'OsVersion': '4.4.4',
      'OsName': 'android',
      'Market': 'android',   
      'Authorization': 'Bearer '+token,
      #'TimeStamp': '2017-09-04 11:04:45'
    }  
    urln="https://res.cinetrailer.tv/api/v1/"+language+"/movie/"+url+"/trailers"  


    quality = str(addon.getSetting("quality"))

    content = cache.cacheFunction(getUrl,urln,"GET",False,False,cj,values)    
    struktur = json.loads(content)
    debug("PLAY")
    debug("URLN :"+urln)
    debug(struktur)
    url=struktur["items"][0]["clips"][0]["url"]
    for video in struktur["items"][0]["clips"]:
      if quality==video["quality"]:
          url=video["url"]
    listitem = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)  
    debug(struktur)
    
def newlist(url,page=1):
   token=getsession()  
   nurl=url +"&pageNumber="+str(page)
   debug("URL newlist :"+url)
   values = {
      'Model' : 'Huawei MLA-TL10',
      'AppVersion' : '3.3.15',
      'OsVersion': '4.4.4',
      'OsName': 'android',
      'Market': 'android',   
      'Authorization': 'Bearer '+token,
      #'TimeStamp': '2017-09-04 11:04:45'
    }  
   debug("Newlist url :"+url)
   content = cache.cacheFunction(getUrl,nurl,"GET",False,False,cj,values)    
   struktur = json.loads(content)
   debug(struktur)
   count=0
   for trailer in struktur["items"]:
      id=trailer["id"]
      image=trailer["poster_high"]
      name=trailer["title"].encode('utf-8')
      addLink(name,str(id),"Play",image)
      count+=1
   if int(struktur["page_count"]) > int(page):
     debug("## NEXT ##")
     addDir("Next",url,"newlist","",page=str(int(page)+1))
   xbmcplugin.endOfDirectory(pluginhandle) 
   
def tolibrary(url,name,stunden):
    mediapath=addon.getSetting("mediapath")
    if mediapath=="":
      dialog = xbmcgui.Dialog()
      dialog.notification("Error", "Pfad setzen in den Settings", xbmcgui.NOTIFICATION_ERROR)
      return        
    urlx = quote_plus(url)
    name = quote_plus(name)
    urln="plugin://plugin.video.L0RE.cinetrailer?mode=generatefiles&url="+urlx+"&name="+name
    urln = quote_plus(urln)
    debug("tolibrary urln : "+urln)
    xbmc.executebuiltin('XBMC.RunPlugin(plugin://service.L0RE.cron/?mode=adddata&name=%s&stunden=%s&url=%s)'%(name,stunden,urln))
    #xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True)

def generatefiles(url,fname):
   debug("Start generatefiles")
   mediapath=addon.getSetting("mediapath")
   pageanz=addon.getSetting("pages_anz")   
   for page in range(1, int(pageanz)+1):
      debug("Start Page :"+str(page))
      token=getsession()  
      nurl=url +"&pageNumber="+str(page)
      debug("URL newlist :"+url)
      values = {
          'Model' : 'Huawei MLA-TL10',
      'AppVersion' : '3.3.15',
      'OsVersion': '4.4.4',
      'OsName': 'android',
      'Market': 'android',   
      'Authorization': 'Bearer '+token,
      #'TimeStamp': '2017-09-04 11:04:45'
      }  
      debug("Newlist url :"+url)
      content = cache.cacheFunction(getUrl,nurl,"GET",False,False,cj,values)    
      struktur = json.loads(content)
      debug(struktur)
      count=0
      once=0
      for trailer in struktur["items"]:
          id=trailer["id"]
          image=trailer["poster_high"]
          name=trailer["title"].encode('utf-8')
          ppath=os.path.join(mediapath,fname.replace(" ","_"),"")
          debug("ppath :"+ppath)
          addLink(name,str(id),"Play",image)
          count+=1
          filename=os.path.join(ppath,name+".strm") 
          if xbmcvfs.exists(ppath):            
            if once==1:
              shutil.rmtree(ppath)
              once=0
              xbmcvfs.mkdir(ppath)
          else:
             ret=xbmcvfs.mkdir(ppath) 
             debug("Angelegt ppath "+str(ret))
             once=0                       
          file = xbmcvfs.File(filename,"w")             
          file.write("plugin://plugin.video.L0RE.cinetrailer/?mode=Play&url="+str(id))
          file.close()          
   xbmcplugin.endOfDirectory(pluginhandle) 
   
if mode == "":
    index()
if mode == "newlist":
     newlist(url,page)
if mode == "Play":
     Play(url)
if mode == "genres":
     genres()
if mode == 'Settings':
          addon.openSettings()   
if mode == 'tolibrary':                      
           tolibrary(url,name,stunden)          
if mode == 'generatefiles':         
          generatefiles(url,name)            