#!/usr/bin/env python
"""
This is a script to parse and compare info from
a baseliner script in a managable fashon.
jtishey 2017
"""

import os
import sys
import logging
import argparse
import subprocess
from modules import yaml
from modules import the_extractorator
from modules import the_differentiator
from modules import the_recyclanator


def arguments():
    """ Parse entered CLI arguments with argparse """
    p = argparse.ArgumentParser(description='Parse and compare before/after baseline files.')
    p.add_argument('-m', '--mop', help='Specify a MOP number to parse', required=True)
    p.add_argument('-a', '--after', help='Keyword to identify "After" files (default=after)', metavar='PRE')
    p.add_argument('-b', '--before', help='Keyword to identify "Before" files (default=before)', metavar='PST')
    p.add_argument('-c', '--config', action='count', default=0, help='Display configuration diff only')
    p.add_argument('-d', '--dev', help='Run baseline checks on a specific device only', metavar='DEV')
    p.add_argument('-l', '--log', action='count', default=0, help='Display no output, only log to file')
    p.add_argument('-o', '--override', action='count', default=0, help='Ignore previous log files and force new check')
    p.add_argument('-s', '--summary', action='count', default=0, help='Display summary output only')
    p.add_argument('-v', '--verbose', action='count', default=0, help='Display verbose output')
    args = vars(p.parse_args())
    tag1, tag2, stest, override, verbose = 'before', 'after', [], False, 0
    mop = args['mop']
    if args['verbose']:
        verbose = args['verbose']
    if args['before']:
        tag1 = args['before']
    if args['after']:
        tag2 = args['after']
    if  args['config']:
        verbose = 20
    if args['summary']:
        verbose = 40
    if args['dev']:
        for device in  args['dev'].split(','):
            stest.append(device)
    if args['log']:
        verbose = 60
    if args['override']:
        override = True
    return mop, tag1, tag2, stest, override, verbose


class Config(object):
    """ Variables used by all devices """
    def __init__(self):
        """ Init variables """
        self.mop_number, self.before_kw, self.after_kw, self.stest, self.override, self.verbose = arguments()
        proj_path = os.path.dirname(os.path.realpath(__file__))
        with open(proj_path + '/config.yml') as _f:
            self.cfg = yaml.load(_f)
        self.mop_path = ''
        self.before_files = []
        self.after_files = []

    def folder_search(self):
        """ Method to recursivly seach for a folder name """
        os.chdir(self.cfg['mop_path'])
        found_list = []
        for root, dirnames, filenames in os.walk(u'.'):
            for directory in dirnames:
                if str(directory) == str(self.mop_number):
                    found_list.append(os.path.abspath(root + '/' + directory))
        if len(found_list) == 1:
            self.mop_path = found_list[0]
            print("\nFound " + self.mop_path)
        elif len(found_list) > 1:
            # if log file only, just use the newest folder
            if self.verbose == 60:
                best_fldr = found_list[0]
                newest = os.path.getctime(best_fldr)
                for fldr in found_list:
                    if os.path.getctime(fldr) > newest:
                        newest = os.path.getctime(fldr)
                        best_fldr = fldr
                self.mop_path = best_fldr
            else:
                print("\nFound " + str(len(found_list)) + " baselines for MOP " +
                      self.mop_number + ":")
                print("-" * 36)
                for i, mop_folder in enumerate(found_list):
                    print(str(i + 1) + ': ' + mop_folder)
                selection = raw_input("\nSelect a folder to test: ")
                print("\n")
                try:
                    selection = int(selection)
                    self.mop_path = found_list[selection - 1]
                except:
                    print("ERROR: Please enter the number of the selection only\n")
                    exit(1)
        else:
            print("ERROR: MOP number not found!")
            exit(1)
        if os.path.exists(self.mop_path + '/BaselineParser.log'):
            if self.override is False:
                the_recyclanator.Run(self)

    def file_search(self):
        """ Creates 2 sorted lists - before & after filenames """
        file_list = os.listdir(self.mop_path)
        for _file in file_list:
            f_part = _file.split('.')
            try:
                if f_part[3] == self.before_kw:
                    self.before_files.append(_file)
                elif f_part[3] == self.after_kw:
                    self.after_files.append(_file)
            except:
                continue
        if len(self.before_files) == 0 or \
           len(self.after_files) == 0:
            print("\nBefore/After files not found\n")
            exit(1)
        self.before_files.sort()
        self.after_files.sort()
        os.chdir(self.cfg['project_path'])

    def setup_logging(self):
        """ Set logging format, level, and handlers """
        log_file = self.mop_path + '/' + "BaselineParser.log"
        if os.path.exists(log_file):
            os.remove(log_file)
        msg_only_formatter = logging.Formatter('%(message)s')
        self.logger = logging.getLogger("BaselineParser")
        self.logger.setLevel(logging.DEBUG)
        # File Handler:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(msg_only_formatter)
        fh.setLevel(logging.DEBUG)
        # Stream Handler:  - set level based on verbose settings (-c -s -v)
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(msg_only_formatter)
        if self.verbose == 40:
            sh.setLevel(logging.WARN)
        elif self.verbose > 0:
            sh.setLevel(logging.DEBUG)
        else:
            sh.setLevel(logging.INFO)

        self.logger.addHandler(fh)
        if self.verbose != 60:
            self.logger.addHandler(sh)


class Device(object):
    """Create Deviec Object"""
    def __init__(self):
        """ Init device variables and inherit from Config """
        self.hostname = ''
        self.os_type = ''
        self.results = ''
        self.files = []
        self.output = []
        self.skip_device = False

    def assign_values(self, host, i):
        """ Assign device-specific values """
        self.hostname = host
        self.skip_device = False
        # self.files includes the before AND after filename for the device
        try:
            self.files.append(os.path.abspath(self.config.mop_path + '/' +
                              self.config.before_files[i]))
            if self.hostname in self.config.after_files[i]:
                self.files.append(os.path.abspath(self.config.mop_path + "/" +
                                 self.config.after_files[i]))
            else:
                for b_file in self.config.after_files:
                    if self.hostname in b_file:
                        self.files.append(os.path.abspath(self.config.mop_path + "/" + b_file))
        except IndexError:
            pass
        if len(self.files) < 2:
            self.output = "ERROR: Missing baseline for " + host + "\n"
            self.skip_device = True
        # 'gimme' is a script that returns an os_type that matches the testfile folder names
        os_type = subprocess.Popen(
            ["gimme", "os_type", host], stdout=subprocess.PIPE).communicate()
        self.os_type = os_type[0].rstrip()


if __name__ == '__main__':
    # Init config, find folder/MOP files and setup logger
    CONFIG = Config()
    CONFIG.folder_search()
    CONFIG.file_search()
    CONFIG.setup_logging()
    logger = CONFIG.logger

    # One device at a time copy the config, parse, and compare
    for i, item in enumerate(CONFIG.before_files):
        hostname = str(item.split('.')[1] + '.' + item.split('.')[2])
        if CONFIG.stest and hostname not in CONFIG.stest:
            continue
        device = Device()
        device.config = CONFIG
        device.assign_values(hostname, i)
        if device.skip_device is False:
            # Get commands and output from baseline files
            logger.info("\n\nRunning " + device.hostname)
            logger.info("-" * 24)
            device.output = the_extractorator.run(device)

        # Execute the diff on the command output
        if type(device.output) is dict:
            the_differentiator.Run(device)
        else:
            logger.info(device.output)

    # Update log file permissions
    os.chmod(CONFIG.mop_path + '/' + "BaselineParser.log", 0777)
