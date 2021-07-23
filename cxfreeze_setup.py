from os.path import basename, join

import pkg_resources
from cx_Freeze import Executable, setup


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
