# -*- coding=utf-8 -*-

"""
    anviz-sync real-time
    ~~~~~~~~~~~~~~~~~~~~

    Software that listen on socket connection for Anviz A300 device request and store data in db.

    :copyright: (c) 2022 by Augusto Roccasalva
    :license: BSD, see LICENSE for more details.
"""

import socket
import struct
from configparser import ConfigParser
from datetime import datetime

from anviz_sync import anviz
from anviz_sync.models import AttendanceRecord, configure_db, db
from anviz_sync.saw import SQLAlchemy


TYPES = {
    0: "Entrada",
    1: "Salida",
    2: "BREAK",
}


def get_record(raw_data):
    crc_ok = anviz.crc16(raw_data[:23]) == raw_data[-2:]
    if not crc_ok:
        raise ValueError("CRC verificaton failed")
    stx, dev_id, ack, ret, length = struct.unpack(">BLBBH", raw_data[:9])
    record = anviz.parse_record(raw_data[9 : 9 + length])
    return dev_id, record


def show_data(dev_id, record):
    time = datetime.now()
    print(
        f"> dev_id={dev_id} user_id={record.code} {record.datetime.isoformat()} bkp={record.bkp} {TYPES[record.type]} work={record.work} [{time}]"
    )


def main():
    config = ConfigParser()
    config.read("anviz-sync.ini")

    # config device
    ip_addr = config.get("anviz-rt", "ip_addr")
    ip_port = config.getint("anviz-rt", "ip_port")

    reconnect = True

    while reconnect:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((ip_addr, ip_port))
            s.listen()
            conn, addr = s.accept()
            with conn:
                time = datetime.now()
                print(f"[{time}] Connected by {addr}")
                try:
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        dev_id, record = get_record(data)
                        show_data(dev_id, record)
                except ConnectionResetError as err:
                    time = datetime.now()
                    print(f"[{time}] Closing socket, reconnecting...")
                    pass
                except socket.timeout as err:
                    time = datetime.now()
                    print(f"[{time}] Reconnecting ...")
                    pass
                except KeyboardInterrupt as err:
                    reconnect = False
                    print("Quit")

if __name__ == "__main__":
    main()
