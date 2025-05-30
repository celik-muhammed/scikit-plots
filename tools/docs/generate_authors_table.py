"""
This script generates an html table of contributors, with names and avatars.
The list is generated from scikit-plots's teams on GitHub, plus a small number
of hard-coded contributors.

The table should be updated for each new inclusion in the teams.
Generating the table requires admin rights.
"""

# Authors: The scikit-plots developers
# SPDX-License-Identifier: BSD-3-Clause

import getpass
import os
import sys
import time
from os import path
from pathlib import Path

import requests

if not (os.getenv("GITHUB_USER") or os.getenv("GITHUB_TOKEN")):
    print("Can be use env variable: 'GITHUB_USER', 'GITHUB_TOKEN'")
    print("user:", file=sys.stderr)
    user = input()
    token = getpass.getpass("access token:\n")
else:
    user = os.getenv("GITHUB_USER")
    token = os.getenv("GITHUB_TOKEN")

auth = (user, token)

LOGO_URL = "https://avatars2.githubusercontent.com/u/365630?v=4"
REPO_FOLDER = Path(path.abspath(__file__)).parent.parent.parent
print(REPO_FOLDER)


def get(url):
    for sleep_time in [10, 30, 0]:
        reply = requests.get(url, auth=auth)
        api_limit = (
            "message" in reply.json()
            and "API rate limit exceeded" in reply.json()["message"]
        )
        if not api_limit:
            break
        print("API rate limit exceeded, waiting..")
        time.sleep(sleep_time)

    reply.raise_for_status()
    return reply


def get_contributors():
    """Get the list of contributor profiles. Require admin rights."""
    entry_point = "https://api.github.com/orgs/scikit-plots/"

    # get members of scikit-plots on GitHub
    members = []
    for page in [1, 2, 3]:  # 30 per page
        reply = get(f"{entry_point}members?page={page}")
        members.extend(reply.json())

    # get core devs and contributor experience team
    comm_team = []
    contributor_experience_team = []
    documentation_team = []
    core_devs = []
    comm_team_slug = "communication-team"
    contributor_experience_team_slug = "contributor-experience-team"
    core_devs_slug = "core-devs"
    documentation_team_slug = "documentation-team"

    for team_slug, lst in zip(
        (
            comm_team_slug,
            contributor_experience_team_slug,
            core_devs_slug,
            documentation_team_slug,
        ),
        (comm_team, contributor_experience_team, core_devs, documentation_team),
    ):
        for page in [1, 2]:  # 30 per page
            reply = get(f"{entry_point}teams/{team_slug}/members?page={page}")
            lst.extend(reply.json())

    # keep only the logins
    members = set(c["login"] for c in members)
    comm_team = set(c["login"] for c in comm_team)
    contributor_experience_team = set(c["login"] for c in contributor_experience_team)
    core_devs = set(c["login"] for c in core_devs)
    documentation_team = set(c["login"] for c in documentation_team)

    # add missing contributors with GitHub accounts
    # members |= {"dubourg", "mbrucher", "thouis", "jarrodmillman"}
    # add missing contributors without GitHub accounts
    # members |= {"Angel Soler Gollonet"}
    # remove CI bots
    members -= {"sklearn-ci", "sklearn-wheels", "sklearn-lgtm"}
    contributor_experience_team -= (
        core_devs  # remove ogrisel from contributor_experience_team
    )

    emeritus = (
        members
        - comm_team
        - contributor_experience_team
        - core_devs
        - documentation_team
    )

    # hard coded
    comm_team -= set(
        [
            # in the comm team but not on the web page
            "muhammed celik"
        ]
    )
    emeritus_comm_team = set(["muhammed celik"])
    emeritus_contributor_experience_team = set(["muhammed celik"])
    # Up-to-now, we can subtract the team emeritus from the original emeritus
    emeritus -= emeritus_comm_team | emeritus_contributor_experience_team

    # get profiles from GitHub
    comm_team = [get_profile(login) for login in comm_team]
    emeritus_comm_team = [get_profile(login) for login in emeritus_comm_team]
    contributor_experience_team = [
        get_profile(login) for login in contributor_experience_team
    ]
    emeritus_contributor_experience_team = [
        get_profile(login) for login in emeritus_contributor_experience_team
    ]
    core_devs = [get_profile(login) for login in core_devs]
    emeritus = [get_profile(login) for login in emeritus]
    documentation_team = [get_profile(login) for login in documentation_team]

    # sort by last name
    comm_team = sorted(comm_team, key=key)
    emeritus_comm_team = sorted(emeritus_comm_team, key=key)
    contributor_experience_team = sorted(contributor_experience_team, key=key)
    emeritus_contributor_experience_team = sorted(
        emeritus_contributor_experience_team, key=key
    )
    core_devs = sorted(core_devs, key=key)
    emeritus = sorted(emeritus, key=key)
    documentation_team = sorted(documentation_team, key=key)

    return (
        core_devs,
        emeritus,
        contributor_experience_team,
        emeritus_contributor_experience_team,
        comm_team,
        emeritus_comm_team,
        documentation_team,
    )


