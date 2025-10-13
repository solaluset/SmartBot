from modules import i18n
from . import TicTacToe, UltimateTicTacToe


i18n.init()

TicTacToe
UltimateTicTacToe

t = TicTacToe(3, 3, ["me", "you"], ephemeral_threshold=0)

while t.winner is None and not t.draw:
    print(t)
    t.update(input("Move: "))
print(t)
