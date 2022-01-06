#!/usr/bin/env python
from setuptools import setup, find_packages  # This setup relies on setuptools since distutils is insufficient and badly hacked code

version = '0.1.0'
author = 'Pascal Wolf'
author_email = 'wolf@physik.uni-bonn.de'

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='silab_tools',
    version=version,
    description='Collection of often-used routines for measurements as well as analysis and visualization',
    url='https://github.com/SiLab-Bonn/silab_tools',
    license='MIT License',
    long_description='',
    author=author,
    maintainer=author,
    author_email=author_email,
    maintainer_email=author_email,
    packages=find_packages(),
    setup_requires=['setuptools'],
    install_requires=required,
    include_package_data=True,  # accept all data files and directories matched by MANIFEST.in or found in source control
    package_data={'': ['README.*', 'VERSION'], 'docs': ['*'], 'examples': ['*']},
    keywords=['silab', 'fitting', 'measurement', 'basil'],
    platforms='any'
)
