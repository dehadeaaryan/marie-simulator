export const examples = [
  { name: 'Add two numbers', description: 'Load, add, and send a result to output.', source: `/ Add two numbers\n/ Step through to see each register change.\n\n        Load    First\n        Add     Second\n        Store   Result\n        Output\n        Halt\n\nFirst,  DEC     12\nSecond, DEC     8\nResult, DEC     0\n` },
  { name: 'Echo your input', description: 'The machine waits until you supply a value.', source: `/ Read a number and echo it back.\n        Input\n        Output\n        Halt\n` },
  { name: 'Countdown', description: 'Branch with Skipcond and loop with Jump.', source: `/ Count down from five.\n        Load    Five\nLoop,   Output\n        Subt    One\n        Skipcond 400\n        Jump    Loop\n        Halt\nFive,   DEC     5\nOne,    DEC     1\n` },
  { name: 'Indirect addressing', description: 'A pointer holds the address of a value.', source: `/ Read and write through a pointer.\n        LoadI   Pointer\n        AddI    Pointer\n        StoreI  Pointer\n        Output\n        Halt\nPointer, HEX    0006\nValue,   DEC    21\n` },
  { name: 'Subroutine', description: 'JnS saves a return address; JumpI returns.', source: `/ Call a subroutine that doubles a number.\n        Load    Value\n        Store   Temp\n        JnS     Double\n        Output\n        Halt\nDouble, HEX     0000\n        Load    Temp\n        Add     Temp\n        JumpI   Double\nValue,  DEC     9\nTemp,   DEC     0\n` }
];
export const instructions = [
  ['Load X','AC ← M[X]'], ['Store X','M[X] ← AC'], ['Add X','AC ← AC + M[X]'], ['Subt X','AC ← AC − M[X]'],
  ['Input','Wait for a 16-bit number → AC'], ['Output','Send AC to the output panel'], ['Halt','Stop execution'],
  ['Skipcond 000 / 400 / 800','Skip next if AC < 0 / = 0 / > 0'], ['Jump X','PC ← X'], ['Clear','AC ← 0'],
  ['AddI X','AC ← AC + M[M[X]]'], ['JumpI X','PC ← low 12 bits of M[X]'], ['LoadI X','AC ← M[M[X]]'],
  ['StoreI X','M[M[X]] ← AC'], ['JnS X','M[X] ← PC; AC, PC ← X + 1'], ['HEX / DEC','Store a hexadecimal / signed decimal word'], ['ORG X','Set the next assembly address (hex)']
];
export const registerHelp: Record<string, string> = { AC: 'Accumulator', PC: 'Program counter · next instruction', MAR: 'Memory address register', MBR: 'Memory buffer register', IR: 'Instruction register · last fetched', InReg: 'Last input word', OutReg: 'Last output word' };
export function hex(value: number, width = 4) { return value.toString(16).toUpperCase().padStart(width, '0'); }
export function signed(value: number) { return value >= 0x8000 ? value - 0x10000 : value; }
