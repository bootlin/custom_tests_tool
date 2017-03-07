#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Skia < skia AT libskia DOT so >
#
# Beerware licensed software - 2017
#


boards = {
        'bbb': {
            'name': 'bbb', # A pretty name, just to name it
            'defconfigs': ['arm-multi_v7_defconfig'], # This are the defconfigs you want to use with this board
                                                      # It must be available in kernel CI mainline subtree
            'dt': 'am335x-boneblack', # The DT name (without extension)
            'device_type': 'beaglebone-black', # The device-type that LAVA knows
            },
        'orangepi': {
            'name': 'orangepi',
            'defconfigs': ['arm-multi_v7_defconfig'],
            'dt': 'sun8i-h3-orangepi-pc',
            'device_type': 'orangepi-pc',
            },
        }


