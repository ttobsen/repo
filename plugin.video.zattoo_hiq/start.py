# coding=utf-8
#
#    copyright (C) 2020 Steffen Rolapp (github@rolapp.de)
#
#    This file is part of zattooHiQ
#
#    zattooHiQ is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    zattooHiQ is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with zattooHiQ.  If not, see <http://www.gnu.org/licenses/>.
#

import resources.lib.service as service
import xbmc, xbmcgui, xbmcaddon, xbmcvfs


__addon__ = xbmcaddon.Addon()
__addondir__  = xbmc.translatePath( __addon__.getAddonInfo('profile') ) 
__ALT__ = xbmcaddon.Addon('plugin.video.zattooHiQ')
__ALTDIR__ =  xbmc.translatePath( __ALT__.getAddonInfo('profile') ) 

if xbmc.getCondVisibility(System.HasAddon(plugin.video.zattooHiQ)):
    dialog = xbmcgui.Dialog()
    ret = dialog.yesno('ZattooHiQ', 'Eine Vorgänger version des Addon wurde gefunden., Sollen die Einstellungen übernommen Werden?')
    
    if ret:
        if xbmcvfs.exists(__ALTDIR__):
             xbmcvfs.copy(__ALTDIR__'/settings.xml', __addindir__'/settings.xml')
             xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","id":7,"params":{"addonid": "%s","enabled":false}}' % 'plugin.video.zattooHiQ')
    




service.start() 

