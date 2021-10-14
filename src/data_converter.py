import numpy as np
import pandas as pd
import os


def dat_to_array(ind):
    """takes values in .dat files in the data folder
    and holds them in a numpy array. 

    Args:
        ind ([int]): val[ind] value; for example, ind=0
        wo           would be val0.dat 
    """
    dat_loc = os.getcwd() + r'/data/vals{}.dat'.format(ind)
    X.append(np.fromfile(dat_loc, dtype=np.uint16).reshape((-1, 8)))
    Y.append(ind + np.zeros(X[-1].shape[0]))


def arr_to_csv(ind):
    """Converts the numpy array to a csv file

    Args:
        ind ([int]): index of val.dat file to convert to csv.
    """
    csv_file_loc = os.getcwd() + r'/data/vals{}.csv'.format(ind)
    globals()['df%s' % i] = pd.DataFrame(
        X[ind], columns=["A", "B", "C", "D", "E", "F", "G", "H"])
    globals()['df%s' % i].to_csv(
        csv_file_loc, index=False, header=False)


if __name__ == "__main__":
    # Initialize empty X and Y to
    # store myo_data X
    # for given class Y
    X = []
    Y = []

    # Loop over the number of class data collected
    # where range(#), # is the number of classes + 1
    for i in range(5):
        # this will convert the .dat files to an array
        dat_to_array(ind=i)
        # finally this save the array into a
        # csv in the data folder
        arr_to_csv(ind=i)
