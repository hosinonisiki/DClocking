from chips import *

def init_FH8052(spi, port):
    init_AD9528(spi, port, 3)
    init_AD9680(spi, port, 1)
    init_AD9152(spi, port, 2)
    return