def get_profile(login):
    """Get the GitHub profile from login"""
    print("get profile for %s" % (login,))
    try:
        profile = get("https://api.github.com/users/%s" % login).json()
    except requests.exceptions.HTTPError:
        return dict(name=login, avatar_url=LOGO_URL, html_url="")

    if profile["name"] is None:
        profile["name"] = profile["login"]

    # fix missing names
    missing_names = {
        # "bthirion": "Bertrand Thirion",
        # "dubourg": "Vincent Dubourg",
        # "Duchesnay": "Edouard Duchesnay",
        # "Lars": "Lars Buitinck",
        # "MechCoder": "Manoj Kumar",
    }
    if profile["name"] in missing_names:
        profile["name"] = missing_names[profile["name"]]

    return profile


def key(profile):
    """Get a sorting key based on the lower case last name, then firstname"""
    components = profile["name"].lower().split(" ")
    return " ".join([components[-1]] + components[:-1])


def generate_table(contributors):
    lines = [
        ".. raw :: html\n",
        "    <!-- Generated by tools/docs/generate_authors_table.py -->",
        '    <div class="sk-authors-container">',
        "    <style>",
        "      img.avatar {border-radius: 6px;}",
        "    </style>",
    ]
    for contributor in contributors:
        lines.append("    <div>")
        lines.append(
            "    <a href='%s'><img src='%s' class='avatar' /></a> <br />"
            % (contributor["html_url"], contributor["avatar_url"])
        )
        lines.append("    <p>%s</p>" % (contributor["name"],))
        lines.append("    </div>")
    lines.append("    </div>")
    return "\n".join(lines) + "\n"


def generate_list(contributors):
    lines = []
    for contributor in contributors:
        lines.append("- %s" % (contributor["name"],))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    (
        core_devs,
        emeritus,
        contributor_experience_team,
        emeritus_contributor_experience_team,
        comm_team,
        emeritus_comm_team,
        documentation_team,
    ) = get_contributors()

    with open(
        REPO_FOLDER / "docs/source/project/teams" / "communication_team.rst",
        "w+",
        encoding="utf-8",
    ) as rst_file:
        rst_file.write(generate_table(comm_team))
    with open(
        REPO_FOLDER / "docs/source/project/teams" / "communication_team_emeritus.rst",
        "w+",
        encoding="utf-8",
    ) as rst_file:
        rst_file.write(generate_list(emeritus_comm_team))

    with open(
        REPO_FOLDER / "docs/source/project/teams" / "contributor_experience_team.rst",
        "w+",
        encoding="utf-8",
    ) as rst_file:
        rst_file.write(generate_table(contributor_experience_team))
    with open(
        (
            REPO_FOLDER
            / "docs/source/project/teams"
            / "contributor_experience_team_emeritus.rst"
        ),
        "w+",
        encoding="utf-8",
    ) as rst_file:
        rst_file.write(generate_list(emeritus_contributor_experience_team))

    with open(
        REPO_FOLDER / "docs/source/project/teams" / "maintainers.rst",
        "w+",
        encoding="utf-8",
    ) as rst_file:
        rst_file.write(generate_table(core_devs))
    with open(
        REPO_FOLDER / "docs/source/project/teams" / "maintainers_emeritus.rst",
        "w+",
        encoding="utf-8",
    ) as rst_file:
        rst_file.write(generate_list(emeritus))

    with open(
        REPO_FOLDER / "docs/source/project/teams" / "documentation_team.rst",
        "w+",
        encoding="utf-8",
    ) as rst_file:
        rst_file.write(generate_table(documentation_team))
