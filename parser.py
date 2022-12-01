import os
from typing import List
from utils import regfile, twos_components

class opcodes(enumerate): # instruction opcodes
    movrr = 0b00000000
    movrm = 0b00000001
    movmr = 0b00000010
    movri = 0b00000011

    addrr = 0b00001000
    addmr = 0b00001001
    addrm = 0b00001010
    addri = 0b00001011
    subrr = 0b00001100
    submr = 0b00001101
    subrm = 0b00001110
    subri = 0b00001111

    call =  0b00110000

    jp  =   0b00011000
    jnz =   0b00011001
    jne =   0b00011010
    je  =   0b00011011
    jge =   0b00011100
    jle =   0b00011101
    jg  =   0b00011110
    jl  =   0b00011111

    push =  0b00111000
    pop  =  0b00111001

    ret =    0b00010000
    halt =   0b00010100
    passop = 0b00100000



variables = {} # variables from .data
functions_addresses = {} # function_addresses for call instructions
address_points = {} # address_poinst for jump instructions

instruction_stack = []

def get_number_of_bytes(instruction: int) -> int:
    opcode = instruction & ((1 << 8) - 1)
    if opcode in [0b00010000, 0b00010100, 0b00100000]:
        return 1
    elif opcode in [0b00000000,0b00001000, 0b00001100]:
        return 2
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
            return parsed + (lop << 8) + (rop << 12)
        elif op == 'movrm':
            parsed = opcodes.movrm
            lop = regfile[lop]
            rop = int(rop, 16)
            return parsed + (lop << 8) + (rop << 16)
        elif op == 'movmr':
            parsed = opcodes.movmr
            lop = int(lop, 16)
            rop = regfile[rop]
            return parsed + (lop << 16) + (rop << 12)
        elif op == 'movri':
            parsed = opcodes.movri
            lop = regfile[lop]
            if rop in variables.keys():
                rop = variables[rop]
            else:
                rop = int(rop, 16)
            rop = twos_components(rop)
            print(rop)
            return parsed + (lop << 8) + (rop << 16)
        elif op == 'addrr':
            parsed = opcodes.addrr
            lop = int(regfile[lop], 16)
            rop = int(regfile[rop], 16)
            return parsed + (lop << 8) + (rop << 12)
        elif op == 'addrm':
            parsed = opcodes.addrm
            lop = regfile[lop]
            rop = int(rop, 16)
            return parsed + (lop << 8) + (rop << 16)
        elif op == 'addmr':
            parsed = opcodes.addmr
            lop = int(lop, 16)
            rop = regfile[rop]
            return parsed + (lop << 16) + (rop << 12)
        elif op == 'addri':
            parsed = opcodes.addri
            lop = regfile[lop]
            if rop in variables.keys():
                rop = variables[rop]
            else:
                rop = int(rop, 16)
            rop = twos_components(rop)
            return parsed + (lop << 8) + (rop << 16)
        elif op == 'subri':
            parsed = opcodes.subri
            lop = regfile[lop]
            if rop in variables.keys():
                rop = variables[rop]
            else:
                rop = int(rop, 16)
            rop = twos_components(rop)
            return parsed + (lop << 8) + (rop << 16)
        elif op == 'subrr':
            parsed = opcodes.subrr
            lop = regfile[lop]
            rop = regfile[rop]
            return parsed + (lop << 8) + (rop << 12)
        elif op == 'submr':
            parsed = opcodes.submr
            lop = int(lop, 16)
            rop = regfile[rop]
            return parsed + (rop << 12) + (lop << 16)
        elif op == 'subrm':
            parsed = opcodes.subrm
            lop = regfile[lop]
            rop = int(rop, 16)
            return parsed + (lop << 8) + (rop << 16)


    elif n == 2: # Type: operation left
        lop = instruction[1]
        if op == 'call':
            parsed = opcodes.call
            if lop in functions_addresses:
                lop = int(functions_addresses[lop], 16)
            else:
                lop = int(lop, 16)
            return parsed + (lop << 16)
        if op in ['jnz', 'je', 'jne', 'jp', 'jge', 'jg', 'jl', 'jle']:
            parsed = 0
            if op == 'jnz':
                parsed = opcodes.jnz
            elif op == 'je':
                parsed = opcodes.je
            elif op == 'jne':
                parsed = opcodes.jne
            elif op == 'jp':
                parsed = opcodes.jp
            elif op == 'jge':
                parsed = opcodes.jge
            elif op == 'jg':
                parsed = opcodes.jg
            elif op == 'jl':
                parsed = opcodes.jl
            elif op == 'jle':
                parsed = opcodes.jle
            
            if lop not in address_points.keys():
                raise Exception('Unknown address point: .{}'.format(lop))
            parsed += (address_points[lop] << 16)

            return parsed

        elif op == 'push':
            parsed = opcodes.push
            lop = regfile[lop]
            return parsed + (lop << 8)
        elif op == 'pop':
            parsed = opcodes.pop
            lop = regfile[lop]
            return parsed + (lop << 8)
    
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
    
    cur_line = 0 # current line
    section_type = 0 # for current file section

    for line in data:
        if not line:
            continue
        if line[0] == '.':
            line_len = len(line)
            if line_len != 5 and line_len > 1 or (line_len == 5 and line[1:5] != 'text' and line[1:5] != 'data'):
                address_points[line[1: len(line)]] = instruction_address # getting address point for loops
                print(address_points)
            elif line_len == 5:
                if line[1:5] == 'text':
                    section_type = 2
                elif line[1:5] == 'data':
                    section_type = 1
            else:
                raise Exception('Irregular address {}'.format(line[1:line_len]))
        elif '<' in line and '>' in line: # detecting function
            if section_type == 2: # if current section is .text
                parsed = line.split('<')[1].split(':')
                function_name = parsed[0]
                function_address = int(parsed[1].split('>')[0], 16)
                functions_addresses[function_name] = function_address
                instruction_address = function_address
                if function_name == "main":
                    pc_val = function_address
                    entry_point = cur_line
            else:
                raise Exception('function declaration should be in .text section: {}'.format(line))
        elif section_type == 2:
            instruction_address+=6

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
            cur_line += 1
            continue
        if section_type == 1: # if current section is .data
            parse_variable(line) # parsing variable
        elif '<' in line and '>' in line: # detecting function
            if section_type == 2: # if current section is .text
                parsed = line.split('<')[1].split(':')
                function_name = parsed[0]
                function_address = int(parsed[1].split('>')[0], 16)
                functions_addresses[function_name] = function_address
                instruction_address = function_address
                if function_name == "main":
                    pc_val = function_address
                    entry_point = cur_line
            else:
                raise Exception('function declaration should be in .text section: {}'.format(line))
        elif section_type == 2:
                # Current line is instruction
                splited_line = line.split(' ') # split line
                instruction = parse_instruction(splited_line) # getting int instruction value
                num_of_bytes = get_number_of_bytes(instruction)
                computer.writeMem(instruction_address,
                                  instruction.to_bytes(num_of_bytes, 'little')) # writting instruction into memory
                instruction_address += 6 # increasing instruction_address by 4 to get instruction address for next instruction
        cur_line += 1 
    computer.set_pc(pc_val) # setting init program counter value
