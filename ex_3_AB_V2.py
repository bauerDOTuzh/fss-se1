import concurrent.futures
import datetime
import json
import os
import time
from collections import deque

import numpy as np
import datetime as dt

import tzdata
from pydriller import Repository, Git
from tqdm import tqdm

from timeit import default_timer
from scipy.sparse import csc_matrix, vstack


def create_commit_vector(commit, files):
    modifications = [file.new_path for file in commit.modified_files]
    v = np.zeros((1, len(files)), dtype=int)

    for m in modifications:
        if m in files:
            index = files.index(m)
            v[0][index] = 1
    v_sparse = csc_matrix(v)
    return {"time": commit.committer_date,
            "modifications": v_sparse}


def convert_to_format(result_dict, matrix, idx, debug):
    for row, col in zip(*matrix.nonzero()):
        if row == col:
            continue
        val = matrix[row, col]
        key = str(row) + "_" + str(col)
        if key not in result_dict:
            result_dict[key] = {"file_pair": [entities[row], entities[col]],
                                    "coupled_commits": [
                                        {
                                            "time_window": 24,
                                            "commit_count": 0
                                        },
                                        {
                                            "time_window": 48,
                                            "commit_count": 0
                                        },
                                        {
                                            "time_window": 72,
                                            "commit_count": 0
                                        },
                                        {
                                            "time_window": 168,
                                            "commit_count": 0
                                        }
                                    ]}
        else:
            pass
        result_dict[key]["coupled_commits"][idx]["commit_count"] = int(val)


if __name__ == '__main__':

    start = default_timer()

    path = "./kafka"
    since = dt.datetime(2023, 9, 1, 0, 0, 0)

    entities = [os.path.relpath(entity, path) for entity in Git(path).files()]

    numberOfFiles = len(entities)

    commits = [c for c in Repository(path).traverse_commits()]

    global_progress = tqdm(unit="commit", total=len(commits), desc="Computing temporal coupling matrix", position=0,
                           leave=False)

    time_frame = deque()

    avgLength = 0
    update_v_24 = []
    update_w_24 = []
    update_v_48 = []
    update_w_48 = []
    update_v_72 = []
    update_w_72 = []
    update_v_168 = []
    update_w_168 = []

    for commit in commits:
        c1 = create_commit_vector(commit, entities)
        inside168Window = False
        inside72Window = False
        inside48Window = False
        inside24Window = False
        i = 0
        avgLength += 1 / len(commits) * len(time_frame)
        while i < len(time_frame):
            c2 = time_frame[i]
            if not inside24Window:
                delta = c1["time"] - c2["time"]
            if inside168Window or delta <= datetime.timedelta(hours=168):
                f1 = c1["modifications"]
                f2 = c2["modifications"]
                update_v_168.append(f1)
                update_w_168.append(f2)
                inside168Window = True
                if inside72Window or delta <= datetime.timedelta(hours=72):
                    update_v_72.append(f1)
                    update_w_72.append(f2)
                    inside72Window = True
                    if inside48Window or delta <= datetime.timedelta(hours=48):
                        update_v_48.append(f1)
                        update_w_48.append(f2)
                        inside48Window = True
                        if inside24Window or delta <= datetime.timedelta(hours=24):
                            update_v_24.append(f1)
                            update_w_24.append(f2)
                            inside24Window = True
                i += 1
            else:
                time_frame.popleft()

        time_frame.append(c1)
        global_progress.update(1)

    global_progress.close()

    math_total = 4
    math_progress = tqdm(unit="commit", total=math_total, desc="Computing temporal coupling matrix", position=0,
                           leave=False)

    v_matrix24 = vstack(update_v_24)
    w_matrix24 = vstack(update_w_24)
    v_matrix48 = vstack(update_v_48)
    w_matrix48 = vstack(update_w_48)
    v_matrix72 = vstack(update_v_72)
    w_matrix72 = vstack(update_w_72)
    v_matrix168 = vstack(update_v_168)
    w_matrix168 = vstack(update_w_168)
    temporal_coupling_matrix_24h = v_matrix24.transpose() @ w_matrix24
    math_progress.update(1)
    temporal_coupling_matrix_48h = v_matrix48.transpose() @ w_matrix48
    math_progress.update(1)
    temporal_coupling_matrix_72h = v_matrix72.transpose() @ w_matrix72
    math_progress.update(1)
    temporal_coupling_matrix_168h = v_matrix168.transpose() @ w_matrix168
    math_progress.update(1)

    math_progress.close()

    print("avg: {}".format(avgLength))

    temporal_coupling = {}

    convert_to_format(temporal_coupling, temporal_coupling_matrix_24h, 0, "24")
    convert_to_format(temporal_coupling, temporal_coupling_matrix_48h, 1, "48")
    convert_to_format(temporal_coupling, temporal_coupling_matrix_72h, 2, "72")

    convert_to_format(temporal_coupling, temporal_coupling_matrix_168h, 3, "168")

    print("saving")

    with open("./ex_3_AB_results.json", "w") as f:
        json.dump(list(temporal_coupling.values()), f, indent=4)

    duration = default_timer() - start

    print("done in {}sec".format(duration))
