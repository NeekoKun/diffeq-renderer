class Attractor:
    def __init__(self, q: float, x: float, y: float, sign: int) -> None:
        self.q = q
        self.x = x
        self.y = y
        self.sign = sign

    def move(self, dx, dy):
        self.x += dx
        self.y += dy