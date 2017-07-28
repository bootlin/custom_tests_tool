import logging
import requests


class BaseError(Exception):
    pass


class InvalidParameterError(BaseError):
    pass


class RemoteEmptyError(BaseError):
    pass


class RemoteAccessError(BaseError):
    pass


class CTTCrawler(object):

    def __init__(self, cfg):
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
    __BASE_URL = 'https://storage.kernelci.org/'
    __RELEASE_URL = 'https://api.kernelci.org/build?limit=1&job=%s&field=kernel&sort=created_on&git_branch=%s'

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

        return json['result'][0]['kernel']
