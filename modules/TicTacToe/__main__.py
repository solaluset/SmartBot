from modules import i18n
from . import TicTacToe, UltimateTicTacToe


i18n.init()

TicTacToe

t = UltimateTicTacToe(None, 2, 2, "me", "you", ephemeral_threshold=1)

while t.winner is None:
    print(t)
    t.update(input("Move: "))
print(t)
