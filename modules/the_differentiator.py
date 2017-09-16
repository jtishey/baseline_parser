#!/usr/bin/env python
"""
baseline_compare module to compare command output from Pinky_baseliner 
john.tishey@windstream.com 2017
"""

import yaml

# Step 1: Loop through commands, using pre-determined logic where available
def run(device):
    """ Compare output of commands according to test rules
        device['output']['before'] and device['output']['after'] contain the outputs """
    project_path = os.path.abspath('/opt/ipeng/scripts/baseline_parser/')
    with open(project_path + 'config.yml') as _f:
        config = yaml.load(_f)
    test_list = config[device['os-type']]
    test_path = project_path + 'testfiles/' + device['os_type'] + '/'
    for test_case in test_list:
        with open(test_path + test_case) as _f:
            test_values = yaml.load(_f.read())
        before_cmd = device['output']['before'][test_values[0]['command']]
        after_cmd = device['output']['after'][test_values[0]['command']]
        execute_diff(test_values, before_cmd, after_cmd)


def execute_diff(test_values, before, after):
    """ Gets before/after command and yaml test values to compare """
    # First, determine the test from test_values:
    for line in before:  
        fail_flag = False
        skip_line = False
        for word in test_values[0]['blacklist']:
            # Skip lines that include a blacklisted word or are not to be iterated
            if word in line:
                skip_line = True
            if test_values[0]['iterate'] != 'all':
                if test_values[0]['iterate'] not in line:
                    skip_line = True
        if skip_line is not True:
            if 'no-diff' in test_values[0]['tests'][0]:
                line = line.split()
                line_id = line[test_values[0]]['tests'][0]['index'][0]
                for i, after_line in enumerate(after):
                    after_line = after_line.split()
                    if line[line_id] == after_line[line_id]:
                        for index in test_values[0]]['tests'][0]['index'][0]:
                            if line[index] != after_line[index]:
                                print("FAIL: " + line[line_id] + " was " + line[index] +" and is now " + after_line[index])
                                fail_flag = True
                        if fail_flag == False:
                            after.pop(i)
            if fail_flag == True:
                print(test_values[0]['tests'][0]['err'])
            else:
                print(test_values[0]['tests'[0]['info'])
                    