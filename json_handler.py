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

    def _set_device_type(self, value):
        self.job["device_type"] = self.board["device_type"]

    def _set_device_tree(self, value):
        self.job["actions"][0]["parameters"]["dtb"] = value

    def _set_rootfs(self, value, nfs=False):
        if nfs:
            self.job["actions"][0]["parameters"]["nfsrootfs"] = value
        else:
            self.job["actions"][0]["parameters"]["ramdisk"] = value

    def _set_kernel(self, value):
        self.job["actions"][0]["parameters"]["kernel"] = value

    def _set_modules(self, value):
        self.job["actions"][0]["parameters"]["overlays"] = [value]

    def _set_tests(self, value):
        self.job["actions"][2]["parameters"]["commands"][0] = value

    def _set_lava_server(self, value):
        self.job["actions"][3]["parameters"]["server"] = value

    def _set_lava_stream(self, value):
        self.job["actions"][3]["parameters"]["stream"] = value

    def _set_job(self, value):
        self.job["job_name"] = value

    def make_jobs(self, kci_data={}):
        job_name_prefix = "%s--%s--" % (self.kwargs["kernelci_tree"],
                self.board['device_type'])
        if kci_data:
            job_name_prefix += kci_data["defconfig"] + "--"
        self.override_kernel(kci_data.get('kernel'))
        self.override_dtb(kci_data.get('dtb'))
        self.override_modules(kci_data.get('modules'))
        self.override_rootfs()
        self.override_lava_infos()
        self.override_device_type()
        for test in self.board["tests"]:
            job_name = job_name_prefix + test
            self.override_job_name(job_name)
            self.override_tests(test)
            if self.kwargs["send"]:
                self.send_to_lava()
            else:
                self.save_job_to_file()

    def get_job_from_file(self, file):
        with open(file) as f:
            self.job = json.load(f, object_pairs_hook=collections.OrderedDict)

    def override_device_type(self):
        print("device-type: Overriding")
        self._set_device_type(self.board['device_type'])
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
            self._set_rootfs("file://" + remote_path)
            print("rootfs: ramdisk overridden")
        elif self.board["test_plan"] == "boot-nfs":
            self._set_rootfs("file://" + remote_path, True)
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
            self._set_device_tree("file://" + remote_path)
            print("DTB: Overridden")
        elif dtb_url:
            print("DTB: Overriding with Kernel CI URL:", dtb_url)
            self._set_device_tree(dtb_url)
            print("DTB: Overridden")
        else:
            print("DTB: Nothing to override")

    def override_kernel(self, kernel_url=None):
        if self.kwargs["kernel"]:
            local_path = os.path.abspath(self.kwargs["kernel"])
            print("kernel: Overriding with local file:", local_path)
            remote_path = os.path.join(REMOTE_ROOT, os.path.basename(local_path))
            remote_path = self.handle_file(local_path, remote_path)
            self._set_kernel("file://" + remote_path)
            print("kernel: Overridden")
        elif kernel_url:
            print("kernel: Overriding with Kernel CI URL:", kernel_url)
            self._set_kernel(kernel_url)
            print("kernel: Overridden")
        else:
            print("kernel: Nothing to override")

    def override_modules(self, modules_url=None):
        if self.kwargs["modules"]:
            local_path = os.path.abspath(self.kwargs["modules"])
            print("modules: Overriding with local file:", local_path)
            remote_path = os.path.join(REMOTE_ROOT, os.path.basename(local_path))
            remote_path = self.handle_file(local_path, remote_path)
            self._set_modules("file://" + remote_path)
            print("modules: Overridden")
        elif modules_url:
            print("modules: Overriding with Kernel CI URL:", modules_url)
            self._set_modules(modules_url)
            print("modules: Overridden")
        else:
            print("modules: Nothing to override")

    def override_tests(self, test):
        print("tests: Overriding")
        self._set_tests("/tests/tests/" + test + " " + self.board['device_type'])
        print("tests Overridden")

    def override_lava_infos(self):
        try:
            self._set_lava_server(self.kwargs["server"])
            self._set_lava_stream(self.kwargs["stream"])
        except: pass

    def override_job_name(self, name="job_name"):
        if self.kwargs.get('job_name'):
            name += "--" + self.kwargs.get('job_name')
        self._set_job(name)
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



