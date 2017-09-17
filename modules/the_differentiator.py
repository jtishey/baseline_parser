#!/usr/bin/env python
"""
baseline_compare module to compare command output from Pinky_baseliner
john.tishey@windstream.com 2017
"""

import os
from modules import jinja2
from modules import yaml

# Step 1: Loop through commands, using pre-determined logic where available
def run(device):
    """ Compare output of commands according to test rules
        device['output']['before'] and device['output']['after'] contain the outputs """
    project_path = os.path.abspath('/opt/ipeng/scripts/baseline_parser/')
    with open(project_path + '/config.yml') as _f:
        config = yaml.load(_f)
    test_list = config[(device['os_type'])]
    test_path = project_path + '/testfiles/' + device['os_type']
    for test_case in test_list:
        with open(test_path + '/' + test_case) as _f:
            test_values = yaml.load(_f.read())
        before_cmd = device['output']['before'][test_values[0]['command']]
        after_cmd = device['output']['after'][test_values[0]['command']]
        execute_diff(device, test_values, before_cmd, after_cmd)


def execute_diff(device, test_values, before, after):
    """ Gets before/after command and yaml test values to compare """
    # First, determine the test from test_values:
    for line in before[:]:
        pass_status = 'UNSET'
        skip_line = False
        after_line = ''
        # Skip lines that include a blacklisted word or are not to be iterated
        for word in test_values[0]['blacklist']:
            if word in line:
                skip_line = True
        # If an iterator is set, skip lines that don't have the iterator
        if test_values[0]['iterate'] != 'all':
            if test_values[0]['iterate'] not in line:
                skip_line = True
        if skip_line is not True:
            # For no-diff tests, loop through lines in after
            if 'no-diff' in test_values[0]['tests'][0]:
                line = line.split()
                line_id = test_values[0]['tests'][0]['no-diff'][0]
                for after_line in after:
                    pos_match = after_line
                    after_line = after_line.split()
                    # If the first index matches, check the rest
                    if line[line_id] == after_line[line_id]:
                        for index in test_values[0]['tests'][0]['no-diff']:
                            # If an index fails, mark as failed
                            if line[index] != after_line[index]:
                                pass_status = 'FAIL'
                                break
                        # If it looped through indexes without failing, mark as pass
                        if pass_status == 'UNSET':
                            pass_status = 'PASS'
                        after.remove(pos_match)
                        break
            # If it didnt find a match, mark as failed
            if pass_status == 'UNSET':
                pass_status = 'FAIL'
            if pass_status == 'FAIL':
                msg = jinja2.Template(str(test_values[0]['tests'][0]['err']))
                if after_line == '':
                    after_line = ['null', 'null', 'null', 'null', 'null', 'null', 'null', 'null']
                print msg.render(device=device, pre=line, post=after_line)
            else:
                if device['verbose'] is True:
                    msg = jinja2.Template(str(test_values[0]['tests'][0]['info']))
                    if after_line == '':
                        after_line = ['null', 'null', 'null', 'null', 'null', 'null', 'null', 'null']
                    print msg.render(device=device, pre=line, post=after_line)
    if len(after) > 0:
        for after_line in after:
            skip_line = False
            for word in test_values[0]['blacklist']:
                if word in after_line:
                    skip_line = True
            if skip_line is False:
                after_line = after_line.split()
                line = ['null', 'null', 'null', 'null', 'null', 'null', 'null', 'null']
                msg = jinja2.Template(str(test_values[0]['tests'][0]['err']))
                #print msg.render(device=device, pre=line, post=after_line)
                print 'FAILED! ISIS adj to ' + after_line[1] + ' on ' + after_line[0] + ' is now ' + after_line[3]

