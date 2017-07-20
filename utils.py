import urllib.request
import urllib.error
import urllib.parse

import xmlrpc.client
import ssl

import os
import argparse
import configparser
import logging

import sys
import re

import requests

import paramiko

parse_re = re.compile('href="([^./"?][^"?]*)/"')

class ArtifactsFinder():

    def __init__(self, cfg, root_url, *args):
        self.cfg = cfg
        self.root_url = root_url

    def get_image_name(board):
        if board['arch'] == 'arm':
            return "zImage"
        elif board['arch'] == 'arm64':
            return "Image"
        return "unknownImage"

    def get_latest_release(self):
        if "kernelci" in self.root_url: # KernelCI's case
            try:
                r = requests.get("https://api.kernelci.org/build?limit=1&job=%s&field=kernel&sort=created_on&git_branch=%s" % (self.cfg['tree'], self.cfg['branch']),
                                 headers={'Authorization': self.cfg['api_token']})
                r.raise_for_status()
                return r.json()['result'][0]['kernel']
            except IndexError:
                raise IOError
        else:
            if self.root_url.startswith("http"):
                r = requests.get("/".join([self.root_url, self.cfg['tree'],
                                           self.cfg['branch'], "latest"]))
                return r.text
            else:
                with open(os.path.join(self.root_url, self.cfg['tree'],
                                       self.cfg['branch'], "latest")) as f:
                    return f.read().strip()

    def get_latest_full_url(self):
        return self.root_url + self.cfg["tree"] + "/" + self.cfg["branch"] + "/" + self.get_latest_release()

    def crawl(self, board, defconfig):
        logging.debug("Crawling %s for %s (%s)" % (self.root_url, board['name'],
                                                   defconfig))
        url = self.get_latest_full_url()
        url = '/'.join([url, board['arch']])
        if not url.endswith('/'):
            url += "/"
        if url.startswith("http"):
            try:
                html = urllib.request.urlopen(url).read().decode('utf-8')
                files = parse_re.findall(html)
            except urllib.error.HTTPError as e:
                logging.error(repr(e))
                return
        else: # It seems we have a local defconfig to find
            try:
                files = [f.name for f in os.scandir(url)]
                url = "file://" + url
            except Exception as e:
                logging.error(repr(e))
                raise e
        for name in files:
            if defconfig == name:
                logging.debug("Found a kernel for %s in %s" % (board["name"],
                                                               url + name))
                common_url = url + name + '/'
                return {
                        'kernel': common_url + ArtifactsFinder.get_image_name(board),
                        'dtb': common_url + 'dtbs/' + board['dt'] + '.dtb',
                        'modules': common_url + 'modules.tar.xz',
                        }

        logging.debug("Nothing found at address %s" % (url))
        raise IOError

def get_connection(cfg):
    u = urllib.parse.urlparse(cfg['server'])
    url = "%s://%s:%s@%s/RPC2" % (u.scheme,
                                  cfg['username'],
                                  cfg['token'],
                                  u.netloc)

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
        logging.error("Unable to connect to %s" % url)
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

    logging.warning("host key unavailable")
    return None

def pkey_connect(transport, user):
    for pkey in paramiko.Agent().get_keys():
        try:
            transport.auth_publickey(user, pkey)
            break
        except paramiko.SSHException:
            pass

def get_sftp(hostname, port, user):
    logging.debug("Opening SSH connection...")
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
            logging.error("Remote host identification has changed!")
            sys.exit(1)

    # We don't use the connect() method directly because it can't handle
    # multiple keys from the SSH agent. It's also not possible to call it
    # multiple time as a workaround because this genius calls start_client()
    pkey_connect(transport, user)
    if not transport.is_authenticated():
        logging.error("Authentication failed")
        transport.close()
        sys.exit(1)

    sftp_client = transport.open_sftp_client()
    logging.debug('Connection established')
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

