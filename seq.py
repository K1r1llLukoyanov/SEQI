import struct
from typing import List
from parser import asm_parser
from time import sleep


class opcodes(enumerate):
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


class SEQ(object):
    def __init__(self, bits, memory) -> None:
        self.bits: int = bits
        self.memsize: int = memory
        self.memory: bytearray = bytearray(memory)
        self.regfile: dict[str, int] = {
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
        }

        self.registers: List[bytearray] = bytearray(4*16)

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

    def readMem(self, addr: str | int) -> int:
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
            return struct.unpack('>I', self.memory[addr: addr+4])[0]
        return struct.unpack('>I', self.memory[addr: addr+4])[0]

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
        return struct.unpack('>I', self.registers[4*reg: 4*reg+4])[0]

    def fetch_instruction(self, instruction_address):
        instruction = self.readMem(instruction_address)
        opcode = instruction >> 26
        loperand = instruction >> 22 & 0b1111
        roperand = instruction >> 18 & 0b1111
        immediate = instruction & ((1 << 18) - 1)

        operation_data = [opcode, loperand, roperand]

        if opcode in [opcodes.movmr, opcodes.addmr, opcodes.jnz, opcodes.je, opcodes.jp, opcodes.jne]:
            operation_data[1] = immediate
        elif opcode in [opcodes.movrm, opcodes.addrm, opcodes.movri]:
            operation_data[2] = immediate
        elif opcode == opcodes.call:
            operation_data[1] = immediate

        return operation_data

    def compute(self):
        stop_computing = False
        finish_prev = 3
        top_stage = 4
        bottom_stage = -1
        finish_write_back = False
        while not stop_computing or finish_prev > 0:
            print()
            print(self.PC)
            opcode, loper, roper = self.fetch_instruction(
                self.PC)
            new_PC = self.PC+4
            self.stage_active[0] = True
            complete_steps = ""
            for i in range(top_stage, bottom_stage, -1):
                if self.stage_active[i]:
                    if i == 4:
                        if not self.write_back_registers['stat'] == 0b0000:
                            print('Write back error')
                        elif self.write_back_control == 1:
                            self.writeReg(
                                self.write_back_registers['valE'], self.write_back_registers['valM'].to_bytes(4, 'big'))
                            self.write_back_control = 0
                            if finish_write_back:
                                print('Written back: {} {}'.format(
                                    self.write_back_registers['valE'], self.write_back_registers['valM']))
                                top_stage = 4
                                bottom_stage = -1
                        self.stage_active[4] = False
                        complete_steps = "W" + complete_steps
                    elif i == 3:
                        if not self.memory_registers['stat'] == 0b0000:
                            print('Memory stage error')
                        elif self.memory_control == 1:
                            print('M: Writing into memory: {}, {}'.format(
                                self.memory_registers['valE'], self.memory_registers['valA']))
                            self.writeMem(
                                self.memory_registers['valE'], self.memory_registers['valA'].to_bytes(4, 'big'))
                            self.write_back_control = 0
                            self.memory_control = 0
                        elif self.memory_control == 2:
                            print('M: Send to write back: ', end="")
                            print(
                                self.memory_registers['valE'], self.memory_registers['valA'])
                            self.write_back_registers['valE'] = self.memory_registers['valE']
                            self.write_back_registers['valM'] = self.memory_registers['valA']
                            self.write_back_control = 1
                            self.memory_control = 0
                            self.stage_active[4] = True

                        self.write_back_registers['stat'] = self.write_back_registers['stat']
                        self.write_back_registers['dstE'] = self.memory_registers['dstE']
                        self.write_back_registers['dstM'] = self.memory_registers['dstM']
                        self.write_back_registers['icode'] = self.memory_registers['icode']
                        self.stage_active[3] = False
                        complete_steps = "M" + complete_steps
                    elif i == 2:
                        complete_steps = "E" + complete_steps
                        if not self.execute_registers['stat'] == 0:
                            print('Execute stage error')
                        else:
                            exec_opcode = self.execute_registers['icode'] * \
                                4 + self.execute_registers['ifun']
                            if exec_opcode == opcodes.movrr:
                                print('E: movrr {}, {}'.format(
                                    self.execute_registers['valA'], self.execute_registers['valB']))

                                if self.stage_active[4] and self.write_back_registers['valE'] == self.execute_registers['valB']:
                                    print(
                                        'E: Waiting register to be written back')
                                    top_stage = 4
                                    bottom_stage = 2
                                    finish_write_back = True
                                    break
                                self.memory_registers['valE'] = self.execute_registers['valA']
                                self.memory_registers['valA'] = self.readReg(
                                    self.execute_registers['valB'])

                                self.memory_control = 2
                            elif exec_opcode == opcodes.movrm:
                                self.memory_registers['valM'] = self.readMem(
                                    self.execute_registers['valB'])
                                self.memory_registers['valE'] = self.execute_registers['valA']
                                print('E: movrm {}, {}'.format(
                                    self.memory_registers['valE'], self.memory_registers['valA']))
                                self.memory_control = 2
                            elif exec_opcode == opcodes.movmr:
                                print('E: movmr {}, {}'.format(
                                    self.execute_registers['valA'], self.execute_registers['valB']))

                                if self.stage_active[4] and self.write_back_registers['valE'] == self.execute_registers['valB']:
                                    print(
                                        'E: Waiting register to be written back')
                                    top_stage = 4
                                    bottom_stage = 2
                                    finish_write_back = True
                                    break

                                self.memory_registers['valE'] = self.execute_registers['valA']
                                self.memory_registers['valA'] = self.readReg(
                                    self.execute_registers['valB'])
                                self.memory_control = 1
                            elif exec_opcode == opcodes.movri:
                                self.memory_registers['valE'] = self.execute_registers['valA']
                                self.memory_registers['valA'] = self.execute_registers['valB']
                                print('E: movri {}, {}'.format(
                                    self.memory_registers['valE'], self.memory_registers['valA']))
                                self.memory_control = 2
                            elif exec_opcode == opcodes.halt:
                                self.stage_active[0], self.stage_active[1], self.stage_active[2] = False, False, False
                                stop_computing = True
                                print('E: halt')
                                top_stage = 4
                                bottom_stage = 2
                                break
                            elif exec_opcode == opcodes.passop:
                                print('E: Instruction passoped')
                                self.memory_control = 0
                            else:
                                self.memory_registers['stat'] = 0b0001

                        self.memory_registers['stat'] = self.execute_registers['stat']
                        self.memory_registers['icode'] = self.execute_registers['icode']
                        self.memory_registers['dstM'] = self.execute_registers['dstM']
                        self.memory_registers['dstE'] = self.execute_registers['dstE']
                        self.stage_active[3] = True
                        self.stage_active[2] = False
                    elif i == 1:
                        self.execute_registers['stat'] = self.decode_registers['stat']
                        self.execute_registers['icode'] = self.decode_registers['icode']
                        self.execute_registers['ifun'] = self.decode_registers['ifun']
                        self.execute_registers['valA'] = self.decode_registers['rA']
                        self.execute_registers['valB'] = self.decode_registers['rB']
                        self.stage_active[2] = True
                        self.stage_active[1] = False
                        complete_steps = "D" + complete_steps
                    elif i == 0:
                        self.decode_registers['stat'] == 0b0000
                        self.decode_registers['icode'] = opcode >> 2
                        self.decode_registers['ifun'] = opcode & 0b11
                        self.decode_registers['rA'] = loper
                        self.decode_registers['rB'] = roper
                        complete_steps = "F" + complete_steps

                        # Program counter prediction
                        if opcode == opcodes.call:
                            print('F: call PREDICTED')
                            self.writeMem(self.readReg(7),
                                          new_PC.to_bytes(4, 'big'))
                            self.set_stack_pointer(self.readReg(7) + 1)
                            self.PC = loper
                            break
                        elif opcode == opcodes.ret:
                            print('F: ret PREDICTED')
                            self.set_stack_pointer(self.readReg(7) - 1)
                            self.PC = self.readMem(self.readReg(7))
                            break
                        elif opcode in [opcodes.jne, opcodes.je, opcodes.jnz]:
                            pass
                        elif opcode == opcodes.jp:
                            print('F: JUMP PREDICTED')
                            self.PC = loper
                            break

                        self.PC = new_PC
                        self.stage_active[1] = True
                        self.stage_active[0] = False
            if stop_computing:
                finish_prev -= 1
            print(complete_steps)
            sleep(0.2)

    def set_pc(self, pc_val):
        self.PC = pc_val

    def set_stack_pointer(self, pointer: int):
        self.writeReg(7, pointer.to_bytes(4, 'big'))

    def memDump(self) -> None:
        keys = list(self.regfile.keys())
        for i in range(16):
            print('{:<6}\t'.format(keys[i]), end="")
            for j in range(4):
                print('{:x}{:x}'.format(self.registers[self.regfile[keys[i]]*4 + j] >> 4 &
                      0b1111, self.registers[self.regfile[keys[i]]*4 + j] & 0b1111), end="\t")
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
    asm_parser('exec.txt', seq)
    seq.set_stack_pointer(200)
    seq.memDump()
    seq.compute()
    seq.memDump()


if __name__ == "__main__":
    main()
