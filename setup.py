#!/usr/bin/python3 -tt

from setuptools import setup, find_packages


with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name='certbot-dns-bonk',
    version='0.2.1',
    author="Daniel Hokka Zakrisson",
    author_email="daniel@hozac.com",
    description="Certbot plugin for authentication using bonk",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dhozac/certbot-dns-bonk",
    py_modules=['certbot_dns_bonk'],
    python_requires=' >=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    install_requires=[
        'certbot',
        'zope.interface',
        'requests>=2.4.2',
    ],
    entry_points={
        'certbot.plugins': [
            'dns-bonk = certbot_dns_bonk:Authenticator',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
    ],
)
