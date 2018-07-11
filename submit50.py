#!/usr/bin/env python3

import argparse
import gettext
import logging
import pkg_resources
import re
import readline
import shutil
import sys
import textwrap
import traceback

import push50
import requests
import termcolor

# Internationalization
gettext.install("submit50", pkg_resources.resource_filename("submit50", "locale"))


class Error(Exception):
    pass


def check_announcements():
    """Check for any announcements from cs50.me, raise Error if so"""
    res = requests.get("https://cs50.me/status/submit50")  # TODO change this to submit50.io!
    if res.status_code == 200 and res.text.strip():
        raise Error(res.text.strip())


def check_version():
    """Check that submit50 is the latest version according to submit50.io"""
    # retrieve version info
    res = requests.get("https://cs50.me/versions/submit50")  # TODO change this to submit50.io!
    if res.status_code != 200:
        raise Error(_("You have an unknown version of submit50. "
                      "Email sysadmins@cs50.harvard.edu!"))

    # check that latest version == version installed
    required_required = pkg_resources.parse_version(res.text.strip())
    # local_version = pkg_resources.parse_version(pkg_resources.get_distribution("submit50").version)

    # TODO re-enable
    # if required_version > local_version:
    #    raise Error(_("You have an old version of submit50. "
    #                  "Run update50, then re-run {}!".format(org)))


def cprint(text="", color=None, on_color=None, attrs=None, **kwargs):
    """Colorizes text (and wraps to terminal's width)."""
    # assume 80 in case not running in a terminal
    columns, lines = shutil.get_terminal_size()
    if columns == 0:
        columns = 80  # because get_terminal_size's default fallback doesn't work in pipes

    # print text
    termcolor.cprint(textwrap.fill(text, columns, drop_whitespace=False),
                     color=color, on_color=on_color, attrs=attrs, **kwargs)

# example check50 call


def prompt(included, excluded):
    if included:
        cprint(_("Files that will be submitted:"), "green")
        for file in included:
            cprint("./{}".format(file), "green")
    else:
        raise Error(_("No files in this directory are expected for submission."))

    # files that won't be submitted
    if excluded:
        cprint(_("Files that won't be submitted:"), "yellow")
        for other in excluded:
            cprint("./{}".format(other), "yellow")

    # prompt for honesty
    readline.clear_history()
    try:
        answer = input(_("Keeping in mind the course's policy on academic honesty, "
                         "are you sure you want to submit these files (yes/no)? "))
    except EOFError:
        answer = None
        print()
    if not answer or not re.match("^\s*(?:y|yes)\s*$", answer, re.I):
        return False

    return True


def excepthook(type, value, tb):
    """Report an exception."""
    if (issubclass(type, Error) or issubclass(type, push50.Error)) and str(value):
        cprint(str(value), "yellow")
    else:
        cprint(_("Sorry, something's wrong! Let sysadmins@cs50.harvard.edu know!"), "yellow")

    if excepthook.verbose:
        traceback.print_exception(type, value, tb)

    cprint(_("Submission cancelled."), "red")


excepthook.verbose = True

class LogoutAction(argparse.Action):
    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help=_("logout of submit50")):
        super().__init__(option_strings, dest=dest, nargs=0, default=default, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            push50.logout()
        except Error:
            raise Error(_("failed to logout")) from None
        else:
            cprint(_("logged out successfully"), "green")
        parser.exit()


def main():
    sys.excepthook = excepthook

    # define command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--logout", action=LogoutAction)
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        help=_("show commands being executed"))
    parser.add_argument("slug", help=_(
        "prescribed identifier of work to submit"))

    args = parser.parse_args()

    excepthook.verbose = args.verbose
    if args.verbose:
        logging.basicConfig(level="INFO")
        push50.ProgressBar.DISABLED = True

    check_announcements()
    check_version()

    push50.push(org="submit50", slug=args.slug, tool="submit50", prompt=prompt)


if __name__ == "__main__":
    main()
