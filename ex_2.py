from pydriller import Repository, Git
import json
import glob
import lizard


def get_all_java_files(path):
    """
    Get all java files in a given directory.
    :param path: path of the directory
    :return: a list of java files
    """
    return glob.glob(path + "/**/*.java", recursive=True)

def get_cyclomatic_complexity(file_list):
    """
    Get the cyclomatic complexity of each entity in a given list.
    :param l: list of entities
    :return: a list of tuples (entity, cyclomatic complexity)
    """
    result = {}
    for file in file_list:
        result[file.split("\\")[-1]] = lizard.analyze_file(file).average_cyclomatic_complexity
        print(f"File {file.split("\\")[-1]} has cyclomatic complexity {result[file.split('\\')[-1]]}")
    return result

def get_lines_of_code(file_list):
    """
    Get the lines of code of each entity in a given list.
    :param l: list of entities
    :return: a list of tuples (entity, lines of code)
    """
    result = {}
    for file in file_list:
        result[file.split("\\")[-1]] = lizard.analyze_file(file).nloc
        print(f"File {file.split('\\')[-1]} has {result[file.split('\\')[-1]]} lines of code")
    return result

def get_indentation_based_complexity(file_list):
    """
    Get the indentation based complexity of each entity in a given list.
    :param l: list of entities
    :return: a list of tuples (entity, indentation based complexity)
    """
    result = {}
    for file in file_list:
        result[file.split("\\")[-1]] = compute_indentation_based_complexity(file)
        print(f"File {file.split('\\')[-1]} has indentation based complexity {result[file.split('\\')[-1]]}")
    return result

def compute_indentation_based_complexity(file):
    with open(file, "r", encoding="utf8") as f:
        lines = f.readlines()
    indentation_based_complexity = 0
    for line in lines:
        indentation_based_complexity += line.count("    ")
    return indentation_based_complexity

def get_number_of_code_changes(json):
    """
    Get the number of code changes of each entity in a given list.
    :param l: list of entities
    :return: a list of tuples (entity, number of code changes)
    """
    result = {}
    for file in json:
        if not file.endswith(".java"):
            continue
        result[file.split("\\")[-1]] = json[file]["num of revisions"]
        print(f"File {file.split('\\')[-1]} has {result[file.split('\\')[-1]]} number of code changes")
    return result

if __name__ == "__main__":
    path = "./kafka"
    java_files = get_all_java_files(path)
    cyclomatic_complexity = get_cyclomatic_complexity(java_files)
    lines_of_code = get_lines_of_code(java_files)
    json_ = json.load(open("ex_1_result.json", "r"))
    number_of_code_changes = get_number_of_code_changes(json_)
    indentation_based_complexity = get_indentation_based_complexity(java_files)