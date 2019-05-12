#!/usr/bin/python
# -*- coding: utf-8 -*-

from resources.lib.tools import *
from resources.lib.sonoff import Sonoff_Switch

iconpath = os.path.join(PATH, 'resources', 'media')
writeLog('Addon started')

devices = []
for i in xrange(1, 9):
    if getAddonSetting('%s_enabled' % (i), sType=BOOL):
        for j in xrange(0, getAddonSetting('%s_channels' % (i), sType=NUM) + 1):
            device_properties = {'switchable': getAddonSetting('%s_switchable' % (i), sType=BOOL),
                                      'ip': getAddonSetting('%s_ip' % (i)),
                                      'channel': j,
                                      'multichannel': True if getAddonSetting('%s_channels' % (i), sType=NUM) > 0 else False,
                                      'name': getAddonSetting('%s_name_%s' % (i, j))}
            devices.append(device_properties)

writeLog(str(devices))
_devlist = []
for device in devices:
    sd = Sonoff_Switch()
    if device['multichannel']:
        device.update({'status': sd.send_command(device['ip'], sd.STATUS[device['channel']], channel=device['channel'] + 1, timeout=5)})
    else:
        device.update({'status': sd.send_command(device['ip'], sd.STATUS[device['channel']], timeout=5)})

    if device['status'] == 'ON':
        L2 = LS(30021) if device['switchable'] else LS(30024)
        icon = os.path.join(iconpath, 'sonoff_on.png')
    elif device['status'] == 'OFF':
        L2 = LS(30020) if device['switchable'] else LS(30024)
        icon = os.path.join(iconpath, 'sonoff_off.png')
    elif device['status'] == 'UNREACHABLE':
        L2 = LS(30022)
        icon = os.path.join(iconpath, 'sonoff_undef.png')
        device.update({'switchable': False})
    else:
        L2 = LS(30023)
        icon = os.path.join(iconpath, 'sonoff_undef.png')
        device.update({'switchable': False})

    liz = xbmcgui.ListItem(label=device['name'], label2=L2, iconImage=icon)
    liz.setProperty('name', device['name'])
    liz.setProperty('ip', device['ip'])
    liz.setProperty('channel', str(device['channel']))
    liz.setProperty('switchable', str(device['switchable']))
    _devlist.append(liz)

if len(_devlist) > 0:
    dialog = xbmcgui.Dialog()
    _idx = dialog.select(LS(30000), _devlist, useDetails=True)
    if _idx > -1:
        if strToBool(_devlist[_idx].getProperty('switchable')):
            res = sd.send_command(_devlist[_idx].getProperty('ip'), sd.TOGGLE[int(_devlist[_idx].getProperty('channel'))])
            writeLog('%s (%s) switched to %s' % (_devlist[_idx].getProperty('name'), _devlist[_idx].getProperty('ip'), res))
        else:
            writeLog('%s (%s) is not switchable' % (_devlist[_idx].getProperty('name'), _devlist[_idx].getProperty('ip')))
            notify(LS(30000), LS(30014) % (_devlist[_idx].getProperty('name')), icon=xbmcgui.NOTIFICATION_WARNING)
else:
    writeLog('no switchable devices found')
    notify(LS(30000), LS(30015), icon=xbmcgui.NOTIFICATION_WARNING)
