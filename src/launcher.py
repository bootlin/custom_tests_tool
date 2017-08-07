import json
import logging
import os
import sys

from src.CTTFormatter import CTTFormatter
from src.CTTConfig import CTTConfig, OptionError, ConfigFileError, CICmdline
from src.crafter import JobCrafter

class BaseLauncher(object):
    """
    This class makes the basic stages of initialization, such as logging and
    configuration, but must be subclassed to add at least a `_CMDLINE_CLASS`
    attribute, and a `launch` method.
    """
    def __init__(self):
        self._set_logging()
        self._set_config()

    def _set_logging(self):
        self._logger = logging.getLogger()
        self._logger.setLevel(logging.DEBUG)

        requests_logger = logging.getLogger("requests")
        requests_logger.setLevel(logging.WARN)

        handler = logging.StreamHandler()

        formatter = CTTFormatter()
        handler.setFormatter(formatter)

        self._logger.addHandler(handler)

    def _set_config(self):
        ctt_root_location = os.path.abspath(os.path.dirname(
            os.path.dirname(os.path.realpath(__file__))))

        with open(os.path.join(ctt_root_location, "boards.json")) as f:
            self._boards_config = json.load(f)
            # Add the name field
            for k,v in self._boards_config.items():
                v['name'] = k
                v['device_type'] = k

        try:
            with open(os.path.expanduser('~/.cttrc')) as f:
                self._cfg = self._CONFIG_CLASS(f, self._CMDLINE_CLASS,
                        self._boards_config)
        except OptionError as e:
            logging.critical(e)
            sys.exit(1)
        except ConfigFileError as e:
            logging.critical(e)
            sys.exit(2)

        if self._cfg['debug']:
            self._logger.setLevel(logging.DEBUG)
        else:
            self._logger.setLevel(logging.INFO)

        # TODO: handle exceptions
        self.crafter = JobCrafter(self._boards_config, self._cfg)

    def launch(self):
        raise NotImplementedError("Missing launching function")


