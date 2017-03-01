#!/usr/bin/env python3
# -*- coding:utf-8 -*
# PYTHON_ARGCOMPLETE_OK
#
# Skia < skia AT libskia DOT so >
#
# Beerware licensed software - 2017
#

import argparse

from json_handler import JSONHandler
from yaml_handler import YAMLHandler
from utils import KCIHTMLParser



def main(**kwargs):
    print("main kwargs: ")
    print(kwargs)
    print("Latest Kernel CI URL in %s: %s" %
            (kwargs["kernelci_tree"], KCIHTMLParser(tree=kwargs["kernelci_tree"]).get_latest_full_url()))
    # JSONHandler(**kwargs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build up LAVA jobs')
    # parser.add_argument('--v1', '--json', action='store_true', help='Outputs the job as a JSON file, good for LAVA v1')
    # parser.add_argument('--v2', '--yaml', action='store_true', help='Outputs the job as a YAML file, good for LAVA v2')
    parser.add_argument('--kernelci-tree', default="mainline", help='Path to the KernelCI tree you want to use')
    parser.add_argument('--kernel', help='Path to the kernel image you want to use')
    parser.add_argument('--modules', help='Path to the modules tar.gz you want to use as overlay to rootfs')
    parser.add_argument('--output-dir', default="jobs", help='Path where the jobs will be stored (default=./jobs/)')
    parser.add_argument('--job-name', default="custom_job", help='The name you want to give to your job')
    parser.add_argument('--job-template', default="jobs_templates/minimal_linaro_kernel.json", help='The template you want to use for the job')

    main(**vars(parser.parse_args()))

