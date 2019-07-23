from git import Repo
import os
import sys

from .autobranch import Autobranch


class Submit:
    def handler(self, args):
        ab = Autobranch()
        repo = Repo(os.getcwd())
        commits = list(repo.iter_commits(args.revs))
        created_branches = ab.run(repo, commits)
        if len(created_branches) == 0:
            print("Exiting because no branches were created.")
            sys.exit(0)

        origin = repo.remote()
        assert origin.exists()

        results = origin.push(created_branches, **{"force-with-lease": True})
        assert results is not None
        # TODO: Maybe check error bit here.

    def register_command(self, parser):
        submit_parser = parser.add_parser(
            "submit", help="Uploads branches by pushing to remotes.", aliases="s"
        )
        submit_parser.add_argument(
            "--revs",
            default="develop..HEAD",
            help="Rev specifier of commits to look at.",
        )
        submit_parser.set_defaults(handler=self.handler)
