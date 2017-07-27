#!/usr/bin/env python3
# -*- coding:utf-8 -*
#

import json
import logging
import os
import sys

from src.CTTConfig import CTTConfig, OptionError, ConfigFileError, CICmdline
from src.CTTFormatter import CTTFormatter
from src.crawlers import FreeElectronsCrawler, KernelCICrawler
from src.crawlers import RemoteAccessError, RemoteEmptyError
from src.rootfs_chooser import RootfsChooser, RootfsAccessError
from src.crafter import JobCrafter

class CILauncher:
    def __init__(self):
        self._set_logging()
        self._set_config()

    def _set_logging(self):
        self._logger = logging.getLogger()
        self._logger.setLevel(logging.DEBUG)

        requests_logger = logging.getLogger("requests")
        requests_logger.setLevel(logging.WARN)

        handler = logging.StreamHandler()

        formatter = CTTFormatter()
        handler.setFormatter(formatter)

        self._logger.addHandler(handler)

    def _set_config(self):
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

        try:
            with open(os.path.expanduser('~/.cttrc')) as f:
                self._cfg = CTTConfig(f, CICmdline, self._boards_config)
        except OptionError as e:
            logging.critical(e)
            sys.exit(1)
        except ConfigFileError as e:
            logging.critical(e)
            sys.exit(2)

        if self._cfg['debug']:
            self._logger.setLevel(logging.DEBUG)
        else:
            self._logger.setLevel(logging.INFO)

        self.crawlers = [
                FreeElectronsCrawler(self._cfg),
                KernelCICrawler(self._cfg)
            ]

        # TODO: handle exceptions
        self.crafter = JobCrafter(self._boards_config, self._cfg)

    def launch(self):
        for board in self._tests_config:

            logging.info(board)
            if not self._tests_config[board]['tests']:
                logging.info("  No test set")

            try:
                rootfs = RootfsChooser().get_url(self._boards_config[board])
            except RootfsAccessError as e:
                logging.warning(e)
                continue
            for test in self._tests_config[board]['tests']:
                logging.debug("  Building job(s) for %s" % test['name'])

                # Check if configs has been overridden by test
                if 'configs' in test:
                    configs = test['configs']
                    logging.debug("  Configs overridden: %s" % configs)
                else:
                    configs = self._tests_config[board]['configs']
                    logging.debug("  Using default configs: %s" % configs)

                for config in configs:
                    logging.debug("  Fetching artifacts for %s" % config)
                    artifacts = None
                    for crawler in self.crawlers:
                        try:
                            artifacts = crawler.crawl(self._boards_config[board],
                                    config['tree'], config['branch'],
                                    config['defconfig'])
                        except (RemoteEmptyError, RemoteAccessError):
                            logging.debug("  No artifacts returned by crawler %s" %
                                    crawler.__class__.__name__)
                    if artifacts:
                        artifacts['rootfs'] = rootfs
                        logging.info("  Making %s job on %s -> %s -> %s" %
                                (test['name'], config['tree'], config['branch'],
                                    config['defconfig']))
                        job_name = "%s--%s--%s--%s--%s" % (
                                board, config['tree'], config['branch'],
                                config['defconfig'], test['name']
                                )
                        self.crafter.make_jobs(board, artifacts, test['name'], job_name)

if __name__ == "__main__":
    CILauncher().launch()

