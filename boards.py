#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Skia < skia AT libskia DOT so >
#
# Beerware licensed software - 2017
#


boards = {
        'alpine-db': {
            'name': 'Alpine DB', # A pretty name, just to name it
            'device_type': 'alpine-db', # The device-type that LAVA knows
            'defconfigs': ['arm-multi_v7_defconfig'], # This are the defconfigs you want to use with this board
                                                      # It must be available in kernel CI mainline subtree
            'dt': 'alpine-db', # The DT name (without extension)
            'rootfs': 'rootfs_armv7.cpio.gz',
            },
        'armada-370-rd': {
            'name': 'Armada 370 RD',
            'device_type': 'armada-370-rd',
            'defconfigs': ['arm-multi_v7_defconfig'],
            'dt': 'armada-370-rd',
            'rootfs': 'rootfs_armv7.cpio.gz',
            },
        'armada-3720-db': {
            'name': 'Armada 3720 DB',
            'device_type': 'armada-3720-db',
            'defconfigs': ['arm-multi_v7_defconfig'],
            'dt': 'armada-3720-db',
            'rootfs': 'rootfs_armv7.cpio.gz',
            },
        'armada-3720-espressobin': {
            'name': 'Armada 3720 Espressobin',
            'device_type': 'armada-3720-espressobin',
            'defconfigs': ['arm-multi_v7_defconfig'],
            'dt': 'armada-3720-espressobin',
            'rootfs': 'rootfs_armv7.cpio.gz',
            },
        'armada-385-db-ap': {
            'name': 'Armada 385 DB AP',
            'device_type': 'armada-385-db-ap',
            'defconfigs': ['arm-multi_v7_defconfig'],
            'dt': 'armada-385-db-ap',
            'rootfs': 'rootfs_armv7.cpio.gz',
            },
        'armada-388-clearfog': {
            'name': 'Armada 388 Clearfog',
            'device_type': 'armada-388-clearfog',
            'defconfigs': ['arm-multi_v7_defconfig'],
            'dt': 'armada-388-clearfog',
            'rootfs': 'rootfs_armv7.cpio.gz',
            },
        'at91sam9x35ek': {
            'name': 'at91sam9x35ek',
            'device_type': 'at91sam9x35ek',
            'defconfigs': ['arm-multi_v5_defconfig', 'arm-at91_dt_defconfig'],
            'dt': 'at91sam9x35ek',
            'rootfs': 'rootfs_armv5.cpio.gz',
            },
        'beaglebone-black': {
            'name': 'BeagleBone Black',
            'device_type': 'beaglebone-black',
            'defconfigs': ['arm-multi_v7_defconfig'],
            'dt': 'am335x-boneblack',
            'rootfs': 'rootfs_armv7.cpio.gz',
            },
        'orangepi-pc': {
            'name': 'OrangePi PC',
            'device_type': 'sun8i-h3-orangepi-pc',
            'defconfigs': ['arm-multi_v7_defconfig'],
            'dt': 'sun8i-h3-orangepi-pc',
            'rootfs': 'rootfs_armv7.cpio.gz',
            },
        }

