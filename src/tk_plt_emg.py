from matplotlib import pyplot as plt, animation
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
import tkinter
import multiprocessing
import queue
import numpy as np
import mpl_toolkits.mplot3d as plt3d
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.cm import get_cmap
from myo import MyoRaw

q = multiprocessing.Queue()


def worker(q):
    m = MyoRaw()
    m.connect()

    def add_to_queue(emg, movement):
        q.put(emg)

    def print_battery(bat):
        print("Battery level:", bat)

    m.add_battery_handler(print_battery)
    m.add_emg_handler(add_to_queue)

    while True:
        try:
            m.run()
        except:
            quit()


QUEUE_SIZE = 100
SENSORS = 8
subplots = []
lines = []

plt.rcParams["figure.figsize"] = (4, 8)
fig, subplots = plt.subplots(SENSORS, 1)
fig.tight_layout()

name = "tab10"
cmap = get_cmap(name)
colors = cmap.colors

for i in range(0, SENSORS):
    ch_line,  = subplots[i].plot(
        range(QUEUE_SIZE), [0]*(QUEUE_SIZE), color=colors[i])
    lines.append(ch_line)

emg_queue = queue.Queue(QUEUE_SIZE)


def animate(i):
    while not(q.empty()):
        myox = list(q.get())
        if (emg_queue.full()):
            emg_queue.get()
        emg_queue.put(myox)

    channels = np.array(emg_queue.queue)

    if (emg_queue.full()):
        for i in range(0, SENSORS):
            channel = channels[:, i]
            lines[i].set_ydata(channel)
            subplots[i].set_ylim(0, max(1024, max(channel)))


if __name__ == '__main__':
    root = tkinter.Tk()
    p = multiprocessing.Process(target=worker, args=(q,))
    p.start()

    while(q.empty()):
        continue
    anim = animation.FuncAnimation(fig, animate, blit=False, interval=2)

    def on_close(event):
        p.terminate()
        raise KeyboardInterrupt
    fig.canvas.mpl_connect('close_event', on_close)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()

    toolbar = NavigationToolbar2Tk(canvas, root, pack_toolbar=False)
    toolbar.update()

    canvas.mpl_connect(
        "key_press_event", lambda event: print(f"you pressed {event.key}"))
    canvas.mpl_connect("key_press_event", key_press_handler)

    toolbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
    canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

    def init():
        line.set_data([], [])
        return line,

    tkinter.mainloop()

    try:
        root.wm_title("Embedding in Tk")
        plt.show()
    except KeyboardInterrupt:
        plt.close()
        p.close()
        quit()
