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

import os
import sys

import paramiko

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

# The next three function are borrowed from Lavabo, thx Oleil! :)
def get_hostkey(hostname):
    try:
        hkeys = paramiko.util.load_host_keys(os.path.expanduser("~/.ssh/known_hosts"))
    except IOError:
        hkeys = {}

    if hostname in hkeys:
        hkeytype = hkeys[hostname].keys()[0]
        return hkeys[hostname][hkeytype]

    print("WARNING: host key unavailable")
    return None

def pkey_connect(transport, user):
    for pkey in paramiko.Agent().get_keys():
        try:
            transport.auth_publickey(user, pkey)
            break
        except paramiko.SSHException:
            pass

def get_sftp(hostname, port, user):
    print("    Opening SSH connection... ", end='')
    hkey = get_hostkey(hostname)
    transport = paramiko.Transport((hostname, port))

    # We must set _preferred_keys before calling start_client() otherwise
    # there's a chance Paramiko won't negotiate the host key type we have
    # in our local known_keys... And there's no way to set it properly.
    if hkey is not None:
        transport._preferred_keys = [hkey.get_name()]

    transport.start_client()

    # Host key checks
    if hkey is not None:
        rkey = transport.get_remote_server_key()
        if rkey.get_name() != hkey.get_name() or rkey.asbytes() != hkey.asbytes():
            print("ERROR: remote host identification has changed!")
            sys.exit(1)

    # We don't use the connect() method directly because it can't handle
    # multiple keys from the SSH agent. It's also not possible to call it
    # multiple time as a workaround because this genius calls start_client()
    pkey_connect(transport, user)
    if not transport.is_authenticated():
        print("ERROR: Authentication failed.")
        transport.close()
        sys.exit(1)

    sftp_client = transport.open_sftp_client()
    print("Done")
    return sftp_client

def mkdir_p(sftp, remote_directory):
    dir_path = str()
    for dir_folder in remote_directory.split("/"):
        if dir_folder == "":
            continue
        dir_path += r"/{0}".format(dir_folder)
        try:
            sftp.listdir(dir_path)
        except IOError:
            sftp.mkdir(dir_path)

