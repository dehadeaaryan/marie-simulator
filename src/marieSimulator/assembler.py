"""Two-pass MARIE assembler shared by desktop and HTTP clients. No host execution."""
from dataclasses import dataclass
import re

OPCODES = dict(zip(('JNS','LOAD','STORE','ADD','SUBT','INPUT','OUTPUT','HALT','SKIPCOND','JUMP','CLEAR','ADDI','JUMPI','LOADI','STOREI'), range(15)))
NO_OPERAND = {'INPUT', 'OUTPUT', 'HALT', 'CLEAR'}
MAX_SOURCE_BYTES = 65536

class AssemblyError(ValueError):
    def __init__(self, line, message):
        self.line = line
        self.message = message
        super().__init__(f'Line {line}: {message}')

@dataclass
class Program:
    M: list[int]
    symbolTable: dict[str, int]
    entry: int
    lines: dict[int, int]
    listing: list[dict]


def assemble(source: str) -> Program:
    try:
        source_size = len(source.encode('utf-8'))
    except UnicodeEncodeError:
        raise AssemblyError(1, 'Source contains invalid Unicode characters.') from None
    if source_size > MAX_SOURCE_BYTES:
        raise AssemblyError(1, 'Source exceeds 64 KiB.')
    memory = [0] * 4096
    symbols, lines, listing, records = {}, {}, [], []
    address, entry, occupied = 0, None, set()
    for number, raw in enumerate(source.splitlines(), 1):
        text = re.split(r'[/;]', raw, maxsplit=1)[0].strip()
        if not text:
            continue
        label = None
        if ',' in text:
            label, text = (part.strip() for part in text.split(',', 1))
            if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', label):
                raise AssemblyError(number, 'Invalid label. Use letters, digits, and underscores.')
            label = label.upper()
            if label in symbols:
                raise AssemblyError(number, f'Duplicate label {label}.')
        tokens = text.split()
        if not tokens:
            raise AssemblyError(number, 'A label needs an instruction or data directive.')
        op = tokens[0].upper()
        if op == 'ORG':
            if label or len(tokens) != 2:
                raise AssemblyError(number, 'ORG needs one hexadecimal address and no label.')
            try:
                address = int(tokens[1], 16)
            except ValueError:
                raise AssemblyError(number, 'ORG address must be hexadecimal.') from None
            if not 0 <= address < 4096:
                raise AssemblyError(number, 'Address must be between 000 and FFF.')
            continue
        if op not in OPCODES and op not in ('HEX','DEC'):
            raise AssemblyError(number, f'Unknown instruction {op}.')
        if len(tokens) != (1 if op in NO_OPERAND else 2):
            raise AssemblyError(number, f'{op} expects {"no operand" if op in NO_OPERAND else "one operand"}.')
        if not 0 <= address < 4096 or address in occupied:
            raise AssemblyError(number, 'Memory address exceeds FFF or overlaps an earlier word.')
        if label:
            symbols[label] = address
        if entry is None:
            entry = address
        records.append((number, address, label, op, tokens[1] if len(tokens) == 2 else None, raw))
        occupied.add(address)
        address += 1
    if entry is None:
        raise AssemblyError(1, 'Write at least one instruction.')
    for number, address, label, op, operand, raw in records:
        value = 0
        if operand is not None:
            try:
                value = symbols[operand.upper()] if op in OPCODES and operand.upper() in symbols else int(operand, 10 if op == 'DEC' else 16)
            except ValueError:
                raise AssemblyError(number, f'Undefined label or invalid number: {operand}.') from None
        if op in ('HEX','DEC'):
            if not (-32768 <= value <= (32767 if op == 'DEC' else 65535)):
                raise AssemblyError(number, 'Data must fit a 16-bit word (DEC −32768…32767, HEX −8000…FFFF).')
            word = value & 0xFFFF
        else:
            if not 0 <= value < 4096:
                raise AssemblyError(number, 'Instruction address must be between 000 and FFF.')
            if op == 'SKIPCOND' and value not in (0x000,0x400,0x800):
                raise AssemblyError(number, 'Skipcond accepts 000 (negative), 400 (zero), or 800 (positive).')
            word = (OPCODES[op] << 12) | value
        memory[address] = word
        lines[address] = number
        listing.append(dict(address=address, line=number, label=label, operation=op, word=word, source=raw))
    return Program(memory, symbols, entry, lines, listing)
