from __future__ import annotations

OP_INC = 0
OP_DEC = 1
OP_INC_PTR = 2
OP_DEC_PTR = 3
OP_WRITE = 4
OP_READ = 5


OPS = {
    "+": OP_INC,
    "-": OP_DEC,
    ">": OP_INC_PTR,
    "<": OP_DEC_PTR,
    ".": OP_WRITE,
    ",": OP_READ,
}


class BFException(Exception):
    pass


class Tree:
    def __init__(self):
        self.body = []
        self.finished = False

    def _branch_is_unfinished(self):
        return (
            self.body
            and isinstance(self.body[-1], Tree)
            and not self.body[-1].finished
            and not self.finished
        )

    def append(self, part: int | Tree):
        if self._branch_is_unfinished():
            self.body[-1].append(part)
        else:
            self.body.append(part)

    def finish(self):
        if self._branch_is_unfinished():
            self.body[-1].finish()
        elif not self.finished:
            self.finished = True
        else:
            raise BFException("unmatched ']'")


def parse(code: str) -> Tree:
    result = Tree()
    for c in code:
        if c in OPS:
            result.append(OPS[c])
        elif c == "[":
            result.append(Tree())
        elif c == "]":
            result.finish()
    result.finish()
    if not result.finished:
        raise BFException("'[' was never closed")
    return result


class State:
    def __init__(self, input: bytes, ops_limit: int, mem_size: int = 30_000):
        self.memory = bytearray(mem_size)
        self.current_cell = 0
        self.input = bytearray(input)
        self.output = bytearray()
        self.ops_left = ops_limit

    def decrement_ops(self):
        self.ops_left -= 1
        if self.ops_left == 0:
            raise BFException("operation limit reached")

    def interpret(self, code: Tree):
        for op in code.body:
            if isinstance(op, Tree):
                while self.memory[self.current_cell]:
                    self.interpret(op)
                    self.decrement_ops()
                continue
            elif op == OP_INC:
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
            elif op == OP_WRITE:
                self.output.append(self.memory[self.current_cell])
            elif op == OP_READ:
                if self.input:
                    self.memory[self.current_cell] = self.input.pop(0)
                else:
                    self.memory[self.current_cell] = 0
            self.decrement_ops()
