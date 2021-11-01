"""
Original Author of this Library https://github.com/dzhu/myo-raw
Modified by https://github.com/Aakash-Tripathi/
"""

import enum
import re
import struct
import sys
import threading
import time
import logging
import serial
from serial.tools.list_ports import comports

logging.basicConfig(filename='logs/{}.log'.format(time.strftime("%Y-%m-%d")),
                    filemode='a', level=logging.DEBUG, format='%(message)s')

logging.info("\nStart Time \t\t " + time.strftime("%H:%M.%S"))


def pack(fmt, *args):
    return struct.pack('<' + fmt, *args)


def unpack(fmt, *args):
    return struct.unpack('<' + fmt, *args)


def multichr(ords):
    if sys.version_info[0] >= 3:
        return bytes(ords)
    else:
        return ''.join(map(chr, ords))


def multiord(b):
    if sys.version_info[0] >= 3:
        return list(b)
    else:
        return map(ord, b)


class Arm(enum.Enum):
    UNKNOWN = 0
    RIGHT = 1
    LEFT = 2


class XDirection(enum.Enum):
    UNKNOWN = 0
    X_TOWARD_WRIST = 1
    X_TOWARD_ELBOW = 2


class Pose(enum.Enum):
    REST = 0
    FIST = 1
    WAVE_IN = 2
    WAVE_OUT = 3
    FINGERS_SPREAD = 4
    THUMB_TO_PINKY = 5
    UNKNOWN = 255


class Packet(object):
    def __init__(self, ords):
        self.typ = ords[0]
        self.cls = ords[2]
        self.cmd = ords[3]
        self.payload = multichr(ords[4:])

    def __repr__(self):
        return 'Packet(%02X, %02X, %02X, [%s])' % \
            (self.typ, self.cls, self.cmd,
             ' '.join('%02X' % b for b in multiord(self.payload)))


class BT(object):
    '''Implements the non-Myo-specific details of the Bluetooth protocol.'''

    def __init__(self, tty):
        self.ser = serial.Serial(port=tty, baudrate=9600, dsrdtr=1)
        self.buf = []
        self.lock = threading.Lock()
        self.handlers = []

    # internal data-handling methods
    def recv_packet(self, timeout=None):
        t0 = time.time()
        self.ser.timeout = None
        while timeout is None or time.time() < t0 + timeout:
            if timeout is not None:
                self.ser.timeout = t0 + timeout - time.time()
            c = self.ser.read()
            if not c:
                return None

            ret = self.proc_byte(ord(c))
            if ret:
                if ret.typ == 0x80:
                    self.handle_event(ret)
                return ret

    # internal data-handling methods
    def recv_packet(self, timeout=.5):
        n = self.ser.inWaiting()  # Windows fix

        while True:
            c = self.ser.read()
            if not c:
                return None

            ret = self.proc_byte(ord(c))
            if ret:
                if ret.typ == 0x80:
                    self.handle_event(ret)
                    # Windows fix
                    if n >= 5096:
                        print("Clearning", n)
                        self.ser.flushInput()
                    # End of Windows fix
                return ret

    def proc_byte(self, c):
        if not self.buf:
            if c in [0x00, 0x80, 0x08, 0x88]:
                self.buf.append(c)
            return None
        elif len(self.buf) == 1:
            self.buf.append(c)
            self.packet_len = 4 + (self.buf[0] & 0x07) + self.buf[1]
            return None
        else:
            self.buf.append(c)

        if self.packet_len and len(self.buf) == self.packet_len:
            p = Packet(self.buf)
            self.buf = []
            return p
        return None

    def handle_event(self, p):
        for h in self.handlers:
            h(p)

    def add_handler(self, h):
        self.handlers.append(h)

    def remove_handler(self, h):
        try:
            self.handlers.remove(h)
        except ValueError:
            pass

    def wait_event(self, cls, cmd):
        res = [None]

        def h(p):
            if p.cls == cls and p.cmd == cmd:
                res[0] = p
        self.add_handler(h)
        while res[0] is None:
            self.recv_packet()
        self.remove_handler(h)
        return res[0]

    # specific BLE commands
    def connect(self, addr):
        return self.send_command(6, 3, pack('6sBHHHH', multichr(addr), 0, 6, 6, 64, 0))

    def get_connections(self):
        return self.send_command(0, 6)

    def discover(self):
        return self.send_command(6, 2, b'\x01')

    def end_scan(self):
        return self.send_command(6, 4)

    def disconnect(self, h):
        return self.send_command(3, 0, pack('B', h))

    def read_attr(self, con, attr):
        self.send_command(4, 4, pack('BH', con, attr))
        return self.wait_event(4, 5)

    def write_attr(self, con, attr, val):
        self.send_command(4, 5, pack('BHB', con, attr, len(val)) + val)
        return self.wait_event(4, 1)

    def send_command(self, cls, cmd, payload=b'', wait_resp=True):
        s = pack('4B', 0, len(payload), cls, cmd) + payload
        self.ser.write(s)

        while True:
            p = self.recv_packet()
            # no timeout, so p won't be None
            if p.typ == 0:
                return p
            # not a response: must be an event
            self.handle_event(p)


