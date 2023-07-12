from logging import INFO, basicConfig, getLogger
from sys import stdout

# One-line lambda wrapper for the singleton design pattern
singleton = lambda c: c()


@singleton
class Logger:
    def __init__(self):
        # Setup logger
        basicConfig(stream=stdout, level=INFO)
        self.log = getLogger('root')
