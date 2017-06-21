import os
import collections
import utils
import paramiko
import getpass
from boards import boards
from jinja2 import FileSystemLoader, Environment

from utils import red, green, ArtifactsFinder

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
                "notify": [],
                "notify_on_incomplete": [],
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
        try:
            self.job["lava_server"] = self.options["server"]
            self.job["lava_stream"] = self.options["stream"]
        except: pass

        # rootfs
        self.override('rootfs', self.options['rootfs'] or
                os.path.join(self.options["rootfs_path"], self.board["rootfs"]))

        # rootfs type
        if self.board["test_plan"] == "boot":
            self.job["rootfs_type"] = "ramdisk"
        elif self.board["test_plan"] == "boot-nfs":
            self.job["rootfs_type"] = "nfsrootfs"
        else:
            raise Exception(red("Invalid test_plan for board %s" %
                    self.board["name"]))

        self.job["device_type"] = self.board['device_type']

        for n in "notify", "notify_on_incomplete":
            if self.options['default_notify']:
                self.job[n] = self.board.get(n, [])
            else:
                self.job[n] = self.options[n]
        print("notify recipients: Overridden")

        # Define which test to run
        tests = []
        if self.options['tests']:
            tests = [next(iter([e for e in self.board['tests'] if e['name'] == t]), {'name': t}) for t in self.options['tests']]
        else:
            tests = self.board.get("tests", [])
        for test in tests:
            if self.options['kernel']:
                defconfigs = ['custom_kernel']
                # If we use a custom kernel
                if self.options["dtb"]:
                    dt_path = os.path.abspath(self.options["dtb"])
                else:
                    dt_path = os.path.abspath(os.path.join(self.options["dtb_folder"],
                        self.board['dt'] + '.dtb'))
                data = {
                        'kernel': self.options['kernel'],
                        'dtb': dt_path,
                        'modules': self.options['modules'],
                        }
            else:
                defconfigs = test.get('defconfigs', self.board['defconfigs'])
                # No custom kernel, go fetch artifacts on kernelci.org
                for defconfig in defconfigs:
                    data = (ArtifactsFinder("https://storage.kernelci.org/",
                            **self.options).crawl(self.board, defconfig) or
                            ArtifactsFinder("/home/ctt/builds/",
                            **self.options).crawl(self.board, defconfig))
            for defconfig in defconfigs:
                job_name = "%s--%s--%s--%s" % (
                        self.board['device_type'],
                        self.options["tree"],
                        defconfig,
                        test['name']
                        )

                self.override('kernel', data.get('kernel'))
                self.override('device_tree', data.get('dtb'))
                self.override('modules', data.get('modules'))

                self.get_template_from_file(os.path.join(TEMPLATE_FOLDER,
                    test.get('template', DEFAULT_TEMPLATE)))

                self.job["tests"] = test['name']
                print("tests: Overridden")
                self.job["job_name"] = self.options['job_name'] or job_name
                print("job name: %s" % self.job["job_name"])

                # Complete job creation
                if self.options["no_send"]:
                    self.save_job_to_file()
                else:
                    self.send_to_lava()

    def override(self, key, value=None):
        if value:
            print("%s: Overriding with file:" % key, value)
            remote_path = self.handle_file(value)
            self.job[key] = remote_path
            print("%s: Overridden" % key)
        else:
            print("%s: Nothing to override" % key)

# Files handling
    def handle_file(self, local):
        if not (local.startswith("http://") or local.startswith("file://") or
                local.startswith("https://")):
            remote = os.path.join(REMOTE_ROOT, os.path.basename(local))
            self.send_file(local, remote)
            remote = "file://" + remote
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

