# Copyright (c) 2022 Nordic Semiconductor ASA
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause


import subprocess
import os

NCS_DIR = os.path.abspath(os.path.join(__file__, "../../.."))

ESSENTIAL_MODULES = ["sidewalk", "nrf", "zephyr"]


def west_module_list():
    west_list = subprocess.run(["west", "list"], capture_output=True)
    west_list_lines = west_list.stdout.decode("utf-8").strip()

    return [x.split()[1:3] for x in west_list_lines.split("\n")]


def get_last_common_commit_with_upstream(ncs_dir):
    merge_base_cmd = subprocess.run(["git", "merge-base", "--fork-point", "origin/main",
                                    "HEAD"], cwd=os.path.join(ncs_dir, "sidewalk"),  capture_output=True)
    if merge_base_cmd.returncode != 0:
        return "0000000"
    return merge_base_cmd.stdout.decode("utf-8").strip()


def print_warning_header():
    return """
/*
 * Copyright (c) 2023 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
 */

/******************************************
*      This file is autogenerated.        *
* Do not commit this file, or modify it.  *
******************************************/
"""


def print_includes():
    return """
#include <zephyr/kernel.h>
#include <stdint.h>
#include <stddef.h>
"""


def x_macro_always_raport_swith():
    return """
#define DO_NOTHING

#if CONFIG_SIDEWALK_GENERATE_VERSION_MINIMAL
#define ALWAYS_RAPORT0(name, version) DO_NOTHING
#define ALWAYS_RAPORT1(name, version) X(name, version)
#else
#define ALWAYS_RAPORT0(name, version) ALWAYS_RAPORT1(name, version)
#define ALWAYS_RAPORT1(name, version) X(name, version)
#endif

#define ITEM(name, version, x) ALWAYS_RAPORT##x(name, version)

"""


def print_x_macro(ncs_dir_path, essential_modules, west_module_list):
    result = "// module_path, version, always_raport\n//define macro X(name, version) to operate on Xmacro\n"
    result += "#define SIDEWALK_VERSION_COMPONENTS "

    for path, hash in west_module_list():

        describe_cmd = subprocess.run(["git", "describe", "--always", "--dirty"],
                                      cwd=os.path.join(ncs_dir_path, path),  capture_output=True)
        if describe_cmd.returncode != 0:
            version = hash[:7] + "-suspicious"
        else:
            version = describe_cmd.stdout.decode("utf-8").strip()

        result += f"\\\n\tITEM(\"{path}\", \"{version}\", {int(path in essential_modules)})"
    return result + '\n'


def component_name_repo():
    return """
#define X(name, version) name,
const char * const sidewalk_version_component_name[] = {SIDEWALK_VERSION_COMPONENTS};
#undef X

"""


def versions_repo():
    return """
#define X(name, version) version,
const char * const sidewalk_version_component[] = {SIDEWALK_VERSION_COMPONENTS};
#undef X

"""


def helper_variables(ncs_dir_path, get_last_common_commit_with_upstream):
    return "const size_t sidewalk_version_component_count = sizeof(sidewalk_version_component)/sizeof(*sidewalk_version_component);\n" + \
        f"const char * const sidewalk_version_common_commit = \"{get_last_common_commit_with_upstream(ncs_dir_path)}\";\n"


def build_time():
    from datetime import datetime, timezone
    return f"const char * const build_time_stamp = \"{str(datetime.now(timezone.utc))}\";\n"


file_output = ""
file_output += print_warning_header()
file_output += print_includes()
file_output += x_macro_always_raport_swith()
file_output += print_x_macro(NCS_DIR, ESSENTIAL_MODULES, west_module_list)
file_output += component_name_repo()
file_output += versions_repo()
file_output += helper_variables(NCS_DIR, get_last_common_commit_with_upstream)
file_output += build_time()
print(file_output)
