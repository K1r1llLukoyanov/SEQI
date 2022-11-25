import os
from typing import List

regfile: dict[str, int] = {'EAX':  0x0,
                           'EBX':  0x1,
                           'ECX':  0x2,
                           'EDX':  0x3,
                           'ESI':  0x4,
                           'EDI':  0x5,
                           'EBP':  0x6,
                           'ESP':  0x7,
                           'R8D':  0x8,
                           'R9D':  0x9,
                           'R10D': 0xA,
                           'R11D': 0xB,
                           'R12D': 0xC,
                           'R13D': 0xD,
                           'R14D': 0xE,
                           'R15D': 0xF
                           }


class opcodes(enumerate):
    MOVRR = 0b000000
    MOVRM = 0b000001
    MOVMR = 0b000010
    MOVRI = 0b000011
    ADDRR = 0b000100
    ADDMR = 0b000101
    ADDRM = 0b000110
    ADDRI = 0b000111
    CALL = 0b001100
    RET = 0b010000
    HALT = 0b001000
    PASS = 0b100000


variables = {}
functions_addresses = {}


def parse_instruction(instruction: List['str']):
    global opcodes
    print(instruction)
    op = instruction[0]
    n = len(instruction)
    if n == 3:
        lop, rop = instruction[1: 3]
        lop = lop.split(',')[0]
        parsed = 0
        if op == 'MOVRR':
            parsed = opcodes.MOVRR << 26
            lop = regfile[lop]
            rop = regfile[rop]
            return parsed + (lop << 22) + (rop << 18)
        elif op == 'MOVRM':
            parsed = opcodes.MOVRM << 26
            lop = regfile[lop]
            rop = int(rop, 16)
            return parsed + (lop << 22) + (rop << 18)
        elif op == 'MOVMR':
            parsed = opcodes.MOVMR << 26
            lop = int(lop, 16)
            rop = regfile[rop]
            return parsed + (lop << 22) + (rop << 18)
        elif op == 'MOVRI':
            parsed = opcodes.MOVRI << 26
            lop = regfile[lop]
            if rop in variables.keys():
                rop = int(variables[rop], 16)
            else:
                rop = int(rop, 16)
            return parsed + (lop << 22) + (rop << 18)
        elif op == 'ADDRR':
            parsed = opcodes.ADDRR << 26
            lop = int(regfile[lop], 16)
            rop = int(regfile[rop], 16)
            return parsed + (lop << 22) + (rop << 18)
        elif op == 'ADDRM':
            parsed = opcodes.ADDRM << 26
            lop = regfile[lop]
            rop = int(rop, 16)
            return parsed + (lop << 22) + (rop << 18)
        elif op == 'ADDMR':
            parsed = opcodes.ADDMR << 26
            lop = int(lop, 16)
            rop = regfile[rop]
            return parsed + (lop << 22) + (rop << 18)
        elif op == 'ADDRI':
            parsed = opcodes.ADDRI << 26
            rop = regfile[rop]
            if lop in variables.keys():
                lop = variables[lop]
            else:
                lop = int(lop, 16)
            return parsed + (lop << 22) + (rop << 18)
    elif n == 2:
        lop = instruction[1]
        if op == 'CALL':
            parsed = opcodes.CALL << 26
            if lop in functions_addresses:
                lop = int(functions_addresses[lop], 16)
            else:
                lop = int(lop, 16)
            return parsed + (lop << 22)
    elif n == 1:
        if op == 'HALT':
            parsed = opcodes.HALT << 26
            return parsed
        elif op == 'PASS':
            return opcodes.PASS << 26
        elif op == 'RET':
            return opcodes.RET << 26
    else:
        print('{} - unknown instruction'.format(op))
        exit(0)


def parse_variable(encoded):
    var_name, var_value = encoded.split(' ')
    variables[var_name] = var_value
    print(variables)


def asm_parser(file_name, computer):
    global entry_point
    entry_point = -1
    pc_val = 0
    instruction_address = -1
    f = open(file_name)
    file_size = os.path.getsize(file_name)
    data = f.read(file_size).split('\n')
    data = list(map(lambda x: x.strip(' ').lstrip(' '), data))
    section_type = 0
    cur_line = 0
    for line in data:
        if not line:
            cur_line += 1
            continue
        if line[0] == '.':
            if len(line) > 4:
                if line[1:5] == 'text':
                    section_type = 2
                elif line[1:5] == 'data':
                    section_type = 1
            cur_line
            continue
        if section_type == 1:
            parse_variable(line)
        elif section_type == 2:
            if '<' in line and '>' in line:
                if 'main' in line:
                    pc_val = int(line.split('main')[1].split(
                        ':')[1].split('>')[0], 16)
                    entry_point = cur_line
                    instruction_address = pc_val
                else:
                    parsed = line.split('<')[1].split(':')
                    function_name = parsed[0]
                    function_address = int(parsed[1].split('>')[0], 16)
                    functions_addresses[function_name] = function_address
                    instruction_address = function_address
            else:
                splited_line = line.split(' ')
                instruction = parse_instruction(splited_line)
                instruction = instruction + instruction_address + 1
                computer.writeMem(instruction_address,
                                  instruction.to_bytes(4, 'big'))
                instruction_address += 1
        cur_line += 1
    computer.set_pc(pc_val)
