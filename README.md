# Overview

This repo contains code from
[Danny Zhu](https://github.com/dzhu/myo-raw), and provides a method for connecting the Myo Arm Band to devices running Linux.
# Installation and Usage

```bash
$ sudo chmod +x MyoConnect.sh
$ ./MyoConnect.sh
```

# File structure

```TXT
docs/
logs/
lib/
    Myo.py
src/
    Myo/
        __init__.py
        multiprocesing_data.py
        get_raw_data.py
    User/
        __init__.py
        interface.py
        data_collection.py
    Servo/
        __init__.py
        control.py
models/
    model_type1/
        model-revision#.pkl
    model_type2/
        model-revision#.pkl
requirements.txt
MyoConnect.sh
.gitignore
```
