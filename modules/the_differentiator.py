#!/usr/bin/env python
"""
baseline_compare module to compare command output from baselines
john.tishey@windstream.com 2017
"""

import difflib
import logging
from modules import jinja2
from modules import yaml

class Run(object):
    """ Run tests on the before and after commands """
    def __init__(self, device):
        """ Compare output of commands according to test rules
        device.output['before'] and device.output['after'] contain the outputs """
        self.device = device
        self.test_list = self.device.config.cfg[(self.device.os_type)]
        self.test_path = self.device.config.cfg['project_path'] + '/testfiles/' + \
                         self.device.os_type
        self.pre, self.post = '', ''
        self.pass_status, self.cmd_totals = '', ''
        if self.device.config.verbose == 20:
            self.config_diff()
            return

        self.get_command_lists()
        self.config_diff()
        self.test_ping_output()

    def get_command_lists(self):
        """ For each yaml file in the config file, open testfile and gather command output. """
        logger = logging.getLogger("BaselineParser")
        for test_case in self.test_list:
            try:
                with open(self.test_path + '/' + test_case) as _f:
                    self.test_values = yaml.load(_f.read())
            except:
                logger.error("ERROR: Could not load " + self.test_path + '/' + test_case)
                continue
            try:
                self.before_cmd_output = self.device.output['before'][(self.test_values[0]['command'])]
                self.after_cmd_output = self.device.output['after'][(self.test_values[0]['command'])]
            except KeyError:
                logger.error("ERROR: " + self.test_values[0]['command'] + " not found in the baseline!\n")
                continue
            self.test_cmd_output()

    def test_cmd_output(self):
        """ Gets before/after command and yaml test values to compare """
        # Reset totals and variables
        logger = logging.getLogger("BaselineParser")
        logger.info("******** Command: " + self.test_values[0]['command'] + " ********")
        self.cmd_totals = {'PASS': 0, 'FAIL': 0}
        line = ''
        for line in self.before_cmd_output:
            self.pass_status = 'UNSET'
            skip_line = False
            # Skip lines that include a blacklisted word
            for word in self.test_values[0]['blacklist']:
                if word in line:
                    skip_line = True
            # If an iterator is set, skip lines that don't have the iterator
            if self.test_values[0]['iterate'] != ['all']:
                iter_match = False
                for word in self.test_values[0]['iterate']:
                    if word in line:
                        iter_match = True
                if iter_match is False:
                    skip_line = True
            if skip_line is True:
                continue
            # NO-DIFF =  All indexes must match before/after
            if 'no-diff' in self.test_values[0]['tests'][0]:
                self.no_diff(line)
            # If testing didn't find a match, mark as failed
            if self.pass_status == 'UNSET':
                self.pass_status = 'FAIL'
                self.post = ''
            self.print_result()
        self.after_only_lines()
        self.print_totals()

    def no_diff(self, line):
        """ Execute no-diff tests (indicating all indexes match before/after)"""
        line = line.split()
        after_line = ''
        line_id = self.test_values[0]['tests'][0]['no-diff'][0]
        for after_line in self.after_cmd_output:
            after_line_orig = after_line
            after_line = after_line.split()
            try:
                if line[line_id] == after_line[line_id]:
                    for index in self.test_values[0]['tests'][0]['no-diff']:
                        # If an index fails, mark as failed
                        try:
                            if line[index] != after_line[index]:
                                self.pass_status = 'FAIL'
                                break
                        except:
                            self.pass_status = 'FAIL'
                    # If it looped through indexes without failing, mark as pass
                    if self.pass_status == 'UNSET':
                        self.pass_status = 'PASS'
                    self.after_cmd_output.remove(after_line_orig)
                    break
            except IndexError:
                continue
        self.pre = line
        self.post = after_line

    def print_result(self):
        """ Print and count the results """
        logger = logging.getLogger("BaselineParser")
        if self.pass_status == 'FAIL':
            self.cmd_totals['FAIL'] += 1
            msg = jinja2.Template(str(self.test_values[0]['tests'][0]['err']))
            if self.post == '' or self.post == []:
                self.post = ['null'] * 12
            logger.info(msg.render(device=self.device, pre=self.pre, post=self.post))
        else:
            self.cmd_totals['PASS'] += 1
            msg = jinja2.Template(str(self.test_values[0]['tests'][0]['info']))
            if self.post == '':
                self.post = ['null'] * 12
            logger.debug(msg.render(device=self.device, pre=self.pre, post=self.post))

    def after_only_lines(self):
        """ Account for lines in AFTER that aren't in BEFORE """
        logger = logging.getLogger("BaselineParser")
        if len(self.after_cmd_output) > 0:
            for after_line in self.after_cmd_output:
                skip_line = False
                for word in self.test_values[0]['blacklist']:
                    if word in after_line:
                        skip_line = True
                # If an iterator is set, skip lines that don't have the iterator
                if self.test_values[0]['iterate'] != ['all']:
                    for word in self.test_values[0]['iterate']:
                        if word not in after_line:
                            skip_line = True
                if skip_line is False:
                    self.cmd_totals['FAIL'] += 1
                    self.pre = after_line.split()
                    self.post = ['null', 'null', 'null', 'null', 'null', 'null', 'null', 'null']
                    msg = jinja2.Template(str(self.test_values[0]['tests'][0]['err']))
                    logger.info(msg.render(device=self.device, pre=self.pre, post=self.post))

    def print_totals(self):
        """ Print command test results for all lines of that command output """
        logger = logging.getLogger("BaselineParser")
        if self.cmd_totals['FAIL'] == 0:
            logger.info("PASS! All " + str(self.cmd_totals['PASS']) + " tests passed!\n")
        else:
            logger.info("FAIL! " + str(self.cmd_totals['PASS']) + " tests passed, " + \
                  str(self.cmd_totals['FAIL']) + " tests failed!\n")

    def config_diff(self):
        """ Run diff on before and after config """
        logger = logging.getLogger("BaselineParser")
        cmds = {'JUNOS': 'show configuration',
                'IOS': 'show run',
                'XR': 'show configuration running-config',
                'TiMOS': 'admin display-config'}
        logger.info("******** Command: " + cmds[self.device.os_type] + " ********")
        try:
            before_cfg = self.device.output['before'][(cmds[self.device.os_type])]
            after_cfg = self.device.output['after'][(cmds[self.device.os_type])]
        except KeyError:
            logger.error("ERROR: " + (cmds[self.device.os_type] + " not found in baseline\n"))
            return

        diff = difflib.unified_diff(before_cfg, after_cfg)
        cfg_diff = '\n'.join(diff)
        if cfg_diff != '':
            if self.device.config.verbose > 0:
                logger.info("FAILED! " + self.device.hostname + " configuation changed")
                for line in cfg_diff.splitlines():
                    if '@@' in line:
                        line = '=' * 36
                    if '+++' not in line and '---' not in line and line != '':
                        logger.debug(line)
                logger.info('\n')
            else:
                logger.info("FAILED! " + self.device.hostname + " configuation changed ('-v' to view)\n")
        else:
            logger.info("PASS! No changes in " + self.device.hostname + " configuration\n")

    def test_ping_output(self):
        """ Run ping tests """
        logger = logging.getLogger("BaselineParser")
        logger.info("******** Testing ping commands ********")
        self.ping_totals = {"PASS": 0, "FAIL": 0, "SKIP": 0}
        for self.ping_test in self.device.output['before'].keys():
            if self.ping_test[:4] == 'ping':
                try:
                    self.before_cmd_output = self.device.output['before'][self.ping_test]
                    self.after_cmd_output = self.device.output['after'][self.ping_test]
                except KeyError:
                    self.ping_totals["SKIP"] += 1
                    continue
                self.execute_ping_check()

        if self.ping_totals['FAIL'] == 0:
            logger.info("PASS! " + str(self.ping_totals["PASS"]) + " ping checks passed! (" + \
                  str(self.ping_totals["SKIP"]) + " skipped) \n")
        else:
            logger.info("FAIL! " + str(self.ping_totals['PASS']) + " tests passed, " + \
                   str(self.ping_totals['FAIL']) + " tests failed!\n")

    def execute_ping_check(self):
        """ Test ping commands - no testfile needed """
        logger = logging.getLogger("BaselineParser")
        ping_vars = {'JUNOS': {'iterword': 'packets', 'match_index': 6},
                     'TiMOS': {'iterword': 'packets', 'match_index': 6},
                     'IOS': {'iterword': 'Success', 'match_index': 3},
                     'XR': {'iterword': 'Success', 'match_index': 3}}
        iterword = ping_vars[self.device.os_type]['iterword']
        match_index = ping_vars[self.device.os_type]['match_index']
        # Look for the results line in the BEFORE
        found_match = False
        line, after_line = '', ''
        for line in self.before_cmd_output:
            if iterword in line:
                line = line.split()
                found_match = True
                break
        if found_match is False:
            self.ping_totals['SKIP'] += 1
            return
        # Look for the results line in the AFTER
        found_match = False
        for after_line in self.after_cmd_output:
            if iterword in after_line:
                after_line = after_line.split()
                found_match = True
                break
        if found_match is False:
            logger.info("FAILED! " + self.ping_test + " not found in the after baseline")
            self.ping_totals['FAIL'] += 1
            return
        # Standardize output across platforms
        if self.device.os_type == 'JUNOS' or self.device.os_type == 'TiMOS':
            success_rate = str(100 - int(line[match_index].replace('%', '').split('.')[0]))
        else:
            success_rate = str(line[match_index])
        # Compare BEFORE and AFTER packet loss results
        if line[match_index] == after_line[match_index]:
            logger.debug("PASSED! " + self.ping_test + " " + success_rate + \
                 '% success before and after')
            self.ping_totals['PASS'] += 1
        else:
            logger.info("FAILED! " + self.ping_test  + " pre=" + \
               str(line[match_index]) + "% post=" + str(after_line[match_index]) + "% success")
            self.ping_totals['FAIL'] += 1
