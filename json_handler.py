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
import paramiko
import getpass
from boards import boards

from utils import red, green

REMOTE_ROOT = os.path.join("/tmp/ctt/", getpass.getuser())

class JSONHandler:
    """
    This class handle the JSON jobs.

    This means updating a template with the given values, then sending it to
    LAVA before following the progress of the job to make some reporting when it
    completes (or not).
    """
    def __init__(self, board, **kwargs):
        self.board = boards[board]
        self.kwargs = kwargs
        self.get_job_from_file(self.kwargs["job_template"])

    def apply_overrides(self, kci_data=None):
        if kci_data:
            self.override_kernel(kci_data['kernel'])
            self.override_dtb(kci_data['dtb'])
            self.override_modules(kci_data['modules'])
            self.override_job_name(kci_data)
        else:
            self.override_kernel()
            self.override_dtb()
            self.override_modules()
            self.override_job_name()
        self.override_rootfs()
        # self.override_tests()
        self.override_lava_infos()
        self.override_device_type()

    def get_job_from_file(self, file):
        with open(file) as f:
            self.job = json.load(f, object_pairs_hook=collections.OrderedDict)

    def override_device_type(self):
        print("device-type: Overriding")
        self.job["device_type"] = self.board["device_type"]
        print("device-type: Overridden")

    def override_rootfs(self):
        if self.kwargs["rootfs"]:
            rootfs = self.kwargs['rootfs']
        else:
            rootfs = os.path.join(self.kwargs["rootfs_path"], self.board["rootfs"])
        print("rootfs: Overriding")
        local_path = os.path.abspath(rootfs)
        remote_path = os.path.join(REMOTE_ROOT, os.path.basename(local_path))
        remote_path = self.handle_file(local_path, remote_path)
        if self.board["test_plan"] == "boot":
            self.job["actions"][0]["parameters"]["ramdisk"] = "file://" + remote_path
            print("rootfs: ramdisk overridden")
        elif self.board["test_plan"] == "boot-nfs":
            self.job["actions"][0]["parameters"]["nfsrootfs"] = "file://" + remote_path
            print("rootfs: nfsrootfs overridden")
        else:
            raise Exception(red("Invalid test_plan for board %s" %
                    self.board["name"]))

    def override_dtb(self, dtb_url=None):
        if self.kwargs["dtb"]:
            local_path = os.path.abspath(self.kwargs["dtb"])
            print("DTB: Overriding with local file:", local_path)
            remote_path = os.path.join(REMOTE_ROOT, os.path.basename(local_path))
            remote_path = self.handle_file(local_path, remote_path)
            self.job["actions"][0]["parameters"]["dtb"] = "file://" + remote_path
            print("DTB: Overridden")
        elif dtb_url:
            print("DTB: Overriding with Kernel CI URL:", dtb_url)
            self.job["actions"][0]["parameters"]["dtb"] = dtb_url
            print("DTB: Overridden")
        else:
            print("DTB: Nothing to override")

    def override_kernel(self, kernel_url=None):
        if self.kwargs["kernel"]:
            local_path = os.path.abspath(self.kwargs["kernel"])
            print("kernel: Overriding with local file:", local_path)
            remote_path = os.path.join(REMOTE_ROOT, os.path.basename(local_path))
            remote_path = self.handle_file(local_path, remote_path)
            self.job["actions"][0]["parameters"]["kernel"] = "file://" + remote_path
            print("kernel: Overridden")
        elif kernel_url:
            print("kernel: Overriding with Kernel CI URL:", kernel_url)
            self.job["actions"][0]["parameters"]["kernel"] = kernel_url
            print("kernel: Overridden")
        else:
            print("kernel: Nothing to override")

    def override_modules(self, modules_url=None):
        if self.kwargs["modules"]:
            local_path = os.path.abspath(self.kwargs["modules"])
            print("modules: Overriding with local file:", local_path)
            remote_path = os.path.join(REMOTE_ROOT, os.path.basename(local_path))
            remote_path = self.handle_file(local_path, remote_path)
            self.job["actions"][0]["parameters"]["overlays"] = ["file://" + remote_path]
            print("modules: Overridden")
        elif modules_url:
            print("modules: Overriding with Kernel CI URL:", modules_url)
            self.job["actions"][0]["parameters"]["overlays"] = [modules_url]
            print("modules: Overridden")
        else:
            print("modules: Nothing to override")

    def override_tests(self):
        if self.kwargs["tests"]:
            print("Overriding tests:")
            local_path = os.path.abspath(self.kwargs["tests"])
            remote_path = os.path.join(REMOTE_ROOT, os.path.basename(local_path))
            remote_path = self.handle_file(local_path, remote_path)
            self.job["actions"][2]["parameters"]["testdef_urls"] = ["file://" + remote_path]
            print("tests Overridden")
        else:
            print("tests: Nothing to override")

    def override_lava_infos(self):
        try:
            self.job["actions"][3]["parameters"]["server"] = self.kwargs["server"]
            self.job["actions"][3]["parameters"]["stream"] = self.kwargs["stream"]
        except: pass

    def override_job_name(self, kci_data=None):
        # TODO: add some more information, like the user crafting the job, or
        # the kernel version, or anything else that can be useful
        if kci_data:
            self.job["job_name"] = "%s--%s--%s" % (
                    self.kwargs["job_name"],
                    self.board['device_type'],
                    kci_data["defconfig"],
                    )
        else:
           self.job["job_name"] = self.kwargs["job_name"] + "--" + self.board['device_type']
        print("job name: new name is: %s" % self.job["job_name"])

    def handle_file(self, local, remote):
        if self.kwargs["upload"]:
            self.send_file(local, remote)
            return remote
        else:
            return local

    def send_file(self, local, remote):
        scp = utils.get_sftp(self.kwargs["ssh_server"], 22, self.kwargs["ssh_username"])
        print("    Sending", local, "to", remote, "... ", end='')
        try:
            scp.put(local, remote)
        except IOError as e:
            utils.mkdir_p(scp, os.path.dirname(remote))
            scp.put(local, remote)
        print("Done")

    def send_to_lava(self):
        print("Sending to LAVA")
        job_str = json.dumps(self.job)
        ret = utils.get_connection(**self.kwargs).scheduler.submit_job(job_str)
        print(green("Job send (id: %s)" % ret))
        print("Potential working URL: ", "http://%s/scheduler/job/%s" % (self.kwargs['ssh_server'], ret))

    def save_job_to_file(self):
        try: os.makedirs(self.kwargs["output_dir"])
        except: pass
        file = os.path.join(self.kwargs["output_dir"], self.job["job_name"] + ".json")
        with open(file, 'w') as f:
            json.dump(self.job, f, indent=4)
        print(green("File saved to %s" % file))



