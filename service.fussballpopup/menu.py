#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import re
import xbmc
import xbmcplugin
import xbmcaddon
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
	reload(sys)
	sys.setdefaultencoding('utf8')
	from urllib import quote, unquote, quote_plus, unquote_plus, urlencode  # Python 2.X
elif PY3:
	from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode  # Python 3+
import json
import xbmcvfs
import shutil
import time

from resources.lib.django.utils.encoding import smart_str
from resources.lib.funktionen import *

pluginhandle   = int(sys.argv[1])
tickerADDON   = xbmcaddon.Addon()
tickerA_Name  = tickerADDON.getAddonInfo('name')
tickerA_Path    = xbmc.translatePath(tickerADDON.getAddonInfo('path')).encode('utf-8').decode('utf-8')
tickerA_Profile = xbmc.translatePath(tickerADDON.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
tickerA_Temp   = xbmc.translatePath(os.path.join(tickerA_Profile, 'temp', '')).encode('utf-8').decode('utf-8')
icon = os.path.join(tickerA_Path, 'icon.png')
pic = os.path.join(tickerA_Path, 'resources', 'media', '').encode('utf-8').decode('utf-8')
filename = os.path.join(tickerA_Temp, 'spiel.txt')

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TRACKNUM)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)

if not xbmcvfs.exists(tickerA_Temp):
	xbmcvfs.mkdirs(tickerA_Temp)

def index():    
	debug("Start Menu")
	addDir(translation(30061), "", "listCategories", icon)
	addDir(translation(30060), "", "gameOverview_DEL", icon)
	addDir(translation(30059), "", "settings", icon) 
	xbmcplugin.endOfDirectory(pluginhandle)

