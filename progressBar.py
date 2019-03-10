import sys
import time


class ProgressBar:
    def __init__(self, total, name, done='#', pending='.', size=100):
        self.start = time.time()
        self.done = done
        self.pending = pending
        self.total = total
        self.size = size
        self.name = name
        self.count = 0

        self.completed = False

        self._create_bar()

    def _create_bar(self):
        full = int(self.size * self.count / self.total)
        self.bar = self.done * full + self.pending * (self.size - full)
        self._print_bar()
    
    def _print_bar(self):
        sys.stdout.write("[{}]  {}".format(self.bar, self.name))
        if self.completed:
            total_time = time.time() - self.start
            sys.stdout.write(' ({:.5f} seconds)\n'.format(total_time))
        else:
            sys.stdout.write('\r')
        sys.stdout.flush()

    def __iadd__(self, other):
        self.count += 1
        if self.count >= self.total:
            self.completed = True
        self._create_bar()
        return self




    
        
     
