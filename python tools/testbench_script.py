command_list = [ \
b':BUS_.ROUT.WRTE.ADDR.\x00\x00\x00\x00.DATA.MLKJ!', \
b':BUS_.MMWR.CTRL.RSTR!', \
b':BUS_.MMWR.CTRL.SETR!', \
b':BUS_.MMWR.CTRL.RSTC!', \
b':BUS_.MMWR.CTRL.SETC!', \
b':BUS_.MMWR.MISC.DATA.\x00\x00\x00\x01!', \
b':BUS_.MMWR.MISC.DATA.\x01\x00\x00\x01!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x1f.DATA.\x00\x00\x03\xe8!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x1e.DATA.\x01\x94\x10\x10!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x1d.DATA.\x00\x00\x00\x00!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x1c.DATA.\xff\xff\xd8\xf0!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x1b.DATA.\xff\xfc\xf2\xc0!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x1a.DATA.\t\xf4\xff\\!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x19.DATA.O\xa1\x06\x00!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x18.DATA.\x000\x0f\xed!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x17.DATA.\x01@\x03\xf0!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x16.DATA.\x12\x00\x06\x00!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x15.DATA.;\x80\x02V!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x14.DATA.\x00\x149*!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x13.DATA.:O\x17S!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x12.DATA.\x01\xe8\x1c\x9c!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x11.DATA.\x1c\x9c]\xdc!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x10.DATA.\x00\x00\x00\x05!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x10.DATA.\x00\x00\x00\x07!', \
b':BUS_.MMWR.WRTE.ADDR.\x00\x00\x00\x10.DATA.\x00\x00\x00\x06!'
]

filename = "wrapper_tb.vhdl"
with open(filename, 'r') as file:
    # Locate script generation indicators
    command_generation_beg_token = "-- COMMAND GENERATION START"
    command_generation_end_token = "-- COMMAND GENERATION END"

    lines = file.readlines()
    line_number = 0
    while True:
        if lines[line_number].strip() == command_generation_beg_token:
            break
        line_number += 1
    command_generation_beg = line_number
    while True:
        if lines[line_number].strip() == command_generation_end_token:
            break
        line_number += 1
    command_generation_end = line_number

    begin = lines[:command_generation_beg + 1]
    end = lines[command_generation_end:]

    code = []
    code += begin
    code.append("\n")
    indent_level = lines[command_generation_beg].index("--")
    indent = " " * indent_level
    char_count = 0
    for command in command_list:
        for char in command:
            if char_count == 0:
                code.append(f"{indent}if counter = 102 then\n")
                code.append(f"{indent}    en <= '1';\n")
            else:
                code.append(f"{indent}elsif counter = {char_count + 102} then\n")
            code.append(f"{indent}    char <= x\"{hex(char)[2:].zfill(2)}\";\n")
            char_count += 1
    code.append(f"{indent}elsif counter = {char_count + 102} then\n")
    code.append(f"{indent}    en <= '0';\n")
    code.append(f"{indent}end if;\n")
    code.append("\n")
    code += end

# Write to file
with open(filename, 'w') as file:
    file.writelines(code)