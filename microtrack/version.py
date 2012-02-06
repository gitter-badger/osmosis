"""Microtrack version/release information"""

# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
_version_major = 0
_version_minor = 1
_version_micro = ''  # use '' for first of series, number for 1 and above
_version_extra = 'dev'
#_version_extra = ''  # Uncomment this for full releases

# Construct full version string from these.
_ver = [_version_major, _version_minor]
if _version_micro:
    _ver.append(_version_micro)
if _version_extra:
    _ver.append(_version_extra)

__version__ = '.'.join(map(str, _ver))

CLASSIFIERS = ["Development Status :: 3 - Alpha",
               "Environment :: Console",
               "Intended Audience :: Science/Research",
               "License :: OSI Approved :: BSD License",
               "Operating System :: OS Independent",
               "Programming Language :: Python",
               "Topic :: Scientific/Engineering"]

description = "Microtrack"

long_description = """

XXX 

Copyright (c) 2011, VISTA lab 

All rights reserved.

"""

NAME = "microtrack"
MAINTAINER = "Ariel Rokem"
MAINTAINER_EMAIL = "arokem@gmail.com"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
URL = "http://white.stanford.edu"
DOWNLOAD_URL = "http://white.stanford.edu"
LICENSE = "GPL"
AUTHOR = "VISTA team"
AUTHOR_EMAIL = "arokem@gmail.com"
PLATFORMS = "OS Independent"
MAJOR = _version_major
MINOR = _version_minor
MICRO = _version_micro
VERSION = __version__
PACKAGES = ['microtrack',
            'microtrack.tests',
            'microtrack.fibers',
            'microtrack.tensor',
            'microtrack.viz'
            ]
PACKAGE_DATA = {"microtrack": ["LICENSE", "data/*.pdb", "data/*.mat",
                               "camino_pts/*.txt"]}

REQUIRES = ["numpy", "matplotlib", "scipy", "nibabel"]
