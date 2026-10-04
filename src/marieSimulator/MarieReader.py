from .assembler import assemble


class MarieReader:
    """File interface retained for existing callers; source assembly is reusable."""
    def __init__(self, filename):
        with open(filename, 'r', encoding='utf-8') as file:
            self.program = assemble(file.read())
        self.M = self.program.M.copy()
        self.symbolTable = self.program.symbolTable.copy()
        self.entry = self.program.entry
        # Desktop table consumes normalized effective statements.
        self.input = [row['source'].split('/')[0].split(';')[0].strip() for row in self.program.listing]
