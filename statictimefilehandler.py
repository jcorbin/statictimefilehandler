import datetime
import errno
import logging
import os
import time

class StaticTimeRotatingFileHandler(logging.FileHandler):
    stream = None

    def __init__(self, template, next_rollover, encoding=None, utc=False, symlink=None):
        self.template = template
        self.next_rollover = next_rollover
        self.encoding = encoding
        self.mode = 'a'
        self.utc = utc
        self.symlink = symlink
        logging.Handler.__init__(self)

    def emit(self, record):
        try:
            if self.shouldRollover(record):
                self.doRollover(record)
            logging.FileHandler.emit(self, record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def shouldRollover(self, record):
        if not self.stream: return True
        return record.created >= self.rolloverAt

    def doRollover(self, record):
        if self.stream:
            self.stream.close()
            del self.stream
        self.baseFilename, self.rolloverAt = self.computeRollover(record)
        basedir = os.path.dirname(self.baseFilename)
        try:
            os.makedirs(basedir)
        except OSError as err:
            if err.errno != errno.EEXIST: raise
        self.stream = self._open()
        if self.symlink is not None:
            try:
                os.symlink(self.baseFilename, self.symlink)
            except OSError as err:
                if err.errno != errno.EEXIST: raise
                os.unlink(self.symlink)
                os.symlink(self.baseFilename, self.symlink)

    def computeRollover(self, record):
        t = record.created
        timeTuple = time.gmtime(t) if self.utc else time.localtime(t)
        filename = time.strftime(self.template, timeTuple)
        newRolloverAt = self.next_rollover(timeTuple)
        return filename, newRolloverAt

# way to easily build next_rollover functions
def make_next_interval(delta):
    zero = ['microsecond']
    n = delta.seconds
    for field, k in (('second', 60),
                     ('minute', 60),
                     ('hour', 24)):
        if n < k: break
        q, r = divmod(n, k)
        if r == 0:
            zero.append(field)
            n = q
    zero = {field: 0 for field in zero}
    def next_interval(timeTuple):
        t = time.mktime(timeTuple)
        d = datetime.datetime.fromtimestamp(t)
        d = d.replace(**zero) + delta
        return time.mktime(d.timetuple())
    return next_interval

def _test_statictimerotatingfilehandler():
    # TODO: turn into actual test case

    hndl = StaticTimeRotatingFileHandler(
        '/tmp/logtest/%Y/%m/%d/%H%M.log',
        make_next_interval(datetime.timedelta(minutes=1)),
        symlink='/tmp/logtest/foo.log')
    log = logging.Logger('foolog')
    log.setLevel(logging.DEBUG)
    hndl.setLevel(logging.DEBUG)
    hndl.setFormatter(logging.Formatter(
        '%(asctime)s [%(process)s] %(name)s %(levelname)s %(message)s'))
    log.addHandler(hndl)

    import random
    words = [line.strip() for line in open('/usr/share/dict/words')]

    mess = lambda: ' '.join(random.choice(words) for _ in xrange(10))

    levels = [logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]

    while True:
        log.log(random.choice(levels), mess())
        time.sleep(random.randint(2, 9))
