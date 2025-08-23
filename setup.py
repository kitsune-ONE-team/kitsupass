#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='kitsupass',
    version='0.0.1',
    install_requires=[
        'pyotp==2.9.0',
    ],
    extras_require = {
        'all': [
            'bottle==0.13.2',
            'jwskate==0.11.1',
            'SecretStorage==3.3.3',
        ],
        'buttercup':  [
            'bottle==0.13.2',
            'jwskate==0.11.1',
        ],
        'keyring':  [
            'SecretStorage==3.3.3',
        ]
    }
    packages=find_packages(
        include=['kitsupass*'],
        exclude=['tests', 'importer'],
    ),
    entry_points={'console_scripts': [
        'kitsupass = kitsupass.__main__:main',
        'kitsupass-askpass = kitsupass.askpass:main',
    ]},
    include_package_data=True,
    package_dir={'': '.'},
    package_data={'kitsupass.buttercup': ['*.service']}
)
