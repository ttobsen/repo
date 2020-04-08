# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from kodi_six.utils import py2_decode


def warning(text, title='Zattoo Live TV', time=4500, exit=False):
    import xbmc
    import xbmcaddon
    import os.path
    icon = py2_decode(os.path.join(xbmc.translatePath(xbmcaddon.Addon('plugin.video.zattoo_com').getAddonInfo('path')), 'icon.png'))
    xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (title, text, time, icon))
    if exit:
        import sys
        sys.exit(0)