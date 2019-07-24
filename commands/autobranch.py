from git import Repo
import re
import textwrap
from typing import List
import os
import sys

REPO_DIR = "/Users/bshin/software"
EMAIL = "brian@brishin.com"
SAFETY_LIMIT = 30


def _parse_git_message(message):
    match = re.match(r"\[([^\]\s]+)\]\[([^\]\s]+)\]", message)
    if match is None:
        simple_match = re.match(r"\[([^\]\s]+)\]", message)
        if simple_match is None:
            return None
        return simple_match.group(1)
    return match.group(1) + match.group(2)


def _short_description(commit, info_message=None):
    git = commit.repo.git
    short_rev = git.rev_parse("--short", commit.hexsha)
    message = commit.message.splitlines()[0]
    short_message = textwrap.shorten(message, width=60, placeholder="...")

    description = f"{short_rev} {short_message}"
    if info_message is not None:
        description += info_message
    return description


def _create_or_update_branch(commit, branch_name):
    if branch_name not in commit.repo.heads:
        branch = commit.repo.create_head(branch_name)
    else:
        branch = commit.repo.heads[branch_name]

    branch.set_commit(commit)
    return branch


class Autobranch:
    def handler(self, args):
        repo = Repo(os.getcwd())
        commits = list(repo.iter_commits(args.revs))
        self.run(repo, commits, **vars(args))

    def run(self, repo, commits, **kwargs) -> List[str]:
        commits.reverse()
        print(f"Found {len(commits)} commits.")
        if len(commits) > 30 and not kwargs.get('skip', False):
            print("Stopping because number of commits exceeded the safety limit.")
            sys.exit(1)

        def parse_commit(commit):
            if commit.author.email != EMAIL:
                print(_short_description(commit, ": Skipped due to author mismatch."))
                return (commit, None)

            message = commit.message.splitlines()[0]
            branch_name = _parse_git_message(message)
            return (commit, branch_name)

        parsed_commits = [parse_commit(c) for c in commits]

        pending_branches = []
        current_branch = None
        for idx, parsed_commit in enumerate(parsed_commits):
            commit, branch_name = parsed_commit
            if branch_name is not None:
                current_branch = branch_name

            if current_branch is None:
                if kwargs.get('skip', False):
                    continue

                print("Expected commit to have a branch name")
                sys.exit(1)

            if idx + 1 >= len(parsed_commits):
                # End of commits, always apply the current one.
                pending_branches.append((commit, current_branch))
                current_branch = None
                continue

            if parsed_commits[idx + 1][1] is not None:
                # Next commit has a branch, apply the current one.
                pending_branches.append((commit, current_branch))
                current_branch = None
                continue
            else:
                # Next commit doesn't have a branch, continue with current_branch.
                continue

        created_branches = []
        for pending_branch in pending_branches:
            commit, branch_name = pending_branch
            branch = _create_or_update_branch(commit, branch_name)
            print(_short_description(commit, f" -> {branch_name}"))
            created_branches.append(branch)

        last_branch = created_branches[-1]
        if repo.active_branch != last_branch:
            last_branch.checkout()

        return created_branches

    def register_command(self, parser):
        ab_parser = parser.add_parser(
            "autobranch",
            help="Automatically update branches based on commit title.",
            aliases=["ab"],
        )
        ab_parser.add_argument(
            "--revs",
            default="develop..HEAD",
            help="Rev specifier of commits to look at.",
        )
        ab_parser.add_argument(
            "--skip",
            action="store_true",
            help="If set, skips any unknown commits instead of failing.",
        )
        ab_parser.set_defaults(handler=self.handler)
