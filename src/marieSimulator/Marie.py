from collections import deque


def signed(word):
    word &= 0xFFFF
    return word - 65536 if word & 0x8000 else word


class ExecutionError(ValueError):
    pass


class Marie:
    def __init__(self, mr=None, *, nonblocking=False, input_provider=None):
        self.AC = 0x0000
        self.PC = 0b000000000000
        self.MAR = 0b000000000000
        self.MBR = 0x0000
        self.IR = 0x0000
        self.InReg = 0x00
        self.OutReg = 0x00

        self.GUI = False
        self.nonblocking = nonblocking
        self.input_provider = input_provider
        self.inputs = deque()
        self.outputs = []
        self.waiting = False
        self.last_address = None

        self.M = [0 for i in range(4096)]

        self.operation = None
        self.running = True
        self.canStep = True

        if mr != None:
            self.parse(mr)
    
    def parse(self, mr):
        self.M = [word & 0xFFFF for word in mr.M]
        self.M += [0] * (4096 - len(self.M))
        self.symbolTable = mr.symbolTable.copy()
        self.PC = getattr(mr, 'entry', 0)

    def show(self):
        output = "\n"

        for item in self.M:
            output += hex(item) + " | "
        output = output[:-3] + "\n"

        print(output)
    
    def run(self):
        while self.running:
            self.tick()
            if self.waiting:
                break

    def step(self):
        if not self.canStep:
            return None
        previous = self.M.copy()
        self.tick()
        return [i for i, word in enumerate(self.M) if word != previous[i]]

    def tick(self):
        """Execute one instruction without a memory scan; Input can yield to a caller."""
        if not self.canStep:
            return False
        if self.nonblocking and (self.M[self.PC] >> 12) == 5 and not self.inputs:
            self.waiting = True
            return False
        self.waiting = False
        self.last_address = self.PC
        self.__fetch()
        self.__incrementPC()
        self.__decode()
        self.__getOperand()
        self.__execute()
        self.AC &= 0xFFFF
        self.MBR &= 0xFFFF
        self.PC &= 0xFFF
        return True

    def __fetch(self):
        self.MAR = self.PC
        self.MBR = self.M[self.MAR]
        self.IR = self.MBR
    
    def __incrementPC(self):
        self.PC = (self.PC + 1) & 0xFFF
    
    def __decode(self):
        self.MAR = (self.IR & 0x0FFF)
        self.operation = (self.IR & 0xF000) >> 12

    def __getOperand(self):
        if self.operation not in [0x5, 0x6, 0x7, 0x8, 0x9, 0xA, 0xF]:
            self.MBR = self.M[self.MAR]

    def __execute(self):
        if self.operation == 0x0:
            self.__jnS()
        elif self.operation == 0x1:
            self.__load()
        elif self.operation == 0x2:
            self.__store()
        elif self.operation == 0x3:
            self.__add()
        elif self.operation == 0x4:
            self.__subt()
        elif self.operation == 0x5:
            self.__input()
        elif self.operation == 0x6:
            self.__output()
        elif self.operation == 0x7:
            self.__halt()
        elif self.operation == 0x8:
            self.__skipcond()
        elif self.operation == 0x9:
            self.__jump()
        elif self.operation == 0xA:
            self.__clear()
        elif self.operation == 0xB:
            self.__addI()
        elif self.operation == 0xC:
            self.__jumpI()
        elif self.operation == 0xD:
            self.__loadI()
        elif self.operation == 0xE:
            self.__storeI()
        else:
            raise ExecutionError("Opcode F is data, not an executable instruction.")
        


    def __jnS(self):
        self.MBR = self.PC
        self.M[self.MAR] = self.MBR
        self.MBR = (self.IR & 0x0FFF)
        self.AC = 0x1
        self.AC = self.AC + self.MBR
        self.PC = self.AC

    def __load(self):
        self.AC = self.MBR

    def __store(self):
        self.MBR = self.AC
        self.M[self.MAR] = self.MBR

    def __add(self):
        self.AC = self.AC + self.MBR

    def __subt(self):
        self.AC = self.AC - self.MBR

    def __input(self):
        if self.nonblocking:
            self.InReg = self.inputs.popleft() & 0xFFFF
        elif self.input_provider:
            self.InReg = self.input_provider() & 0xFFFF
        else:
            self.InReg = int(input("Input (HEX): "), 16) & 0xFFFF
        self.AC = self.InReg

    def __output(self):
        self.OutReg = self.AC
        self.outputs.append(self.OutReg)
        if not self.nonblocking and not self.GUI:
            print("Output (HEX): " + hex(self.OutReg))

    def __halt(self):
        self.running = False
        self.canStep = False

    def __skipcond(self):
        skipBits = (self.IR & 0b0000110000000000) >> 8
        if skipBits == 0b0000:
            if signed(self.AC) < 0:
                self.__incrementPC()
        elif skipBits == 0b0100:
            if self.AC == 0:
                self.__incrementPC()
        elif skipBits == 0b1000:
            if signed(self.AC) > 0:
                self.__incrementPC()
        else:
            raise ExecutionError("Skipcond condition C00 is undefined.")

    def __jump(self):
        self.PC = (self.IR & 0x0FFF)
    
    def __clear(self):
        self.AC = 0x0
    
    def __addI(self):
        self.MAR = self.MBR & 0xFFF
        self.MBR = self.M[self.MAR]
        self.AC = self.AC + self.MBR

    def __jumpI(self):
        self.PC = self.MBR & 0xFFF
    
    def __loadI(self):
        self.MAR = self.MBR & 0xFFF
        self.MBR = self.M[self.MAR]
        self.AC = self.MBR
    
    def __storeI(self):
        self.MAR = self.MBR & 0xFFF
        self.MBR = self.AC
        self.M[self.MAR] = self.MBR

