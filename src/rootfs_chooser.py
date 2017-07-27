import logging
import requests

class RootfsAccessError(Exception):
    pass

class RootfsChooser(object):
    __ROOTFS_BASE = 'http://lava.free-electrons.com/downloads/rootfs'

    def get_url(self, board):
        rootfs = '%s/%s' % (self.__ROOTFS_BASE, board['rootfs'])
        try:
            r = requests.get(rootfs)
            r.raise_for_status()
        except (requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError):
            raise RootfsAccessError(
                'Rootfs not available: %s' % rootfs)

        return rootfs

