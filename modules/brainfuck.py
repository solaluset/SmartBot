class Tree:
    def __init__(self):
        self.body = []
        self.finished = False

    def _branch_is_unfinished(self):
        return self.body and isinstance(self.body[-1], Tree) and not self.body[-1].finished

    def append(self, part: int | Tree):
        if self._branch_is_unfinished():
            self.body[-1].append(part)
        else:
            self.body.append(part)

    def finish(self):
        if self._branch_is_unfinished():
            self.body[-1].finish()
        else:
            self.finished = True


class State:
    def __init__(self, input: bytes, ops_limit: int, mem_size: int = 30_000):
        self.memory = bytearray(mem_size)
        self.current_cell = 0
        self.input = input
        self.output = b""
        self.ops_left = ops_limit

    def interpret(self, code):
        for op in code.body:
            if isinstance(op, Loop):
                if self.memory[self.current_cell]:
                    self.interpret(op)
            if op == OP_INC:
                try:
                    self.memory[self.current_cell] += 1
                except ValueError:  # overflow
                    self.memory[self.current_cell] = 0
            elif op == OP_DEC:
                try:
                    self.memory[self.current_cell] -= 1
                except ValueError:  # overflow
                    self.memory[self.current_cell] = 0xFF
            elif op == OP_INC_PTR:
                self.current_cell += 1
                self.current_cell %= len(self.memory)
            elif op == OP_DEC_PTR:
                self.current_cell -= 1
                self.current_cell %= len(self.memory)
            elif op == OP_READ:
                self.memory[self.current_cell] = self.input[0]
                self.input = self.input[1:]
            elif op == OP_WRITE:
                self.output += self.memory[self.current_cell]
            self.ops_left -= 1
