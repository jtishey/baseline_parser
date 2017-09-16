#!/usr/bin/env python
"""
baseline_compare module to extract commands and output from Pinky_Baseliner
john.tishey@windstream.com 2017
"""

# Step 1: Get the device hostname and Vendor/OS
def run(device, before, after):
    """ Get device and baselines """
    if device['os_type'] == 'JUNOS':
        #commands = get_commands_juniper()
        extract_junos(device, before, after)
    elif device['os_type'] == 'IOS':
        #commands = get_commands_ios()
        extract_ios(device, before, after)
    elif device['os_type'] == 'xr':
        #commands = get_commands_xr()
        extract_xr(device, before, after)
    else:
        print("ERROR: Device OS not yet supported")
        return ""

## Step 2: Get command list or prompt string
#def get_commands_juniper():
#    """ get commands list """
#
#def get_commands_ios():
#    """ get commands list """
#
#def get_commands_xr():
#    """ get commands list """


# Step 3: Split into individual commands
def extract_junos(device, before, after):
    """ extract commands from baselines """
    prompt = 'deip@' + device['hostname'] + '>'


def extract_ios(device, before, after, commands):
    """ extract commands from baselines """
    pass


def extract_xr(device, before, after, commands):
    """ extract commands from baselines """
    pass


# Step 4: Do any formatting and return