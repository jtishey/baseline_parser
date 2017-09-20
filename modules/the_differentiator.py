#!/usr/bin/env python
"""
baseline_compare module to compare command output from baselines
john.tishey@windstream.com 2017
"""

import os
from modules import jinja2
from modules import yaml

# Step 1: Open config file and get testfile(s)
def run(device):
    """ Compare output of commands according to test rules
        device.output['before'] and device.output['after'] contain the outputs """
    project_path = os.path.abspath('/opt/ipeng/scripts/baseline_parser/')
    with open(project_path + '/config.yml') as _f:
        config = yaml.load(_f)
    test_list = config[(device.os_type)]
    test_path = project_path + '/testfiles/' + device.os_type
    # For each yaml file in the config file:
    for test_case in test_list:
        # Open testfile and gather command output:
        with open(test_path + '/' + test_case) as _f:
            test_values = yaml.load(_f.read())
        before_cmd = device.output['before'][test_values[0]['command']]
        after_cmd =  device.output['after'][test_values[0]['command']]
        print("******** Command: " + test_values[0]['command'] + " ********")
        execute_diff(device, test_values, before_cmd, after_cmd)
    print("******** Testing ping commands ********")

    # Run ping tests:
    ping_totals = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    for cmd in device.output['before'].keys():
        if cmd[:4] == 'ping':
            try:
                before_cmd = device.output['before'][cmd]
                after_cmd =  device.output['after'][cmd]
            except KeyError, e:
                ping_totals["SKIP"] +=1
                continue
            r = execute_ping_check(device, cmd, before_cmd, after_cmd)
            ping_totals[r] +=1
    if ping_totals['FAIL'] == 0:
        print("PASS! " + str(ping_totals["PASS"]) + " ping checks passed! (" + str(ping_totals["SKIP"]) + " skipped) \n")
    else:
        print("FAIL! " + str(ping_totals['PASS']) + " tests passed, " + str(ping_totals['FAIL']) + " tests failed!\n")


def execute_ping_check(device, cmd, before, after):
    """ Test ping commands - no testfile needed """
    if device.os_type == "XR" or device.os_type == "IOS":
        iter_word = 'Success'
        match_index = 3
    elif device.os_type == "JUNOS" or device.os_type == "TiMOS":
        iter_word = 'packets'
        match_index = 6

    found_match = False
    for line in before:
        if iter_word in line:
            line = line.split()
            found_match = True
    if found_match is False:
        return "SKIP"
    found_match = False
    for after_line in after:
        if iter_word in after_line:
            after_line = after_line.split()
            found_match = True
    if found_match is False:
        return "SKIP"
    try:
        if line[match_index] == after_line[match_index]:
            if device.config.verbose == True:
                print "PASSED! " + cmd + " " + str(line[match_index]) + '% Success before and after'
            return "PASS"
        else:
            print("FAILED! " + cmd + " pre=" + str(line[match_index]) + "% post=" + str(after_line[match_index]) + "% Success")
            return "FAIL"
    except IndexError, e:
        return "FAIL"

def execute_diff(device, test_values, before, after):
    """ Gets before/after command and yaml test values to compare """
    # Reset totals and variables
    totals = {'PASS': 0, 'FAIL': 0}
    for line in before[:]:
        pass_status = 'UNSET'
        skip_line = False
        after_line = ''
        # Skip lines that include a blacklisted word or are not to be iterated
        for word in test_values[0]['blacklist']:
            if word in line:
                skip_line = True
        # If an iterator is set, skip lines that don't have the iterator
        if test_values[0]['iterate'] != ['all']:
            iter_match = False
            for word in test_values[0]['iterate']:
                if word in line:
                     iter_match = True
            if iter_match is False:
                skip_line = True
        if skip_line is not True:
            # For no-diff tests, loop through lines in after to find a match
            if 'no-diff' in test_values[0]['tests'][0]:
                line = line.split()
                line_id = test_values[0]['tests'][0]['no-diff'][0]
                for after_line in after:
                    pos_match = after_line
                    after_line = after_line.split()
                    # If the first index matches, check the rest
                    try:
                        if line[line_id] == after_line[line_id]:
                            for index in test_values[0]['tests'][0]['no-diff']:
                                # If an index fails, mark as failed
                                try:
                                    if line[index] != after_line[index]:
                                        pass_status = 'FAIL'
                                        break
                                except:
                                        pass_status = 'FAIL'
                            # If it looped through indexes without failing, mark as pass
                            if pass_status == 'UNSET':
                                pass_status = 'PASS'
                            after.remove(pos_match)
                            break
                    except IndexError, e:
                        continue

           # If testing didn't find a match, mark as failed
            if pass_status == 'UNSET':
                pass_status = 'FAIL'

            # Print status message:
            if pass_status == 'FAIL':
                totals['FAIL'] += 1
                msg = jinja2.Template(str(test_values[0]['tests'][0]['err']))
                if after_line == '':
                    after_line = ['null', 'null', 'null', 'null', 'null', 'null', 'null', 'null']
                print(msg.render(device=device, pre=line, post=after_line))
            else:
                totals['PASS'] += 1
                if device.config.verbose is True:
                    msg = jinja2.Template(str(test_values[0]['tests'][0]['info']))
                    if after_line == '':
                        after_line = ['null', 'null', 'null', 'null', 'null', 'null', 'null', 'null']
                    print(msg.render(device=device, pre=line, post=after_line))

    # Entries in the "AFTER" that aren't in the "BEFORE"
    if len(after) > 0:
        for after_line in after:
            skip_line = False
            for word in test_values[0]['blacklist']:
                if word in after_line:
                    skip_line = True
            # If an iterator is set, skip lines that don't have the iterator
            if test_values[0]['iterate'] != ['all']:
                for word in test_values[0]['iterate']:
                    if word not in after_line:
                        skip_line = True
            if skip_line is False:
                totals['FAIL'] += 1
                line = after_line.split()
                after_line = ['null', 'null', 'null', 'null', 'null', 'null', 'null', 'null']
                msg = jinja2.Template(str(test_values[0]['tests'][0]['err']))
                print(msg.render(device=device, pre=line, post=after_line))
                #print 'FAILED! ISIS adj to ' + after_line[1] + ' on ' + after_line[0] + ' is now ' + after_line[3]

    # Print command test results for all lines:
    if totals['FAIL'] == 0:
        print("PASS! All " + str(totals['PASS']) + " tests passed!\n")
    else:
        print("FAIL! " + str(totals['PASS']) + " tests passed, " + str(totals['FAIL']) + " tests failed!\n")
