import logging

formatter = logging.Formatter('[%(levelname)s] %(message)s')

sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(formatter)

log = logging.getLogger("LOG")
log.setLevel(logging.INFO)
log.addHandler(sh)

