#!/usr/bin/env python3
# -*- coding:utf-8 -*
# PYTHON_ARGCOMPLETE_OK
#
# Florent Jacquet <florent.jacquet@free-electrons.com>
#

from job_crafter import JobCrafter
from utils import get_config, red
from boards import boards


def main(**kwargs):
    # con = get_connection(**kwargs)
    # print(con.dashboard.bundles("/anonymous/skia/"))


    if kwargs['list']:
        print("Board list: ")
        for b in sorted(boards.keys()):
            print("\t - ", b)
        return
    if not kwargs['boards']:
        print("No board specified, you may want to add a `-b my-board` option?")
        print("See help for more informations")
        return
    if kwargs['boards'][0] == 'all': # Helper to gain some time
        kwargs['boards'] = boards.keys()
    for b in kwargs["boards"]:
        if b in boards.keys():
            try:
                h = JobCrafter(b, kwargs)
                h.make_jobs()
            except Exception as e:
                print(red(str(e)))
        else:
            print(red("No board named %s" % b))


if __name__ == "__main__":
    kwargs = get_config()
    main(**kwargs)

