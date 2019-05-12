#! /usr/bin/python

import urllib
import xbmcgui

ext_ip = urllib.urlopen('http://ident.me').read().decode('utf-8')
wid = xbmcgui.Window(xbmcgui.getCurrentWindowId())
try:
    wid.getControl(10).setLabel('WAN IP-Adresse: %s' % (ext_ip))
except AttributeError:
    xbmcgui.Dialog().notification('Externe IP-Adresse (WAN)', ext_ip)
except RuntimeError:
    xbmcgui.Dialog().notification('Externe IP-Adresse (WAN)', ext_ip)