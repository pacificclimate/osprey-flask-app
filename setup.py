#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup

__version__ = (0, 2, 0)

classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "Operating System :: MacOS :: MacOS X",
    "Operating System :: POSIX",
    "Programming Language :: Python",
    "Natural Language :: English",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Topic :: Scientific/Engineering :: Atmospheric Science",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
]

setup(
    name="osprey-flask-app",
    version=".".join(str(d) for d in __version__),
    description="A service to expose on-demand routed streamflow.",
    classifiers=classifiers,
    license="GNU General Public License v3",
    keywords="osprey flask",
    packages=["osprey_flask_app"],
    package_data={
        "osprey-flask-app": ["tests/configs/*.cfg", "tests/data/samples/*.cfg"],
        "tests": ["configs/*.cfg", "data/samples/*.cfg"],
    },
    include_package_data=True,
    install_requires=["flask", "netCDF4", "xarray", "birdhouse-birdy", "wps-tools"],
)
