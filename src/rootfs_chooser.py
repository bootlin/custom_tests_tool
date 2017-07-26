import logging
import requests

class RootfsAccessError(Exception):
    pass

class RootfsChooser(object):
    __ROOTFS_BASE = 'http://lava.free-electrons.com/downloads/rootfs'

    def get_url(self, board):
        rootfs = '%s/%s' % (self.__ROOTFS_BASE, board['rootfs'])
        r = requests.get(rootfs)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise RootfsAccessError(
                'Rootfs not available: %s' % rootfs)
        return rootfs

