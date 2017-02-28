#!/usr/bin/env python3
# -*- coding:utf-8 -*
# PYTHON_ARGCOMPLETE_OK
#
# Skia < skia AT libskia DOT so >
#
# Beerware licensed software - 2017
#

import os
import json
import ruamel.yaml
import collections
import argparse
import argcomplete


def get_job_from_yaml_file(file):
    with open(file) as f:
        job = ruamel.yaml.load(f, Loader=ruamel.yaml.RoundTripLoader)
        return job
        job['actions'][0]['deploy']['timeout']['minutes'] = 4000
        print(ruamel.yaml.dump(job, Dumper=ruamel.yaml.RoundTripDumper))

def save_job_to_yaml_file(job, file):
    with open(file, 'w') as f:
        f.write(ruamel.yaml.dump(job, Dumper=ruamel.yaml.RoundTripDumper))

class JSONHandler:
    job_template = "jobs_templates/minimal_linaro_kernel.json"

    def get_job_from_file(self, file):
        with open(file) as f:
            self.job = json.load(f, object_pairs_hook=collections.OrderedDict)

    def save_job_to_file(self):
        try: os.makedirs(self.kwargs["output_dir"])
        except: pass
        file = os.path.join(self.kwargs["output_dir"], self.kwargs["job_name"] + ".json")
        with open(file, 'w') as f:
            json.dump(self.job, f, indent=4)

    def override_kernel(self):
        self.job["actions"][0]["parameters"]["kernel"] = os.path.abspath(self.kwargs["kernel"])
        # Serve local kernel somewhere and compute the right URL, instead of
        # just the given local path

    def override_modules(self):
        if self.kwargs["modules"]:
            self.job["actions"][0]["parameters"]["overlays"] += [os.path.abspath(self.kwargs["modules"])]

    def override_job_name(self):
        # TODO: add some more information, like the user crafting the job, or
        # the kernel version, or anything else that can be useful
        self.job["job_name"] = self.kwargs["job_name"]

    def handle(self, **kwargs):
        self.kwargs = kwargs
        self.get_job_from_file(self.job_template)
        self.override_kernel()
        self.override_modules()
        self.override_job_name()
        self.save_job_to_file()

def main(**kwargs):
    print("main kwargs: ")
    print(kwargs)
    JSONHandler().handle(**kwargs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build up LAVA jobs')
    # parser.add_argument('--v1', '--json', action='store_true', help='Outputs the job as a JSON file, good for LAVA v1')
    # parser.add_argument('--v2', '--yaml', action='store_true', help='Outputs the job as a YAML file, good for LAVA v2')
    parser.add_argument('--kernel', required=True, help='Path to the kernel image you want to use')
    parser.add_argument('--modules', help='Path to the modules tar.gz you want to use as overlay to rootfs')
    parser.add_argument('--output-dir', default="jobs", help='Path where the jobs will be stored (default=./jobs/)')
    parser.add_argument('--job-name', default="custom_job", help='The name you want to give to your job')
    argcomplete.autocomplete(parser)
    main(**vars(parser.parse_args()))

