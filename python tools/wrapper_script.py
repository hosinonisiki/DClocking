from configuration_list import *

configurations = [FL9627_configuration, FL1010_configuration, FL9613_configuration]
fmc_name = ["fmc1_lpc", "fmc2_lpc", "fmc3_hpc"]
fmc_id = [1, 2, 3]
for i in range(3):
    configurations[i].fmc_name = fmc_name[i]
    configurations[i].fmc_id = fmc_id[i]
    configurations[i].make()

filename = "wrapper.vhdl"
with open(filename, 'r') as file:
    # Locate script generation indicators
    pin_declaration_beg_token = "-- PIN DECLARATION GENERATION START"
    pin_declaration_end_token = "-- PIN DECLARATION GENERATION END"
    signal_declaration_beg_token = "-- SIGNAL DECLARATION GENERATION START"
    signal_declaration_end_token = "-- SIGNAL DECLARATION GENERATION END"
    instantiation_code_beg_token = "-- ADAPTER INSTANTIATION GENERATION START"
    instantiation_code_end_token = "-- ADAPTER INSTANTIATION GENERATION END"
    signal_assignment_beg_token = "-- SIGNAL ASSIGNMENT GENERATION START"
    signal_assignment_end_token = "-- SIGNAL ASSIGNMENT GENERATION END"
    io_buffer_beg_token = "-- IO BUFFER GENERATION START"
    io_buffer_end_token = "-- IO BUFFER GENERATION END"

    lines = file.readlines()
    line_number = 0
    while True:
        if lines[line_number].strip() == pin_declaration_beg_token:
            break
        line_number += 1
    pin_declaration_beg = line_number
    while True:
        if lines[line_number].strip() == pin_declaration_end_token:
            break
        line_number += 1
    pin_declaration_end = line_number
    while True:
        if lines[line_number].strip() == signal_declaration_beg_token:
            break
        line_number += 1
    signal_declaration_beg = line_number
    while True:
        if lines[line_number].strip() == signal_declaration_end_token:
            break
        line_number += 1
    signal_declaration_end = line_number
    while True:
        if lines[line_number].strip() == instantiation_code_beg_token:
            break
        line_number += 1
    instantiation_code_beg = line_number
    while True:
        if lines[line_number].strip() == instantiation_code_end_token:
            break
        line_number += 1
    instantiation_code_end = line_number
    while True:
        if lines[line_number].strip() == signal_assignment_beg_token:
            break
        line_number += 1
    signal_assignment_beg = line_number
    while True:
        if lines[line_number].strip() == signal_assignment_end_token:
            break
        line_number += 1
    signal_assignment_end = line_number
    while True:
        if lines[line_number].strip() == io_buffer_beg_token:
            break
        line_number += 1
    io_buffer_beg = line_number
    while True:
        if lines[line_number].strip() == io_buffer_end_token:
            break
        line_number += 1
    io_buffer_end = line_number

    begin = lines[:pin_declaration_beg + 1]
    post_pin_declaration = lines[pin_declaration_end:signal_declaration_beg + 1]
    post_signal_declaration = lines[signal_declaration_end:instantiation_code_beg + 1]
    post_instantiation_code = lines[instantiation_code_end:signal_assignment_beg + 1]
    post_signal_assignment = lines[signal_assignment_end:io_buffer_beg + 1]
    end = lines[io_buffer_end:]

    # Generate code
    code = []
    code += begin
    code.append("\n")
    indent_level = lines[pin_declaration_beg].index('--')
    indent = ' ' * indent_level
    for i in range(2):
        code += list(map(lambda x: indent + x, configurations[i].get_code('pin_declaration', 'list')))
        code.append("\n")
    code += list(map(lambda x: indent + x, configurations[2].get_code('pin_declaration', 'list')[:-1]))
    code.append(indent + configurations[2].get_code('pin_declaration', 'list')[-1][:-2] + "\n") # Remove the last comma
    code.append("\n")
    code += post_pin_declaration
    code.append("\n")
    indent_level = lines[signal_declaration_beg].index('--')
    indent = ' ' * indent_level
    for i in range(3):
        code += list(map(lambda x: indent + x, configurations[i].get_code('signal_declaration', 'list')))
        code.append("\n")
    code += post_signal_declaration
    code.append("\n")
    indent_level = lines[instantiation_code_beg].index('--')
    indent = ' ' * indent_level
    for i in range(3):
        code += list(map(lambda x: indent + x, configurations[i].get_code('instantiation_code', 'list'))
                     )
        code.append("\n")
    code += post_instantiation_code
    code.append("\n")
    indent_level = lines[signal_assignment_beg].index('--')
    indent = ' ' * indent_level
    for i in range(3):
        code += list(map(lambda x: indent + x, configurations[i].get_code('signal_assignment', 'list')))
        code.append("\n")
    code += post_signal_assignment
    code.append("\n")
    indent_level = lines[io_buffer_beg].index('--')
    indent = ' ' * indent_level
    for i in range(3):
        code += list(map(lambda x: indent + x, configurations[i].get_code('io_buffer', 'list')))
        code.append("\n")
    code += end

# Write to file
with open(filename, 'w') as file:
    file.writelines(code)

