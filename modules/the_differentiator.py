#!/usr/bin/env python
"""
baseline_compare module to compare command output from baselines
jtishey 2017
"""

import difflib
import logging
from modules import jinja2
from modules import yaml


class Run(object):
    """ Run tests on the before and after commands  """
    def __init__(self, device):
        """ Compare output of commands according to test rules
        device.output['before'] and device.output['after'] contain the outputs """
        self.device = device
        self.test_list = self.device.config.cfg[(self.device.os_type)]
        self.test_path = self.device.config.cfg['project_path'] + '/testfiles/' + \
                         self.device.os_type
        self.pre, self.post = '', ''
        self.pass_status = ''
        self.summary = {}
        if self.device.config.verbose == 20:
            self.config_diff()
            return

        self.get_command_lists()
        self.config_diff()
        self.test_ping_output()
        self.print_summary()

    def get_command_lists(self):
        """ For each yaml file in the config file, open testfile and gather command output. """
        logger = logging.getLogger("BaselineParser")
        for test_case in self.test_list:
            try:
                with open(self.test_path + '/' + test_case) as _f:
                    self.test_values = yaml.load(_f.read())
            except:
                logger.info("ERROR: Could not load " + self.test_path + '/' + test_case)
                continue
            try:
                self.before_cmd_output = self.device.output['before'][(self.test_values[0]['command'])]
                self.after_cmd_output = self.device.output['after'][(self.test_values[0]['command'])]
            except KeyError:
                logger.info("ERROR: " + self.test_values[0]['command'] + " not found in the baseline!\n")
                continue
            self.test_cmd_output()

    def test_cmd_output(self):
        """ Gets before/after command and yaml test values to compare """
        # Reset totals and variables
        logger = logging.getLogger("BaselineParser")
        logger.info("******** Command: " + self.test_values[0]['command'] + " ********")
        self.summary[(self.test_values[0]['command'])] = {'PASS': 0, 'FAIL': 0}
        line = ''
        wrap_word = ''
        for i, line in enumerate(self.before_cmd_output):
            self.pass_status = 'UNSET'
            self.delta_value = 0
            skip_line = False
            if wrap_word == self.before_cmd_output[i - 1]:
                line = wrap_word + ' ' + line
            wrap_word = ''
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
            if skip_line:
                continue
            line = line.split()
            if len(line) == 1:
                if self.before_cmd_output[i + 1][:4] == '    ':
                    wrap_word = line[0]
                    continue
            # NO-DIFF =  All indexes must match before/after
            if 'no-diff' in self.test_values[0]['tests'][0]:
                self.no_diff(line)
            # DELTA = Delta between 2 integers must be less than specified
            elif 'delta' in self.test_values[0]['tests'][0]:
                self.delta(line)

            # If testing didn't find a match, mark as failed
            if self.pass_status == 'UNSET':
                self.pass_status = 'FAIL'
                self.post = ''
            self.print_result()
        self.after_only_lines()
        self.print_totals()

    def no_diff(self, line):
        """ Execute no-diff tests (indicating all indexes match before/after)"""
        after_line = ''
        wrap_word = ''
        line_id = self.test_values[0]['tests'][0]['no-diff'][0]
        for i, after_line in enumerate(self.after_cmd_output):
            after_line_orig = after_line
            if wrap_word == self.after_cmd_output[i - 1]:
                after_line = wrap_word + ' ' + after_line
            wrap_word = ''
            after_line = after_line.split()
            if len(after_line) == 1:
                if self.after_cmd_output[i + 1][:4] == '    ':
                    wrap_word = after_line[0]
                    continue
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
                    if self.after_cmd_output[i - 1] == after_line[0]:
                        del self.after_cmd_output[i - 1]
                    self.after_cmd_output.remove(after_line_orig)
                    break
            except IndexError:
                continue
        self.pre = line
        self.post = after_line

    def delta(self, line):
        """ Execute delta tests (identifier / index/percent)"""
        after_line = ''
        line_id = self.test_values[0]['tests'][0]['delta'][0]
        index = self.test_values[0]['tests'][0]['delta'][1]
        max_percent = self.test_values[0]['tests'][0]['delta'][2]
        for after_line in self.after_cmd_output:
            after_line_orig = after_line
            after_line = after_line.split()
            try:
                if line[line_id] == after_line[line_id]:
                    if line[index].isdigit() and after_line[index].isdigit():
                        self.delta_value = abs(int(line[index]) - int(after_line[index]))
                        if self.delta_value > float(line[index]) * max_percent:
                            self.pass_status = 'FAIL'
                        else:
                            self.pass_status = 'PASS'
                        self.after_cmd_output.remove(after_line_orig)
                        break
                    else:
                        if line[index] == after_line[index]:
                            self.pass_status = 'PASS'
                            self.delta_value = '0'
                        else:
                            self.pass_status = 'FAIL'
                            self.delta_value = '100%'
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
            self.summary[(self.test_values[0]['command'])]['FAIL'] += 1
            msg = jinja2.Template(str(self.test_values[0]['tests'][0]['err']))
            if self.post == '' or self.post == []:
                self.post = ['null'] * 12
            logger.info(msg.render(device=self.device, pre=self.pre, post=self.post, delta=self.delta_value))
        else:
            self.summary[(self.test_values[0]['command'])]['PASS'] += 1
            msg = jinja2.Template(str(self.test_values[0]['tests'][0]['info']))
            if not self.post:
                self.post = ['null'] * 12
            logger.debug(msg.render(device=self.device, pre=self.pre, post=self.post, delta=self.delta_value))

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
                if not skip_line:
                    self.summary[(self.test_values[0]['command'])]['FAIL'] += 1
                    self.post = after_line.split()
                    self.pre = ['null', 'null', 'null', 'null', 'null', 'null', 'null', 'null']
                    try:
                        line_id = self.test_values[0]['tests'][0]['no-diff'][0]
                    except:
                        line_id = self.test_values[0]['tests'][0]['delta'][0]
                        self.delta_value = '100%'
                    self.pre[line_id] = self.post[line_id]
                    msg = jinja2.Template(str(self.test_values[0]['tests'][0]['err']))
                    logger.info(msg.render(device=self.device, pre=self.pre, post=self.post, delta=self.delta_value))

    def print_totals(self):
        """ Print command test results for all lines of that command output """
        logger = logging.getLogger("BaselineParser")
        if self.summary[(self.test_values[0]['command'])]['FAIL'] == 0:
            if self.summary[(self.test_values[0]['command'])]['PASS'] == 0:
                if self.test_values[0]['ignore-null']:
                    logger.info("PASS! No output matched\n")
                    self.summary[(self.test_values[0]['command'])]['PASS'] += 1
                else:
                    logger.info("FAIL! No output matched\n")
                    self.summary[(self.test_values[0]['command'])]['FAIL'] += 1
            else:
                logger.info("PASS! All " + str(self.summary[(self.test_values[0]['command'])]['PASS']) + " tests passed!\n")
        else:
            logger.info("FAIL! " + str(self.summary[(self.test_values[0]['command'])]['PASS']) + " tests passed, " + \
                  str(self.summary[(self.test_values[0]['command'])]['FAIL']) + " tests failed!\n")

    def config_diff(self):
        """ Run diff on before and after config """
        logger = logging.getLogger("BaselineParser")
        self.summary['show configuration'] = {'PASS': 0, 'FAIL': 0}
        cmds = {'JUNOS': 'show configuration',
                'IOS': 'show run',
                'XR': 'show configuration running-config',
                'TiMOS': 'admin display-config'}
        logger.info("******** Command: " + cmds[self.device.os_type] + " ********")
        try:
            before_cfg = self.device.output['before'][(cmds[self.device.os_type])]
            after_cfg = self.device.output['after'][(cmds[self.device.os_type])]
        except KeyError:
            logger.info("ERROR: " + (cmds[self.device.os_type] + " not found in baseline\n"))
            self.summary['show configuration']['FAIL'] = 1
            return

        diff = difflib.unified_diff(before_cfg, after_cfg)
        cfg_diff = '\n'.join(diff)
        if cfg_diff:
            logger.info("FAILED! " + self.device.hostname + " configuation changed")
            for line in cfg_diff.splitlines():
                if '@@' in line:
                    line = '=' * 36
                if '+++' not in line and '---' not in line and line != '':
                    logger.debug(line)
                    if line[0] == '-' or line[0] == '+':
                        self.summary['show configuration']['FAIL'] += 1
            logger.info('\n')
        else:
            logger.info("PASS! No changes in " + self.device.hostname + " configuration\n")
            self.summary['show configuration']['PASS'] += 1

    def test_ping_output(self):
        """ Run ping tests """
        logger = logging.getLogger("BaselineParser")
        logger.info("******** Testing ping commands ********")
        self.ping_totals = {"PASS": 0, "FAIL": 0, "SKIP": 0}
        self.summary['ping checks'] = {'PASS': 0, 'FAIL': 0}
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
            self.summary['ping checks']['PASS'] = self.ping_totals['PASS']
        else:
            logger.info("FAIL! " + str(self.ping_totals['PASS']) + " tests passed, " + \
                   str(self.ping_totals['FAIL']) + " tests failed!\n")
            self.summary['ping checks']['FAIL'] = self.ping_totals['FAIL']

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
        if not found_match:
            self.ping_totals['SKIP'] += 1
            return
        # Look for the results line in the AFTER
        found_match = False
        for after_line in self.after_cmd_output:
            if iterword in after_line:
                after_line = after_line.split()
                found_match = True
                break
        if not found_match:
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

    def print_summary(self):
        """ Print test results summary """
        logger = logging.getLogger("BaselineParser")
        passed, failed = 0, 0
        failed_list = []
        for command in self.summary.keys():
            if self.summary[command]['PASS'] > 0:
                passed += 1
            if self.summary[command]['FAIL'] > 0:
                failed += 1
                failed_list.append(command)
        logger.warn(self.device.hostname + ' totals: \n'+ ('*' * 46) + '\n' + \
                    '  PASSED: ' + str(passed) + ' FAILED: ' + str(failed))
        for test in failed_list:
            fail_cnt = self.summary[test]['FAIL']
            logger.warn("  Failed - " + str(fail_cnt) + ' lines - ' + str(test))
        logger.warn("\n")