def listCategories():
	addDir(translation(30058), "https://www.sport1.de/fussball/alle-ligen-und-wettbewerbe", "gameOverview_ADD", icon)
	addDir(translation(30057), "https://www.sport1.de/fussball/alle-ligen-und-wettbewerbe/nationale-ligen", "gameOverview_ADD", icon)
	addDir(translation(30056), "https://www.sport1.de/fussball/alle-ligen-und-wettbewerbe/internationale-ligen-und-pokalwettbewerbe", "gameOverview_ADD", icon)
	addDir(translation(30055), "https://www.sport1.de/fussball/alle-ligen-und-wettbewerbe/internationale-turniere", "gameOverview_ADD", icon)
	addDir(translation(30054), "https://www.sport1.de/fussball/alle-ligen-und-wettbewerbe/internationale-klubwettbewerbe", "gameOverview_ADD", icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def gameOverview_ADD(url):
	# MATCH = <div class="s1-table-row s1-table-row-competition-overview"><a href="/liga/91" title="Zur Seite von Premier League"><span class="s1-logo-team"><img alt="" class="s1-lazy-img" onerror="this.style.display = 'none';" data-original="https://reshape.sport1.de/unsafe/50x50/sport1.weltsport.net/gfx/competition/50/91.gif"/></span><span class="s1-table-row-team">Premier League</span><span class="s1-table-row-details">
	oneENTRY = []
	count = 0
	debug("(gameOverview_ADD) Start Spielübersicht")
	content = getUrl(url)
	match = re.findall('s1-table-row-competition-overview">(.+?)<span class="s1-table-row-details">', content, re.DOTALL)
	for chtml in match:
		liganumber = re.compile('a href="/liga/(.+?)" title', re.DOTALL).findall(chtml)[0]
		if not liganumber in oneENTRY:
			count += 1
			oneENTRY.append(liganumber)
			name = re.compile('title="Zur Seite von (.+?)"><span class="s1-logo-team">', re.DOTALL).findall(chtml)[0]
			if liganumber == "13":
				name = "Bundesliga (Österreich)"
			if liganumber == "115":
				name = "Super League (Schweiz)"
			name = name.replace("&#039;", "'")
			try:
				image = re.compile('data-original="(.+?)"/></span>', re.DOTALL).findall(chtml)[0]
			except:
				try:
					image = re.compile('src="(.+?)"', re.DOTALL).findall(chtml)[0]
				except: image = ""
			imgName = name.replace('Europameisterschaft', 'EM').replace('Weltmeisterschaft', 'WM').replace('-Qualifikation', '').replace('-Quali.', '')
			newIMG = pic+imgName+".png"
			debug("(gameOverview_ADD) newIMG: {0}".format(newIMG))
			if xbmcvfs.exists(newIMG):
				image = newIMG
			addDir(name, liganumber, "listLeagues", image, sortname=str(count))
			debug("(gameOverview_ADD) Name : {0}".format(name))
			debug("(gameOverview_ADD) Liganr. : {0}".format(liganumber))
			debug("(gameOverview_ADD) Image : {0}".format(image))
	xbmcplugin.endOfDirectory(pluginhandle)

def listLeagues(LGnumber, LGname):
	oldi=0
	try:
		content1=getUrl("https://api.sport1.de/api/sports/competition/co"+LGnumber)
		struktur1 = json.loads(content1) 
		day=struktur1["current_matchday"]
		debug("(listLeagues) Liga Day {0}".format(day))
		debug("(listLeagues) Url Day : "+"https://api.sport1.de/api/sports/matches-by-season/co"+LGnumber+"/se/")
		content2 = getUrl("https://api.sport1.de/api/sports/matches-by-season/co"+LGnumber+"/se/")
		struktur2 = json.loads(content2)
	except: return
	tage=struktur2["round"]
	if xbmcvfs.exists(filename):
		with open(filename, 'r') as fp:
			stored_Games=fp.read()
	else:
		stored_Games=""
	if not "Alle Spiele "+LGname in stored_Games:
		all_Games="Alle Spiele "+LGname+"##-##"+ str(LGnumber) +"##"+ str(day) +"##-1##-##-##-##-"
		addDir("Alle Spiele "+LGname, all_Games, "saveGame", icon)
	for tag in tage:
		spiele=tag["match"]
		for spiel in spiele:
			live_status=smart_str(spiel["live_status"])
			ins=smart_str(spiel["home"]["name"])
			aus=smart_str(spiel["away"]["name"])
			ende=spiel["finished"]
			match_date=smart_str(spiel["match_date"])
			match_time=smart_str(spiel["match_time"])
			if match_time=="unknown":
				match_time="-1"
				name=match_date+" : "+ins+" - "+aus 
			else:
				name=match_date+" "+match_time+" : "+ins+" - "+aus 
			id=spiel["id"]
			debug("(listLeagues) Name : {0}".format(name))
			debug("(listLeagues) End : {0}".format(ende))
			debug("(listLeagues) live_status : {0}".format(live_status))
			if ende=="no" and not live_status=="none" and not live_status=="result" or oldi==1:
				actual_Games=name+"##"+live_status +"##"+ str(LGnumber) +"##"+ str(day) +"##"+str(id)+"##"+ins+"##"+aus+"##"+match_date+"##"+match_time       
				debug("(listLeagues) ACTUAL ::::")
				debug("(listLeagues) actual_Games : {0}".format(str(actual_Games)))
				if actual_Games not in stored_Games:
					addDir(name, actual_Games, "saveGame", icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def saveGame(section):
	debug("(saveGame) saveGame start")
	with open(filename, 'a+') as input:
		content = input.read()
		if content.find(section) == -1:
			input.seek(0,2) # change is here (for Windows-Error = "IOError: [Errno 0] Error") - because Windows don't like switching between reading and writing at same time !!!
			input.write(section+"\n")
	xbmc.executebuiltin("Container.Refresh")

def gameOverview_DEL():
	if xbmcvfs.exists(filename):
		with open(filename, 'r') as textobj:
			lines = textobj.readlines()
			for line in lines:
				if "##" in line:
					debug("(gameOverview_DEL) found in Line : {0}".format(str(line)))
					arr=line.split("##")
					name=arr[0]
					live_status=arr[1]
					lieganr=arr[2]
					dayid=arr[3]
					spielnr=arr[4]
					ins=arr[5]
					aus=arr[6]
					match_date=arr[7]
					match_time=arr[8]
					addDir(name, line, "delGame", icon)
	xbmcplugin.endOfDirectory(pluginhandle)

def delGame(section):
	debug("(delGame) delGame start")
	with open(filename, 'r') as output:
		lines = output.readlines()
	with open(filename, 'w') as input:
		for line in lines:
			if section not in line:
				input.write(line)

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
referer = unquote_plus(params.get('referer', ''))

if mode=="listCategories":
	listCategories()
elif mode=="gameOverview_ADD":
	gameOverview_ADD(url)
elif mode=="listLeagues":
	listLeagues(url, name)
elif mode=="saveGame":
	saveGame(url)
elif mode=="gameOverview_DEL":
	gameOverview_DEL()
elif mode=="delGame":
	delGame(url)
elif mode == 'settings':
	tickerADDON.openSettings()
else:
	index()
