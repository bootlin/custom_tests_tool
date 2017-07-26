
marvell = [ "thomas.petazzoni@free-electrons.com",
            "gregory.clement@free-electrons.com",
            "antoine.tenart@free-electrons.com" ]

boards = {
        'alpine-db': {
            'name': 'Alpine DB', # A pretty name, just to name it
            'device_type': 'alpine-db', # The device-type that LAVA knows
            'arch': 'arm', # The architecture of the board
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],  # This are the configs you want to use with this board
                    # The format is as simple as tree/branch/defconfig
                    # If a branch contains a '/' in its name, the builders
                    # generally replace it with a '_', and you need to do the
                    # same here.
            'dt': 'alpine-db', # The DT name (without extension)
            'rootfs': 'rootfs_armv7.cpio.gz', # The rootfs to use (must exist in rootfs_path)
            'test_plan': 'boot', # boot or boot-nfs if the board can not boot with ramdisk
            'tests': [ # A list of tests to run.
                #{
                #    'name': 'boot', # Name matching a file in the script folder of the test suite
                #    'configs': ['multi_v7_defconfig'], # You can override the configs to use, but it's not mandatory
                #    'template': 'generic_simple_job.jinja', # You can also override the template.
                #                                            # If not, default is generic_simple_job.jinja
                #    },
                # {
                #     'name': 'network',
                #     'template': 'generic_multinode_job.jinja',
                #     },
                ],
            'notify': [], # The list of email addresses to notify in case of failure
            },
        'alpine-v2-evp': {
            'name': 'alpine-v2-evp',
            'device_type': 'alpine-v2-evp',
            'arch': 'arm64',
            'configs': [
                'mainline/master/defconfig',
                ],
            'dt': 'al/alpine-v2-evp',
            'rootfs': 'rootfs_aarch64.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': [],
            },
        'armada-370-db': {
            'name': 'armada-370-db',
            'device_type': 'armada-370-db',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'armada-370-db',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                {
                    'name': 'crypto',
                    },
                {
                    'name': 'crypto-tcrypt',
                    'configs': [
                        'mvebu-backports/4.12-rc6_backports/mvebu_v7_defconfig+tcrypt',
                        ],
                    'template': 'generic_simple_job_long_timeout.jinja',
                    },
                {
                    'name': 'sata',
                    },
                {
                    'name': 'network',
                    'template': 'generic_multinode_job.jinja',
                    },
                ],
            'notify': marvell,
            },
        'armada-370-rd': {
            'name': 'Armada 370 RD',
            'device_type': 'armada-370-rd',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'armada-370-rd',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                {
                    'name': 'crypto',
                    },
                {
                    'name': 'crypto-tcrypt',
                    'configs': [
                        'mvebu-backports/4.12-rc6_backports/mvebu_v7_defconfig+tcrypt',
                        ],
                    'template': 'generic_simple_job_long_timeout.jinja',
                    },
                {
                    'name': 'network',
                    'template': 'generic_multinode_job.jinja',
                    },
                ],
            'notify': marvell,
            },
        'armada-3720-db': {
            'name': 'Armada 3720 DB',
            'device_type': 'armada-3720-db',
            'arch': 'arm64',
            'configs': [
                'mainline/master/defconfig',
                ],
            'dt': 'marvell/armada-3720-db',
            'rootfs': 'rootfs_aarch64.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': marvell,
            },
        'armada-3720-espressobin': {
            'name': 'Armada 3720 Espressobin',
            'device_type': 'armada-3720-espressobin',
            'arch': 'arm64',
            'configs': [
                'mainline/master/defconfig',
                ],
            'dt': 'marvell/armada-3720-espressobin',
            'rootfs': 'rootfs_aarch64.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': marvell,
            },
        'armada-375-db': {
            'name': 'armada-375-db',
            'device_type': 'armada-375-db',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'armada-375-db',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                {
                    'name': 'crypto',
                    },
                {
                    'name': 'crypto-tcrypt',
                    'configs': [
                        'mvebu-backports/4.12-rc6_backports/mvebu_v7_defconfig+tcrypt',
                        ],
                    'template': 'generic_simple_job_long_timeout.jinja',
                    },
                ],
            'notify': marvell,
            },
        'armada-385-db-ap': {
            'name': 'Armada 385 DB AP',
            'device_type': 'armada-385-db-ap',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'armada-385-db-ap',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                {
                    'name': 'crypto',
                    },
                {
                    'name': 'crypto-tcrypt',
                    'configs': [
                        'mvebu-backports/4.12-rc6_backports/mvebu_v7_defconfig+tcrypt',
                        ],
                    'template': 'generic_simple_job_long_timeout.jinja',
                    },
                ],
            'notify': marvell,
            },
        'armada-388-clearfog': {
            'name': 'Armada 388 Clearfog',
            'device_type': 'armada-388-clearfog',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'armada-388-clearfog',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                {
                    'name': 'crypto',
                    },
                {
                    'name': 'crypto-tcrypt',
                    'configs': [
                        'mvebu-backports/4.12-rc6_backports/mvebu_v7_defconfig+tcrypt',
                        ],
                    'template': 'generic_simple_job_long_timeout.jinja',
                    },
                {
                    'name': 'network',
                    'template': 'generic_multinode_job.jinja',
                    },
                ],
            'notify': marvell,
            },
        'armada-388-gp': {
            'name': 'Armada 388 GP',
            'device_type': 'armada-388-gp',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'armada-388-gp',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                {
                    'name': 'crypto',
                    },
                {
                    'name': 'crypto-tcrypt',
                    'configs': [
                        'mvebu-backports/4.12-rc6_backports/mvebu_v7_defconfig+tcrypt',
                        ],
                    'template': 'generic_simple_job_long_timeout.jinja',
                    },
                {
                    'name': 'network',
                    'template': 'generic_multinode_job.jinja',
                    },
                ],
            'notify': marvell,
            },
        'armada-7040-db': {
            'name': 'armada-7040-db',
            'device_type': 'armada-7040-db',
            'arch': 'arm64',
            'configs': [
                'mainline/master/defconfig',
                ],
            'dt': 'marvell/armada-7040-db',
            'rootfs': 'rootfs_aarch64.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': marvell,
            },
        'armada-8040-db': {
            'name': 'armada-8040-db',
            'device_type': 'armada-8040-db',
            'arch': 'arm64',
            'configs': [
                'mainline/master/defconfig',
                ],
            'dt': 'marvell/armada-8040-db',
            'rootfs': 'rootfs_aarch64.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': marvell,
            },
        'armada-398-db': {
            'name': 'Armada 398 DB',
            'device_type': 'armada-398-db',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'armada-398-db',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': marvell,
            },
        'armada-xp-db': { # NFS boot
            'name': 'Armada XP DB',
            'device_type': 'armada-xp-db',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'armada-xp-db',
            'rootfs': 'rootfs_armv7.tar.gz',
            'test_plan': 'boot-nfs',
            'tests': [
                {
                    'name': 'crypto',
                    },
                {
                    'name': 'crypto-tcrypt',
                    'configs': [
                        'mvebu-backports/4.12-rc6_backports/mvebu_v7_defconfig+tcrypt',
                        ],
                    'template': 'generic_simple_job_long_timeout.jinja',
                    },
                {
                    'name': 'network',
                    'template': 'generic_multinode_job.jinja',
                    },
                ],
            'notify': marvell,
            },
        'armada-xp-gp': { # NFS boot
            'name': 'Armada XP GP',
            'device_type': 'armada-xp-gp',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'armada-xp-gp',
            'rootfs': 'rootfs_armv7.tar.gz',
            'test_plan': 'boot-nfs',
            'tests': [
                {
                    'name': 'crypto',
                    },
                {
                    'name': 'crypto-tcrypt',
                    'configs': [
                        'mvebu-backports/4.12-rc6_backports/mvebu_v7_defconfig+tcrypt',
                        ],
                    'template': 'generic_simple_job_long_timeout.jinja',
                    },
                {
                    'name': 'network',
                    'template': 'generic_multinode_job.jinja',
                    },
                ],
            'notify': marvell,
            },
        'armada-xp-linksys-mamba': {
            'name': 'armada-xp-linksys-mamba',
            'device_type': 'armada-xp-linksys-mamba',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'armada-xp-linksys-mamba',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                {
                    'name': 'crypto',
                    },
                {
                    'name': 'crypto-tcrypt',
                    'configs': [
                        'mvebu-backports/4.12-rc6_backports/mvebu_v7_defconfig+tcrypt',
                        ],
                    'template': 'generic_simple_job_long_timeout.jinja',
                    },
                {
                    'name': 'network',
                    'template': 'generic_multinode_job.jinja',
                    },
                ],
            'notify': marvell,
            },
        'armada-xp-openblocks-ax3-4': {
            'name': 'Armada XP Openblocks AX3 4',
            'device_type': 'armada-xp-openblocks-ax3-4',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'armada-xp-openblocks-ax3-4',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                {
                    'name': 'crypto',
                    },
                {
                    'name': 'crypto-tcrypt',
                    'configs': [
                        'mvebu-backports/4.12-rc6_backports/mvebu_v7_defconfig+tcrypt',
                        ],
                    'template': 'generic_simple_job_long_timeout.jinja',
                    },
                {
                    'name': 'network',
                    'template': 'generic_multinode_job.jinja',
                    },
                ],
            'notify': marvell,
            },
        'at91-sama5d2_xplained': {
            'name': 'at91-sama5d2_xplained',
            'device_type': 'at91-sama5d2_xplained',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                'linux4sam/master/sama5_defconfig',
                ],
            'dt': 'at91-sama5d2_xplained',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': [],
            },
        'at91-sama5d4_xplained': {
            'name': 'AT91 sama5d4 Xplained',
            'device_type': 'at91-sama5d4_xplained',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                'linux4sam/master/sama5_defconfig',
                ],
            'dt': 'at91-sama5d4_xplained',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                {
                    'name': 'network',
                    'template': 'generic_multinode_job.jinja',
                    },
                ],
            'notify': [],
            },
        'at91rm9200ek': {
            'name': 'at91rm9200ek',
            'device_type': 'at91rm9200ek',
            'arch': 'arm',
            'configs': [
                'mainline/master/at91_dt_defconfig',
                ],
            'dt': 'at91rm9200ek',
            'rootfs': 'rootfs_armv4.tar.gz',
            'test_plan': 'boot-nfs',
            'tests': [
                {
                    'name': 'network',
                    'template': 'generic_multinode_job.jinja',
                    },
                ],
            'notify': [],
            },
        'at91sam9261ek': {
            'name': 'at91sam9261ek',
            'device_type': 'at91sam9261ek',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v5_defconfig',
                'linux4sam/master/at91_dt_defconfig',
                ],
            'dt': 'at91sam9261ek',
            'rootfs': 'rootfs_armv5.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': [],
            },
        'at91sam9m10g45ek': {
            'name': 'at91sam9m10g45ek',
            'device_type': 'at91sam9m10g45ek',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v5_defconfig',
                'linux4sam/master/at91_dt_defconfig',
                ],
            'dt': 'at91sam9m10g45ek',
            'rootfs': 'rootfs_armv5.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                {
                    'name': 'network',
                    'template': 'generic_multinode_job.jinja',
                    },
                ],
            'notify': [],
            },
        'at91sam9x25ek': {
            'name': 'at91sam9x25ek',
            'device_type': 'at91sam9x25ek',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v5_defconfig',
                'linux4sam/master/at91_dt_defconfig',
                ],
            'dt': 'at91sam9x25ek',
            'rootfs': 'rootfs_armv5.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                {
                    'name': 'network',
                    'template': 'generic_multinode_job.jinja',
                    },
                ],
            'notify': [],
            },
        'at91sam9x35ek': {
            'name': 'at91sam9x35ek',
            'device_type': 'at91sam9x35ek',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v5_defconfig',
                'linux4sam/master/at91_dt_defconfig',
                ],
            'dt': 'at91sam9x35ek',
            'rootfs': 'rootfs_armv5.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                {
                    'name': 'network',
                    'template': 'generic_multinode_job.jinja',
                    },
                ],
            'notify': [],
            },
        'beagle-xm': {
            'name': 'beagle-xm',
            'device_type': 'beagle-xm',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'omap3-beagle-xm',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': [],
            },
        'beaglebone-black': {
            'name': 'BeagleBone Black',
            'device_type': 'beaglebone-black',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'am335x-boneblack',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                {
                    'name': 'mmc',
                    'template': 'generic_simple_job.jinja',
                    },
                {
                    'name': 'network',
                    'template': 'generic_multinode_job.jinja',
                    },
                ],
            'notify': [],
            },
        'imx6q-nitrogen6x': {
            'name': 'imx6q nitrogen6x',
            'device_type': 'imx6q-nitrogen6x',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'imx6q-nitrogen6x',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': [],
            },
        'kirkwood-db-88f6282': {
            'name': 'kirkwood-db-88f6282',
            'device_type': 'kirkwood-db-88f6282',
            'arch': 'arm',
            'configs': [
                'mainline/master/mvebu_v5_defconfig',
                ],
            'dt': 'kirkwood-db-88f6282',
            'rootfs': 'rootfs_armv5.tar.gz',
            'test_plan': 'boot-nfs',
            'tests': [
                ],
            'notify': marvell,
            },
        'kirkwood-openblocks_a7': {
            'name': 'kirkwood-openblocks_a7',
            'device_type': 'kirkwood-openblocks_a7',
            'arch': 'arm',
            'configs': [
                'mainline/master/mvebu_v5_defconfig',
                ],
            'dt': 'kirkwood-openblocks_a7',
            'rootfs': 'rootfs_armv5.tar.gz',
            'test_plan': 'boot-nfs',
            'tests': [
                ],
            'notify': marvell,
            },
        'optimus-a80': {
            'name': 'optimus-a80',
            'device_type': 'optimus-a80',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'sun9i-a80-optimus',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': [],
            },
        'orion5x-rd88f5182-nas': {
            'name': 'orion5x-rd88f5182-nas',
            'device_type': 'orion5x-rd88f5182-nas',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v5_defconfig',
                ],
            'dt': 'orion5x-rd88f5182-nas',
            'rootfs': 'rootfs_armv5.tar.gz',
            'test_plan': 'boot-nfs',
            'tests': [
                ],
            'notify': marvell,
            },
        'sama53d': {
            'name': 'sama5d3 Xplained',
            'device_type': 'sama53d',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                'linux4sam/master/sama5_defconfig',
                ],
            'dt': 'at91-sama5d3_xplained',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                {
                    'name': 'mmc',
                    },
                {
                    'name': 'usb',
                    },
                {
                    'name': 'network',
                    'template': 'generic_multinode_job.jinja',
                    },
                ],
            'notify': ['florent.jacquet@free-electrons.com'],
            },
        'sama5d34ek': {
            'name': 'sama5d34ek',
            'device_type': 'sama5d34ek',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                'linux4sam/master/sama5_defconfig',
                ],
            'dt': 'sama5d34ek',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': [],
            },
        'sama5d36ek': {
            'name': 'sama5d36ek',
            'device_type': 'sama5d36ek',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                'linux4sam/master/sama5_defconfig',
                ],
            'dt': 'sama5d36ek',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': [],
            },
        'sama5d4ek': {
            'name': 'sama5d4ek',
            'device_type': 'sama5d4ek',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                'linux4sam/master/sama5_defconfig',
                ],
            'dt': 'sama5d4ek',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': [],
            },
        'sun5i-r8-chip': {
            'name': 'sun5i r8 chip',
            'device_type': 'sun5i-r8-chip',
            'arch': 'arm',
            'configs': [
                'mainline/master/sunxi_defconfig',
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'sun5i-r8-chip',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                {
                    'name': 'boot'
                    }
                ],
            'notify': [],
            },
        'sun6i-a31-app4-evb1': {
            'name': 'sun6i-a31-app4-evb1',
            'device_type': 'sun6i-a31-app4-evb1',
            'arch': 'arm',
            'configs': [
                'mainline/master/sunxi_defconfig',
                ],
            'dt': 'sun6i-a31-app4-evb1',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': [],
            },
        'sun8i-a23-evb': {
            'name': 'sun8i-a23-evb',
            'device_type': 'sun8i-a23-evb',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'sun8i-a23-evb',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': [],
            },
        'sun8i-a33-sinlinx-sina33': {
            'name': 'sun8i-a33-sinlinx-sina33',
            'device_type': 'sun8i-a33-sinlinx-sina33',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'sun8i-a33-sinlinx-sina33',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': [],
            },
        'sun8i-a83t-allwinner-h8homlet-v2': {
            'name': 'sun8i-a83t-allwinner-h8homlet-v2',
            'device_type': 'sun8i-a83t-allwinner-h8homlet-v2',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'sun8i-a83t-allwinner-h8homlet-v2',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': [],
            },
        'sun8i-h3-orangepi-pc': {
            'name': 'OrangePi PC',
            'device_type': 'sun8i-h3-orangepi-pc',
            'arch': 'arm',
            'configs': [
                'mainline/master/multi_v7_defconfig',
                ],
            'dt': 'sun8i-h3-orangepi-pc',
            'rootfs': 'rootfs_armv7.cpio.gz',
            'test_plan': 'boot',
            'tests': [
                ],
            'notify': [],
            },
        }

