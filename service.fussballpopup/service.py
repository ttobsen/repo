#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import xbmc
import xbmcaddon
PY2 = sys.version_info[0] == 2
if PY2:
	reload(sys)
	sys.setdefaultencoding('utf8')
import json
import xbmcvfs
import shutil
import time

import popwindow
from dateutil import parser
from resources.lib.django.utils.encoding import smart_str
from resources.lib.funktionen import *

tickerADDON   = xbmcaddon.Addon()
tickerA_Name  = tickerADDON.getAddonInfo('name')
tickerA_Path    = xbmc.translatePath(tickerADDON.getAddonInfo('path')).encode('utf-8').decode('utf-8')
tickerA_Profile = xbmc.translatePath(tickerADDON.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
tickerA_Temp   = xbmc.translatePath(os.path.join(tickerA_Profile, 'temp', '')).encode('utf-8').decode('utf-8')
yellowcard = os.path.join(tickerA_Path, 'resources', 'media', 'yellowcard.png')
redcard = os.path.join(tickerA_Path, 'resources', 'media', 'redcard.png')
MAX_ERRORS = tickerADDON.getSetting('max_events')
filename = os.path.join(tickerA_Temp, 'spiel.txt')

wait_time = 155  # 180 seconds = 3 minutes - wait at KODI start
loop_time = 60  # 60 seconds = 1 minute - time when the process started again

if not xbmcvfs.exists(tickerA_Temp):
	xbmcvfs.mkdirs(tickerA_Temp)

def delspiel(ids, liste):
	fileinhalt = False
	for zeile in liste:
		try:  
			arr=zeile.split("##")
			spielnr=arr[4] 
		except:
			spielnr="leer"
		if spielnr in ids and "##" in zeile:
			debug("(delspiel) ##### Delete Line : {0} #####".format(str(zeile)))
			fileinhalt=zeile
		else:
			debug("(delspiel) ##### Attach Line : {0} #####".format(str(zeile)))
	if fileinhalt:
		with open(filename, 'r') as output:
			lines = output.readlines()
		with open(filename, 'w') as input:
			for line in lines:
				if fileinhalt not in line:
					input.write(line)

if __name__ == '__main__':
	time.sleep(25)
	special("##########################################################################################")
	special("########## RUNNING: "+tickerADDON.getAddonInfo('id')+" PLUGIN VERSION "+tickerADDON.getAddonInfo('version')+" / ON PLATFORM: "+sys.platform+" ##########")
	special("################## Start the Service in 3 minutes - wait for other Instances to close ###################")
	special("##########################################################################################")
	time.sleep(wait_time)
	xbmc.getInfoLabel('System.ScreenWidth')
	log("########## START FUSSBALL-TICKER ##########")
	xbmc.sleep(200)
	ScreenWith = xbmc.getInfoLabel('System.ScreenWidth')
	enableManual = tickerADDON.getSetting("enableManual") == "true"
	widemessage = tickerADDON.getSetting("breite-message")
	debug("(MAIN) ##### BREITE Message (settings) : {0} #####".format(str(widemessage)))
	debug("(MAIN) ##### ScreenWith : {0} #####".format(str(ScreenWith)))
	if not enableManual and int(ScreenWith) != int(widemessage):
		tickerADDON.setSetting("breite-message", str(ScreenWith))
	xbmc.sleep(200)
	debug("(MAIN) ##### BREITE Message (adjusted) : {0} #####".format(str(tickerADDON.getSetting("breite-message"))))
	errors = 0
	cimg=""
	schown=[]
	oldi=0
	monitor = xbmc.Monitor()
	while not monitor.abortRequested():
		#log("########## START LOOP ... ##########")
		try:
			titlelist=[]
			cimglist1=[]
			cimglist2=[]
			greyoutlist=[]
			lesezeitlist=[]
			timelist=[] 
			ids=[]
			ins=[]
			auss=[]
			anzal_meldungen=[]
			foto1=""
			foto2=""
			debug("(MAIN) Get Enviroment")
			bild=tickerADDON.getSetting("bild") 
			lesezeit=tickerADDON.getSetting("lesezeit")
			greyout=tickerADDON.getSetting("greyout")
			xmessage=tickerADDON.getSetting("x-message")
			ymessage=tickerADDON.getSetting("y-message")
			hoehemessage=tickerADDON.getSetting("hoehe-message")
			breitemessage=tickerADDON.getSetting("breite-message")
			hoehebild1=tickerADDON.getSetting("hoehe-bild1")
			breitebild1=tickerADDON.getSetting("breite-bild1")
			hoehebild2=tickerADDON.getSetting("hoehe-bild2")
			breitebild2=tickerADDON.getSetting("breite-bild2")
			font=tickerADDON.getSetting("font")
			fontcolor=tickerADDON.getSetting("fontcolor")
			oldmessages=tickerADDON.getSetting("oldmessages")
			spielzeit=tickerADDON.getSetting("spielzeit")
			karten=tickerADDON.getSetting("karten")
			tor=tickerADDON.getSetting("tor")
			elfmeter=tickerADDON.getSetting("elfmeter")
			spielerwechsel=tickerADDON.getSetting("spielerwechsel")
			anzahlmeldungen=tickerADDON.getSetting("anzahlmeldungen")
			gesamtliste=[]
			if xbmcvfs.exists(filename):
				with open(filename, 'r') as textobj:
					contentfile=textobj.read()
				liste=contentfile.split("\n")
				spiellisteneu=[]
				delliste=[]
				timelist=[]
				# Spiele ermitteln
				# File wird in Arrays geladen
				name=[]
				live_status=[]
				lieganr=[]
				dayid=[]
				spielnr=[]
				aus=[]
				inn=[]
				match_date=[]
				match_time=[]
				lsv=[]
				ganzeliega=[]
				minute_now=[]
				for spiel in liste:
					if "##" in spiel:
						arr=spiel.split("##")
						debug("(MAIN) ##### Spiel-NR : {0} #####".format(arr[4]))
						if arr[4]=="-1":
							ganzeliega.append(arr[2])
							name.append(arr[0])
							lieganr.append(arr[2])
							dayid.append(arr[3])
						else:
							name.append(arr[0])
							live_status.append(arr[1])
							lieganr.append(arr[2])
							dayid.append(arr[3])
							spielnr.append(arr[4])
							minute_now.append("-")
							inn.append(arr[5])
							aus.append(arr[6])
							hdate=arr[7]
							match_date.append(hdate)
							if arr[8]=="-1":
								zeitpunkt=hdate
							else:
								htime=arr[8]
								match_time.append(htime)
								zeitpunkt=hdate+" "+htime
							debug("(MAIN) ##### Zeitpunkt = {0} #####".format(str(zeitpunkt)))
							dt = parser.parse(zeitpunkt, fuzzy=True, dayfirst=True)  
							lss=dt.timetuple()
							lsv.append(time.mktime(lss))
							debug("(MAIN) ---------ADDE FILE-----------")
							debug(arr[0])

				liegadone=[]
				# Spiele überprüfen  
				delliste=[]
				# Jede Liga wird einmal geladen
				for i in range(len(lieganr)):
					liga=lieganr[i]
					debug("(MAIN) ---------LIGA LOOP-----------")
					debug("(MAIN) ##### Liga : {0}".format(str(liga)))
					if not liga in liegadone:
						day=dayid[i]
						liegadone.append(liga)
						debug("(MAIN) Hole Liga")
						if oldi==1:
							day="1"
						nurl1="https://api.sport1.de/api/sports/matches-by-season/co"+liga+"/se/md"+day
						debug("(MAIN) ##### Ganze Liga : {0} ##### Spiel-Nr : {1} #####".format(str(ganzeliega), str(spielnr)))
						content1 = getUrl(nurl1)
						struktur = json.loads(content1)
						try:
							tage=struktur["round"] 
						except:
							debug("Fehler")
							continue
						# Jeder Tag in der Liga 
						for tag in tage:
							debug("(MAIN) Neuer Tag")
							spiele=tag["match"]
							# Jedes Spiel an dem Tag
							for spiel in spiele:   
								aminute_now=spiel["current_minute"]
								id=spiel["id"] 
								debug("(MAIN) ##### Spiel-NR-1 : {0} ##### Liga : {1} #####".format(str(id), str(liga)))
								ende=spiel["finished"] 
								# Wenn das Spiel oder die ganze Liga ausgewählt wurde
								debug("(MAIN) ##### Spiel-NR-2 : {0} #####".format(str(spielnr)))
								if str(id) in spielnr or liga in ganzeliega: 
									debug("(MAIN) Spiel Ausgewählt")
									# Spiel zuende? und keine Liga
									if not ende=="no" and liga not in ganzeliega and oldi==0:
										debug("(MAIN) Spiel Zuende")
										delliste.append(id)
										debug("(MAIN) ##### Löschen : {0} #####".format(str(id)))
									else:
										# Wenn ganze Liga oder Spiel noch nicht zuende     
										debug("(MAIN) Neues Spiel")
										if ende=="no" or oldi==1:
											debug("(MAIN) Spiel läuft")
											# Nur wenn das Spiel begonnen hat
											if str(id) in spielnr:
												if spielnr.index(id) not in spiellisteneu:
													spiellisteneu.append(spielnr.index(id))
													minute_now[spielnr.index(id)]=aminute_now
													debug("(MAIN) ##### Hinzufügen : {0} #####".format(str(spielnr.index(id))))
											else:
												a_live_status=smart_str(spiel["live_status"])
												a_ins=smart_str(spiel["home"]["name"])
												a_aus=smart_str(spiel["away"]["name"])
												a_ende=spiel["finished"]
												a_match_date=smart_str(spiel["match_date"])
												a_match_time=smart_str(spiel["match_time"])
												a_id=spiel["id"]
												a_name=a_match_date+" "+a_match_time+" : "+a_ins +" - "+a_aus 
												a_zeitpunkt=a_match_date+" "+a_match_time
												if match_time=="unknown":
													a_name=a_match_date +" : "+a_ins +" - "+ a_aus 
													a_zeitpunkt=a_match_date
												a_dt = parser.parse(a_zeitpunkt, fuzzy=True, dayfirst=True)  
												a_lss=a_dt.timetuple()
												lsv.append(time.mktime(a_lss))
												name.append(a_name)
												live_status.append(a_live_status)
												lieganr.append(liga)
												dayid.append(day)
												spielnr.append(a_id)
												aus.append(a_aus)
												inn.append(a_ins)
												match_date.append(a_match_date)
												if match_time!="unknown":
													match_time.append(a_match_time)
												spiellisteneu.append(spielnr.index(id))
												debug("(MAIN) ##### Hinzufügen NEU : {0} #####".format(str(spielnr.index(id))))
												minute_now.append(aminute_now)

				debug("(MAIN) ##### Minute now : {0} #####".format(str(minute_now)))
				# Löschliste löschen
				if len(delliste) > 0:
					delspiel(delliste, liste)
				# Spiele abarbeiten
				debug("(MAIN) ##### Spielliste NEU : {0} #####".format(str(spiellisteneu)))
				for nr in spiellisteneu:
					debug ("(MAIN) Array")
					debug("(MAIN) ##### SPIEL-no. : {0} #####".format(str(nr)))
					out_spieler=""
					out_id=""
					in_spieler=""
					in_id=""
					nurl2="https://api.sport1.de/api/sports/match-event/ma"+spielnr[nr]
					content2 = getUrl(nurl2)
					struktur = json.loads(content2)
					debug("(MAIN) Struktur")
					debug("(MAIN) $$$$$$$$$$$$$$$$$$$$ JSON-Webseite-Ergebnisse : "+str(struktur)+" $$$$$$$$$$$$$$$$$$$$")
					ccontent="0:0"
					anzal_meldung=0
					for element in struktur:
						Meldung=""
						foto1=""
						foto2=""
						anzal_meldung +=1
						minute=element["minute"]
						aktion=element["action"]
						spielstatus=element["kind"]
						if not element["content"]=="":
							ccontent=smart_str(element["content"])
						created=element["created"]
						id=element["id"]
						if aktion=="match":
							if spielzeit=="false":
								continue
							if spielstatus=="game-end":
								Meldung=translation(30049)+inn[nr]+translation(30041)+aus[nr]+translation(30053)+ccontent
							if spielstatus=="game-start":
								Meldung=translation(30049)+inn[nr]+translation(30041)+aus[nr]+translation(30052)
							if spielstatus=="first-half-end":
								Meldung=translation(30048)+inn[nr]+translation(30041)+aus[nr]+translation(30050)+ccontent
							if spielstatus=="second-half-start":
								Meldung=translation(30047)+ inn[nr]+translation(30041)+aus[nr]+translation(30051)+ccontent
							if spielstatus=="second-half-end":
								Meldung=translation(30047)+ inn[nr]+translation(30041)+aus[nr]+translation(30050)+ccontent
							if spielstatus=="first-extra-start":
								Meldung=translation(30045)+ inn[nr]+translation(30041)+aus[nr]+translation(30051)+ccontent
							if spielstatus=="first-extra-end":
								Meldung=translation(30045)+ inn[nr]+translation(30041)+aus[nr]+translation(30050)+ccontent
							if spielstatus=="second-extra-start":
								Meldung=translation(30043)+ inn[nr]+translation(30041)+aus[nr]+translation(30051)+ccontent
							if spielstatus=="second-extra-end":
								Meldung=translation(30043)+ inn[nr]+translation(30041)+aus[nr]+translation(30050)+ccontent
							if spielstatus=="penalty-start":
								Meldung=translation(30040)+ inn[nr]+translation(30041)+aus[nr]+translation(30042)+ccontent
						if aktion=="card":
							try:
								if karten=="false":
									continue
								team=element["team"]["name"]
								person=element["person"]["name"]
								personid=element["person"]["id"]
								if spielstatus=="yellow":
									Meldung=minute+translation(30039)+person+translation(30036)+team
									foto1=yellowcard
									newIMG1 = validLOCATION("https://s.weltsport.net/gfx/person/l/"+personid+".jpg")
									if newIMG1:
										foto2="https://s.weltsport.net/gfx/person/l/"+personid+".jpg"
								if spielstatus=="red":
									Meldung=minute+translation(30038)+person+translation(30036)+team
									foto1=redcard
									newIMG2 = validLOCATION("https://s.weltsport.net/gfx/person/l/"+personid+".jpg")
									if newIMG2:
										foto2="https://s.weltsport.net/gfx/person/l/"+personid+".jpg"
							except: failing("########## FEHLER - Aktion Card: "+str(Meldung)+" ##########")
						if aktion=="goal":
							try:
								if tor=="false":
									continue
								team=element["team"]["name"]
								person=element["person"]["name"]
								personid=element["person"]["id"]
								if spielstatus=="penalty":    
									Meldung=translation(30031)+minute+translation(30035)+person+translation(30029)+team +translation(30034)+ccontent
								else:
									Meldung=translation(30031)+minute+translation(30032)+person+translation(30033)+team+translation(30037)+ccontent
								newIMG3 = validLOCATION("https://s.weltsport.net/gfx/person/l/"+personid+".jpg")
								if newIMG3:
									foto1="https://s.weltsport.net/gfx/person/l/"+personid+".jpg"
							except: failing("########## FEHLER - Aktion Goal: "+str(Meldung)+" ##########")
						if aktion=="pso":
							try:
								if elfmeter=="false":
									continue
								team=element["team"]["name"]
								person=element["person"]["name"]
								personid=element["person"]["id"]
								if spielstatus=="goal": 
									Meldung=translation(30030)+person+translation(30029)+team
								else: 
									Meldung=translation(30028)+person+translation(30029)+team
								newIMG4 = validLOCATION("https://s.weltsport.net/gfx/person/l/"+personid+".jpg")
								if newIMG4:
									foto1="https://s.weltsport.net/gfx/person/l/"+personid+".jpg"
							except: failing("########## FEHLER - Aktion Pso: "+str(Meldung)+" ##########")
						if aktion=="playing":
							try:
								if spielerwechsel=="false":
									continue
								team=element["team"]["name"]
								if spielstatus=="substitute-out":
									out_spieler=element["person"]["name"]
									out_id=element["person"]["id"]
									Meldung=""
								if spielstatus=="substitute-in":
									in_spieler=element["person"]["name"]
									in_id=element["person"]["id"]
									Meldung=""
								if not in_spieler=="" and not out_spieler=="":
									Meldung=minute+translation(30025)+team+translation(30026)+out_spieler+translation(30027)+in_spieler
									newIMG5 = validLOCATION("https://s.weltsport.net/gfx/person/l/"+out_id+".jpg")
									if newIMG5:
										foto1="https://s.weltsport.net/gfx/person/l/"+out_id+".jpg"
									newIMG6 = validLOCATION("https://s.weltsport.net/gfx/person/l/"+in_id+".jpg")
									if newIMG6:
										foto2="https://s.weltsport.net/gfx/person/l/"+in_id+".jpg"
									out_spieler=""
									out_id=""
									in_spieler=""
									in_id=""
							except: failing("########## FEHLER - Aktion Playing: "+str(Meldung)+" ##########")
						if not Meldung=="" and (int(minute)>int(minute_now[nr]) or oldmessages=="true" ):
							titlelist.append(Meldung)
							cimglist1.append(foto1)
							cimglist2.append(foto2)
							greyoutlist.append(greyout)
							lesezeitlist.append(lesezeit) 
							ins.append(inn)
							auss.append(aus)
							anzal_meldungen.append(anzal_meldung)
							timelist.append(lsv[nr]+int(minute)*60)
							ids.append(id)
				# Sind Meldungen da ?
				if len(timelist)>0 :
					# Meldungen sortieren
					timelist,anzal_meldungen,titlelist,cimglist1,cimglist2,lesezeitlist,greyoutlist,ids,ins,auss = (list(x) for x in zip(*sorted(zip(timelist,anzal_meldungen,titlelist,cimglist1,cimglist2,lesezeitlist,greyoutlist,ids,ins,auss))))
					for i in range(len(titlelist)):  
						# Meldungen die schon da waren - nicht mehr zeigen 
						if not ids[i] in schown:
							debug("(MAIN) ##### Zeit ist : {0} #####".format(str(timelist[i])))
							popwindow.saveMESSAGE(tickerADDON,titlelist[i],cimglist1[i],greyoutlist[i],lesezeitlist[i],xmessage,ymessage,breitemessage,hoehemessage,breitebild1,hoehebild1,font,fontcolor,-1,-1,cimglist2[i],-1,-1,breitebild2,hoehebild2)
							schown.append(ids[i])
							if len(schown)>anzahlmeldungen:
								schown.pop(0)
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
		#log("########## ... END LOOP ##########")
		if monitor.waitForAbort(loop_time):
			break
