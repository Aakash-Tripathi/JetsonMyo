import numpy as np
import pandas as pd
import os


def dat_to_array(ind):
    dat_loc = os.getcwd() + r'/data/vals{}.dat'.format(ind)
    X.append(np.fromfile(dat_loc, dtype=np.uint16).reshape((-1, 8)))
    Y.append(ind + np.zeros(X[-1].shape[0]))


def arr_to_csv(ind):
    csv_file_loc = os.getcwd() + r'/data/vals{}.csv'.format(ind)
    globals()['df%s' % i] = pd.DataFrame(
        X[ind], columns=["A", "B", "C", "D", "E", "F", "G", "H"])
    globals()['df%s' % i].to_csv(
        csv_file_loc, index=False, header=False)


if __name__ == "__main__":
    X = []
    Y = []

    for i in range(5):
        dat_to_array(ind=i)
        arr_to_csv(ind=i)
