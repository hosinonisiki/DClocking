from chips import *

def init_FH8052(spi, port):
    print("Configuring FH8052 (no external ref) on fmc port {}".format(port))
    init_AD9528(spi, port, 3)
    init_AD9680(spi, port, 1)
    init_AD9152(spi, port, 2)
    return

def init_FH8052_ext_ref(spi, port):
    print("Configuring FH8052 (external ref) on fmc port {}".format(port))
    init_AD9528_ext_ref(spi, port, 3)
    init_AD9680(spi, port, 1)
    init_AD9152(spi, port, 2)
    return

def init_FL9627(spi, port):
    print("Configuring FL9627 on fmc port {}".format(port))
    init_AD9627(spi, port, 1)
    init_AD9627(spi, port, 2)
    return