#!/usr/bin/env python
"""
baseline_compare module to reuse existing log files to save resources
john.tishey@windstream.com 2017
"""


class Run(object):
    """ Method is called when an existing log file is found and override is false """
    def __init__(self, CONFIG):
        """ Gets CONFIG object from baseline_parser and output based on that """
        # All we really have to do is open the log file and figure out how to print it
        try:
            with open(CONFIG.mop_path + '/BaselineParser.log') as _f:
                prev_run = _f.readlines()
        except:
            print("ERROR: Could not open log file")
            exit(1)

        print("Using log file from previous check, use -o to override and run new checks\n")

        sum_flag, cfg_flag, dev_flag = False, False, False
        for line in prev_run:
            line = line.rstrip()
            if line.startswith('Running'):
                sum_flag = False
                if line.split()[1] in CONFIG.stest:
                    dev_flag = True
                else:
                    dev_flag = False
            elif 'Command: show run' in line or 'Command: show config' in line:
                cfg_flag = True
            elif 'Testing ping commands' in line:
                cfg_flag = False
            elif 'totals:' in line:
                sum_flag = True

            # set dev_flag to true if not set so it outputs all devs
            if len(CONFIG.stest) == 0:
                dev_flag = True

            if dev_flag is True:
                #VERBOSE = 1
                if CONFIG.verbose == 1:
                    print(line)
                # NORMAL = 0
                elif CONFIG.verbose == 0:
                    if line.startswith('PASSED') is False:
                        print(line)
                # CCONFIG = 20
                elif CONFIG.verbose == 20:
                    if cfg_flag is True:
                        print(line)
                # SUMMARY = 40
                elif CONFIG.verbose == 40:
                    if sum_flag is True:
                        print(line)
        exit()
