#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Skia < skia AT libskia DOT so >
#
# Beerware licensed software - 2017
#

import os
import json
import collections
import utils


class JSONHandler:
    """
    This class handle the JSON jobs.

    This means updating a template with the given values, then sending it to
    LAVA before following the progress of the job to make some reporting when it
    completes (or not).
    """
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.get_job_from_file(self.kwargs["job_template"])

    def apply_overrides(self):
        self.override_kernel()
        self.override_modules()
        self.override_job_name()
        self.override_lava_infos()

    def get_job_from_file(self, file):
        with open(file) as f:
            self.job = json.load(f, object_pairs_hook=collections.OrderedDict)

    def save_job_to_file(self):
        try: os.makedirs(self.kwargs["output_dir"])
        except: pass
        file = os.path.join(self.kwargs["output_dir"], self.kwargs["job_name"] + ".json")
        with open(file, 'w') as f:
            json.dump(self.job, f, indent=4)
        print("File saved to", file)

    def override_kernel(self):
        if self.kwargs["kernel"]:
            self.job["actions"][0]["parameters"]["kernel"] = os.path.abspath(self.kwargs["kernel"])
        else:
            print("kernel: Nothing to override")
        # Serve local kernel somewhere and compute the right URL, instead of
        # just the given local path

    def override_modules(self):
        if self.kwargs["modules"]:
            self.job["actions"][0]["parameters"]["overlays"] += [os.path.abspath(self.kwargs["modules"])]
        else:
            print("modules: Nothing to override")

    def override_lava_infos(self):
        try:
            self.job["actions"][2]["parameters"]["server"] = self.kwargs["server"]
            self.job["actions"][2]["parameters"]["stream"] = self.kwargs["stream"]
        except: pass

    def override_job_name(self):
        # TODO: add some more information, like the user crafting the job, or
        # the kernel version, or anything else that can be useful
        self.job["job_name"] = self.kwargs["job_name"]
        print("job name: new name is: %s" % self.kwargs["job_name"])

    def send_to_lava(self):
        print("Sending to LAVA")
        job_str = json.dumps(self.job)
        ret = utils.get_connection(**self.kwargs).scheduler.submit_job(job_str)
        print("Job send (id:", ret, ")")
        print("Potential working URL: ", "http://%s/scheduler/job/%s" % (self.kwargs['local_server'], ret))



