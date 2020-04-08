# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import json

from .api import get_json_data
import pyxbmct.addonwindow as pyxbmct

URI = sys.argv[0]
ADDON_HANDLE = int(sys.argv[1])


def list_epg_item(pid, SESSION, pg_hash):
    url = 'https://zattoo.com/zapi/v2/cached/program/power_details/%s?program_ids=%s&complete=True' % (pg_hash, pid)
    json_data = get_json_data(url, SESSION)
    program_info = json.loads(json_data)['programs'][0]
    channel_name = program_info['channel_name']
    cid = program_info['cid']
    countries = program_info['country'].replace('|', ', ')
    genres = ', '.join(program_info['g'])
    categories = ', '.join(program_info['c'])
    directors = ', '.join([d for d in program_info['cr']['director']])
    actors = ', '.join([a for a in program_info['cr']['actor']])
    desc = program_info['d']
    subtitle = (program_info['et'] or '')
    thumb = program_info['i']
    title = program_info['t']
    if subtitle:
        title = '%s: %s' % (title, subtitle)
    year = program_info['year']
    text = ''
    if desc:
        text += '[COLOR blue]Plot:[/COLOR] %s\n\n' % desc
    if categories:
        text += '[COLOR blue]Kategorien:[/COLOR] %s' % categories
    if genres:
        text += '\n[COLOR blue]Genre:[/COLOR] %s' % genres
    if countries:
        text += '\n[COLOR blue]Produktionsland:[/COLOR] %s' % countries
    if directors:
        text += '\n[COLOR blue]Direktoren:[/COLOR] %s' % directors
    if actors:
        text += '\n[COLOR blue]Schauspieler:[/COLOR] %s' % actors

    if text:
        title = '[B][COLOR blue]%s[/COLOR][/B] %s' % (channel_name, title)
        if year:
            title = '%s (%i)' % (title, year)
        window = pyxbmct.AddonDialogWindow(title)
        window.connect(pyxbmct.ACTION_NAV_BACK, window.close)
        window.setGeometry(1000, 700, 1, 1)
        box = pyxbmct.TextBox()
        window.placeControl(box, 0, 0)
        box.setText(text)
        window.doModal()
        del window