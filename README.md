# Overview

This repo contains code from
[Danny Zhu](https://github.com/dzhu/myo-raw), which provides a method for connecting the Myo Arm Band to devices running Linux and code from [PerlinWarp](https://github.com/PerlinWarp/pyomyo), which provides a simple KNN classifer used for temperorily testing MYOBands functionality with the servos. The code was modified by adding functionality to:

1) Save the data collected from the Myo Arm Band.
2) Make position predictions from the data.
3) Use predicitions to move an array of servos connected to a Jetson Nano.
4) Auto Connect the Myo in case of connection loss.
5) Automatic Logging.
6) Myo Configuration
   1) LED colors
   2) Vibration
   3) Battery information

# Data Collected

The initial data collected from the Myo Arm Band was divided into 5 classes shown in the figure below algonside their respective class value. The raw data collected from the Myo Arm Band can be found in the data directory of the repo.

![plot](./docs/imgs/Hand_pos_classes.jpg)

# Code Functions

```myo.py``` -> Library file used for connecting, configuring, and logging the MYO-Band behaviour.

```servo.py``` -> A work in progress file, will be used to control the servos connected to the Nano using the neural network model infernce.

```get_raw_data.py``` -> When executed, it prints the raw data from the armband to the terminal

```multiprocessing_get_raw_data.py``` -> Multithreaded version of the get_raw_data.py

```simple_classifier.py``` -> This is the code from [PerlinWarp](https://github.com/PerlinWarp/pyomyo) and needs to be modified for our use case.

```data_converter.py``` -> converts the .dat files stored from the simple_classifier to .csv, that can be then used for training the model.

# TODO

- [ ] code documentation
- [ ] Train Model
- [ ] Servo actuation code
  - [ ] Implement I2C
  - [ ] From model inference activate servos
