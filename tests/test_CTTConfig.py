#!/usr/bin/env python3

import io
import random
import string

from unittest import mock

from nose.tools import assert_equal, assert_false, assert_true
from nose.tools import raises

from CTTConfig import CTTConfig, OptionError, SectionError
import boards

#
# TODO:
#
#   - Validate that we cannot enter an invalid test. This would
#     require a few changes to the way tests are handled, most
#     notably:
#     + Import the test suite as a submodule
#     + Check each test against the test suite configuration
#     + Any test not in the suite configuration should generate an
#       error
#
#   - Validate that the test set when we don't specify a test on the
#     command line is the proper one, both when we have a board, and
#     when we don't (or when we have -b all)
#

config_dict = [
    {
        'cmdline': '--api-token',
        'in_config': True,
        'key': 'api_token',
    },
    {
        'cmdline': '--boards',
        'key': 'boards',
        'multiple': True,
    },
    {
        'cmdline': '--branch',
        'key': 'branch',
        'default': 'master',
    },
    {
        'cmdline': '--default-notify',
        'key': 'default_notify',
        'boolean': True,
    },
    {
        'cmdline': '--defconfigs',
        'key': 'defconfigs',
        'multiple': True,
    },
    {
        'cmdline': '--dtb',
        'key': 'dtb',
    },
    {
        'cmdline': '--dtb-folder',
        'key': 'dtb_folder',
    },
    {
        'cmdline': '--kernel',
        'key': 'kernel',
    },
    {
        'cmdline': '--job-name',
        'key': 'job_name',
    },
    {
        'cmdline': '--list',
        'key': 'list',
        'boolean': True,
    },
    {
        'cmdline': '--modules',
        'key': 'modules',
    },
    {
        'cmdline': '--no-kci',
        'key': 'no_kci',
        'boolean': True,
    },
    {
        'cmdline': '--no-send',
        'key': 'no_send',
        'boolean': True,
    },
    {
        'cmdline': '--notify',
        'in_config': True,
        'key': 'notify',
        'multiple': True,
    },
    {
        'cmdline': '--output-dir',
        'key': 'output_dir',
        'default': 'jobs',
    },
    {
        'cmdline': '--rootfs',
        'key': 'rootfs',
    },
    {
        'cmdline': '--rootfs-path',
        'in_config': True,
        'key': 'rootfs_path',
    },
    {
        'cmdline': '--server',
        'in_config': True,
        'key': 'server',
    },
    {
        'cmdline': '--ssh-server',
        'in_config': True,
        'key': 'ssh_server',
    },
    {
        'cmdline': '--ssh-username',
        'in_config': True,
        'key': 'ssh_username',
    },
    {
        'cmdline': '--tests',
        'key': 'tests',
        'multiple': True,
    },
    {
        'cmdline': '--token',
        'in_config': True,
        'key': 'token',
    },
    {
        'cmdline': '--tree',
        'key': 'tree',
        'default': 'mainline',
    },
    {
        'cmdline': '--username',
        'in_config': True,
        'key': 'username',
    },
    {
        'in_config': True,
        'key': 'web_ui_address',
    },
]


def generate_random_string(length=16):
    return ''.join(random.choices(string.ascii_lowercase, k=length))


def generate_minimal_cmdline():
    return ['ctt', '-b', generate_random_string(), '-t',
            generate_random_string()]


#
# Generates a valid configuration that will go through the parser
# validation. In order to force errors, we can choose to remove keys,
# or change the section that will be generated
#
def generate_config(section='ctt', ignore_key=None):
    config = io.StringIO()
    values = dict()

    print('[%s]' % section, file=config)

    for option in config_dict:
        if ('in_config' in option and option['in_config'] and
                option['key'] is not ignore_key):
            value = generate_random_string()
            print('%s = %s' % (option['key'], value), file=config)
            values[option['key']] = value

    config.seek(0)

    return config, generate_minimal_cmdline(), values


#
# Test that the value all for the boards is properly expanded
#
def test_cfg_board_all():
    cfg, cmdline, values = generate_config()

    with mock.patch('sys.argv', ['ctt', '-t' 'boot', '-b', 'all']):
        ctt = CTTConfig(file = cfg)
        assert_equal(ctt['boards'], list(boards.boards.keys()))

#
# Test that the value all for the boards is properly expanded, even if
# we have other values set
#
def test_cfg_board_all_multiple():
    cfg, cmdline, values = generate_config()

    with mock.patch('sys.argv', ['ctt', '-t' 'boot',
                                 '-b', 'all', generate_random_string()]):
        ctt = CTTConfig(file = cfg)

        assert_equal(ctt['boards'], list(boards.boards.keys()))


