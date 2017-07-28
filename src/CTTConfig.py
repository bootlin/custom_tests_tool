from configparser import ConfigParser

from src.cmdline import CICmdline, CTTCmdline, OptionError

class BaseError(Exception):
    pass

class ConfigFileError(BaseError):
    pass


DEFAULT_SECTION = 'ctt'



class CTTConfig:
    _CI_MANDATORY_KEYS = [
        'server', # LAVA server
        'token', # LAVA token
        'username', # LAVA user name
        'api_token', # KCI token
    ]
    _CTT_MANDATORY_KEYS = [
        'server', # LAVA server
        'token', # LAVA token
        'username', # LAVA user name
        'ssh_server', # SSH server to push artifacts
        'ssh_username', # SSH user name
        'web_ui_address', # To print nice links
        'notify', # To get emails
    ]

    def __init__(self, file, cmdline_class, boards, validate=True):
        self._config = ConfigParser()
        self._config.read_file(file)

        self._cmdline = {}

        if cmdline_class == CTTCmdline:
            self._MANDATORY_KEYS = self._CTT_MANDATORY_KEYS
        elif cmdline_class == CICmdline:
            self._MANDATORY_KEYS = self._CI_MANDATORY_KEYS

        if (validate):
            self.__validate_config_file()

        self._cmdline = cmdline_class(boards, validate)


    def __validate_config_file(self):
        if not self._config.has_section(DEFAULT_SECTION):
            raise ConfigFileError('Missing %s section in config file' % DEFAULT_SECTION)
        for option in self._MANDATORY_KEYS:
            if not self.__contains__(option):
                raise ConfigFileError('Missing %s option in config file' % option)

    def __getitem__(self, key):
        if key in self._cmdline:
            return self._cmdline[key]

        if (self._config.has_section(DEFAULT_SECTION) and
            key in self._config[DEFAULT_SECTION]):
                #
                # The notify key can be multiple values, we
                # should return it as a list
                #
                if key == 'notify':
                    return self._config[DEFAULT_SECTION][key].split()

                return self._config[DEFAULT_SECTION][key]

        raise KeyError

    def __contains__(self, key):
        if key in self._cmdline:
            return True

        if (self._config.has_section(DEFAULT_SECTION) and
                key in self._config[DEFAULT_SECTION]):
            return True

        return False
