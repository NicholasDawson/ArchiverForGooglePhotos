from os.path import basename, join

import pkg_resources
from cx_Freeze import Executable, setup

"""
    Archiver For Google Photos
    - A tool to maintain an archive/mirror of your Google Photos library for backup purposes.
    Copyright (C) 2021  Nicholas Dawson

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""


def collect_dist_info(packages):
    """
    Recursively collects the path to the packages' dist-info.
    From: https://github.com/marcelotduarte/cx_Freeze/issues/438#issuecomment-472954154
    """
    if not isinstance(packages, list):
        packages = [packages]
    dirs = []
    for pkg in packages:
        distrib = pkg_resources.get_distribution(pkg)
        for req in distrib.requires():
            dirs.extend(collect_dist_info(req.key))
        dirs.append((distrib.egg_info, join("Lib", basename(distrib.egg_info))))
    return dirs


# Dependencies
build_exe_options = {
    "packages": [
        "io",
        "json",
        "os",
        "pickle",
        "multiprocessing",
        "piexif",
        "google.auth.transport.requests",
        "google_auth_oauthlib.flow",
        "googleapiclient.discovery",
        "httplib2",
        "PIL",
        "tqdm",
        "pkg_resources",
    ],
    "include_files": collect_dist_info("google_api_python_client") + ["gparch.py"],
}

base = None

setup(
    name="Archiver for Google Photos (CLI)",
    version="2.0.0",
    description="A tool to maintain an archive/mirror of your Google Photos library for backup purposes.",
    options={"build_exe": build_exe_options},
    executables=[Executable("gparch_cli.py", base=base)],
)
