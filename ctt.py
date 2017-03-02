#!/usr/bin/env python3
# -*- coding:utf-8 -*
# PYTHON_ARGCOMPLETE_OK
#
# Skia < skia AT libskia DOT so >
#
# Beerware licensed software - 2017
#

import os
import argparse
import configparser
import urllib.parse

from json_handler import JSONHandler
from yaml_handler import YAMLHandler
from utils import KCIHTMLParser, get_connection


def main(**kwargs):
    print("main kwargs: ")
    print(kwargs)
    print("Latest Kernel CI URL in %s: %s" %
            (kwargs["kernelci_tree"], KCIHTMLParser(tree=kwargs["kernelci_tree"]).get_latest_full_url()))
    h = JSONHandler(**kwargs)
    h.apply_overrides()
    if kwargs["send"]:
        h.send_to_lava()
    else:
        h.save_job_to_file()


def get_config(section="ctt"):
    conf = {
            "username": None,
            "server": None,
            "token": None,
            "stream": "/anonymous/test/",
            "ssh_server": None,
            "ssh_username": "root", # XXX that's not really good
            }
    filename = os.path.expanduser('~/.lavarc')

    config = configparser.ConfigParser()

    config.read(filename)
    conf.update(dict(config[section]))
    return conf

if __name__ == "__main__":
    kwargs = get_config()

    parser = argparse.ArgumentParser(description='Build up LAVA jobs')
    # parser.add_argument('--v1', '--json', action='store_true', help='Outputs the job as a JSON file, good for LAVA v1')
    # parser.add_argument('--v2', '--yaml', action='store_true', help='Outputs the job as a YAML file, good for LAVA v2')
    job = parser.add_argument_group("Job handling")
    job.add_argument('--output-dir', default="jobs", help='Path where the jobs will be stored (default=./jobs/)')
    job.add_argument('--job-name', default="custom_job", help='The name you want to give to your job')
    job.add_argument('--job-template', default="jobs_templates/minimal_linaro_kernel.json", help='The template you want to use for the job')
    job.add_argument('--kernel', help='Path to the kernel image you want to use')
    job.add_argument('--dtb', help='Path to the dtb file you want to use')
    job.add_argument('--modules', help='Path to the modules tar.gz you want to use as overlay to rootfs')

    lava = parser.add_argument_group("LAVA server options")
    lava.add_argument('--stream', default=kwargs["stream"], help='The bundle stream where to send the job')
    lava.add_argument('--server', default=kwargs["server"], help='The LAVA server URL to send results')
    lava.add_argument('--username', default=kwargs["username"], help='The user name to talk to LAVA')
    lava.add_argument('--token', default=kwargs["token"], help='The token corresponding to the user to talk to LAVA')

    ssh = parser.add_argument_group("SSH server options")
    ssh.add_argument('--ssh-server', default=kwargs["ssh_server"], help='The ssh server IP, where to send the custom files')
    ssh.add_argument('--ssh-username', default=kwargs["ssh_username"], help='The ssh username to send the custom files')

    parser.add_argument('--kernelci-tree', default="mainline", help='Path to the KernelCI tree you want to use')
    parser.add_argument('--send', action='store_true', help='Send the job directly, rather than saving it to output')

    kwargs.update(vars(parser.parse_args()))

    main(**kwargs)

