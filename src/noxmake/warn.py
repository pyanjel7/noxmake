import nox.logger


def warning(message):
    nox.logger.logger.warning(message, stacklevel=2)
