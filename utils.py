#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Skia < skia AT libskia DOT so >
#
# Beerware licensed software - 2017
#

import urllib.request
import urllib.error
import urllib.parse

import xmlrpc.client
import ssl

from html.parser import HTMLParser

class KCIHTMLParser(HTMLParser):
    root_url = "https://storage.kernelci.org/"
    in_tbody = False
    in_tr = False
    stop_handling = False

    def __init__(self, *args, **kwargs):
        self.tree = kwargs.pop("tree", "mainline")
        return super(KCIHTMLParser, self).__init__(*args, **kwargs)

    def handle_starttag(self, tag, attrs):
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr":
            self.in_tr = True

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr":
            self.in_tr = False

    def handle_data(self, data):
        if not self.stop_handling and self.in_tbody and self.in_tr:
            if data in ["Parent directory/", "-"]:
                pass
            else:
                self.latest = data.strip('/')
                self.stop_handling = True

    def get_latest_release(self):
        url = self.root_url + self.tree + "/?C=M&O=D"

        try:
            page = urllib.request.urlopen(url)
        except urllib.error.HTTPError as e:
            return repr(e)

        self.feed(page.read().decode('utf-8'))
        return self.latest

    def get_latest_full_url(self):
        return self.root_url + self.tree + "/" + self.get_latest_release()

def get_connection(**kwargs):
    u = urllib.parse.urlparse(kwargs["server"])
    url = "%s://%s:%s@%s/RPC2" % (u.scheme,
        kwargs["username"], kwargs["token"], u.netloc)

    # Taken from Lavabo: https://github.com/free-electrons/lavabo/blob/master/utils.py#L88
    try:
        if 'https' == u.scheme:
            context = hasattr(ssl, '_create_unverified_context') and ssl._create_unverified_context() or None
            connection = xmlrpc.client.ServerProxy(url,
                    transport=xmlrpc.client.SafeTransport(use_datetime=True, context=context))
        else:
            connection = xmlrpc.client.ServerProxy(url)
        return connection
    except (xmlrpc.client.ProtocolError, xmlrpc.client.Fault, IOError) as e:
        print("Unable to connect to %s" % url)
        sys.exit(1)

