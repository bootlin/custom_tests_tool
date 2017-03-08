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
import argparse
import configparser

import sys
import re

import requests

import paramiko

parse_re = re.compile('href="([^./"?][^"?]*)"')

def green(str):
    return "\033[32m" + str + "\033[39m"

def red(str):
    return "\033[31m" + str + "\033[39m"

def get_file_config(f_name=None, section="ctt"):
    filename = f_name or os.path.expanduser('~/.cttrc')

    try:
        config = configparser.ConfigParser()
        config.read(filename)
        return dict(config[section])
    except Exception as e:
        print(repr(e))
        print(red("Likely you have no %s section in your configuration file, which is %s" % (section, filename)))
        return {}

def get_args_config(kwargs):
    parser = argparse.ArgumentParser(description='Build up LAVA jobs')
    # parser.add_argument('--v1', '--json', action='store_true', help='Outputs the job as a JSON file, good for LAVA v1')
    # parser.add_argument('--v2', '--yaml', action='store_true', help='Outputs the job as a YAML file, good for LAVA v2')
    job = parser.add_argument_group("Job handling")
    job.add_argument('--no-kci', action='store_true',
            help="Don't go fetch file from KernelCI, but rather use my provided files (you must then provide a kernel, a dtb, a modules.tar.xz, and a rootfs)")
    job.add_argument('--output-dir', default="jobs", help='Path where the jobs will be stored (default=./jobs/)')
    job.add_argument('--job-name', default="ctt", help='The name you want to give to your job')
    job.add_argument('--job-template', default="jobs_templates/job_template.json", help='The template you want to use for the job')
    job.add_argument('--rootfs', help='Path to the rootfs image you want to use (cpio.gz format)')
    job.add_argument('--kernel', help='Path to the kernel image you want to use')
    job.add_argument('--dtb', help='Path to the dtb file you want to use')
    job.add_argument('--modules', help='Path to the modules tar.gz you want to use as overlay to rootfs')
    job.add_argument('--tests', default="jobs_templates/test_launcher.yaml", help='Path to the test file you want to use run')

    lava = parser.add_argument_group("LAVA server options")
    lava.add_argument('--stream', default=kwargs["stream"], help='The bundle stream where to send the job')
    lava.add_argument('--server', default=kwargs["server"], help='The LAVA server URL to send results')
    lava.add_argument('--username', default=kwargs["username"], help='The user name to talk to LAVA')
    lava.add_argument('--token', default=kwargs["token"], help='The token corresponding to the user to talk to LAVA')

    kci = parser.add_argument_group("KernelCI options")
    kci.add_argument('--api-token', default=kwargs["api_token"], help="The token to query KernelCI's API")
    kci.add_argument('--kernelci-tree', default="mainline", help='Path to the KernelCI tree you want to use')

    ssh = parser.add_argument_group("SSH server options")
    ssh.add_argument('--ssh-server', default=kwargs["ssh_server"], help='The ssh server IP, where to send the custom files')
    ssh.add_argument('--ssh-username', default=kwargs["ssh_username"], help='The ssh username to send the custom files')

    parser.add_argument('--upload', action='store_true', help='Send the custom files to the server')
    parser.add_argument('--send', action='store_true', help='Send the job directly, rather than saving it to output')
    parser.add_argument('-b', '--boards', required=True, nargs='+', help='List of board for which you want to create jobs')
    kwargs.update(vars(parser.parse_args()))
    return kwargs

def get_config(section="ctt"):
    kwargs = {
            "username": None,
            "server": None,
            "token": None,
            "stream": "/anonymous/test/",
            "ssh_server": None,
            "ssh_username": "root", # XXX that's not really good
            "api_token": None,
            }
    kwargs.update(get_file_config())
    kwargs = get_args_config(kwargs)
    return kwargs

class KCIFetcher():
    root_url = "https://storage.kernelci.org/"
    in_tbody = False
    in_tr = False
    stop_handling = False
    latests = []
    count = 5

    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs

    def get_latest_release(self):
        try:
            r = requests.get("https://api.kernelci.org/build?limit=1&date_range=5&job=mainline&field=kernel&sort=created_on",
                    headers={'Authorization': get_config()['api_token']})
            r.raise_for_status()
            return r.json()['result'][0]['kernel']
        except Exception as e:
            print(red(repr(e)))

    def get_latest_full_url(self):
        return self.root_url + self.kwargs["kernelci_tree"] + "/" + self.get_latest_release()

    def crawl(self, board, base_url=None):
        print("Crawling KernelCI for %s" % board['name'])
        url = base_url or self.get_latest_full_url()
        if not url.endswith('/'):
            url += "/"
        try:
            html = urllib.request.urlopen(url).read().decode('utf-8')
        except urllib.error.HTTPError as e:
            return repr(e)
        files = parse_re.findall(html)
        dirs = []
        for name in files:
            for defconfig in board['defconfigs']:
                if defconfig == name[:-1]:
                    print("Found a kernel for %s in %s" % (board["name"], url+name))
                    common_url = url+name
                    yield {
                            'kernel': common_url + 'zImage',
                            'dtb': common_url + 'dtbs/' + board['dt'] + '.dtb',
                            'modules': common_url + 'modules.tar.xz',
                            }



    def get_latest_kernel(self):
        return self.kernel_url

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
        print(red("Unable to connect to %s" % url))
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

    print(red("WARNING: host key unavailable"))
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
            print(red("ERROR: remote host identification has changed!"))
            sys.exit(1)

    # We don't use the connect() method directly because it can't handle
    # multiple keys from the SSH agent. It's also not possible to call it
    # multiple time as a workaround because this genius calls start_client()
    pkey_connect(transport, user)
    if not transport.is_authenticated():
        print(red("ERROR: Authentication failed."))
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

