#!/usr/bin/env python3
# -*- coding:utf-8 -*
# PYTHON_ARGCOMPLETE_OK
#
# Florent Jacquet <florent.jacquet@free-electrons.com>
#

import os
import logging
import sys

from job_crafter import JobCrafter
from utils import red
from boards import boards
from src.CTTConfig import CTTConfig, OptionError, SectionError

def main(**kwargs):
    try:
        config = open(os.path.expanduser('~/.cttrc'))
    except OSError as e:
        logging.warning("Couldn't open the configuration file: %s" % e.strerror)
        config = None

    try:
        cfg = CTTConfig(file=config)
    except OptionError as e:
        logging.error("Invalid configuration: %s" % e.args)
        sys.exit(2)
    except SectionError as e:
        logging.error("Invalid configuration file: %s" % e.args)
        sys.exit(1)

    if cfg['list']:
        print("Board list: ")
        for b in sorted(boards.keys()):
            print("\t - ", b)

        sys.exit()

    for b in cfg['boards']:
        try:
            h = JobCrafter(b, cfg)
            h.make_jobs()
        except Exception as e:
            print(red(str(e)))

if __name__ == "__main__":
    main()

