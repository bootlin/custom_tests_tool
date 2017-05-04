import os
import collections
import utils
import paramiko
import getpass
from boards import boards
from jinja2 import FileSystemLoader, Environment

from utils import red, green

REMOTE_ROOT = os.path.join("/tmp/ctt/", getpass.getuser())

class JobCrafter:
    """
    This class handle the jobs.
    """
    def __init__(self, board, **kwargs):
        self.board = boards[board]
        self.kwargs = kwargs
        self.job = {
                "kernel": "",
                "device_tree": "",
                "rootfs": "",
                "rootfs_type": "",
                "modules": "",
                "tests": "",
                "lava_server": "",
                "lava_stream": "",
                "device_type": "",
                "job_name": "",
                "notify": []
                }
        self.jinja_env = Environment(loader=FileSystemLoader(os.getcwd()))

    def get_device_status(self):
        try:
            return self._device_status
        except:
            self._device_status = utils.get_connection(**self.kwargs).scheduler.get_device_status(
                    self.board["device_type"] + "_01"
                    )
            return self._device_status

    @property
    def is_pipeline(self):
        return self.get_device_status()["is_pipeline"]

# Template handling
    def get_job_from_file(self, file):
        self.job_template = self.jinja_env.get_template(file)

    def save_job_to_file(self, ext):
        try: os.makedirs(self.kwargs["output_dir"])
        except: pass
        file = os.path.join(self.kwargs["output_dir"], self.job["job_name"] + "." + ext)
        with open(file, 'w') as f:
            f.write(self.job_template.render(self.job))
        print(green("File saved to %s" % file))

    def send_to_lava(self):
        try:
            dev = self.get_device_status()
            if dev["status"] == "offline":
                print(red("Device seems offline, not sending the job"))
                return
        except Exception as e:
            print(red(repr(e)))
            print(red("Not sending the job"))
            return
        print("Sending to LAVA")
        job_str = self.job_template.render(self.job)
        ret = utils.get_connection(**self.kwargs).scheduler.submit_job(job_str)
        try:
            for r in ret:
                print(green("Job send (id: %s)" % r))
                print("Potential working URL: ", "http://%s/scheduler/job/%s" % (self.kwargs['ssh_server'], r))
        except:
            print(green("Job send (id: %s)" % ret))
            print("Potential working URL: ", "http://%s/scheduler/job/%s" % (self.kwargs['ssh_server'], ret))

# Job handling
    def make_jobs(self, kci_data={}):
        # Set job name's prefix
        job_name_prefix = "%s--%s--" % (self.kwargs["kernelci_tree"],
                self.board['device_type'])
        if kci_data:
            job_name_prefix += kci_data["defconfig"] + "--"

        # Override basic values that are constant over each test
        self.override_kernel(kci_data.get('kernel'))
        self.override_dtb(kci_data.get('dtb'))
        self.override_modules(kci_data.get('modules'))
        self.override_rootfs()
        self.override_lava_infos()
        self.override_device_type()
        self.override_recipients()

        # Define which test to run
        use_default = True
        tests = tests_multinode = []
        if self.kwargs['tests']:
            tests = self.kwargs['tests']
            use_default = False
        if self.kwargs['tests_multinode']:
            tests_multinode = self.kwargs['tests_multinode']
            use_default = False
        if use_default:
            tests = self.board.get("tests", [])
            tests_multinode = self.board.get("tests_multinode", [])

        # Define which template to use
        job_extension = "yaml"
        template_simple = "jobs_templates/simple_test_job_template_v2.jinja"
        template_multi = "jobs_templates/multinode_job_template_v2.jinja"

        # Simple tests
        self.get_job_from_file(template_simple)
        self.is_multinode = False
        for test in tests:
            job_name = job_name_prefix + test
            self.override_job_name(job_name)
            self.override_tests(test, (not self.is_pipeline))
            if self.kwargs["no_send"]:
                self.save_job_to_file(job_extension)
            else:
                self.send_to_lava()

        # MultiNode tests
        self.get_job_from_file(template_multi)
        self.is_multinode = True
        for test in tests_multinode:
            job_name = job_name_prefix + test
            self.override_job_name(job_name)
            self.override_tests(test)
            if self.kwargs["no_send"]:
                self.save_job_to_file(job_extension)
            else:
                self.send_to_lava()

    def override_recipients(self):
        print("notify recipients: Overriding")
        for n in "notify", "notify_on_incomplete":
            if self.kwargs['default_notify']:
                self.job[n] = self.board.get(n, [])
            else:
                self.job[n] = self.kwargs[n]
        print("notify recipients: Overridden")

    def override_device_type(self):
        print("device-type: Overriding")
        self.job["device_type"] = self.board['device_type']
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
        self.job["rootfs"] = "file://" + remote_path
        if self.board["test_plan"] == "boot":
            self.job["rootfs_type"] = "ramdisk"
            print("rootfs: ramdisk overridden")
        elif self.board["test_plan"] == "boot-nfs":
            self.job["rootfs_type"] = "nfsrootfs"
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
            self.job["device_tree"] = "file://" + remote_path
            print("DTB: Overridden")
        elif dtb_url:
            print("DTB: Overriding with Kernel CI URL:", dtb_url)
            self.job["device_tree"] = dtb_url
            print("DTB: Overridden")
        else:
            print("DTB: Nothing to override")

    def override_kernel(self, kernel_url=None):
        if self.kwargs["kernel"]:
            local_path = os.path.abspath(self.kwargs["kernel"])
            print("kernel: Overriding with local file:", local_path)
            remote_path = os.path.join(REMOTE_ROOT, os.path.basename(local_path))
            remote_path = self.handle_file(local_path, remote_path)
            self.job["kernel"] = "file://" + remote_path
            print("kernel: Overridden")
        elif kernel_url:
            print("kernel: Overriding with Kernel CI URL:", kernel_url)
            self.job["kernel"] = kernel_url
            print("kernel: Overridden")
        else:
            print("kernel: Nothing to override")

    def override_modules(self, modules_url=None):
        if self.kwargs["modules"]:
            local_path = os.path.abspath(self.kwargs["modules"])
            print("modules: Overriding with local file:", local_path)
            remote_path = os.path.join(REMOTE_ROOT, os.path.basename(local_path))
            remote_path = self.handle_file(local_path, remote_path)
            self.job["modules"] = "file://" + remote_path
            print("modules: Overridden")
        elif modules_url:
            print("modules: Overriding with Kernel CI URL:", modules_url)
            self.job["modules"] = modules_url
            print("modules: Overridden")
        else:
            print("modules: Nothing to override")

    def override_tests(self, test, append_device_type=False):
        print("tests: Overriding")
        if self.is_pipeline or self.is_multinode:
            ext = ""
            folder = ""
        else:
            ext = ""
            folder = ""
        test = folder + test + ext
        if append_device_type:
            self.job["tests"] = test + " " + self.board['device_type']
        else:
            self.job["tests"] = test
        print("tests Overridden")

    def override_lava_infos(self):
        try:
            self.job["lava_server"] = self.kwargs["server"]
            self.job["lava_stream"] = self.kwargs["stream"]
        except: pass

    def override_job_name(self, name="job_name"):
        if self.kwargs.get('job_name'):
            name += "--" + self.kwargs.get('job_name')
        self.job["job_name"] = name
        print("job name: new name is: %s" % self.job["job_name"])

# Files handling
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

