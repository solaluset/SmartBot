from modules import i18n
from . import TicTacToe


i18n.init()

t = TicTacToe(None, 3, 3, "me", "you", ephemeral_threshold=3)

while t.winner is None:
    print(t)
    t.update(input("Move: "))
print(t)
