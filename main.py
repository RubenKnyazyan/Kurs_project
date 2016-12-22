#!/usr/bin/env python3
import sys
import os
import shutil
import logging
import time
import subprocess
import pyudev
from daemonize import Daemon
 
context = pyudev.Context()
logging.basicConfig(filename='/tmp/kursovoi.log', level=logging.DEBUG)
SOURCE_SERIAL = 'Verbatim_STORE_N_GO_07AB1608151B5B72'
DESTINATION_SERIAL = 'Corsair_Voyager_Mini_c3f41ad10ff131'
WAIT = 60
PIDFILE = '/tmp/daemon-kurs.pid'
 
class KursDaemon(Daemon):
 
    def run(self):
        while True:
            if try_copy():
                sys.exit(0)
            else:
                time.sleep(WAIT)
 
 
def copytree(src, dst):
    result = None
    process = subprocess.Popen('cp -rvf {0} {1}'.format(src, dst).split(), stdout=subprocess.PIPE)
    result, error = process.communicate()
    logging.debug(result)
    return result.decode('utf-8').split('\n')
 
 
def try_copy():
    src, dst = None, None
 
    # получить device name для флешек
    src_id = '/dev/disk/by-id/usb-{0}-0:0-part1'.format(SOURCE_SERIAL)
    dst_id = '/dev/disk/by-id/usb-{0}-0:0-part1'.format(DESTINATION_SERIAL)
    logging.debug(src_id)
    src_device_name, dst_device_name = None, None
    if os.path.islink(src_id):
        src_device_name = os.readlink(src_id).split("/")[-1]
        logging.debug(src_device_name)
    if os.path.islink(dst_id):
        dst_device_name = os.readlink(dst_id).split("/")[-1]
    if not src_device_name:
        logging.error('No source device')
        return False
    if not dst_device_name:
        logging.error('No destination device')
        return False
    # получить пути, куда смонтированы
    mtab = open('/etc/mtab', 'r')
    src_path, dst_path = None, None
    for line in mtab.readlines():
        if src_device_name in line:
            src_path = line.split(' ')[1]
        if dst_device_name in line:
            dst_path = line.split(' ')[1]
    if not src_path:
        logging.error('Source device is not mounted!')
    if not dst_path:
        logging.error('Destination device is not mounted!')
    if not src_path or not dst_path:
        return False
    # собственно копирование
    result = copytree(src_path + '/', dst_path + '/')
    dst_log = open(dst_path + '/copied.log', 'w')
    src_log = open(src_path + '/copied.log', 'w')
    for f in result:
        dst_log.write(f + '\n')
        src_log.write(f + '\n')
    dst_log.close()
    src_log.close()
    return True
 
 
if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ["start", "stop", "status", "restart"]:
        print("Запускайте так: python main.py start|stop|status|restart")
        sys.exit(1)
    daemon = KursDaemon(PIDFILE)
    if sys.argv[1] == "start":
        daemon.start()
    elif sys.argv[1] == "stop":
        daemon.stop()
    elif sys.argv[1] == "restart":
        daemon.restart()
    elif sys.argv[1] == "status":
        if os.path.isfile(PIDFILE):
            pidfile = open(PIDFILE, "r")
            pid = pidfile.read()
            print("Запущен с PID={0}".format(pid))
        else:
            print("Демон пока что не запущен")
