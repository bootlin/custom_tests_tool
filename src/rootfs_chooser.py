import logging
import requests

class RootfsAccessError(Exception):
    pass

class RootfsConfigError(Exception):
    pass

class RootfsChooser(object):
    """
    This class basically crafts and checks the URL for the rootfs given a board
    dictionary containing at least the `rootfs` key.
    """
    __ROOTFS_BASE = 'http://lava.free-electrons.com/downloads/rootfs'

    def get_url(self, board):
        if board['test_plan'] == "boot":
            rootfs = '%s/%s.cpio.gz' % (self.__ROOTFS_BASE, board['rootfs'])
        elif board['test_plan'] == "boot-nfs":
            rootfs = '%s/%s.tar.gz' % (self.__ROOTFS_BASE, board['rootfs'])
        else:
            raise RootfsConfigError("Unable to guess rootfs type to use.")
        try:
            r = requests.get(rootfs)
            r.raise_for_status()
        except (requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError):
            raise RootfsAccessError(
                'Rootfs not available: %s' % rootfs)

        return rootfs

