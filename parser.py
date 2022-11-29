import os
from typing import List
from utils import regfile, twos_components

class opcodes(enumerate): # instruction opcodes
    movrr = 0b000000
    movrm = 0b000001
    movmr = 0b000010
    movri = 0b000011

    addrr = 0b000100
    addmr = 0b000101
    addrm = 0b000110
    addri = 0b000111

    call = 0b001000

    jp = 0b001100
    jnz = 0b001101
    jne = 0b001110
    je = 0b001111

    ret = 0b010000

    halt = 0b010100

    passop = 0b100000


variables = {} # variables from .data
functions_addresses = {} # function_addresses for call instructions
address_points = {} # address_poinst for jump instructions

def get_number_of_bytes(instruction: int) -> int:
    #opcode = instruction & ((1 << 6) - 1)
    #if opcode in [0b010000, 0b010100, 0b100000]:
    #    return 1
    #elif opcode in [0b000000,0b000100]:
    #    return 2
    return 6

def parse_instruction(instruction: List['str']) -> int: 
    global opcodes
    print(instruction)
    op = instruction[0] # operation
    n = len(instruction) # len of instruction

    if n == 3: # Type: operation left, right
        lop, rop = instruction[1: 3]
        lop = lop.split(',')[0]
        parsed = 0
        if op == 'movrr':
            parsed = opcodes.movrr
            lop = regfile[lop]
            rop = regfile[rop]
            return parsed + (lop << 6) + (rop << 10)
        elif op == 'movrm':
            parsed = opcodes.movrm
            lop = regfile[lop]
            rop = int(rop, 16)
            return parsed + (lop << 6) + (rop << 14)
        elif op == 'movmr':
            parsed = opcodes.movmr
            lop = int(lop, 16)
            rop = regfile[rop]
            return parsed + (lop << 14) + (rop << 10)
        elif op == 'movri':
            parsed = opcodes.movri
            lop = regfile[lop]
            if rop in variables.keys():
                rop = variables[rop]
            else:
                rop = int(rop, 16)
            rop = twos_components(rop)
            print(rop)
            return parsed + (lop << 6) + (rop << 14)
        elif op == 'addrr':
            parsed = opcodes.addrr
            lop = int(regfile[lop], 16)
            rop = int(regfile[rop], 16)
            return parsed + (lop << 6) + (rop << 10)
        elif op == 'addrm':
            parsed = opcodes.addrm << 26
            lop = regfile[lop]
            rop = int(rop, 16)
            return parsed + (lop << 6) + (rop << 14)
        elif op == 'addmr':
            parsed = opcodes.addmr
            lop = int(lop, 16)
            rop = regfile[rop]
            return parsed + (lop << 14) + (rop << 10)
        elif op == 'addri':
            parsed = opcodes.addri
            lop = regfile[lop]
            if rop in variables.keys():
                rop = variables[rop]
            else:
                rop = int(rop, 16)
            rop = twos_components(rop)
            return parsed + (lop << 6) + (rop << 14)

    elif n == 2: # Type: operation left
        lop = instruction[1]
        if op == 'call':
            parsed = opcodes.call
            if lop in functions_addresses:
                lop = int(functions_addresses[lop], 16)
            else:
                lop = int(lop, 16)
            return parsed + (lop << 14)
        elif op == 'jnz':
            parsed = opcodes.jnz
            lop = address_points[lop]
            return parsed + (lop << 14)
        elif op == 'je':
            parsed = opcodes.je
            lop = address_points[lop]
            return parsed + (lop << 14)
        elif op == 'jne':
            parsed = opcodes.jne
            lop = address_points[lop]
            return parsed + (lop << 14)
        elif op == 'jp':
            parsed = opcodes.jp
            lop = address_points[lop]
            return parsed + (lop << 14)
    
    elif n == 1: # Type: operation
        if op == 'halt':
            parsed = opcodes.halt
            return parsed
        elif op == 'passop':
            return opcodes.passop
        elif op == 'ret':
            return opcodes.ret
    else: # if operation is unknown
        print('{} - unknown instruction'.format(op))
        exit(0)


def parse_variable(encoded: str) -> None:
    """
        Function for parsing variable
        def parse_variable(encoded: str) -> None:
        str - string of type: variable_name variable_value
    """
    var_name, var_value = encoded.split(' ')
    variables[var_name] = int(var_value, 16)
    print(variables)


def asm_parser(file_name: str, computer) -> None:
    """
        Function for getting assember instruction, parsing them and loading into memory
        def asm_parser(file_name: str, computer: SEQ) -> None:
    """
    global entry_point
    entry_point = -1
    pc_val = 0
    instruction_address = -1
    f = open(file_name)
    file_size = os.path.getsize(file_name)
    data = f.read(file_size).split('\n') # get lines without \n character
    data = list(map(lambda x: x.rstrip(' ').rstrip('\t').lstrip(' ').lstrip('\t'), data)) # delete spaces from left and from right of all lines
    section_type = 0 # for current file section
    cur_line = 0 # current line
    for line in data:
        if not line:    # line is empty
            cur_line += 1
            continue
        if line[0] == '.': # line begins with .
            line_len = len(line) # len of the line
            if line_len == 5: # checking for len (to not get out of range)
                if line[1:5] == 'text': # line is .text
                    section_type = 2    # set section type to 2
                elif line[1:5] == 'data': # line is .data
                    section_type = 1    # set section type to 1
            elif line_len > 1:
                address_points[line[1: len(line)]] = instruction_address # getting address point for loops
                print(address_points)
            cur_line += 1
            continue
        if section_type == 1: # if current section is .data
            parse_variable(line) # parsing variable
        elif section_type == 2: # if current section is .text
            if '<' in line and '>' in line: # detecting function
                parsed = line.split('<')[1].split(':')
                function_name = parsed[0]
                function_address = int(parsed[1].split('>')[0], 16)
                functions_addresses[function_name] = function_address
                instruction_address = function_address
                if function_name == "main":
                    pc_val = function_address
                    entry_point = cur_line
                cur_line+=1
            else:
                # Current line is instruction
                splited_line = line.split(' ') # split line
                instruction = parse_instruction(splited_line) # getting int instruction value
                num_of_bytes = get_number_of_bytes(instruction)
                computer.writeMem(instruction_address,
                                  instruction.to_bytes(num_of_bytes, 'little')) # writting instruction into memory
                instruction_address += num_of_bytes # increasing instruction_address by 4 to get instruction address for next instruction
        cur_line += 1 
    computer.set_pc(pc_val) # setting init program counter value
