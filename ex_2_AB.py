from pydriller import Repository, Git, ModificationType
import glob
import lizard
import json

repo_base = './kafka/'

entities = glob.glob('./**/*.java', root_dir=repo_base, recursive=True)

with open('ex_1_results_ab.json') as file:
    file_contents = file.read()

parsed_json = json.loads(file_contents)


def compute_ic(f):
    counter = 0
    ic_value = 0
    try:
        with open(".\\kafka\\trogdor\\src\\test\\java\\org\\apache\\kafka\\trogdor\\common\\StringExpanderTest.java") as of:
            counter += 1
            whitespace = 0
            for line in of.readlines():
                for c in line:
                    if c == " ":
                        whitespace += 1
                        if whitespace == 4:
                            ic_value += 1
                            whitespace = 0
                    elif c == "\t":
                        ic_value += 1
    except:
        print("Failed to read file {}".format(f))
    if counter == 0:
        return 0
    else:
        return ic_value / counter


results = {}

for index, entity in enumerate(entities):
    if index % 100 == 0:
        print("{} from {} analyzed".format(index, len(entities)))
    analysis = lizard.analyze_file(repo_base + entity)
    cc = analysis.average_cyclomatic_complexity
    loc = analysis.nloc
    entityName = entity.replace('.\\', '')
    if entityName in parsed_json:
        ncc = parsed_json[entityName]["num_of_revisions"]
    else:
        print("{} does not exists in json".format(entityName))
        ncc = 0
    ic = compute_ic(".\\kafka\\" + entityName)
    results[entityName] = {"cc": cc, "loc": loc, "ncc": ncc, "ic": ic}

# TODO: FIGURE

