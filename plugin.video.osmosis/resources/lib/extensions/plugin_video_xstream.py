# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re


def getProviderId(plugin_id, url):
    provider = plugin_id
    site = re.search('site=(.*)\&function', url)
    if site:
        provider = '{0}: {1}'.format(provider, site.group(1))

    return provider


def getProvidername(provider_name, url):
    site = re.search('site=(.*)\&function', url)
    if site:
        provider_name = '{0}: {1}'.format(provider_name, site.group(1))

    return provider_name