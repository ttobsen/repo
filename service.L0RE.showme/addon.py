#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcaddon
import xbmcgui,xbmcvfs
import json,urllib2,re,urlparse,os
from difflib import SequenceMatcher
from bs4 import BeautifulSoup
from datetime import datetime    
import urllib
import requests,cookielib
from cookielib import LWPCookieJar
import xbmcplugin
import post
import pyxbmct

global debuging
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
addon = xbmcaddon.Addon()
translation = addon.getLocalizedString
cj = cookielib.CookieJar()
addon = xbmcaddon.Addon()

profile    = xbmc.translatePath( addon.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")
session = requests.session()

icon = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8')

thread="https://www.kodinerds.net/index.php/Thread/11148-Was-ist-eure-Lieblingsserie-Serientalk-Empfehlungen/"
if not xbmcvfs.exists(temp):       
       xbmcvfs.mkdirs(temp)
       

def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, thump, desc="",page=1,nosub=0):   
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)+"&nosub="+str(nosub)
  ok = True
  liz = xbmcgui.ListItem(name)  
  liz.setArt({ 'fanart' : thump })
  liz.setArt({ 'thumb' : thump })
  liz.setArt({ 'banner' : icon })
  liz.setArt({ 'fanart' : icon })
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
	
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
  return ok
  
def addLink(name, url, mode, thump, duration="", desc="", genre='',director="",bewertung=""):
  debug("URL ADDLINK :"+url)
  debug( icon  )
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
  ok = True
  liz = xbmcgui.ListItem(name,thumbnailImage=thump)
  liz.setArt({ 'fanart' : icon })
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Genre": genre, "Director":director,"Rating":bewertung})
  liz.setProperty('IsPlayable', 'true')
  liz.addStreamInfo('video', { 'duration' : duration })
	#xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
  return ok
  
  
def geturl(url,data="x",header=[]):
   global cj
   content=""
   debug("URL :::::: "+url)
   opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
   userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"
   header.append(('User-Agent', userAgent))
   header.append(('Accept', "*/*"))
   header.append(('Content-Type', "application/json;charset=UTF-8"))
   header.append(('Accept-Encoding', "plain"))   
   opener.addheaders = header
   try:
      if data!="x" :
         request=urllib2.Request(url)
         cj.add_cookie_header(request)
         content=opener.open(request,data=data).read()
      else:
         content=opener.open(url).read()
   except urllib2.HTTPError as e:
       debug ( e)
   opener.close()
   return content

def index():
    addDir("Transfer Data","","adddata","")
    addDir("TopListe der Movies","movies","topliste","")
    addDir("TopListe der Serien","series","topliste","")
    addDir("TopListe der Folgen","episodes","topliste","")
    addDir("TopListe der Alben","alben","topliste","")
    addDir("TopListe der Songs","songs","topliste","")
    addDir("TopListe der bereits abgespielten Folgen","episodesplay","topliste2","")
    addDir("TopListe der bereits abgespielten Filme","moviesplay","topliste2","")
    addDir("TopListe der bereits abgespielten Songs","songsplay","topliste2","")
    addDir("Settings","Settings","Settings","")        
    xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True) 
def adddata():
    reg,msg=post.postdb()
    if reg=="1":
       dialog = xbmcgui.Dialog()
       nr=dialog.ok("Fehler", msg)
    else:
       dialog = xbmcgui.Dialog()
       nr=dialog.ok("OK", msg)
