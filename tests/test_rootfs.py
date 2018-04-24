import requests
import requests_mock
from nose.tools import assert_equal, assert_raises

from rootfs_chooser import RootfsChooser, RootfsAccessError, RootfsConfigError


class TestRootfsChooser(object):
    BASE_URL = 'http://lava.bootlin.com/downloads/rootfs'
    DEFAULT_ROOTFS = 'rootfs_armv7'

    @requests_mock.mock()
    def test_check_ramdisk(self, mock):
        url = "%s/%s.cpio.gz" % (self.BASE_URL, self.DEFAULT_ROOTFS)
        board = {
            'rootfs': self.DEFAULT_ROOTFS,
            'test_plan': 'boot'
        }

        mock.get(url, status_code=200)

        chooser = RootfsChooser()
        assert_equal(url, chooser.get_url(board))

    @requests_mock.mock()
    def test_check_nfs(self, mock):
        url = "%s/%s.tar.gz" % (self.BASE_URL, self.DEFAULT_ROOTFS)
        board = {
            'rootfs': self.DEFAULT_ROOTFS,
            'test_plan': 'boot-nfs'
        }

        mock.get(url, status_code=200)

        chooser = RootfsChooser()
        assert_equal(url, chooser.get_url(board))

    def test_check_raise_configerror_lack_testplan(self):
        board = {
            'rootfs': self.DEFAULT_ROOTFS,
        }

        chooser = RootfsChooser()
        assert_raises(RootfsConfigError, chooser.get_url, board)

    def test_check_raise_configerror_lack_rootfs(self):
        board = {
            'test_plan': 'boot-nfs'
        }

        chooser = RootfsChooser()
        assert_raises(RootfsConfigError, chooser.get_url, board)

    @requests_mock.mock()
    def test_check_404(self, mock):
        url = "%s/%s.cpio.gz" % (self.BASE_URL, self.DEFAULT_ROOTFS)
        board = {
            'rootfs': self.DEFAULT_ROOTFS,
            'test_plan': 'boot'
        }

        mock.get(url, status_code=404)

        chooser = RootfsChooser()
        assert_raises(RootfsAccessError, chooser.get_url, board)

