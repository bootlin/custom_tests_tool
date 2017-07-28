#!/usr/bin/env python3
# -*- coding:utf-8 -*
#

import json
import logging
import os
import sys

from src.CTTConfig import CICmdline
from src.CTTFormatter import CTTFormatter
from src.crawlers import FreeElectronsCrawler, KernelCICrawler
from src.crawlers import RemoteAccessError, RemoteEmptyError
from src.rootfs_chooser import RootfsChooser, RootfsAccessError
from src.launcher import BaseLauncher

class CILauncher(BaseLauncher):
    _CMDLINE_CLASS = CICmdline

    def _set_config(self):
        super(CILauncher, self)._set_config()
        self._crawlers = [
                FreeElectronsCrawler(self._cfg),
                KernelCICrawler(self._cfg)
            ]

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
                    for crawler in self._crawlers:
                        try:
                            artifacts = crawler.crawl(self._boards_config[board],
                                    config['tree'], config['branch'],
                                    config['defconfig'])
                        except RemoteEmptyError as e:
                            logging.debug("  No artifacts returned by crawler %s: %s" %
                                    (crawler.__class__.__name__, e))
                        except RemoteAccessError as e:
                            logging.debug("  Remote unreachable for crawler %s: %s" %
                                    (crawler.__class__.__name__, e))
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

