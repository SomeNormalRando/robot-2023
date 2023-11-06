#!/usr/bin/env python3
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter(fmt="[%(asctime)s] [main] [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

ch.setFormatter(formatter)
logger.addHandler(ch)

logger.info("hi")