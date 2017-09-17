#!/usr/bin/env python
"""
This is a script to try any parse and compare info from
The Baseliner script in a managable fashon.
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
    parser.add_argument('-a', '--after', help='Keyword to identify "After" files (defautl=before', required=False)
    parser.add_argument('-b', '--before', help='Keyword to identify "Before" files (defautl=before', required=False)
    args = vars(parser.parse_args())
    if args['mop']:
        mop = args['mop']
    if args['before']:
        tag1 = args['before']
    else:
        tag1 = 'before'
    if args['after']:
        tag2 = args['after']
    else:
        tag2 = 'after'
    if mop == '':
        print("ERROR: Please enter a valid MOP number.  Use --help for usage info.")
        exit(1)
    return mop, tag1, tag2
## testing args
#mop_number = '234484'
#before_kw = 'before'
#after_kw = 'after'


def folder_search(mop_number):
    """ Function to recursivly seach for a folder name """
    mop_path = ''
    os.chdir('/opt/ipeng/mops/')
    for root, dirnames, filenames in os.walk(u'.'):
        for directory in dirnames:
            if str(directory) == str(mop_number):
                mop_path = os.path.abspath(root + '/' + directory)
                return mop_path
    if mop_path == '':
        print("ERROR: MOP number not found!")
        exit(1)


def file_search(keyword1, keyword2):
    """ Creates 2 sorted lists - before & after filenames """
    list_a = []
    list_b = []
    file_list = os.listdir(mop_path)
    for _file in file_list:
        f_part = _file.split('.')
        if f_part[3] == keyword1:
            list_a.append(_file)
        elif f_part[3] == keyword2:
            list_b.append(_file)
    list_a.sort()
    list_b.sort()
    return list_a, list_b


# Step 1: Get the CLI arguments
mop_number, before_kw, after_kw = arguments()

# Step 2: Find the baseline folder
mop_path = folder_search(mop_number)

# Step 3: Get list of baseline files
before_files, after_files = file_search(before_kw, after_kw)
os.chdir('/opt/ipeng/scripts/baseline_parser/')

# Step 4: Match the files up and parse:
for i, item in enumerate(before_files):
    # Make a device dict to send to the extractorator
    device = {}
    device['hostname'] = str(item.split('.')[1] + '.' + item.split('.')[2])
    device['files'] = []
    device['files'].append(os.path.abspath(mop_path + '/' + before_files[i]))
    device['files'].append(os.path.abspath(mop_path + "/" + after_files[i]))
    device['before_kw'] = before_kw
    device['after_kw'] = after_kw
    device['os_type'] = subprocess.Popen(
                    ["gimme", "os_type", device['hostname']], stdout=subprocess.PIPE).communicate()
    device['os_type'] = device['os_type'][0].rstrip()
    print "\nRunning " + device['hostname']
    print "---------------------------"

    # Extract commands & output
    device['output'] = the_extractorator.run(device)

    # Compare command output
    results = the_differentiator.run(device)

# Step 5: Do some shit with the results
