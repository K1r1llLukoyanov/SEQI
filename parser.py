import os
from typing import List

regfile: dict[str, int] = {
    'eax':  0x0,
    'ebx':  0x1,
    'ecx':  0x2,
    'edx':  0x3,
    'esi':  0x4,
    'edi':  0x5,
    'ebp':  0x6,
    'esp':  0x7,
    'r8d':  0x8,
    'r9d':  0x9,
    'r10d': 0xA,
    'r11d': 0xB,
    'r12d': 0xC,
    'r13d': 0xD,
    'r14d': 0xE,
    'r15d': 0xF
}


class opcodes(enumerate):
    movrr = 0b000000
    movrm = 0b000001
    movmr = 0b000010
    movri = 0b000011
    addrr = 0b000100
    addmr = 0b000101
    addrm = 0b000110
    ADDRI = 0b000111
    call = 0b001100
    ret = 0b010000
    halt = 0b001000
    passop = 0b100000


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
        if op == 'movrr':
            parsed = opcodes.movrr << 26
            lop = regfile[lop]
            rop = regfile[rop]
            return parsed + (lop << 22) + (rop << 18)
        elif op == 'movrm':
            parsed = opcodes.movrm << 26
            lop = regfile[lop]
            rop = int(rop, 16)
            return parsed + (lop << 22) + rop
        elif op == 'movmr':
            parsed = opcodes.movmr << 26
            lop = int(lop, 16)
            rop = regfile[rop]
            return parsed + lop + (rop << 18)
        elif op == 'movri':
            parsed = opcodes.movri << 26
            lop = regfile[lop]
            if rop in variables.keys():
                rop = int(variables[rop], 16)
            else:
                rop = int(rop, 16)
            return parsed + (lop << 22) + rop
        elif op == 'addrr':
            parsed = opcodes.addrr << 26
            lop = int(regfile[lop], 16)
            rop = int(regfile[rop], 16)
            return parsed + (lop << 22) + (rop << 18)
        elif op == 'addrm':
            parsed = opcodes.addrm << 26
            lop = regfile[lop]
            rop = int(rop, 16)
            return parsed + (lop << 22) + rop
        elif op == 'addmr':
            parsed = opcodes.addmr << 26
            lop = int(lop, 16)
            rop = regfile[rop]
            return parsed + lop + (rop << 18)
        elif op == 'ADDRI':
            parsed = opcodes.ADDRI << 26
            rop = regfile[rop]
            if lop in variables.keys():
                lop = variables[lop]
            else:
                lop = int(lop, 16)
            return parsed + (lop << 22) + rop
    elif n == 2:
        lop = instruction[1]
        if op == 'call':
            parsed = opcodes.call << 26
            if lop in functions_addresses:
                lop = int(functions_addresses[lop], 16)
            else:
                lop = int(lop, 16)
            return parsed + lop
    elif n == 1:
        if op == 'halt':
            parsed = opcodes.halt << 26
            return parsed
        elif op == 'passop':
            return opcodes.passop << 26
        elif op == 'ret':
            return opcodes.ret << 26
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
                instruction = instruction
                computer.writeMem(instruction_address,
                                  instruction.to_bytes(4, 'big'))
                instruction_address += 4
        cur_line += 1
    computer.set_pc(pc_val)
