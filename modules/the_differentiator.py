#!/usr/bin/env python
"""
baseline_compare module to compare command output from Pinky_baseliner 
john.tishey@windstream.com 2017
"""

# Step 1: Loop through commands, using pre-determined logic where available
def run(device):
    """ Compare output of commands according to test rules
        device['output']['before'] and device['output']['after'] contain the outputs """
    if device['os_type'] == 'JUNOS':
        pass