#
# Test that we properly report invalid boards as such. generate_config
# will return a random board name, so it should be good enough.
#
@raises(OptionError)
def test_cfg_board_invalid():
    cfg, cmdline, values = generate_config()

    with mock.patch('sys.argv', cmdline):
        ctt = CTTConfig(file = cfg)

#
# Test that we properly report valid boards as such.
#
def __test_cfg_board_valid(board):
    cfg, cmdline, values = generate_config()

    with mock.patch('sys.argv', ['ctt', '-t', generate_random_string(),
                                 '-b', board]):
        ctt = CTTConfig(file = cfg)
        assert True


def test_cfg_board_valid():
    for board in boards.boards.keys():
        yield __test_cfg_board_valid, board

#
# Test that a mandatory value missing (in the command line) is indeed
# generating an error
#
@raises(OptionError)
def __test_cfg_cmdline_missing_option(cmdline):
    argv = ['ctt']

    for option in config_dict:
        if ('cmdline' in option and option['cmdline'] and
            option['cmdline'] is not cmdline and
                not option['cmdline'] == '--list'):
            argv.append(option['cmdline'])

            if 'boolean' not in option or not option['boolean']:
                argv.append(generate_random_string())

    with mock.patch('sys.argv', argv):
        ctt = CTTConfig()


def test_cfg_cmdline_missing_option():
    for option in config_dict:
        if ('in_config' in option and option['in_config'] and
                'cmdline' in option):
            yield __test_cfg_cmdline_missing_option, option['cmdline']


#
# Test that a mandatory value missing (in the config file) is indeed
# generating an error
#
@raises(OptionError)
def __test_cfg_config_missing_option(key):
    config = generate_config(ignore_key=key)[0]

    with mock.patch('sys.argv', ['ctt']):
        ctt = CTTConfig(file=config)


def test_cfg_config_missing_option():
    for option in config_dict:
        if 'in_config' in option and option['in_config']:
            yield __test_cfg_config_missing_option, option['key']


#
# Test that we report an error when the configuration file is missing
# the ctt section
#
@raises(SectionError)
def test_cfg_config_missing_section():
    config = generate_config(section='test')[0]
    ctt = CTTConfig(file=config)


#
# Test that we report an error when the configuration file is missing
# the ctt section
#
@raises(OptionError)
def test_cfg_config_missing_cmdline_only():
    cfg, cmdline, values = generate_config()

    with mock.patch('sys.argv', ['ctt']):
        ctt = CTTConfig(file=cfg)


#
# Test that we report an error when the board option is missing, and
# we have a test option
#
@raises(OptionError)
def test_config_missing_board():
    cfg, cmdline, values = generate_config()

    with mock.patch('sys.argv', ['ctt', '-t', generate_random_string()]):
        ctt = CTTConfig(file=cfg)


#
# Test that we report an error when the test options are missing, and
# we have a board test option
#
@raises(OptionError)
def test_config_missing_test_board():
    cfg, cmdline, values = generate_config()

    with mock.patch('sys.argv', ['ctt', '-b', generate_random_string()]):
        ctt = CTTConfig(file=cfg)


#
# Test that a value not specified on the command line will either
# return a KeyError when accessed, or return its default value
#
def __test_get_cmdline_missing(key, default=None):
    with mock.patch('sys.argv', ['ctt']):
        ctt = CTTConfig(validate=False)
        if default is not None:
            assert_equal(default, ctt[key])
        else:
            try:
                ctt[key]
                assert False
            except KeyError:
                assert True


def test_get_cmdline_missing():
    for option in config_dict:
        if 'default' in option:
            yield __test_get_cmdline_missing, option['key'], option['default']
        elif 'boolean' in option and option['boolean']:
            yield __test_get_cmdline_missing, option['key'], False
        else:
            yield __test_get_cmdline_missing, option['key']


#
# Test that an option specified in the configuration file is returning
# the proper value
#
def __test_get_config_value(key, multiple = False):
    cfg, cmdline, values = generate_config()

    with mock.patch('sys.argv', cmdline):
        ctt = CTTConfig(validate=False, file=cfg)

        if multiple:
            assert_equal(ctt[key], [values[key]])
        else:
            assert_equal(ctt[key], values[key])


def test_get_config_value():
    for option in config_dict:
        if 'in_config' in option and option['in_config']:
            if 'multiple' in option and option['multiple']:
                yield __test_get_config_value, option['key'], True
            else:
                yield __test_get_config_value, option['key']


