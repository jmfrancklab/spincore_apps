import logging,sys
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
FORMAT = "--> %(filename)s(%(lineno)s):%(name)s %(funcName)20s %(asctime)20s\n%(levelname)s: %(message)s"
formatter = logging.Formatter(FORMAT)
handler.setFormatter(formatter)
logger.addHandler(handler)
