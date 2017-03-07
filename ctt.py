#!/usr/bin/env python3
# -*- coding:utf-8 -*
# PYTHON_ARGCOMPLETE_OK
#
# Skia < skia AT libskia DOT so >
#
# Beerware licensed software - 2017
#

from json_handler import JSONHandler
from yaml_handler import YAMLHandler
from utils import KCIFetcher, get_connection, get_config
from boards import boards


def main(**kwargs):
    print("main kwargs: ")
    print(kwargs)
    for b in kwargs["boards"]:
        if b in boards.keys():
            h = JSONHandler(b, **kwargs)
            if kwargs["no_kci"]:
                h.apply_overrides()
            else:
                for data in KCIFetcher(**kwargs).crawl(boards[b]):
                    h.apply_overrides(data)
            if kwargs["send"]:
                h.send_to_lava()
            else:
                h.save_job_to_file()


if __name__ == "__main__":
    kwargs = get_config()


    main(**kwargs)

