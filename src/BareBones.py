"""
  This pipeline trains a simple dense network with one hidden layer to classify 
  hand open, hand closed and rest gestures, given a table of sample data in 
  CSV format
"""
# imports
import os
import math
import tensorflow as tf
import scipy
import numpy as np
from sklearn.model_selection import train_test_split

glbl_gw = 40
glbl_rmsw = 10

# Function to calculate the rms value over a window and return it as a single float


def calc_rms(data, window):
    sq_sum = np.sum(np.power(data, 2))
    return math.sqrt(sq_sum/window)

    # probably import data directly from myoband into np array instead of this


def get_data(item):
    """
    function to read CSV data into one long 8-channel wide numpy array
    Input:
      item: the name of the csv containing all of the data for the gestures and 
        the class labels as the rightmost column.
    Output:
      data: 8xN matrix, corresponding to the data from the eight sensors of the 
        myoband, returned as a 2D numpy array
      labels: N length array, corresponding to the class labels for the data
    """
    tdata = np.loadtxt(item, delimiter=",")
    data = tdata[:, 0:8]
    labels = tdata[:, 8]

    return data, labels


# I changed this to get the current working directory and then get data.csv from the data folder
data, labels = get_data(os.getcwd()+"/data/data.csv")

# function to convert the raw data into sliding rms data


def preprocess(data, labels, gesture_window=40, rms_window=10):
    step = int(rms_window/2)
    rms_len = int((gesture_window/step)-1)
    gesture_count = int(data.shape[0]/gesture_window)
    features = np.zeros((gesture_count, rms_len, 8))
    ft_labels = np.zeros(gesture_count)
    for g in range(gesture_count):
        for i in range(8):  # For each channel
            for j in range(rms_len):  # for each window
                features[g, j, i] = calc_rms(
                    data[(j*step):(j*step + rms_window), i], rms_window)
        ft_labels[g] = np.rint(
            np.sum(labels[(g*gesture_window):((g+1)*gesture_window)])/gesture_window)
    return features, ft_labels


ppd, ppd_labels = preprocess(data, labels)

train_data, test_data, train_labels, test_labels = train_test_split(
    ppd, ppd_labels, test_size=0.3)

# Code to build and compile the model
model = tf.keras.Sequential([
    tf.keras.layers.Flatten(input_shape=(
        int((2*glbl_gw/glbl_rmsw)-1), 8)),  # input data layer
    tf.keras.layers.Dense(20, activation='relu'),  # black box layer
    tf.keras.layers.Dense(max(ppd_labels)+1)  # output layer
])

model.compile(optimizer='adam',
              loss=tf.keras.losses.SparseCategoricalCrossentropy(
                  from_logits=True),
              metrics=['accuracy'])

# code to train and evaluate the model before saving it into the trained model object
model.fit(train_data, train_labels, epochs=10, verbose=2)
print("\nTesting...\n")
test_loss, test_acc = model.evaluate(test_data,  test_labels, verbose=2)

print('\nTest accuracy:', test_acc)

# export the model as an h5 file in the models directory
model.save("models/Trained.h5")