#
# Test that a value specified on the command line will indeed be
# reported as there in the configuration
#
def __test_has_cmdline_string(cmdline, key):
    value = generate_random_string()
    cmdline = ['ctt', cmdline, value]

    with mock.patch('sys.argv', cmdline):
        ctt = CTTConfig(validate=False)
        assert_true(ctt.__contains__(key))


def test_has_cmdline_string():
    for option in config_dict:
        if ('cmdline' in option and
                ('boolean' not in option or not option['boolean'])):
            yield __test_has_cmdline_string, option['cmdline'], option['key']


#
# Test that a value not specified on the command line will indeed be
# reported as missing in the configuration
#
def __test_has_cmdline_missing(key):
    with mock.patch('sys.argv', ['ctt']):
        ctt = CTTConfig(validate=False)
        assert_false(ctt.__contains__(key))


def test_has_cmdline_missing():
    for option in config_dict:
        if ('default' not in option and
                ('boolean' not in option or not option['boolean'])):
            yield __test_has_cmdline_missing, option['key']

#
# Test that a value specified in the configuration file is properly
# reported as part of the configuration
#


def __test_has_config_value(key):
    cfg, cmdline, values = generate_config()

    with mock.patch('sys.argv', cmdline):
        ctt = CTTConfig(validate=False, file=cfg)
        assert_true(ctt.__contains__(key))


def test_has_config_values():
    for option in config_dict:
        if 'in_config' in option and option['in_config']:
            yield __test_has_config_value, option['key']


#
# Test that a value specified in the configuration file will be
# properly overridden by the command line
#
def __test_override_value(key, cmdoption, multiple):
    cfg, cmdline, values = generate_config()
    new_value = generate_random_string()

    # If our value has multiple options, our parser will return a
    # list with a single element, instead of just the element
    if (multiple):
        test_value = list()
        test_value.append(new_value)
    else:
        test_value = new_value

    cmdline.extend([cmdoption, new_value])

    with mock.patch('sys.argv', cmdline):
        ctt = CTTConfig(validate=False, file=cfg)
        assert_equal(ctt[key], test_value)


def test_override_single_value():
    for option in config_dict:
        if (('in_config' in option and option['in_config']) and
            ('multiple' not in option or not option['multiple']) and
                'cmdline' in option):
            yield (__test_override_value, option['key'], option['cmdline'],
                   False)


def test_override_multiple_value():
    for option in config_dict:
        if (('in_config' in option and option['in_config']) and
            ('multiple' in option and option['multiple']) and
                'cmdline' in option):
            yield __test_override_value, option['key'], option['cmdline'], True


#
# Test that a boolean value specified on the command line will indeed
# return the proper value in the configuration
#
def __test_set_cmdline_bool(cmdline, key):
    argv = ['ctt', cmdline]

    with mock.patch('sys.argv', argv):
        ctt = CTTConfig(validate=False)
        assert_true(ctt[key])


def test_set_cmdline_bool():
    for option in config_dict:
        if ('cmdline' in option and
                ('boolean' in option and option['boolean'])):
            yield __test_set_cmdline_bool, option['cmdline'], option['key']

#
# Test that a string value, that can be there multiple times,
# specified on the command line will indeed return the proper value in
# the configuration
#


def __test_set_cmdline_string_multiple(cmdline, key):
    argv = ['ctt', cmdline]
    value = []

    for i in range(random.randint(2, 16)):
        value.append(generate_random_string())

    argv.extend(value)

    with mock.patch('sys.argv', argv):
        ctt = CTTConfig(validate=False)
        assert_equal(value, ctt[key])


def test_set_cmdline_string_multiple():
    for option in config_dict:
        if ('cmdline' in option and
            ('multiple' in option and option['multiple']) and
                ('boolean' not in option or not option['boolean'])):
            yield (__test_set_cmdline_string_multiple, option['cmdline'],
                   option['key'])

#
# Test that a string value, that can be there only once, specified on
# the command line will indeed return the proper value in the
# configuration
#


def __test_set_cmdline_string_single(cmdline, key):
    value = generate_random_string()
    argv = ['ctt', cmdline, value]

    with mock.patch('sys.argv', argv):
        ctt = CTTConfig(validate=False)
        assert_equal(value, ctt[key])


def test_set_cmdline_string_single():
    for option in config_dict:
        if ('cmdline' in option and
            ('multiple' not in option or not option['multiple']) and
                ('boolean' not in option or not option['boolean'])):
            yield (__test_set_cmdline_string_single, option['cmdline'],
                   option['key'])
