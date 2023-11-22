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
from scipy.sparse import csc_matrix


def create_commit_vector(commit, files):
    modifications = [file.new_path for file in commit.modified_files]
    v = np.zeros((1, len(files)), dtype=int)

    for m in modifications:
        if m in files:
            index = files.index(m)
            v[0][index] = 1
    v_sparse = csc_matrix(v)
    return {"time": commit.committer_date,
            "modifications": v_sparse,
            "modificationsT": v_sparse.transpose(copy=True)}

def convert_to_format(result_dict, matrix, idx):
    for row, col in zip(*matrix.nonzero()):
        if row == col:
            continue
        val = temporal_coupling_matrix_24h[row, col]
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
            result_dict[key]["coupled_commits"][idx]["commit_count"] = int(val)



if __name__ == '__main__':

    start = default_timer()

    path = "./kafka"
    since = dt.datetime(2023, 9, 1, 0, 0, 0)

    entities = [os.path.relpath(entity, path) for entity in Git(path).files()]

    numberOfFiles = len(entities)

    temporal_coupling_matrix_24h = csc_matrix((numberOfFiles, numberOfFiles), dtype=int)
    temporal_coupling_matrix_48h = csc_matrix((numberOfFiles, numberOfFiles), dtype=int)
    temporal_coupling_matrix_72h = csc_matrix((numberOfFiles, numberOfFiles), dtype=int)
    temporal_coupling_matrix_168h = csc_matrix((numberOfFiles, numberOfFiles), dtype=int)

    commits = [c for c in Repository(path).traverse_commits()]

    global_progress = tqdm(unit="commit", total=len(commits), desc="Computing temporal coupling matrix", position=0,
                           leave=False)

    time_frame = deque()

    for commit in commits:
        c1 = create_commit_vector(commit, entities)
        inside168Window = False
        inside72Window = False
        inside48Window = False
        inside24Window = False
        i = 0
        while i < len(time_frame):
            c2 = time_frame[i]
            if not inside24Window:
                delta = c1["time"] - c2["time"]
            if inside168Window or delta <= datetime.timedelta(hours=168):
                f1T = c1["modificationsT"]
                f2 = c2["modifications"]
                update_matrix = f1T @ f2
                temporal_coupling_matrix_168h += update_matrix
                inside168Window = True
                if inside72Window or delta <= datetime.timedelta(hours=72):
                    temporal_coupling_matrix_72h += update_matrix
                    inside72Window = True
                    if inside48Window or delta <= datetime.timedelta(hours=48):
                        temporal_coupling_matrix_48h += update_matrix
                        inside48Window = True
                        if inside24Window or delta <= datetime.timedelta(hours=24):
                            temporal_coupling_matrix_24h += update_matrix
                            inside24Window = True
                i += 1
            else:
                time_frame.popleft()

        time_frame.append(c1)
        global_progress.update(1)

    global_progress.close()

    temporal_coupling = {}

    convert_to_format(temporal_coupling, temporal_coupling_matrix_24h, 0)
    convert_to_format(temporal_coupling, temporal_coupling_matrix_48h, 1)
    convert_to_format(temporal_coupling, temporal_coupling_matrix_72h, 2)
    convert_to_format(temporal_coupling, temporal_coupling_matrix_168h, 3)

    print("saving")

    with open("./ex_3_AB_results.json", "w") as f:
        json.dump(list(temporal_coupling.values()), f, indent=4)

    duration = default_timer() - start

    print("done in {}sec".format(duration))
