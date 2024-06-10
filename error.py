'''Custom errors'''

from enum import Enum


class ErrorCodes(Enum):
    '''List of error codes, and english user-friendly descriptions'''

    FAILED_TO_READ_INPUT_FILE = -1
    BAD_INPUT_FILE = -2
    HOSTNAME_DOES_NOT_EXIST = -3

    def __str__(self):
        if self == ErrorCodes.FAILED_TO_READ_INPUT_FILE:
            return "Failed to read input file"
        if self == ErrorCodes.BAD_INPUT_FILE:
            return "Bad input file"
        if self == ErrorCodes.HOSTNAME_DOES_NOT_EXIST:
            return "Hostname does not exist"
        return super().__str__()


class WhoisScannerException(Exception):
    '''Custom exception for this project'''

    def __init__(self, code: ErrorCodes):
        super().__init__(str(code))
        self.message = str(code)
        self.code = code.value

    def __str__(self):
        return self.message
