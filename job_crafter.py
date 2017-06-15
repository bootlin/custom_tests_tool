import os
import collections
import utils
import paramiko
import getpass
from boards import boards
from jinja2 import FileSystemLoader, Environment

from utils import red, green, KCIFetcher

REMOTE_ROOT = os.path.join("/tmp/ctt/", getpass.getuser())
TEMPLATE_FOLDER = "jobs_templates"
DEFAULT_TEMPLATE = "generic_simple_job.jinja"

class JobCrafter:
    """
    This class handle the jobs.
    """
    def __init__(self, board, options):
        self.board = boards[board]
        self.options = options
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
        self.jinja_env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))

    def get_device_status(self):
        try:
            return self._device_status
        except:
            self._device_status = utils.get_connection(**self.options).scheduler.get_device_status(
                    self.board["device_type"] + "_01"
                    )
            return self._device_status

# Template handling
    def get_template_from_file(self, file):
        print("template: using %s" % file)
        self.job_template = self.jinja_env.get_template(file)

    def save_job_to_file(self, ext="yaml"):
        try: os.makedirs(self.options["output_dir"])
        except: pass
        file = os.path.join(self.options["output_dir"], self.job["job_name"] + "." + ext)
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
        ret = utils.get_connection(**self.options).scheduler.submit_job(job_str)
        try:
            for r in ret:
                print(green("Job send (id: %s)" % r))
                print("Potential working URL: ", "http://%s/scheduler/job/%s" %
                        (self.options['ssh_server'], r))
        except:
            print(green("Job send (id: %s)" % ret))
            print("Potential working URL: ", "http://%s/scheduler/job/%s" %
                    (self.options['ssh_server'], ret))

# Job handling
    def make_jobs(self):
        # Override basic values that are constant over each test
        self.override_rootfs()
        self.override_lava_infos()
        self.override_device_type()
        self.override_recipients()

        # Define which test to run
        tests = []
        if self.options['tests']:
            tests = [next(iter([e for e in self.board['tests'] if e['name'] == t]), {'name': t}) for t in self.options['tests']]
        else:
            tests = self.board.get("tests", [])
        for test in tests:
            if self.options['kernel']:
                # If we use a custom kernel
                job_name = "%s--custom_kernel--%s" % (self.board['device_type'],
                        test['name'])

                self.override_kernel()
                self.override_dtb()
                self.override_modules()

                self.get_template_from_file(os.path.join(TEMPLATE_FOLDER,
                    test.get('template', DEFAULT_TEMPLATE)))

                self.override_tests(test['name'])
                self.override_job_name(job_name)
                if self.options["no_send"]:
                    self.save_job_to_file()
                else:
                    self.send_to_lava()
            else:
                # No custom kernel, go fetch artifacts on kernelci.org
                for defconfig in test.get('defconfigs', self.board['defconfigs']):
                    kci_data = KCIFetcher(**self.options).crawl(self.board, defconfig)
                    job_name = "%s--%s--%s--%s" % (
                            self.board['device_type'],
                            self.options["kernelci_tree"],
                            defconfig,
                            test['name']
                            )

                    self.override_kernel(kci_data.get('kernel'))
                    self.override_dtb(kci_data.get('dtb'))
                    self.override_modules(kci_data.get('modules'))

                    self.get_template_from_file(os.path.join(TEMPLATE_FOLDER,
                        test.get('template', DEFAULT_TEMPLATE)))

                    self.override_tests(test['name'])
                    self.override_job_name(job_name)
                    if self.options["no_send"]:
                        self.save_job_to_file()
                    else:
                        self.send_to_lava()

    def override_recipients(self):
        print("notify recipients: Overriding")
        for n in "notify", "notify_on_incomplete":
            if self.options['default_notify']:
                self.job[n] = self.board.get(n, [])
            else:
                self.job[n] = self.options[n]
        print("notify recipients: Overridden")

    def override_device_type(self):
        print("device-type: Overriding")
        self.job["device_type"] = self.board['device_type']
        print("device-type: Overridden")

    def override_rootfs(self):
        if self.options["rootfs"]:
            rootfs = self.options['rootfs']
            print("rootfs: Overriding with local file")
            local_path = os.path.abspath(rootfs)
            remote_path = os.path.join(REMOTE_ROOT, os.path.basename(local_path))
            remote_path = self.handle_file(local_path, remote_path)
            self.job["rootfs"] = "file://" + remote_path
        else:
            print("rootfs: Using default file")
            rootfs = os.path.join(self.options["rootfs_path"], self.board["rootfs"])
            self.job["rootfs"] = "file://" + rootfs
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
        if self.options["dtb"] or self.options["dtb_folder"]:
            if self.options["dtb"]:
                local_path = os.path.abspath(self.options["dtb"])
            else:
                local_path = os.path.abspath(os.path.join(self.options["dtb_folder"],
                    self.board['dt'] + '.dtb'))
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
        if self.options["kernel"]:
            local_path = os.path.abspath(self.options["kernel"])
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
        if self.options["modules"]:
            local_path = os.path.abspath(self.options["modules"])
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

    def override_tests(self, test):
        print("tests: Overriding")
        test = test
        self.job["tests"] = test
        print("tests: Overridden")

    def override_lava_infos(self):
        try:
            self.job["lava_server"] = self.options["server"]
            self.job["lava_stream"] = self.options["stream"]
        except: pass

    def override_job_name(self, name="job_name"):
        if self.options.get('job_name'):
            name += "--" + self.options.get('job_name')
        self.job["job_name"] = name
        print("job name: %s" % self.job["job_name"])

# Files handling
    def handle_file(self, local, remote):
        if not local.startswith("http"):
            self.send_file(local, remote)
            return remote
        else:
            return local

    def send_file(self, local, remote):
        scp = utils.get_sftp(self.options["ssh_server"], 22, self.options["ssh_username"])
        print("    Sending", local, "to", remote, "... ", end='')
        try:
            scp.put(local, remote)
        except IOError as e:
            utils.mkdir_p(scp, os.path.dirname(remote))
            scp.put(local, remote)
        print("Done")

