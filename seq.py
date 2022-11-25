import struct
from typing import List
from parse import asm_parser
from time import sleep


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


class SEQ(object):
    def __init__(self, bits, memory) -> None:
        self.bits: int = bits
        self.memsize: int = memory
        self.memory: bytearray = bytearray(memory)
        self.regfile: dict[str, int] = {'EAX':  0x0,
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
        self.registers: List[bytearray] = bytearray(4*16)

        self.decode_registers: dict[str, None | int] = {'stat': 0b0000, 'icode': None,
                                                        'ifun': None, 'rA': None, 'rB': None, 'valC': None, 'valP': None}
        self.execute_registers: dict[str, None | int] = {'stat': 0b0000, 'icode': None, 'ifun': None, 'valC': None, 'valA': None,
                                                         'valB': None, 'dstE': None, 'dstM': None, 'srcA': None, 'dstM': None, 'srcA': None, 'srcB': None}
        self.memory_registers: dict[str, None | int] = {'stat': 0b000, 'icode': None,
                                                        'valE': None, 'valA': None, 'dstE': None, 'dstM': None}
        self.write_back_registers: dict[str, None | int] = {
            'stat': 0b0000, 'icode': None, 'valE': None, 'valM': None, 'dstE': None, 'dstM': None}

        self.active = [False]*5

        self.PC = 0x0000

        self.decoded_opcodes = {
            0b000000: 'MOV',
            0b000001: 'ADD',
            0b000010: 'HALT'
        }

        self.memory_control = 0b00
        self.write_back_control = 0b0

    def readMem(self, addr) -> int:
        if type(addr) == type('str'):
            addr = int(addr, 16)
            return struct.unpack('>I', self.memory[4*addr: 4*addr+4])[0]
        return struct.unpack('>I', self.memory[4*addr: 4*addr+4])[0]

    def writeMem(self, addr, data: bytearray) -> bool:
        if type(addr) == type(''):
            addr = int(addr, 16)
        for i in range(len(data)):
            self.memory[4*addr + i] = data[i]

    def writeReg(self, reg, data: bytearray) -> None:
        for i in range(4):
            self.registers[reg*4 + i] = data[i]

    def readReg(self, reg):
        return struct.unpack('>I', self.registers[4*reg: 4*reg+4])[0]

    def fetch_instruction(self, instruction_address):
        instruction = self.readMem(instruction_address)
        opcode = instruction >> 26
        loperand = instruction >> 22 & 0b1111
        roperand = instruction >> 18 & 0b1111
        immediate = instruction >> 10 & 0b11111111
        new_pointer = instruction & 0b11111111

        return (opcode, loperand, roperand, immediate, new_pointer)

    def compute(self):
        stop_computing = False
        finish_prev = 3
        top_stage = 4
        bottom_stage = -1
        finish_write_back = False
        while not stop_computing or finish_prev > 0:
            print()
            opcode, loper, roper, imm, new_PC = self.fetch_instruction(
                self.PC)
            print(self.PC)
            self.active[0] = True
            complete_steps = ""
            for i in range(top_stage, bottom_stage, -1):
                if self.active[i]:
                    if i == 4:
                        if not self.write_back_registers['stat'] == 0b0000:
                            print('Write back error')
                        elif self.write_back_control == 1:
                            self.writeReg(
                                self.write_back_registers['valE'], self.write_back_registers['valM'].to_bytes(4, 'big'))
                            self.write_back_control = 0
                            if finish_write_back:
                                top_stage = 4
                                bottom_stage = -1
                        self.active[4] = False
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
                            self.active[4] = True

                        self.write_back_registers['stat'] = self.write_back_registers['stat']
                        self.write_back_registers['dstE'] = self.memory_registers['dstE']
                        self.write_back_registers['dstM'] = self.memory_registers['dstM']
                        self.write_back_registers['icode'] = self.memory_registers['icode']
                        self.active[3] = False
                        complete_steps = "M" + complete_steps
                    elif i == 2:
                        complete_steps = "E" + complete_steps
                        if not self.execute_registers['stat'] == 0b0000:
                            print('Execute stage error')
                        else:
                            exec_opcode = self.execute_registers['icode'] * \
                                4 + self.execute_registers['ifun']
                            if exec_opcode == opcodes.MOVRR:
                                self.memory_registers['valE'] = self.execute_registers['valB']
                                self.memory_registers['valA'] = self.readReg(
                                    self.execute_registers['valA'])
                                self.memory_control = 2
                            elif exec_opcode == opcodes.MOVRM:
                                self.memory_registers['valM'] = self.readMem(
                                    self.execute_registers['valB'])
                                self.memory_registers['valE'] = self.execute_registers['valA']
                                print('E: MOVRM {}, {}'.format(
                                    self.memory_registers['valE'], self.memory_registers['valA']))
                                self.memory_control = 2
                            elif exec_opcode == opcodes.MOVMR:
                                if self.active[4] and self.write_back_registers['valE'] == self.execute_registers['valB']:
                                    print('E: Waiting register to be written back')
                                    top_stage = 4
                                    bottom_stage = 2
                                    finish_write_back = True
                                    break
                                self.memory_registers['valE'] = self.execute_registers['valA']
                                self.memory_registers['valA'] = self.readReg(
                                    self.execute_registers['valB'])
                                print('E: MOVMR {}, {}'.format(
                                    self.memory_registers['valE'], self.memory_registers['valA']))
                                self.memory_control = 1
                            elif exec_opcode == opcodes.MOVRI:
                                self.memory_registers['valE'] = self.execute_registers['valA']
                                self.memory_registers['valA'] = self.execute_registers['valB']
                                print('E: MOVRI {}, {}'.format(
                                    self.memory_registers['valE'], self.memory_registers['valA']))
                                self.memory_control = 2
                            elif exec_opcode == opcodes.HALT:
                                self.active[0], self.active[1], self.active[2] = False, False, False
                                stop_computing = True
                                print('E: HALT')
                                top_stage = 4
                                bottom_stage = 2
                                break
                            elif exec_opcode == opcodes.PASS:
                                print('E: Instruction passed')
                                self.memory_control = 0
                            else:
                                self.memory_registers['stat'] = 0b0001

                        self.memory_registers['stat'] = self.execute_registers['stat']
                        self.memory_registers['icode'] = self.execute_registers['icode']
                        self.memory_registers['dstM'] = self.execute_registers['dstM']
                        self.memory_registers['dstE'] = self.execute_registers['dstE']
                        self.active[3] = True
                        self.active[2] = False
                    elif i == 1:
                        self.execute_registers['stat'] = self.decode_registers['stat']
                        self.execute_registers['icode'] = self.decode_registers['icode']
                        self.execute_registers['ifun'] = self.decode_registers['ifun']
                        self.execute_registers['valC'] = self.decode_registers['valC']
                        self.execute_registers['valA'] = self.decode_registers['rA']
                        self.execute_registers['valB'] = self.decode_registers['rB']
                        self.active[2] = True
                        self.active[1] = False
                        complete_steps = "D" + complete_steps
                    elif i == 0:
                        self.decode_registers['stat'] == 0b0000
                        self.decode_registers['icode'] = opcode >> 2
                        self.decode_registers['ifun'] = opcode & 0b11
                        self.decode_registers['rA'] = loper
                        self.decode_registers['rB'] = roper
                        self.decode_registers['valC'] = imm
                        complete_steps = "F" + complete_steps

                        if opcode == opcodes.CALL:
                            print('F: CALL PREDICTED')
                            self.writeMem(self.readReg(7),
                                          new_PC.to_bytes(4, 'big'))
                            self.set_stack_pointer(self.readReg(7) + 1)
                            self.PC = loper
                            break
                        elif opcode == opcodes.RET:
                            print('F: RET PREDICTED')
                            self.set_stack_pointer(self.readReg(7) - 1)
                            self.PC = self.readMem(self.readReg(7))
                            break

                        self.PC = new_PC
                        self.active[1] = True
                        self.active[0] = False
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
