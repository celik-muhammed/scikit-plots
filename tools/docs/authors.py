#!/usr/bin/env python
"""
List the authors who contributed within a given revision interval::

    python tools/authors.py REV1..REV2

`REVx` being a commit hash.

To change the name mapping, edit .mailmap on the top-level of the
repository.

"""
# Author: Pauli Virtanen <pav@iki.fi>. This script is in the public domain.

import argparse
import re
import sys
import os
import subprocess
import collections

stdout_b = sys.stdout.buffer
MAILMAP_FILE = os.path.join(os.path.dirname(__file__), "../..", ".mailmap")


def main():
    p = argparse.ArgumentParser(__doc__.strip())
    p.add_argument("range", help=argparse.SUPPRESS)
    p.add_argument("-d", "--debug", action="store_true", help="print debug output")
    p.add_argument("-n", "--new", action="store_true", help="print debug output")
    options = p.parse_args()

    try:
        rev1, rev2 = options.range.split("..")
    except ValueError:
        p.error("argument is not a revision range")

    NAME_MAP = load_name_map(MAILMAP_FILE)

    # Analyze log data
    all_authors = set()
    authors = collections.Counter()

    def analyze_line(line, names, disp=False):
        line = line.strip().decode("utf-8")

        # Check the commit author name
        m = re.match("^@@@([^@]*)@@@", line)
        if m:
            name = m.group(1)
            line = line[m.end() :]
            name = NAME_MAP.get(name, name)
            if disp:
                if name not in names:
                    stdout_b.write((f"    - Author: {name}\n").encode())
            names.update((name,))

        # Look for "thanks to" messages in the commit log
        m = re.search(
            r"([Tt]hanks to|[Cc]ourtesy of|Co-authored-by:) "
            r"([A-Z][A-Za-z]*? [A-Z][A-Za-z]*? [A-Z][A-Za-z]*|[A-Z][A-Za-z]*? [A-Z]\."
            r" [A-Z][A-Za-z]*|[A-Z][A-Za-z ]*? [A-Z][A-Za-z]*|[a-z0-9]+)($|\.| )",
            line,
        )
        if m:
            name = m.group(2)
            if name not in ("this",):
                if disp:
                    stdout_b.write(f"    - Log   : {line.strip().encode()}\n")
                name = NAME_MAP.get(name, name)
                names.update((name,))

            line = line[m.end() :].strip()
            line = re.sub(r"^(and|, and|, ) ", "Thanks to ", line)
            analyze_line(line.encode("utf-8"), names)

    # Find all authors before the named range
    for line in git.pipe("log", "--pretty=@@@%an@@@%n@@@%cn@@@%n%b", f"{rev1}"):
        analyze_line(line, all_authors)

    # Find authors in the named range
    for line in git.pipe("log", "--pretty=@@@%an@@@%n@@@%cn@@@%n%b", f"{rev1}..{rev2}"):
        analyze_line(line, authors, disp=options.debug)

    # Sort
    def name_key(fullname):
        m = re.search(" [a-z ]*[A-Za-z-]+$", fullname)
        if m:
            forename = fullname[: m.start()].strip()
            surname = fullname[m.start() :].strip()
        else:
            forename = ""
            surname = fullname.strip()
        if surname.startswith("van der "):
            surname = surname[8:]
        if surname.startswith("de "):
            surname = surname[3:]
        if surname.startswith("von "):
            surname = surname[4:]
        return (surname.lower(), forename.lower())

    # generate set of all new authors
    if vars(options)["new"]:
        new_authors = set(authors.keys()).difference(all_authors)
        n_authors = list(new_authors)
        n_authors.sort(key=name_key)
        # Print some empty lines to separate
        stdout_b.write(b"\n\n")
        for author in n_authors:
            stdout_b.write((f"- {author}\n").encode())
        # return for early exit so we only print new authors
        return

    try:
        authors.pop("GitHub")
    except KeyError:
        pass
    # Order by name. Could order by count with authors.most_common()
    authors = sorted(authors.items(), key=lambda i: name_key(i[0]))

    # Print
    stdout_b.write(
        b"""
Authors
=======

"""
    )

    for author, count in authors:
        # remove @ if only GH handle is available
        author_clean = author.strip("@")

        if author in all_authors:
            stdout_b.write((f"* {author_clean} ({count})\n").encode())
        else:
            stdout_b.write((f"* {author_clean} ({count}) +\n").encode())

    stdout_b.write(
        (
            f"""
    A total of {len(authors)} people contributed to this release.
    People with a "+" by their names contributed a patch for the first time.
    This list of names is automatically generated, and may not be fully complete.
    """
        ).encode()
    )

    stdout_b.write(
        b"\nNOTE: Check this list manually! It is automatically generated "
        b"and some names\n      may be missing.\n"
    )


def load_name_map(filename):
    name_map = {}

    with open(filename, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue

            m = re.match(r"^(.*?)\s*<(.*?)>(.*?)\s*<(.*?)>\s*$", line)
            if not m:
                print(f"Invalid line in .mailmap: '{line!r}'", file=sys.stderr)
                sys.exit(1)

            new_name = m.group(1).strip()
            old_name = m.group(3).strip()

            if old_name and new_name:
                name_map[old_name] = new_name

    return name_map


# ------------------------------------------------------------------------------
# Communicating with Git
# ------------------------------------------------------------------------------


class Cmd:
    executable = None

    def __init__(self, executable):
        self.executable = executable

    def _call(self, command, args, kw, repository=None, call=False):
        cmd = [self.executable, command] + list(args)
        cwd = None

        if repository is not None:
            cwd = os.getcwd()
            os.chdir(repository)

        try:
            if call:
                return subprocess.call(cmd, **kw)
            else:
                return subprocess.Popen(cmd, **kw)
        finally:
            if cwd is not None:
                os.chdir(cwd)

    def __call__(self, command, *a, **kw):
        ret = self._call(command, a, {}, call=True, **kw)
        if ret != 0:
            raise RuntimeError(f"{self.executable} failed")

    def pipe(self, command, *a, **kw):
        stdin = kw.pop("stdin", None)
        p = self._call(
            command, a, dict(stdin=stdin, stdout=subprocess.PIPE), call=False, **kw
        )
        return p.stdout

    def read(self, command, *a, **kw):
        p = self._call(command, a, dict(stdout=subprocess.PIPE), call=False, **kw)
        out, err = p.communicate()
        if p.returncode != 0:
            raise RuntimeError(f"{self.executable} failed")
        return out

    def readlines(self, command, *a, **kw):
        out = self.read(command, *a, **kw)
        return out.rstrip("\n").split("\n")

    def test(self, command, *a, **kw):
        ret = self._call(
            command,
            a,
            dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE),
            call=True,
            **kw,
        )
        return ret == 0


git = Cmd("git")

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
