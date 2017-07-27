#!/usr/bin/env python3
# -*- coding:utf-8 -*
#

import json
import logging
import os
import sys
import getpass

from pprint import pprint

from src import ssh_utils
from src.CTTConfig import CTTConfig, OptionError, SectionError
from src.CTTFormatter import CTTFormatter
from src.rootfs_chooser import RootfsChooser, RootfsAccessError
from src.crafter import JobCrafter

class CTTLauncher:
    __REMOTE_ROOT = os.path.join("/tmp/ctt/", getpass.getuser())

    def __init__(self):
        self.__set_config()
        self.__set_logging()

    def __set_logging(self):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        paramiko_logger = logging.getLogger("paramiko")
        paramiko_logger.setLevel(logging.WARN)

        requests_logger = logging.getLogger("requests")
        requests_logger.setLevel(logging.WARN)

        handler = logging.StreamHandler()
        if self._cfg['debug']:
            handler.setLevel(logging.DEBUG)
        else:
            handler.setLevel(logging.INFO)

        formatter = CTTFormatter()
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    def __set_config(self):
        ctt_root_location = os.path.abspath(os.path.dirname(
            os.path.realpath(__file__)))
        with open(os.path.join(ctt_root_location, "ci_tests.json")) as f:
            self._tests_config = json.load(f)

        with open(os.path.join(ctt_root_location, "boards.json")) as f:
            self._boards_config = json.load(f)
            # Add the name field
            for k,v in self._boards_config.items():
                v['name'] = k
                v['device_type'] = k

        with open(os.path.expanduser('~/.cttrc')) as f:
            self._cfg = CTTConfig(f, self._boards_config)

        self.crafter = JobCrafter(self._boards_config, self._cfg)

    # Files handling
    def __handle_file(self, local):
        if not (local.startswith("http://") or local.startswith("file://") or
                local.startswith("https://")):
            remote = os.path.join(CTTLauncher.__REMOTE_ROOT, os.path.basename(local))
            self.__send_file(local, remote)
            remote = "file://" + remote
            return remote
        else:
            return local

    def __send_file(self, local, remote):
        scp = ssh_utils.get_sftp(self._cfg["ssh_server"], 22, self._cfg["ssh_username"])
        logging.info('  Sending %s to %s' % (local, remote))
        try:
            scp.put(local, remote)
        except IOError as e:
            ssh_utils.mkdir_p(scp, os.path.dirname(remote))
            scp.put(local, remote)
        logging.info('  File %s sent' % local)


    # Launcher
    def launch(self):
        for board in self._cfg['boards']:
            logging.info(board)

            # Handle rootfs, since it's not mandatory
            if 'rootfs' not in self._cfg:
                try:
                    rootfs = RootfsChooser().get_url(self._boards_config[board])
                except RootfsAccessError as e:
                    logging.warning(e)
                    continue
            else:
                rootfs = self._cfg['rootfs']

            if 'tests' not in self._cfg: # TODO Remove me when CTTCmdline is done
                logging.critical("  No test asked, aborting")
                sys.exit(1)

            for test in self._cfg['tests']:
                logging.debug("  Building job(s) for %s" % test)

                artifacts = {}

                if 'kernel' in self._cfg:
                    artifacts['kernel'] = self.__handle_file(self._cfg['kernel'])

                if 'dtb' in self._cfg:
                    artifacts['dtb'] = self.__handle_file(self._cfg['dtb'])
                elif 'dtb_folder' in self._cfg:
                    artifacts['dtb'] = self.__handle_file("%s/%s.dtb" % (self._cfg['dtb_folder'],
                            self._boards_config[board]['dt']))

                if 'modules' in self._cfg:
                    artifacts['modules'] = self.__handle_file(self._cfg['modules'])

                artifacts['rootfs'] = self.__handle_file(rootfs)

                logging.info("  Making %s job" % test)
                job_name = "%s--custom_kernel--%s" % (board, test)
                self.crafter.make_jobs(board, artifacts, test, job_name)

if __name__ == "__main__":
    CTTLauncher().launch()

