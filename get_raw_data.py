import time
from library import *


if __name__ == '__main__':

    last_vals = None
    m = MyoRaw(sys.argv[1] if len(sys.argv) >= 2 else None)

    def proc_emg(emg, moving, times=[]):
        print(emg)
        # print framerate of received data
        times.append(time.time())
        if len(times) > 20:
            times.pop(0)

    m.add_emg_handler(proc_emg)
    m.connect()

    ltime = time.time()
    try:
        while True:
            if time.time() > (ltime + 1):
                m.connect()
                ltime = time.time()
            else:
                ltime = time.time()
                m.run()
    except KeyboardInterrupt:
        pass
    finally:
        m.disconnect()
        print()
