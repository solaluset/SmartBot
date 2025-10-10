from modules import i18n
from . import TicTacToe, UltimateTicTacToe


i18n.init()

TicTacToe
UltimateTicTacToe

t = UltimateTicTacToe(None, 3, 3, "me", "you", ephemeral_threshold=3)

while t.winner is None:
    print(t)
    t.update(input("Move: "))
print(t)
