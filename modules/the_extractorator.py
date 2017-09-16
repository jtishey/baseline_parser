#!/usr/bin/env python
"""
baseline_compare module to extract commands and output from Pinky_Baseliner
john.tishey@windstream.com 2017
"""

# Step 1: Get the device hostname and Vendor/OS
def run(device):
    """ Get device and baselines """
    if device['os_type'] == 'JUNOS':
        #commands = get_commands_juniper()
        extract_junos(device)
    elif device['os_type'] == 'IOS':
        #commands = get_commands_ios()
        #extract_ios(device)
        print("ERROR: IOS not supported yet")
        return
    elif device['os_type'] == 'xr':
        #commands = get_commands_xr()
        #extract_xr(device)
        print("ERROR: XR not supported yet")
        return
    else:
        print("ERROR: Device OS not found or not yet supported")
        return ""


# Step 3: Split into individual commands
def extract_junos(device):
    """ extract commands from baselines """
    prompt = 'deip@' + device['hostname'] + '>'
    commands = {}
    # Open baseline files and loop through lines
    for _file in device['files']:
        with open(_file) as _f:
            baseline_text = _f.readlines()
        for line in baseline_text:
            line = line.rstrip()
            # if there's a prompt, set it as a new command
            # and capture subsequent lines under it
            if prompt in line:
                current_command = line
                commands[current_command] = []
            else:
                if current_command:
                    commands[current_command].append(line)
        