import logging

class DFLog(object):
    """Generates a custom logger for Dragonfly."

    Attributes:
        origin - name of the logger.
        logfile - file to write messages to.
    """

    def __init__(self, origin:str = "[DEFAULT]", logfile:str = '/tmp/dragonfly_log.txt'):
        
        self.origin = origin
        self.logfile = logfile
        self.logger = None
        
        # Create a logger for this class. Note that this is 
        # a singleton logger, so we need to clear any existing
        # handlers before adding a new one to avoid duplicates.
        log = logging.getLogger(self.origin)
        if (log.hasHandlers()):
            log.handlers.clear()
        fh = logging.FileHandler(self.logfile)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        fh.setFormatter(formatter)
        log.addHandler(fh)
        log.setLevel(logging.DEBUG)
    
        self.logger = log