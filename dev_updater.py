#!/usr/bin/env python3
# Work with Python 3.7+

import os
import json
import shutil

from git import Repo
from git import Git

PROJECT_PATH = "/root/SimplioDevelopmentProgress"


with open("dev-diary.json") as data_file:
    complete_list = json.load(data_file)
    truncated_list = complete_list[-10:]

# make sure .git folder is properly configured
PATH_OF_GIT_REPO = PROJECT_PATH + "/.git"
COMMIT_MESSAGE = "Last work at " + complete_list[-1]["created_at"][:-7]
GIT_SSH_IDENTITY_FILE = os.path.expanduser('~/.ssh/id_ed25519')
GIT_SSH_CMD = f"ssh -i {GIT_SSH_IDENTITY_FILE}"


def git_push():
    try:
        repo = Repo(PATH_OF_GIT_REPO)
        repo.config_writer().set_value("user", "name", "ciripel").release()
        repo.config_writer().set_value(
            "user", "email", "nedelcu.alexandru@yahoo.com").release()
        repo.git.add(update=True)
        repo.git.commit(m=COMMIT_MESSAGE)
        origin = repo.remote(name="origin")
        with Git().custom_environment(GIT_SSH_COMMAND=GIT_SSH_CMD):
            origin.push()
        sha = repo.head.object.hexsha
        print(f"On branch master.\nPushed commit {sha}")
    except Exception as exception:
        print(
            f"On branch master.\nYour branch is up to date with 'origin/master'.\nNothing to commit, working tree clean.\n {exception}"
        )


def description(the_list, index):
    if the_list[index]["author"] == "GitHub":
        try:
            return "[" + the_list[index]["embed_0"]["title"] + "](" + the_list[index]["embed_0"]["url"] + ")"
        except KeyError:
            return "_No Description_"
    else:
        return ""


def commit(the_list, index):
    if the_list[index]["author"] == "GitHub":
        try:
            raw_commits = the_list[index]["embed_0"]["description"]
            raw_commits = raw_commits.replace("\n", "<br>")
            raw_commits = raw_commits.replace("`", "")
            return raw_commits
        except KeyError:
            return "_No Commits_"
    else:
        return ""


def dev_update():
    shutil.copy("dev-diary.json", PROJECT_PATH)
    file = open(PROJECT_PATH + "/Complete_list.md", "w")
    total_commits = len(complete_list)
    message = """
### Simplio Development Progress - Complete history

Here is the complete list of all the commits to the projects we are currently working since 10/09/2021.

| Push Time | Description | Commits |
| --- | --- | --- |
{table}

_You can see more details and commits in our [Discord](https://discord.gg/aKhjuwZmdP) in **#dev-diary** channel._
""".format(
        table="\n".join(
            "| <sub>{}</sub> | <sub>{}</sub> | <sub>{}</sub> |".format(
                complete_list[total_commits - i - 1]["created_at"][:-7],
                description(complete_list, total_commits - i - 1),
                commit(complete_list, total_commits - i - 1),
            )
            for i in range(total_commits)
        )
    )
    file.write(message)
    file.close()

    total_commits = len(truncated_list)
    file = open(PROJECT_PATH + "/README.md", "w")
    message = """
### Simplio Development Progress

Here are the last 10 pushes to the projects we are currently working.

There is a total of {total_commits} commits since 10/09/2021. You can see the complete history in
 [Complete_list.md](Complete_list.md) file.

| Push Time | Description | Commits |
| --- | --- | --- |
{table}

_You can see more details and commits in our [Discord](https://discord.gg/aKhjuwZmdP) in **#dev-diary** channel._
""".format(
        total_commits=len(complete_list),
        table="\n".join(
            "| <sub>{}</sub> | <sub>{}</sub> | <sub>{}</sub> |".format(
                truncated_list[total_commits - i - 1]["created_at"][:-7],
                description(truncated_list, total_commits - i - 1),
                commit(truncated_list, total_commits - i - 1),
            )
            for i in range(total_commits)
        ),
    )
    file.write(message)
    file.close()
    git_push()


if __name__ == "__main__":
    dev_update()