class MyoRaw(object):
    '''Implements the Myo-specific communication protocol.'''

    def __init__(self, tty=None):
        if tty is None:
            tty = self.detect_tty()
        if tty is None:
            raise ValueError('Myo dongle not found!')

        self.bt = BT(tty)
        self.conn = None
        self.emg_handlers = []
        self.imu_handlers = []
        self.battery_handlers = []

    def detect_tty(self):
        for p in comports():
            if re.search(r'PID=2458:0*1', p[2]):
                return p[0]
        return None

    def run(self, timeout=None):
        self.bt.recv_packet(timeout)

    def connect(self):
        # stop everything from before
        self.bt.end_scan()
        self.bt.disconnect(0)
        self.bt.disconnect(1)
        self.bt.disconnect(2)

        # start scanning
        self.bt.discover()
        while True:
            p = self.bt.recv_packet()
            # print('scan response:', p)

            if p.payload.endswith(b'\x06\x42\x48\x12\x4A\x7F\x2C\x48\x47\xB9\xDE\x04\xA9\x01\x00\x06\xD5'):
                addr = list(multiord(p.payload[2:8]))
                break
        self.bt.end_scan()

        # connect and wait for status event
        conn_pkt = self.bt.connect(addr)
        self.conn = multiord(conn_pkt.payload)[-1]
        self.bt.wait_event(3, 0)

        # get firmware version
        fw = self.read_attr(0x17)
        _, _, _, _, v0, v1, v2, v3 = unpack('BHBBHHHH', fw.payload)
        logging.info('firmware \t\t %d.%d.%d.%d', v0, v1, v2, v3)
        logging.info("Connected \t\t " + time.strftime("%H:%M.%S"))

        self.old = (v0 == 0)

        if self.old:
            # don't know what these do; Myo Connect sends them, though we get data
            # fine without them
            self.write_attr(0x19, b'\x01\x02\x00\x00')
            self.write_attr(0x2f, b'\x01\x00')
            self.write_attr(0x2c, b'\x01\x00')
            self.write_attr(0x32, b'\x01\x00')
            self.write_attr(0x35, b'\x01\x00')

            # enable EMG data
            self.write_attr(0x28, b'\x01\x00')
            # enable IMU data
            self.write_attr(0x1d, b'\x01\x00')

            # Sampling rate of the underlying EMG sensor, capped to 1000. If it's
            # less than 1000, emg_hz is correct. If it is greater, the actual
            # framerate starts dropping inversely. Also, if this is much less than
            # 1000, EMG data becomes slower to respond to changes. In conclusion,
            # 1000 is probably a good value.
            C = 1000
            emg_hz = 50
            # strength of low-pass filtering of EMG data
            emg_smooth = 100

            imu_hz = 50

            # send sensor parameters, or we don't get any data
            self.write_attr(0x19, pack('BBBBHBBBBB', 2, 9, 2, 1,
                            C, emg_smooth, C // emg_hz, imu_hz, 0, 0))

        else:
            name = self.read_attr(0x03)
            # enable IMU data
            self.write_attr(0x1d, b'\x01\x00')
            # enable on/off arm notifications
            self.write_attr(0x24, b'\x02\x00')

            # self.write_attr(0x19, b'\x01\x03\x00\x01\x01')
            self.start_raw()

            # enable battery notifications
            self.write_attr(0x12, b'\x01\x10')

        # add data handlers
        def handle_data(p):
            if (p.cls, p.cmd) != (4, 5):
                return

            c, attr, typ = unpack('BHB', p.payload[:4])
            pay = p.payload[5:]

            if attr == 0x27:
                vals = unpack('8HB', pay)
                # not entirely sure what the last byte is, but it's a bitmask that
                # seems to indicate which sensors think they're being moved around or
                # something
                emg = vals[:8]
                moving = vals[8]
                self.on_emg(emg, moving)
            # Read IMU characteristic handle
            elif attr == 0x1c:
                vals = unpack('10h', pay)
                quat = vals[:4]
                acc = vals[4:7]
                gyro = vals[7:10]
                self.on_imu(quat, acc, gyro)

        self.bt.add_handler(handle_data)

    def write_attr(self, attr, val):
        if self.conn is not None:
            self.bt.write_attr(self.conn, attr, val)

    def read_attr(self, attr):
        if self.conn is not None:
            return self.bt.read_attr(self.conn, attr)
        return None

    def disconnect(self):
        if self.conn is not None:
            self.bt.disconnect(self.conn)
        logging.info("Disconnected \t " + time.strftime("%H:%M.%S"))

    def start_raw(self):
        '''Sending this sequence for v1.0 firmware seems to enable both raw data and
        pose notifications.
        '''

        self._extracted_from_mc_end_collection_4(
            0x19, b'\x01\x03\x01\x01\x00', 0x19, b'\x01\x03\x01\x01\x01'
        )

    def mc_start_collection(self):
        '''Myo Connect sends this sequence (or a reordering) when starting data
        collection for v1.0 firmware; this enables raw data but disables arm and
        pose notifications.
        '''

        self._extracted_from_mc_end_collection_4(
            0x1d, b'\x01\x00', 0x24, b'\x02\x00')
        self.write_attr(0x19, b'\x01\x03\x01\x01\x01')
        self.write_attr(0x28, b'\x01\x00')
        self.write_attr(0x1d, b'\x01\x00')
        self.write_attr(0x19, b'\x09\x01\x01\x00\x00')
        self.write_attr(0x1d, b'\x01\x00')
        self.write_attr(0x19, b'\x01\x03\x00\x01\x00')
        self.write_attr(0x28, b'\x01\x00')
        self.write_attr(0x1d, b'\x01\x00')
        self.write_attr(0x19, b'\x01\x03\x01\x01\x00')

    def mc_end_collection(self):
        '''Myo Connect sends this sequence (or a reordering) when ending data collection
        for v1.0 firmware; this reenables arm and pose notifications, but
        doesn't disable raw data.
        '''

        self._extracted_from_mc_end_collection_4(
            0x1d, b'\x01\x00', 0x24, b'\x02\x00')
        self.write_attr(0x19, b'\x01\x03\x01\x01\x01')
        self.write_attr(0x19, b'\x09\x01\x00\x00\x00')
        self.write_attr(0x1d, b'\x01\x00')
        self.write_attr(0x24, b'\x02\x00')
        self.write_attr(0x19, b'\x01\x03\x00\x01\x01')
        self.write_attr(0x28, b'\x01\x00')
        self.write_attr(0x1d, b'\x01\x00')
        self.write_attr(0x24, b'\x02\x00')
        self.write_attr(0x19, b'\x01\x03\x01\x01\x01')

    # TODO Rename this here and in `start_raw`, `mc_start_collection` and `mc_end_collection`
    def _extracted_from_mc_end_collection_4(self, arg0, arg1, arg2, arg3):
        self.write_attr(40, b'\x01\x00')
        self.write_attr(arg0, arg1)
        self.write_attr(arg2, arg3)

    def vibrate(self, length):
        if length in range(1, 4):
            # first byte tells it to vibrate; purpose of second byte is unknown
            self.write_attr(0x19, pack('3B', 3, 1, length))

    def set_leds(self, logo, line):
        self.write_attr(0x19, pack('8B', 6, 6, *(logo + line)))

    def get_battery_level(self):
        battery_level = self.read_attr(0x11)
        return ord(battery_level.payload[5])

    def add_emg_handler(self, h):
        self.emg_handlers.append(h)

    def add_imu_handler(self, h):
        self.imu_handlers.append(h)

    def add_battery_handler(self, h):
        self.battery_handlers.append(h)

    def on_emg(self, emg, moving):
        for h in self.emg_handlers:
            h(emg, moving)

    def on_imu(self, quat, acc, gyro):
        for h in self.imu_handlers:
            h(quat, acc, gyro)

    def on_pose(self, p):
        for h in self.pose_handlers:
            h(p)

    def on_arm(self, arm, xdir):
        for h in self.arm_handlers:
            h(arm, xdir)

    def on_battery(self, battery_level):
        for h in self.battery_handlers:
            h(battery_level)
