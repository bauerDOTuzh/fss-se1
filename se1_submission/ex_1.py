from pydriller import Repository, Git
import json


def list_all_entities(path, tag):
    """
    List all entities (files and directories) of the latest stable release of a given GitHub repository.
    :param url: URL of the GitHub repository
    :return: a list of all entities
    """
    gr = Git(path)
    commit = gr.get_commit_from_tag(tag)
    gr.checkout(commit.hash)
    return gr.files()


def get_num_revisions_and_authors(file_list, path, from_, to):
    """
    Get the number of revisions and authors of each entity in a given list.
    :param l: list of entities
    :return: a list of tuples (entity, num_revisions, num_authors)
    """
    result = {
        file.split("\\")[-1]: {"num of revisions": 0, "authors": {}} for file in file_list
    }

    gr = Git(path)
    from_commit_date = gr.get_commit_from_tag(from_).committer_date
    to_commit_date = gr.get_commit_from_tag(to).committer_date

    for commit in Repository(path, since=from_commit_date, to=to_commit_date).traverse_commits():
        for file in commit.modified_files:
            filename = file.filename
            if filename not in result:
                continue
            result[filename]["num of revisions"] += 1
            if commit.author.name not in result[filename]["authors"]:
                result[filename]["authors"][commit.author.name] = {
                    "added": commit.insertions,
                    "deleted": commit.deletions,
                    "total": commit.lines,
                }
            else:
                result[filename]["authors"][commit.author.name]["added"] += commit.insertions
                result[filename]["authors"][commit.author.name]["deleted"] += commit.deletions
                result[filename]["authors"][commit.author.name]["total"] += commit.lines
        print("Commit {} finished".format(commit.hash))
    return result


def save_as_json(result, path):
    """
    Save the result as a JSON file.
    :param result: the result to save
    :param path: path of the JSON file
    :return: None
    """
    with open(path, "w") as f:
        json.dump(result, f, indent=4)

    print("Saved as {}".format(path))



if __name__ == "__main__":
    path = "./kafka"
    tag = "3.6.0"
    file_list = list_all_entities(path, tag)
    from_ = "3.5.1"
    result = get_num_revisions_and_authors(file_list, path, from_, tag)
    save_as_json(result, "./ex_1_result.json")
