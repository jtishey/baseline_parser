#!/usr/bin/env python
"""
baseline_compare module to extract commands and output from Pinky_Baseliner
john tishey 2017
"""

# Step 1: Get the device hostname and Vendor/OS
def run(device):
    """ Get device and baselines """
    if device.os_type == 'JUNOS':
        prompt = 'deip@' + device.hostname
    elif device.os_type == 'IOS':
        prompt = device.hostname + '#'
    elif device.os_type == 'XR':
        prompt = 'RP/0/RSP0/CPU0:' + device.hostname + '#'    
    elif device.os_type == 'TiMOS':
        prompt = ':' + device.hostname + '#'
    else:
        print("ERROR: Device OS not found or not yet supported")
        return ""
    output = extract(device, prompt)
    return output

# Step 3: Split into individual commands
def extract(device, prompt):
    """ extract commands from baselines """
    # Open baseline files and loop through lines
    output = {}
    for each_file in device.files:
        with open(each_file) as _f:
            baseline_text = _f.readlines()
        commands = {}
        current_command = ''
        for line in baseline_text:
            line = line.rstrip()
            # if there's a prompt, set it as a new command
            # and capture subsequent lines under it
            if prompt in line:
                if line[-1] != '>' or line[-1] != '#':
                    line = line.replace(prompt + '-re0>', '')
                    line = line.replace(prompt + '-re1>', '')
                    line = line.replace('A' + prompt, '')
                    line = line.replace('B' + prompt, '')
                    line = line.replace(prompt, '')
                    current_command = line
                    commands[current_command] = []
            else:
                if current_command is not '':
                    if line != '' and line != '{master}':
                        commands[current_command].append(line)
        if device.config.before_kw in each_file:
            output['before'] = commands
        else:
            output['after'] =  commands
    return output

