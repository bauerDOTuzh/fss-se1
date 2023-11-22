import json
import os

from pydriller import Repository, Git, ModificationType
import datetime as dt

path = "./kafka"
tagOld = "3.5.1"
since = dt.datetime(2023, 7, 14, 18, 51, 0)
tagCurrent = "3.6.0"
to = dt.datetime(2023, 9, 29, 6, 56, 0)

repo = Git(path)

entities = repo.files()


class Author:
    def __init__(self):
        self.added = 0
        self.removed = 0
        self.total = 0


class ChangedFile:
    def __init__(self):
        self.num_of_revisions = 0
        self.authors = {}


revisions = {}

for entity in entities:
    p = os.path.relpath(entity, path)
    revisions[p] = ChangedFile()

for commit in Repository(path, since=since, to=to).traverse_commits():
    for modification in commit.modified_files:
        if modification.new_path in revisions:
            revision = revisions[modification.new_path]
            revision.num_of_revisions += 1
            if commit.author.name in revision.authors:
                author = revision.authors[commit.author.name]
            else:
                author = Author()
                revision.authors[commit.author.name] = author

            author.added += commit.insertions
            author.removed += commit.deletions
            author.total += commit.lines


class Encoder(json.JSONEncoder):
    def default(self, obj):
        return obj.__dict__


with open("./ex_1_results_ab.json", "w") as f:
    f.write(json.dumps(revisions, cls=Encoder, indent=4))

print("Saved as ./ex_1_results_ab.json")

