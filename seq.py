import struct
from typing import List
from asm_parser import asm_parser
from time import sleep
from utils import regfile, twos_components


class opcodes(enumerate):  # Instruction opcodes(6 bits lenght)
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

    call = 0b00110000

    jp = 0b00011000
    jnz = 0b00011001
    jne = 0b00011010
    je = 0b00011011
    jge = 0b00011100
    jle = 0b00011101
    jg = 0b00011110
    jl = 0b00011111

    push = 0b00111000
    pop = 0b00111001

    ret = 0b00010000
    halt = 0b00010100
    passop = 0b00100000


class SEQ(object):
    def __init__(self, bits, memory) -> None:
        self.bits: int = bits  # System type
        self.memsize: int = memory  # memory size (in bytes)
        self.memory: bytearray = bytearray(memory)  # memory bytearray

        self.status_flags = {
            'CF': 0b0,  # carry flag
            'PF': 0b0,  # parity flag
            'AF': 0b0,  # adjust flag
            'ZF': 0b0,  # zero flag
            'SF': 0b0,  # sign flag
            'TF': 0b0,  # trap flag
            'IF': 0b0,  # Interrupt enable flag
            'DF': 0b0,  # direction flag
            'OF': 0b0,  # overflow flag
        }  # Status flags for last operation

        self.registers: List[bytearray] = bytearray(
            4*16)  # registers byte array

        # Decode stage registers
        self.decode_registers: dict[str, None | int] = {
            'stat': 0b0000,
            'icode': None,
            'ifun': None,
            'rA': None,
            'rB': None,
            'valP': None
        }

        # Execute stage registers
        self.execute_registers: dict[str, None | int] = {
            'stat': 0b0000,
            'icode': None,
            'ifun': None,
            'valA': None,
            'valB': None,
            'dstE': None,
            'dstM': None,
            'srcA': None,
            'dstM': None,
            'srcA': None,
            'srcB': None
        }

        # Memory stage registers
        self.memory_registers: dict[str, None | int] = {
            'stat': 0b000,
            'icode': None,
            'valE': None,
            'valA': None,
            'dstE': None,
            'dstM': None
        }

        # Write back stage registers
        self.write_back_registers: dict[str, None | int] = {
            'stat': 0b0000,
            'icode': None,
            'valE': None,
            'valM': None,
            'dstE': None,
            'dstM': None
        }

        # Stage activation flags
        # 0 - Fetch stage
        # 1 - Decode stage
        # 2 - Execute stage
        # 3 - Memory stage
        # 4 - Write back stage
        self.stage_active = [False]*5

        # Program counter
        self.PC = 0x0000

        # Memory control flag
        self.memory_control = 0b00

        # Write back control flag
        self.write_back_control = 0b0

    def readMem(self, addr: str | int, num_of_bytes: int) -> int:
        """
            Function for reading from memory
            def readMem(memory_address: str | int)

            memory_address - string with hex number or int

            It reads 4 bytes:
                1:  memory_address
                2:  memory_address+1
                3:  memory_address+2
                4:  memory_address+3
            from memory.
        """
        if type(addr) == type('str'):
            addr = int(addr, 16)
        return int.from_bytes(self.memory[addr: addr+num_of_bytes], 'little')

    def writeMem(self, addr: int | str, data: bytearray) -> bool:
        """
            Function for writting into memory
            def writeMem(memory_address: int | str, data: bytearray)

            memory_address - int or string with hex number

            Function writes each by of the data into memory beginning with byte at memory_address.
        """
        if type(addr) == type(''):
            addr = int(addr, 16)
        for i in range(len(data)):
            self.memory[addr + i] = data[i]

    def writeReg(self, reg: int, data: bytearray) -> None:
        """
            Function for writting into registers
            def writeRed(reg: int, data: bytearray)

            reg = 0: eax
            reg = 1: ebx
            ...
        """
        for i in range(4):
            self.registers[reg*4 + i] = data[i]

    def readReg(self, reg):
        """
            Function for reading from registers
        """
        return struct.unpack('<I', self.registers[4*reg: 4*reg+4])[0]

    def fetch_instruction(self, instruction_address):
        """
            Fethching instruction
            def fetch_instruction(self, instruction_address: int | str)

            instruction_address - int or string with number.

            0       7 8         11 12         15 16             47
            opcode      reg_A        reg_B          immediate

            0-7    bits - opcode (6 bits)
            8-11   bits - destination register (4 bits)
            12-15  bits - source register (4 bits)
            16-47  bits - immediate value (32 bits)
        """

        instruction = self.readMem(instruction_address, 1)
        new_PC = instruction_address

        if instruction in [0b010000, 0b010100, 0b100000]:
            instruction = self.readMem(instruction_address, 1)
            new_PC += 1
        elif instruction in [0b000000, 0b000100]:
            instruction = self.readMem(instruction_address, 2)
            new_PC += 2
        else:
            instruction = self.readMem(instruction_address, 6)
            new_PC += 6
        opcode = instruction & ((1 << 8) - 1)
        loperand = (instruction >> 8) & ((1 << 4) - 1)
        roperand = (instruction >> 12) & ((1 << 4) - 1)
        immediate = twos_components(instruction >> 16)
        print(immediate)

        # Operation data is an array with 3 items
        operation_data = [opcode, loperand, roperand, new_PC]

        if opcode in [opcodes.movmr, opcodes.addmr, opcodes.jnz, opcodes.je, opcodes.jp, opcodes.jne, opcodes.call, opcodes.jg, opcodes.jl, opcodes.jle, opcodes.jge]:
            operation_data[1] = immediate  # Immediate value is left operand
        elif opcode in [opcodes.movrm, opcodes.addrm, opcodes.movri, opcodes.addri, opcodes.subri, opcodes.subrm, opcodes.submr]:
            operation_data[2] = immediate  # Immediate value is right operand

        return operation_data

    def compute(self):
        """
            Function for reading and executing instructions from memory
            def compute()

            It fetches instructions from memory at address stored in self.PC(program counter).

            It gets opcode, left_operand, right_operang, immediate value from function fetch_instruction(instruction_address).

        """
        stop_computing = False
        finish_prev = 3
        top_stage = 4
        bottom_stage = -1
        finish_write_back = False
        update_flag = False
        while not stop_computing or finish_prev > 0:
            print()
            print(self.PC)
            opcode, loper, roper, new_PC = self.fetch_instruction(
                self.PC)
            self.stage_active[0] = True
            complete_steps = ""
            for i in range(top_stage, bottom_stage, -1):
                if not self.stage_active[i]:
                    continue
                if i == 4:
                    """
                        SEQ's Write-back stage
                        At this stage data is written back to destination register
                    """
                    if not self.write_back_registers['stat'] == 0b0000:  # Checking for errors
                        print('Write back error')
                    self.writeReg(
                        self.write_back_registers['valE'], self.write_back_registers['valM'].to_bytes(4, 'little'))
                    self.write_back_control = 0
                    if finish_write_back:  # Finishing write-back for source register at execute stage
                        print('Written back: {} {}'.format(
                            self.write_back_registers['valE'], self.write_back_registers['valM']))
                        top_stage = 4
                        bottom_stage = -1   # executing all active stages
                    self.stage_active[4] = False            # Disable stage
                    complete_steps = "W" + complete_steps   # Add to completed stages info
                elif i == 3:
                    """
                        SEQ's Memory stage
                        At this stage data is written into memory or sent to written back stage
                    """
                    if not self.memory_registers['stat'] == 0b0000:  # Checking for errors
                        print('Memory stage error')
                    elif self.memory_control == 1:  # Writting into memory
                        print('M: Writing into memory: {}, {}'.format(
                            self.memory_registers['valE'], self.memory_registers['valA']))
                        # Writting into memory_address stored at valE, data is stored at valA
                        self.writeMem(
                            self.memory_registers['valE'], self.memory_registers['valA'].to_bytes(4, 'little'))
                        self.memory_control = 0
                    elif self.memory_control == 2:  # Sending to write-back stage
                        print('M: Send to write back: ', end="")
                        print(
                            self.memory_registers['valE'], self.memory_registers['valA'])
                        # For write-back stage: valE - destination register address, valM - value to store.
                        self.write_back_registers['valE'] = self.memory_registers['valE']
                        self.write_back_registers['valM'] = self.memory_registers['valA']
                        self.memory_control = 0
                        # Activate Write-back stage
                        self.stage_active[4] = True
                    elif self.memory_control == 3:
                        self.write_back_registers['valE'] = self.memory_registers['valA']
                        self.write_back_registers['valM'] = self.readMem(
                            self.memory_registers['valE'], 4)
                        # Activate Write-back stage
                        self.stage_active[4] = True
                        self.memory_control = 0

                    self.write_back_registers['stat'] = self.write_back_registers['stat']
                    self.write_back_registers['dstE'] = self.memory_registers['dstE']
                    self.write_back_registers['dstM'] = self.memory_registers['dstM']
                    self.write_back_registers['icode'] = self.memory_registers['icode']
                    self.stage_active[3] = False    # Disable memory stage
                    complete_steps = "M" + complete_steps
                elif i == 2:
                    """
                        SEQ's Execute stage
                        At this stage instructions are executed.
                    """
                    complete_steps = "E" + complete_steps
                    # Checking for errors
                    if not self.execute_registers['stat'] == 0:
                        print('Execute stage error')
                    else:
                        # Calculating instruction opcode from instruction code and functional code

                        exec_opcode = self.execute_registers['icode'] * \
                            8 + self.execute_registers['ifun']

                        # If source register is now destination register at write-back stage, we need to want until
                        # data will be stored in it.
                        if self.write_back_registers['valE'] == self.execute_registers['valB'] and exec_opcode in [opcodes.movrr, opcodes.addrr, opcodes.addmr, opcodes.submr] and self.stage_active[4]:
                            print('E: Waiting register to be written back')
                            top_stage = 4
                            bottom_stage = 2
                            finish_write_back = True
                            break  # breaking to wait until write-back stage

                        if self.write_back_registers['valE'] == self.execute_registers['valA'] and exec_opcode in [opcodes.movrr, opcodes.addrr, opcodes.addrm, opcodes.subrm, opcodes.subri, opcodes.subrr, opcodes.push] and self.stage_active[4]:
                            print('E: Waiting register to be written back')
                            top_stage = 4
                            bottom_stage = 2
                            finish_write_back = True
                            break  # breaking to wait until write-back stage

                        # Checking opcode type
                        if exec_opcode == opcodes.movrr:
                            print('E: movrr {}, {}'.format(
                                self.execute_registers['valA'], self.execute_registers['valB']))  # Printing operation

                            # Left operand becomes memory_address
                            self.memory_registers['valE'] = self.execute_registers['valA']
                            self.memory_registers['valA'] = self.readReg(
                                self.execute_registers['valB'])  # From register address we get source register data and store it at valA of mem stage

                            # memory_control value for sending from memory stage to write-back stage
                            self.memory_control = 2
                        elif exec_opcode == opcodes.movrm:
                            self.memory_registers['valA'] = self.readMem(
                                self.execute_registers['valB'])  # Getting value from valB address and send it to valA of mem stage
                            # sending destination register
                            self.memory_registers['valE'] = self.execute_registers['valA']
                            print('E: movrm {}, {}'.format(
                                self.memory_registers['valE'], self.memory_registers['valA']))
                            # Set up memory control for sending from memory stage to write-back stage
                            self.memory_control = 2
                        elif exec_opcode == opcodes.movmr:
                            print('E: movmr {}, {}'.format(
                                self.execute_registers['valA'], self.execute_registers['valB']))  # Printing instruction

                            # sending memory_address to the memory stage
                            self.memory_registers['valE'] = self.execute_registers['valA']
                            self.memory_registers['valA'] = self.readReg(
                                self.execute_registers['valB'])  # Getting value from source register
                            self.memory_control = 1  # setting memory contol to write into memory
                        elif exec_opcode == opcodes.movri:
                            # Sending register address to memory stage
                            self.memory_registers['valE'] = self.execute_registers['valA']
                            self.memory_registers['valA'] = twos_components(
                                self.execute_registers['valB'])  # Sending immediate value to memory stage
                            print('E: movri {}, {}'.format(
                                self.memory_registers['valE'], self.memory_registers['valA']))
                            self.memory_control = 2  # setting memory control for writting back

                        elif exec_opcode in [opcodes.addrr, opcodes.addmr, opcodes.addrm, opcodes.addri, opcodes.subrr, opcodes.subri, opcodes.submr, opcodes.subrm]:
                            left_operand = 0
                            right_operand = 0
                            sign = (exec_opcode & (1 << 2))

                            if exec_opcode == opcodes.addrr or exec_opcode == opcodes.subrr:
                                left_operand = twos_components(
                                    self.readReg(self.execute_registers['valA']))
                                right_operand = twos_components(
                                    self.readReg(self.execute_registers['valB']))
                                self.memory_control = 2
                            elif exec_opcode == opcodes.addri or exec_opcode == opcodes.subri:
                                left_operand = twos_components(
                                    self.readReg(self.execute_registers['valA']))
                                right_operand = self.execute_registers['valB']
                                self.memory_control = 2
                            elif exec_opcode == opcodes.addrm or exec_opcode == opcodes.subrm:
                                left_operand = twos_components(
                                    self.readReg(self.execute_registers['valA']))
                                right_operand = twos_components(
                                    self.readMem(self.execute_registers['valB']))
                                self.memory_control = 2
                            elif exec_opcode == opcodes.addmr or exec_opcode == opcodes.addmr:
                                left_operand = twos_components(
                                    self.readMem(self.execute_registers['valA']))
                                right_operand = twos_components(
                                    self.readReg(self.execute_registers['valB']))
                                self.memory_control = 1

                            operation_result = None

                            if sign:
                                print('sub operation: {} {}'.format(
                                    left_operand, right_operand))
                                operation_result = left_operand - right_operand
                            else:
                                print('add operation: {} {}'.format(
                                    left_operand, right_operand))
                                operation_result = left_operand + right_operand

                            if operation_result == 0:
                                self.status_flags['ZF'] = 1
                            else:
                                self.status_flags['ZF'] = 0
                            if operation_result >= (1 << 32) or operation_result < -(1 << 32):
                                self.status_flags['OF'] = 1
                            else:
                                self.status_flags['OF'] = 0
                            if operation_result < 0:
                                self.status_flags['SF'] = 1
                            else:
                                self.status_flags['SF'] = 0

                            self.memory_registers['valE'] = self.execute_registers['valA']
                            print("Opetation result: {}".format(
                                operation_result))
                            self.memory_registers['valA'] = twos_components(
                                operation_result)

                        elif exec_opcode == opcodes.push:
                            print('Push from {}'.format(
                                self.execute_registers['valA']))
                            self.memory_registers['valE'] = self.readReg(7)
                            self.set_stack_pointer(self.readReg(7) + 4)
                            self.memory_registers['valA'] = self.readReg(
                                self.execute_registers['valA'])
                            self.memory_control = 1

                        elif exec_opcode == opcodes.pop:
                            print('POP to {}'.format(
                                self.execute_registers['valA']))
                            self.set_stack_pointer(self.readReg(7) - 4)
                            self.memory_registers['valE'] = self.readReg(7)
                            self.memory_registers['valA'] = self.execute_registers['valA']
                            self.memory_control = 3

                        elif exec_opcode == opcodes.halt:
                            # Next operation are cancelled
                            self.stage_active[0], self.stage_active[1], self.stage_active[2] = False, False, False
                            stop_computing = True  # to exit from loop
                            print('E: halt')
                            top_stage = 4
                            bottom_stage = 3  # Next stage will be only: write-back and memory to wait data to write into memory or registers
                            break

                        elif exec_opcode == opcodes.passop:
                            # This instruction does nothing
                            print('E: Instruction passoped')
                            self.memory_control = 0
                        else:
                            # Unknown instruction
                            self.memory_registers['stat'] = 0b0001

                    # Sending insformation about operation to the next stage
                    self.memory_registers['stat'] = self.execute_registers['stat']
                    self.memory_registers['icode'] = self.execute_registers['icode']
                    self.memory_registers['dstM'] = self.execute_registers['dstM']
                    self.memory_registers['dstE'] = self.execute_registers['dstE']
                    self.stage_active[3] = True     # Activate next stage
                    self.stage_active[2] = False    # Disable current stage
                elif i == 1:
                    """
                        Decode stage
                        By the time it just sent data to the execute stage
                    """
                    self.execute_registers['stat'] = self.decode_registers['stat']
                    self.execute_registers['icode'] = self.decode_registers['icode']
                    self.execute_registers['ifun'] = self.decode_registers['ifun']
                    self.execute_registers['valA'] = self.decode_registers['rA']
                    self.execute_registers['valB'] = self.decode_registers['rB']
                    self.stage_active[2] = True     # Activate execute stage
                    self.stage_active[1] = False    # Disable current stage
                    complete_steps = "D" + complete_steps
                elif i == 0:
                    """
                        Fetch stage
                        Writting information about instruction to the decode stage
                    """
                    # Program counter prediction
                    if opcode == opcodes.call:
                        exec_opcode = self.execute_registers['icode'] * \
                            8 + self.execute_registers['ifun']
                        if self.stage_active[2] and (exec_opcode == opcodes.push or exec_opcode == opcodes.pop):
                            break
                        # If current fetched instruction is call instruction
                        print('F: call PREDICTED')
                        self.writeMem(self.readReg(7),
                                      new_PC.to_bytes(4, 'little'))  # Writting new program counter to the stack
                        print('Before call: {}'.format(new_PC))
                        # Increase stack pointer
                        self.set_stack_pointer(self.readReg(7) + 4)
                        print('CALL program counter: {}'.format(loper))
                        self.PC = loper  # new program counter is now call address
                        break

                    elif opcode == opcodes.ret:
                        # If current fetched instruction is ret instruction
                        print('F: ret PREDICTED')
                        # Decreasing stack pointer
                        self.set_stack_pointer(self.readReg(7) - 4)
                        # Getting value of program coutner from memory at stack pointer address
                        self.PC = self.readMem(self.readReg(7), 4)
                        print('RETURNED TO: {}'.format(self.PC))
                        break

                    elif opcode in [opcodes.jne, opcodes.je, opcodes.jnz, opcodes.jge, opcodes.jg, opcodes.jl, opcodes.jle]:
                        # If current fetched instruction is conditional jump instrucion
                        if not update_flag and (self.execute_registers['icode']*8 + self.execute_registers['ifun']) in [opcodes.addrr, opcodes.addmr, opcodes.addrm, opcodes.addri, opcodes.subri, opcodes.subrm, opcodes.submr, opcodes.subrr]:
                            # waiting status flags to update
                            update_flag = True
                            break

                        update_flag = False

                        if opcode == opcodes.jnz:
                            if not self.status_flags['ZF']:
                                print('JNZ jump to {}'.format(loper))
                                self.PC = loper
                                break
                        elif opcode == opcodes.je:
                            if self.status_flags['ZF']:
                                print('JE jump to {}'.format(loper))
                                self.PC = loper
                                break
                        elif opcode == opcodes.jg:
                            if not self.status_flags['SF'] and not self.status_flags['ZF']:
                                print('JG jump to {}'.format(loper))
                                self.PC = loper
                                break
                        elif opcode == opcodes.jl:
                            if self.status_flags['SF'] and not self.status_flags['ZF']:
                                print('JL jump to {}'.format(loper))
                                self.PC = loper
                                break
                        elif opcode == opcodes.jge:
                            print('SF: {}'.format(self.status_flags['SF']))
                            if not self.status_flags['SF'] or self.status_flags['ZF']:
                                print('JGE jump to {}'.format(loper))
                                self.PC = loper
                                break
                        elif opcode == opcodes.jle:
                            if self.status_flags['SF'] or self.status_flags['ZF']:
                                print('JLE jump to {}'.format(loper))
                                self.PC = loper
                                break

                    elif opcode == opcodes.jp:
                        # If current fetched instruction is unconditional jump instruction
                        print('F: JUMP PREDICTED')
                        self.PC = loper  # Jump at address
                        break

                    self.decode_registers['stat'] == 0b0000
                    self.decode_registers['icode'] = opcode >> 3
                    self.decode_registers['ifun'] = opcode & 0b111
                    self.decode_registers['rA'] = loper
                    self.decode_registers['rB'] = roper
                    complete_steps = "F" + complete_steps

                    self.PC = new_PC  # Setting up new program counter
                    self.stage_active[1] = True     # Activate Decode stage
                    self.stage_active[0] = False    # Disable current stage
            if stop_computing:
                # if stop_computing == true
                # We need to wait to data be stored at registers or momory
                # It will take a maximum of 2 cycles
                finish_prev -= 1
            print(complete_steps)  # Print completed stages
            sleep(0.2)

    def set_pc(self, pc_val):
        """
            Function for setting new program counter value
            def set_pc(self, pc_val) -> None
            pc_val - new program counter value
        """
        self.PC = pc_val

    def set_stack_pointer(self, pointer: int) -> None:
        """
            Function for setting new stack pointer address
            def set_stack_pointer(self, pointer: int) -> None
            pointer - new stack pointer value
        """
        self.writeReg(7, pointer.to_bytes(4, 'little'))

    def memDump(self) -> None:
        """
            Function for printing information about register and memory content
            def memDump(self) -> None:
        """
        keys = list(regfile.keys())
        for i in range(16):
            print('{:<6}\t'.format(keys[i]), end="")
            for j in range(4):
                print('{:x}{:x}'.format(self.registers[regfile[keys[i]]*4 + j] >> 4 &
                      0b1111, self.registers[regfile[keys[i]]*4 + j] & 0b1111), end="\t")
            print()
        for i in range(0, self.memsize//16):
            print("{0:#0{1}x}0".format(i, 5), end="\t")
            for j in range(i*16, i*16+16):
                print("{:x}{:x}".format(
                    self.memory[j] >> 4 & 0b1111, self.memory[j] & 0b1111), end="\t")
            print()

    def info(self):
        print('System type: {}bit'.format(self.bits))
        print('System memory size: {} bytes'.format(self.memsize))


def main():
    seq = SEQ(32, 1024)
    asm_parser('exec.asm', seq)
    seq.set_stack_pointer(200)
    seq.memDump()
    seq.compute()
    seq.memDump()


if __name__ == "__main__":
    main()
