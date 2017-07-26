from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from configparser import ConfigParser

class BaseError(Exception):
    pass


class OptionError(BaseError):
    pass


class SectionError(BaseError):
    pass

DEFAULT_SECTION = 'ctt'

mandatory_keys = [
    'api_token',
    'server',
    'token',
    'username',
    'web_ui_address',
]

class CIConfig:

    def __init__(self, file=None, validate=True):
        self.__config = ConfigParser()

        if file is not None:
            self.__config.read_file(file)

            if (validate):
                self.__validate_config_file()

        self.__parse_cmdline()

        if (validate):
            self.__validate_cmdline()

    def __parse_cmdline(self):
        parser = ArgumentParser(description='Send custom job to a LAVA server')

        parser.add_argument('--no-send', action='store_true',
                            help='Don\'t send the job')
        parser.add_argument('--output-dir', default='jobs',
                         help='Path where the jobs will be stored if not sent')
        parser.add_argument('-b', '--boards', nargs='+',
                            help='Board to run the test on')
        parser.add_argument('-l', '--list', action='store_true',
                            help='List all the available boards')
        parser.add_argument('-d', '--debug', action='store_true',
                            help='Debug mode')

        self.__cmdline = vars(parser.parse_args())

    def __validate_config_file(self):
        if not self.__config.has_section(DEFAULT_SECTION):
            raise SectionError('Missing %s section' % DEFAULT_SECTION)

    def __validate_cmdline(self):
        # We can always just list the boards
        if self.__cmdline['list']:
            return

        # Validate that we have all the basic options...
        for option in mandatory_keys:
            if not self.__contains__(option):
                raise OptionError('Missing %s option' % option)

    def __getitem__(self, key):
        if key in self.__cmdline:
            val = self.__cmdline[key]
            if val is not None:
                return self.__cmdline[key]

        if (self.__config.has_section(DEFAULT_SECTION) and
            key in self.__config[DEFAULT_SECTION]):
                #
                # The notify key can be multiple values, we
                # should return it as a list
                #
                if key == 'notify':
                    return self.__config[DEFAULT_SECTION][key].split()
                return self.__config[DEFAULT_SECTION][key]

        raise KeyError

    def __contains__(self, key):
        if key in self.__cmdline:
            val = self.__cmdline[key]
            if val is not None:
                return True

        if (self.__config.has_section(DEFAULT_SECTION) and
                key in self.__config[DEFAULT_SECTION]):
            return True

        return False
