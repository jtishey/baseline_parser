#!/usr/bin/env python
"""
This is a script to try any parse and compare info from
a baseliner script in a managable fashon.
John.Tishey@windstream.com 2017
"""

import os
import argparse
import subprocess
from modules import the_extractorator
from modules import the_differentiator


def arguments():
    """ Parse entered CLI arguments with argparse """
    parser = argparse.ArgumentParser(description='Parse and compare before/after Pinky_Baseliner files.')
    parser.add_argument('-m', '--mop', help='Specify a MOP number to parse', required=True)
    parser.add_argument('-a', '--after', help='Keyword to identify "After" files (defautl=after)', required=False)
    parser.add_argument('-b', '--before', help='Keyword to identify "Before" files (defautl=before)', required=False)
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Display verbose output')
    args = vars(parser.parse_args())
    verbose = False
    tag1 = 'before'
    tag2 = 'after'

    if args['mop']:
        mop = args['mop']
    if args['verbose']:
        verbose = True
    if args['before']:
        tag1 = args['before']
    if args['after']:
        tag2 = args['after']
    if mop == '':
        print("ERROR: Please enter a valid MOP number.  Use --help for usage info.")
        exit(1)
    return mop, tag1, tag2, verbose


class Config(object):
    """ Variables used by all devices """
    def __init__(self):
        """ Init variables """
        mop_number, before_kw, after_kw, verbose = arguments()
        self.mop_number = mop_number
        self.before_kw = before_kw
        self.after_kw = after_kw
        self.verbose = verbose
        self.mop_path = ''
        self.before_files = []
        self.after_files = []

    def folder_search(self):
        """ Method to recursivly seach for a folder name """
        os.chdir('/opt/ipeng/mops/')
        for root, dirnames, filenames in os.walk(u'.'):
            for directory in dirnames:
                if str(directory) == str(self.mop_number):
                    self.mop_path = os.path.abspath(root + '/' + directory)
        if self.mop_path == '':
            print("ERROR: MOP number not found!")
            exit(1)

    def file_search(self):
        """ Creates 2 sorted lists - before & after filenames """
        file_list = os.listdir(self.mop_path)
        for _file in file_list:
            f_part = _file.split('.')
            if f_part[3] == self.before_kw:
                self.before_files.append(_file)
            elif f_part[3] == self.after_kw:
                self.after_files.append(_file)
        self.before_files.sort()
        self.after_files.sort()
        os.chdir('/opt/ipeng/scripts/baseline_parser/')


class Device(object):
    """Create Deviec Object"""
    def __init__(self):
        """ Init device variables and inherit from Config """
        self.hostname = ''
        self.files = []
        self.os_type = ''
        self.output = []
        self.results = ''

    def __get_attr__(self):
        return getattr(self.before_files)

    def assign_values(self, host, i):
        """ Assign device-specific values """
        self.hostname = host
        self.files.append(os.path.abspath(self.config.mop_path + '/' + self.config.before_files[i]))
        self.files.append(os.path.abspath(self.config.mop_path + "/" + self.config.after_files[i]))
        os_type = subprocess.Popen(
            ["gimme", "os_type", host], stdout=subprocess.PIPE).communicate()
        self.os_type = os_type[0].rstrip()


CONFIG = Config()
CONFIG.folder_search()
CONFIG.file_search()

for i, item in enumerate(CONFIG.before_files):
    hostname = str(item.split('.')[1] + '.' + item.split('.')[2])
    device = Device()
    device.config = CONFIG
    device.assign_values(hostname, i)

    """ Get commands and output from baseline files """
    print "\nRunning " + device.hostname
    print "-" * 16
    device.output = the_extractorator.run(device)

    """ Execute the diff on the command output """
    if device.output != '':
        device.results = the_differentiator.run(device)

