import multiprocessing
import time
from myo import MyoRaw


def worker(q):
    m = MyoRaw()
    m.connect()

    def add_to_queue(emg, movement):
        q.put(emg)
    m.add_emg_handler(add_to_queue)

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


if __name__ == "__main__":
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=worker, args=(q,))
    p.start()
    try:
        while True:
            while not(q.empty()):
                emg = list(q.get())
                print(emg)
    except KeyboardInterrupt:
        quit()
