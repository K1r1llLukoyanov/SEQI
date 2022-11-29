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
} # register file


def twos_components(value: int) -> int:
    if value & (1 << 31) and value < 0:
        return value + (1 << 32)
    elif value >= 0 and not (value & (1 << 31)):
        return value
    return value - (1 << 32)
