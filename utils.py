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

parse_re = re.compile('href="([^./"?][^"?]*)/"')

def green(str):
    return "\033[32m" + str + "\033[39m"

def red(str):
    return "\033[31m" + str + "\033[39m"

def get_file_config(f_name=None, section="ctt"):
    filename = f_name or os.path.expanduser('~/.cttrc')

    try:
        config = configparser.ConfigParser()
        config.read(filename)
        kwargs = dict(config[section])
        try:
            kwargs['notify'] = kwargs['notify'].split(',')
        except: pass
        try:
            kwargs['notify_on_incomplete'] = kwargs['notify_on_incomplete'].split(',')
        except: pass
        return kwargs
    except Exception as e:
        print(repr(e))
        print(red("Likely you have no %s section in your configuration file, which is %s" % (section, filename)))
        return {}

def get_args_config(kwargs):
    parser = argparse.ArgumentParser(description='Build up LAVA jobs')
    job = parser.add_argument_group("Job handling")
    job.add_argument('--output-dir', default="jobs", help='Path where the jobs will be stored (default=./jobs/)')
    job.add_argument('--rootfs-path', default=kwargs["rootfs_path"], help='Path to the rootfs images directory where prebuilt rootfs are stored')
    job.add_argument('--job-name', help='The name you want to give to your job')
    # job.add_argument('--job-template', default="jobs_templates/simple_test_job_template.jinja", help='The template you want to use for the job')
    job.add_argument('--rootfs', help='Path to the rootfs you want to use (cpio.gz format)')
    job.add_argument('--kernel', help='Path to the kernel image you want to use')
    job.add_argument('--dtb', help='Path to the dtb file you want to use')
    job.add_argument('--dtb-folder', help='Path to the dtb folder you want to use (default DT names will be searched)')
    job.add_argument('--modules', help='Path to the modules tar.gz you want to use as overlay to rootfs')
    job.add_argument('-t', '--tests', default=[], nargs='+', help='The tests for which you want to generate jobs')
    job.add_argument('-m', '--tests-multinode', default=[], nargs='+', help='The multinode tests for which you want to generate jobs')

    lava = parser.add_argument_group("LAVA server options")
    lava.add_argument('--stream', default=kwargs["stream"], help='The bundle stream where to send the job')
    lava.add_argument('--server', default=kwargs["server"], help='The LAVA server URL to send results')
    lava.add_argument('--username', default=kwargs["username"], help='The user name to talk to LAVA')
    lava.add_argument('--token', default=kwargs["token"], help='The token corresponding to the user to talk to LAVA')

    artifacts = parser.add_argument_group("Artifacts options")
    artifacts.add_argument('--api-token', default=kwargs["api_token"], help="The token to query KernelCI's API")
    artifacts.add_argument('--tree', default="mainline", help='The tree you want to use (default: mainline)')
    artifacts.add_argument('--branch', default="master", help='The branch you want to use (default: master)')
    artifacts.add_argument('--no-kci', action='store_true',
            help="""Don't go fetch file from KernelCI, but rather use my provided
files (you must then provide a kernel, a dtb, a modules.tar.xz, and a rootfs)
This is useful if something.kernelci.org is down.
""")

    ssh = parser.add_argument_group("SSH server options")
    ssh.add_argument('--ssh-server', default=kwargs["ssh_server"], help='The ssh server IP, where to send the custom files')
    ssh.add_argument('--ssh-username', default=kwargs["ssh_username"], help='The ssh username to send the custom files')

    parser.add_argument('--no-send', action='store_true', help='Don\'t send the job directly, save it to output')
    parser.add_argument('--default-notify', action='store_true', help='Use the default notify list provided by the boards configuration')
    parser.add_argument('--notify', default=kwargs['notify'], nargs='+', help='List of addresses to which the notifications will be sent.')
    parser.add_argument('--notify-on-incomplete', default=kwargs['notify_on_incomplete'], nargs='+', help='List of addresses to which the notifications will be sent if the job is incomplete.')
    parser.add_argument('-b', '--boards', default=[], nargs='+', help='List of board for which you want to create jobs')
    parser.add_argument('-l', '--list', action='store_true', help="List all the known devices")
    kwargs.update(vars(parser.parse_args()))
    return kwargs

def get_config(section="ctt"):
    kwargs = { # args here can be set in the .cttrc file
            "username": None,
            "server": None,
            "token": None,
            "stream": "/anonymous/test/",
            "ssh_server": None,
            "ssh_username": "root", # XXX that's not really good
            "api_token": None,
            "rootfs_path": ".",
            "notify": [],
            "notify_on_incomplete": [],
            }
    kwargs.update(get_file_config())
    kwargs = get_args_config(kwargs)
    return kwargs

class ArtifactsFinder():

    def __init__(self, root_url, *args, **kwargs):
        self.kwargs = kwargs
        self.root_url = root_url

    def get_image_name(board):
        if board['arch'] == 'arm':
            return "zImage"
        elif board['arch'] == 'arm64':
            return "Image"
        return "unknownImage"

    def get_latest_release(self):
        if self.root_url.startswith('http'): # KernelCI's case
            try:
                r = requests.get("https://api.kernelci.org/build?limit=1&job=%s&field=kernel&sort=created_on&git_branch=%s" % (self.kwargs["tree"], self.kwargs["branch"]),
                        headers={'Authorization': get_config()['api_token']})
                r.raise_for_status()
                return r.json()['result'][0]['kernel']
            except Exception as e:
                print(red(repr(e)))
        else:
            with open(os.path.join(self.root_url, self.kwargs['tree'],
                self.kwargs['branch'], "latest")) as f:
                return f.read().strip()

    def get_latest_full_url(self):
        return self.root_url + self.kwargs["tree"] + "/" + self.kwargs["branch"] + "/" + self.get_latest_release()

    def crawl(self, board, defconfig):
        print("Crawling %s for %s (%s)" % (self.root_url, board['name'],
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
                print(red(repr(e)))
                print(red("It seems that we have some problems using %s" % url))
                return repr(e)
        else: # It seems we have a local defconfig to find
            files = [f.name for f in os.scandir(url)]
            url = "file://" + url
        for name in files:
            if defconfig == name:
                print("Found a kernel for %s in %s" % (board["name"], url + name))
                common_url = url + name + '/'
                return {
                        'kernel': common_url + ArtifactsFinder.get_image_name(board),
                        'dtb': common_url + 'dtbs/' + board['dt'] + '.dtb',
                        'modules': common_url + 'modules.tar.xz',
                        }
        print("Nothing found at address %s" % (url))

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

