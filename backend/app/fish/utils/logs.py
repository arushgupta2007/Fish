import logging

class CustomLogFormatter(logging.Formatter):
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    fmt_level = "%(levelname)s"
    fmt_rem = ":     %(asctime)s - %(name)s - %(threadName)s - %(filename)s:%(lineno)d - %(message)s"

    FORMATS = {
        logging.DEBUG: green + fmt_level + reset + fmt_rem,
        logging.INFO: green + fmt_level + reset + fmt_rem,
        logging.WARNING: yellow + fmt_level + reset + fmt_rem,
        logging.ERROR: red + fmt_level + reset + fmt_rem,
        logging.CRITICAL: bold_red + fmt_level + reset + fmt_rem
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