class Infowindow(pyxbmct.AddonDialogWindow):
    text=""
    pos=0
    def __init__(self, title='',text=''):
        super(Infowindow, self).__init__(title)
        self.setGeometry(600,600,1,7)        
        self.text=text                 
        self.set_info_controls()
        # Connect a key action (Backspace) to close the window.
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

    def set_info_controls(self):

      self.textbox0=pyxbmct.TextBox()       
      self.textbox1=pyxbmct.TextBox()
      self.textbox2=pyxbmct.TextBox()       
      self.textbox3=pyxbmct.TextBox()       
      self.textbox4=pyxbmct.TextBox()       
      self.textbox5=pyxbmct.TextBox()       
      self.textbox6=pyxbmct.TextBox()
      self.placeControl(self.textbox0, 0, 0) 
      self.placeControl(self.textbox1, 0, 1)                       
      self.placeControl(self.textbox2, 0, 2)                       
      self.placeControl(self.textbox3, 0, 3)                       
      self.placeControl(self.textbox4, 0, 4)                       
      self.placeControl(self.textbox5, 0, 5)                       
      self.placeControl(self.textbox6, 0, 6)                          
      user=""
      songs=""
      series=""
      folgen=""
      movies=""
      alben=""
      ids=""
      counter=0      
      try:      
       for zeile in self.text.split("\n"):
         debug("ZEILE"+zeile)
         elemente=zeile.split("##")
         user=user+elemente[0]+"\n"
         songs=songs+elemente[1]+"\n"
         series=series+elemente[2]+"\n"
         folgen=folgen+elemente[3]+"\n"
         try:
            movies=movies+elemente[4]+"\n"
            alben=alben+elemente[5]+"\n" 
         except:
             pass
         if counter==0:
           ids=ids+"Platz\n"
         else:
           ids=ids+str(counter)+"\n"
         counter=counter+1         
      except:
        pass
      self.textbox0.setText(ids) 
      self.textbox1.setText(user)         
      self.textbox2.setText(songs)         
      self.textbox3.setText(series)         
      self.textbox4.setText(folgen)         
      self.textbox5.setText(movies)         
      self.textbox6.setText(alben)               
      self.connectEventList(
             [pyxbmct.ACTION_MOVE_UP,
             pyxbmct.ACTION_MOUSE_WHEEL_UP],
            self.hoch)         
      self.connectEventList(
            [pyxbmct.ACTION_MOVE_DOWN,
             pyxbmct.ACTION_MOUSE_WHEEL_DOWN],
            self.runter)                  
      self.setFocus(self.textbox1)            
    def hoch(self):
        self.pos=self.pos-1
        if self.pos < 0:
          self.pos=0
        self.textbox.scroll(self.pos)
    def runter(self):
        self.pos=self.pos+1        
        self.textbox.scroll(self.pos)
        posnew=self.textbox.getPosition()
        debug("POSITION : "+ str(posnew))


        
        
def topliste(search):
    community=addon.getSetting("community")
    username=addon.getSetting("username")
    data='{"comunity":"'+community+'","sorted":"'+search+'"}'
    debug("DATA :")
    debug(data)
    content=geturl("https://l0re.com/kodinerd/listuser.php",data=data)
    debug("++++++")
    debug(content)
    debug("++++++")
    #{ "user":"L0RE","songs":"2047","series":"54","episodes":"530","movies":"290","alben":"149"}
    TEXT="%s##%s##%s##%s##%s##%s\n"%("User","Songs","Series","Folgen","Movies","Alben")
    debug("++++++++")
    debug(content)
    struktur = json.loads(content) 
    for element in struktur["users"]:
         if username==element["user"]:
            TEXT=TEXT+"[COLOR green]%s[/COLOR]##[COLOR green]%d[/COLOR]##[COLOR green]%d[/COLOR]##[COLOR green]%d[/COLOR]##[COLOR green]%d[/COLOR]##[COLOR green]%d[/COLOR]\n"%(element["user"],int(element["songs"]),int(element["series"]),int(element["episodes"]),int(element["movies"]),int(element["alben"]))
         else:
            TEXT=TEXT+"%s##%d##%d##%d##%d##%d\n"%(element["user"],int(element["songs"]),int(element["series"]),int(element["episodes"]),int(element["movies"]),int(element["alben"]))
    window=Infowindow("Liste",TEXT) 
    window.doModal()
    
def topliste2(search):
    community=addon.getSetting("community")
    username=addon.getSetting("username")
    data='{"comunity":"'+community+'","sorted":"'+search+'"}'
    debug("DATA :")
    debug(data)
    content=geturl("https://l0re.com/kodinerd/listuser.php",data=data)
    debug("++++++")
    debug(content)
    debug("++++++")
    #{ "user":"L0RE","songs":"2047","series":"54","episodes":"530","movies":"290","alben":"149"}
    TEXT="%s##%s##%s##%s\n"%("User","PlaydEpisodes","Playdsongs","PlayedMovies")
    debug("++++++++")
    debug(content)
    struktur = json.loads(content) 
    for element in struktur["users"]:
         debug("++")
         debug(element)
         if username==element["user"]:
            TEXT=TEXT+"[COLOR green]%s[/COLOR]##[COLOR green]%d[/COLOR]##[COLOR green]%d[/COLOR]##[COLOR green]%d[/COLOR]\n"%(element["user"],int(element["songsplay"]),int(element["episodesplay"]),int(element["moviesplay"]))
         else:
            TEXT=TEXT+"%s##%d##%d##%d## ##\n"%(element["user"],int(element["songsplay"]),int(element["episodesplay"]),int(element["moviesplay"]))            
    debug(TEXT)
    window=Infowindow("Liste",TEXT) 
    window.doModal()

    
params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))

if mode=="":  
    index()
if mode == 'Settings':
          addon.openSettings()    
if mode == 'adddata':
           adddata() 
if mode == 'topliste':
            topliste(url)
if mode == 'topliste2':
            topliste2(url)
    
