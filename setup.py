#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup

__version__ = (1, 0, 0)

reqs = [line.strip() for line in open("requirements.txt")]
test_reqs = [line.strip() for line in open("test_requirements.txt")]

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
    install_requires=reqs,
    extras_require={
        "dev": test_reqs,
    },  # pip install ".[dev]"
)
