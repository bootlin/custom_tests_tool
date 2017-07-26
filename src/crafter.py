import os
import logging
import getpass

from jinja2 import FileSystemLoader, Environment

from src import ssh_utils

from src.crawlers import FreeElectronsCrawler, KernelCICrawler
from src.crawlers import RemoteAccessError
from src.writers import FileWriter, LavaWriter


class JobCrafter(object):
    """
    This class handle the jobs.
    """
    __REMOTE_ROOT = os.path.join("/tmp/ctt/", getpass.getuser())
    __TEMPLATE_FOLDER = "jobs_templates"
    __DEFAULT_TEMPLATE = "generic_simple_job.jinja"

    def __init__(self, boards, cfg):
        """
        `boards`: dict
            This is the dictionary structure found in the boards.json file.
        `cfg`: dict
            A configuration dict containing at least the following keys:
                - no_send
            If you need to upload custom files for the tests, the following keys
            must be provided:
                - ssh_server
                - ssh_username
            The following keys are also supported, through not mandatory:
                - notify
                - lava_server (for LAVA v1 templates)
                - lava_stream (for LAVA v1 templates)

        TODO: make some check at init time
        """
        self._boards = boards
        self._cfg = cfg
        self.job = {
                "kernel": "",
                "device_tree": "",
                "rootfs": "",
                "rootfs_type": "",
                "modules": "",
                "test": "",
                "lava_server": "",
                "lava_stream": "",
                "device_type": "",
                "job_name": "",
                "notify": [],
                }
        self.jinja_env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)))
        if self._cfg['no_send']:
            self.writer = FileWriter(self._cfg)
        else:
            self.writer = LavaWriter(self._cfg)

# Template handling
    def get_template_from_file(self, file):
        logging.debug("template: using %s" % file)
        self.job_template = self.jinja_env.get_template(file)

# Job handling
    def make_jobs(self, board_name, artifacts, test, job_name="default_job_name"):
        # Get easier access to board config
        board_config = self._boards[board_name]

        if 'server' in self._cfg:
            self.job["lava_server"] = self._cfg['server']

        if 'stream' in self._cfg:
            self.job["lava_stream"] = self._cfg['stream']

        if 'notify' in self._cfg:
            self.job["notify"] = self._cfg['notify']

        logging.info("    Notifications recipients: %s" % ", ".join(self.job['notify']))

        # rootfs type
        if board_config["test_plan"] == "boot":
            self.job["rootfs_type"] = "ramdisk"
        elif board_config["test_plan"] == "boot-nfs":
            self.job["rootfs_type"] = "nfsrootfs"
        else:
            raise Exception(red("Invalid test_plan for board %s" %
                    board_config["name"]))

        self.job["device_type"] = board_config['device_type']

        self.override('rootfs', artifacts.get('rootfs'))
        logging.info("    Root filesystem path: %s" % self.job['rootfs'])

        self.override('kernel', artifacts.get('kernel'))
        logging.info("    Kernel path: %s" % self.job['kernel'])

        self.override('device_tree', artifacts.get('dtb'))
        logging.info("    Device tree path: %s" % self.job['device_tree'])

        # modules are optional if we have our own kernel
        if 'modules' in artifacts:
            self.override('modules', artifacts.get('modules'))
            logging.info('    Modules archive path: %s' % self.job['modules'])

        self.get_template_from_file(os.path.join(JobCrafter.__TEMPLATE_FOLDER,
            test.get('template', JobCrafter.__DEFAULT_TEMPLATE)))

        self.job["test"] = test['name']

        self.job["job_name"] = "%s--%s" % (
                job_name,
                test['name']
                )
        logging.debug("    Job name: %s" % self.job['job_name'])

        out = self.writer.write(board_config, job_name,
                                self.job_template.render(self.job))
        for output in out:
            logging.info('  ==> Job saved to: %s' % output)

    def override(self, key, value):
        logging.debug('Overriding key "%s" with value "%s"' % (key, value))
        remote_path = self.handle_file(value)
        self.job[key] = remote_path

# Files handling
    def handle_file(self, local):
        if not (local.startswith("http://") or local.startswith("file://") or
                local.startswith("https://")):
            remote = os.path.join(JobCrafter.__REMOTE_ROOT, os.path.basename(local))
            self.send_file(local, remote)
            remote = "file://" + remote
            return remote
        else:
            return local

    def send_file(self, local, remote):
        scp = ssh_utils.get_sftp(self._cfg["ssh_server"], 22, self._cfg["ssh_username"])
        logging.info('      Sending %s to %s' % (local, remote))
        try:
            scp.put(local, remote)
        except IOError as e:
            ssh_utils.mkdir_p(scp, os.path.dirname(remote))
            scp.put(local, remote)
        logging.info('      File %s sent' % local)

