import logging
import requests

import time
from datetime import datetime, timedelta


class BaseError(Exception):
    pass


class InvalidParameterError(BaseError):
    pass


class RemoteEmptyError(BaseError):
    pass


class RemoteAccessError(BaseError):
    pass


class CTTCrawler(object):
    """
    This is the base Crawler class. A crawler is an object able to fetch
    artifacts from remote location, given a board, and the tree/branch/defconfig
    combination.
    """

    def __init__(self, cfg):
        """
        `cfg` is any object behaving like a dictionary, and containing at least
        the `api_token`
        TODO: move me to the KernelCICrawler, since it's used only there.
        """
        self._cfg = cfg

    def __get_image_name(self, board):
        if board['arch'] == 'arm':
            return 'zImage'
        elif board['arch'] == 'arm64':
            return 'Image'

        raise InvalidParameterError('Unknown architecture')

    def _get_latest_release(self, tree, branch):
        raise NotImplementedError('Missing release retrieval function')

    def _get_base_url(self, tree, branch, arch, defconfig):
        raise NotImplementedError('Missing base URL retrieval function')

    def crawl(self, board, tree, branch, defconfig):
        """
        This is the main crawling function.

        It returns a dictionary containing the `dtb`, `kernel`, and `modules`
        keys, with their corresponding URLs in values.

        It takes four mandatory arguments:
        - `board`: a dictionary containing at least the following board
          informations:
            "beaglebone-black": {
                "name": "Beaglebone black",
                "arch": "arm",
                "dt": "am335x-boneblack",
            },
        - `tree`: a string containing the name of the asked tree to look for.
        - `branch`: a string containing the name of the asked branch to look
          for.
        - `defconfig`: a string containing the name of the asked defconfig to
          look for.
        """
        logging.debug('%s: Looking for artifacts for board %s, defconfig %s' %
                      (self.__class__.__name__, board['name'], defconfig))

        url = self._get_base_url(tree, branch, board['arch'], defconfig)
        try:
            r = requests.get(url)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise RemoteEmptyError(
                'Defconfig build not available for this version')
        except requests.exceptions.ConnectionError:
            raise RemoteAccessError('Remote host not accessible')

        kernel = '%s/%s' % (url, self.__get_image_name(board))
        try:
            r = requests.get(kernel)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise RemoteEmptyError(
                'Kernel image not available for this version')
        except requests.exceptions.ConnectionError:
            raise RemoteAccessError('Remote host not accessible')

        modules = '%s/%s' % (url, 'modules.tar.xz')
        try:
            r = requests.get(modules)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise RemoteEmptyError(
                'modules tarball not available for this version')
        except requests.exceptions.ConnectionError:
            raise RemoteAccessError('Remote host not accessible')

        dtb = '%s/dtbs/%s.dtb' % (url, board['dt'])
        try:
            r = requests.get(dtb)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise RemoteEmptyError(
                'Device Tree not available for this version')
        except requests.exceptions.ConnectionError:
            raise RemoteAccessError('Remote host not accessible')

        return {
            'dtb': dtb,
            'kernel': kernel,
            'modules': modules,
        }


class FreeElectronsCrawler(CTTCrawler):
    """
    A Free Electrons specific crawler.
    """
    __BASE_URL = 'http://lava.free-electrons.com/downloads/builds/'

    def _get_base_url(self, tree, branch, arch, defconfig):
        return '%s/%s/%s/%s/%s/%s' % (self.__BASE_URL, tree, branch,
                                      self._get_latest_release(tree, branch),
                                      arch, defconfig)

    def _get_latest_release(self, tree, branch):
        url = '%s/%s/%s/latest' % (self.__BASE_URL, tree, branch)
        try:
            r = requests.get(url)
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise RemoteEmptyError('Release page not accessible')
        except requests.exceptions.ConnectionError:
            raise RemoteAccessError('Remote host not accessible')

        return r.text


class KernelCICrawler(CTTCrawler):
    """
    A KernelCI specific crawler.
    """
    __BASE_URL = 'https://storage.kernelci.org/'
    __RELEASE_URL = 'https://api.kernelci.org/build?'\
            'limit=1&job=%s&field=kernel&field=created_on&sort=created_on&git_branch=%s'

    def _get_base_url(self, tree, branch, arch, defconfig):
        return '%s/%s/%s/%s/%s/%s' % (self.__BASE_URL, tree, branch,
                                      self._get_latest_release(tree, branch),
                                      arch, defconfig)

    def _get_latest_release(self, tree, branch):
        try:
            r = requests.get(self.__RELEASE_URL % (tree, branch),
                             headers={'Authorization': self._cfg['api_token']})
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise RemoteEmptyError('Release page not accessible')
        except requests.exceptions.ConnectionError:
            raise RemoteAccessError('Remote host not accessible')

        json = r.json()
        if ('result' not in json or
            len(json['result']) == 0 or
                'kernel' not in json['result'][0]):
            raise RemoteEmptyError('No release found')

        current_time = datetime.utcfromtimestamp(time.time())
        build_time = datetime.utcfromtimestamp(json['result'][0]['created_on']['$date']/1000)
        if current_time - build_time > timedelta(hours=24):
            raise RemoteEmptyError('Release found is too old')

        return json['result'][0]['kernel']

