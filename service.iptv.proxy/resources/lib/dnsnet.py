# -*- coding: utf-8 -*-
import zapisession as zapi

class DnsNet(zapi.ZapiSession):
    def __init__(self, username, password):
        zapi.ZapiSession.__init__(self, username, password)
        self.baseUrl = 'https://www.quantum-tv.com/'
        self.serviceName = 'DNS_NET TV Online'
        self.serviceId = 'dnsnet'

    def announce(self):
        url = self.baseUrl + '/zapi/v2/session/hello'
        params = {"client_app_token" : self.fetchAppToken(),
                  "uuid"    : "9570fd41-c296-498e-8e75-d4f29aee1d19",
                  "lang"    : "de",
                  "app_version": "2.1.0",
                  "format"      : "json"}
        self.session.post(url, data=params, verify=False)
