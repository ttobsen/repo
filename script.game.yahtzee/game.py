#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2018 Mark König (mark.koenig@kleiner-schelm.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import os
import random
from random import randint
import time
import thread
import string
import sys

import xbmc
import xbmcaddon
import xbmcgui

addon = xbmcaddon.Addon()

ADDON_NAME = addon.getAddonInfo('name')
ADDON_PATH = addon.getAddonInfo('path').decode('utf-8')
MEDIA_PATH = os.path.join(
    xbmc.translatePath(ADDON_PATH),
    'resources',
    'skins',
    'default',
    'media'
)
LIB_PATH = os.path.join(
    xbmc.translatePath(ADDON_PATH),
    'resources',
    'lib'
)

libs  = xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'lib' ).encode("utf-8") ).decode("utf-8")
sys.path.append(libs)

import yahtzee_points
import yahtzee_logic

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92

class Game(xbmcgui.WindowXML):

    pointsP1 = []
    pointsP2 = []
    pointsP3 = []
    pointsP4 = []

    hold = []
    dice = []

    soundOn = True

    round = 0
    actualTry = 1
    actualPlayer = 0

    player = 2
    computer = 0
    gameOn = False

    diceOn = False
    diceCnt = 0
    diceFinished = 0

# ----------------------------------------------------------------------------------------------------

    def onInit(self):
        # init vars
        yahtzee_logic.ReadRestgewinn()

        # init points
        for i in range(15):
            self.pointsP1.append(-1)
            self.pointsP2.append(-1)
            self.pointsP3.append(-1)
            self.pointsP4.append(-1)

        for i in range(5):
            self.hold.append(False)
            self.dice.append(6)

        # set points
        self.updatePoints()

        # get controls

        # init the grid

        # start the timer thread
        thread.start_new_thread(self.timer_thread, ())
        # start the game
                
        self.updateToggleButtons(0)

    def onAction(self, action):
        action_id = action.getId()
        focus_id = self.getFocusId()
        
        if action_id == ACTION_PREVIOUS_MENU:
            self.closeApp()
        if action_id == ACTION_NAV_BACK:
            self.closeApp()            

    def closeApp(self):
        dialog = xbmcgui.Dialog()        
        confirmed = dialog.yesno(addon.getLocalizedString(3025),
                                 addon.getLocalizedString(3045),
                                 addon.getLocalizedString(3046)
                                )
        if confirmed:
            self.close()

    def onFocus(self, control_id):
        self.updateToggleButtons(control_id)

    def onClick(self, control_id):

        # set points
        if(control_id >= 5299) and (control_id < 5320):
            btn = control_id - 5300 + 1

            if(self.gameOn and not self.diceOn and (self.actualTry > 0)):
                points = self.GetValuePlayer(self.actualPlayer)
                if(points[btn-1] == -1):

                    value = yahtzee_points.GetCalc(btn, self.dice)
                                        
                    # bonus rule
                    if(value > 0):
                        if(yahtzee_points.GetCalc(13, self.dice) == 50):  # check is yahtzee
                            if(btn == self.dice[0]):                      # correct number for yahtzee
                                if(points[12] == 50):                     # check yahtzee already used
                                    value = value + 50                    # add bonus
                                
                    if(value == 0):
                        dialog = xbmcgui.Dialog()        
                        confirmed = dialog.yesno(addon.getLocalizedString(3042),
                                                 addon.getLocalizedString(3043),
                                                 addon.getLocalizedString(3044),
                                                 addon.getLocalizedString(3012 + btn)
                                                 )
                                         
                        if confirmed:
                            self.SetValuePlayer(self.actualPlayer, btn-1, 0)
                            self.updatePoints()
                            self.NextPlayer()
                    else:
                        self.SetValuePlayer(self.actualPlayer, btn-1, value)
                        self.updatePoints()
                        self.NextPlayer()

        # new game
        if(control_id == 5002):
            if(self.gameOn):
                 dialog = xbmcgui.Dialog()
                 confirmed = dialog.yesno(addon.getLocalizedString(3034),
                                          addon.getLocalizedString(3035),
                                          addon.getLocalizedString(3036)
                                          )
                 if confirmed:
                     self.NewGame()
            else:
                self.NewGame()

        # set player
        if(control_id == 5003):
            if(not self.gameOn):
                if(self.player<4):
                    self.player = self.player + 1
                else:
                    self.player = 1

                if(self.player + self.computer) > 4:
                   self.computer = 4 - self.player
                self.updateToggleButtons(0)

        # set computer
        if(control_id == 5004):
            if(not self.gameOn):
                if self.computer < (4 - self.player):
                    # not implemeneted yet
                    #self.computer = self.computer + 1
                    pass
                else:
                    self.computer = 0
                self.updateToggleButtons(0)

        # sound on/off
        if(control_id == 5005):
            self.soundOn = not self.soundOn
            self.updateToggleButtons(control_id)

        # dice
        if(control_id == 5008):
            if(not self.gameOn):
            
                self.NewGame()
                
                self.gameOn = True
                self.actualPlayer = 1
                self.actualTry = 1

                self.diceOn = True
                
                if(self.soundOn):
                    xbmc.playSFX(MEDIA_PATH + '\\dice.wav')
                    
                self.diceOn = True
                self.diceFinished = False

                self.updateToggleButtons(control_id);
            else:
                if(self.actualTry < 3):
                    self.actualTry = self.actualTry + 1
                    self.diceOn = True
                    self. diceFinished = False

                    if(self.soundOn):
                        xbmc.playSFX(MEDIA_PATH + '\\dice.wav')
                    self.diceOn = True
                    self.diceFinished = False

                    self.updateToggleButtons(control_id);
                else:
                    dialog = xbmcgui.Dialog()
                    confirmed = dialog.ok(addon.getLocalizedString(3025),
                                  addon.getLocalizedString(3029)
                                  )

        # give me a tip
        if(control_id == 5009):
            if(self.gameOn and not self.diceOn and (self.actualTry > 0)):

                testTry = self.actualTry        
                value = self.GetYahzeeMove(testTry)

                # we can already sign a value
                if(value > 9999):
                    testTry = 3
                    value = self.GetYahzeeMove(testTry)
    
                txt = '...'

                if(testTry == 1):
                    if(value != 0):
                        txt = addon.getLocalizedString(3012) + ' : ' + str(value)
                    else:
                        txt = addon.getLocalizedString(3009)
                        
                if(testTry == 2):
                    if(value != 0):
                        txt = addon.getLocalizedString(3012) + ' : ' + str(value)
                    else:
                        txt = addon.getLocalizedString(3009)
                        
                if(testTry == 3):

                    x = value
                    if(x > 5):
                        x = x + 1

                    points = yahtzee_points.GetCalc(x + 1 , self.dice)
                    if(points > 0):
                        txt = addon.getLocalizedString(3040) + ' : ' + addon.getLocalizedString(3013 + x)
                    else:
                        txt = addon.getLocalizedString(3042) + ' : ' + addon.getLocalizedString(3013 + x)
                
                dialog = xbmcgui.Dialog()        
                confirmed = dialog.ok(addon.getLocalizedString(3010),
                                      txt)

        # whats this
        if(control_id == 5010):
            dialog = xbmcgui.Dialog()
            confirmed = dialog.ok(addon.getLocalizedString(3025),
                                  addon.getLocalizedString(3050)
                                  )

        if(self.actualTry > 0) and self.gameOn and not self.diceOn and self.diceFinished:
            if(control_id == 5200):
                self.hold[0] = not self.hold[0]
                self.updateToggleButtons(control_id)
            if(control_id == 5201):
                self.hold[1] = not self.hold[1]
                self.updateToggleButtons(control_id)
            if(control_id == 5202):
                self.hold[2] = not self.hold[2]
                self.updateToggleButtons(control_id)
            if(control_id == 5203):
                self.hold[3] = not self.hold[3]
                self.updateToggleButtons(control_id)
            if(control_id == 5204):
                self.hold[4] = not self.hold[4]
                self.updateToggleButtons(control_id)

    def timer_thread(self):
        while not xbmc.abortRequested:
            if(self.diceOn):
                self.diceCnt = self.diceCnt +1
                if(self.diceCnt < 10):
                    for w in range(5):
                        if (self.hold[w] == False):
                            try:
                                x =randint(1, 6)
                                self.dice[w] = x
                                
                                self.wx = self.getControl(5100 + w)
                                self.wx.setImage('w%s.png' % x)
                            except:
                                pass
                else:
                    self.diceOn = False
                    self.diceFinished = True   
            else:
                self.diceCnt = 0
            xbmc.sleep(150)

    def GetValuePlayer(self, playerNo):
        if(playerNo == 1):
            return self.pointsP1
        if(playerNo == 2):
            return self.pointsP2
        if(playerNo == 3):
            return self.pointsP3
        if(playerNo == 4):
            return self.pointsP4

    def SetValuePlayer(self, playerNo, field, value):
    
        points = self.GetValuePlayer(playerNo)
        points[field] = value
        
        top = 0
        for i in range(6):
            if(points[i] > 0):
                top = top + points[i]
                if(top > 62):
                    top = top + 35      
        bottom = 0
        for i in range(7,14):
            if(points[i] > 0):
                bottom = bottom + points[i]
                
        points[6] = top
        points[14] = top + bottom      

    def NewGame(self):

          self.round = 1
          self.gameOn = False
          self.diceOn = False
          self.diceFinished = False
          
          for i in range(15):
              self.pointsP1[i] = -1
              self.pointsP2[i] = -1
              self.pointsP3[i] = -1
              self.pointsP4[i] = -1
              
          # reset hold
          for i in range(5):
              self.hold[i] = False

          self.updateToggleButtons(0)
          self.updatePoints()

    def NextPlayer(self):
          self.actualTry = 0
          self.actualPlayer = self.actualPlayer + 1

          #reset hold
          for i in range(5):
              self.hold[i] = False

          if (self.actualPlayer > self.player):
              self.actualPlayer = 1
              self.round = self.round + 1
              if (self.round  == 14):
                  self.gameOn = False # game over
                  if(self.soundOn):
                      xbmc.playSFX(MEDIA_PATH + '\\applaus.wav')   

          self.updateToggleButtons(0);

    def updateToggleButtons(self, control_id):

        # update player settings
        self.p0x = self.getControl(5003)
        self.p0x.setLabel(addon.getLocalizedString(3002) + str(self.player))
        
        self.p0x = self.getControl(5004)
        self.p0x.setLabel(addon.getLocalizedString(3003) + str(self.computer))

        # update actual player
        self.p0x = self.getControl(5006)
        if(self.gameOn):
            self.p0x.setLabel(addon.getLocalizedString(3006) + ' ' + str(self.actualPlayer))
        else:
            self.p0x.setLabel(addon.getLocalizedString(3005))

        # protect for startup
        self.p0x = self.getControl(5007)
        self.p0x.setLabel(addon.getLocalizedString(3007) + ' ' + str(self.actualTry) + ' ' +
                          addon.getLocalizedString(3008) + ' 3')

        if len(self.hold) < 4:
            return

        # set fcous / set for the hold button
        for i in range(5):
            self.p0x = self.getControl(5900 + i)

            if(self.hold[i] == False):
                self.p0x.setImage('t_button.png')
            else:
                self.p0x.setImage('t_button_sel.png')

            if(control_id == (5200 + i)):
                if(self.hold[i] == False):
                    self.p0x.setImage('t_button_active.png')
                else:
                    self.p0x.setImage('t_button_active_sel.png')

        # set fcous / set for the sound button
        self.p0x = self.getControl(6005)
        if(self.soundOn == False):
            self.p0x.setImage('t_button.png')
        else:
            self.p0x.setImage('t_button_sel.png')
        if(control_id == (5005)):
            if(self.soundOn == False):
                self.p0x.setImage('t_button_active.png')
            else:
                self.p0x.setImage('t_button_active_sel.png')

    def updatePoints(self):
        for i in range(15):
            self.p0x = self.getControl(5400+ i)
            if(self.pointsP1[i] >= 0):
                self.p0x.setLabel(str(self.pointsP1[i]))
            else:
                self.p0x.setLabel('..')
            self.p0x = self.getControl(5500+ i)
            if(self.pointsP2[i] >= 0):
                self.p0x.setLabel(str(self.pointsP2[i]))
            else:
                self.p0x.setLabel('..')
            self.p0x = self.getControl(5600+ i)
            if(self.pointsP3[i] >= 0):
                self.p0x.setLabel(str(self.pointsP3[i]))
            else:
                self.p0x.setLabel('..')
            self.p0x = self.getControl(5700+ i)
            if(self.pointsP4[i] >= 0):
                self.p0x.setLabel(str(self.pointsP4[i]))
            else:
                self.p0x.setLabel('..')
                
    def GetYahzeeMove(self, actTry):
        data = []
        for i in range(15):
            data.append(0)
            
        for i in range (6):
            data[i] = self.GetValuePlayer(self.actualPlayer)[i]
        for i in range (6,13):
            data[i] = self.GetValuePlayer(self.actualPlayer)[i + 1]

        data[13] = actTry
        data[14] = (self.dice[0] * 10000) + (self.dice[1] * 1000) + (self.dice[2] * 100) + (self.dice[3] * 10) + (self.dice[4] * 1)

        return yahtzee_logic.EinzelAbfrage(data)

    def log(self, msg):
        xbmc.log('[ADDON][%s] %s' % ('TEST', msg.encode('utf-8')),
                 level=xbmc.LOGNOTICE)

# ----------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    game = Game(
        'script-%s-main.xml' % ADDON_NAME,
        ADDON_PATH,
        'default',
        '720p'
    )
    game.doModal()
    del game

sys.modules.clear()
