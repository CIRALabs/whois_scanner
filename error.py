from enum import Enum


class ErrorCodes(Enum):
  FAILED_TO_READ_INPUT_FILE = 1,
  BAD_INPUT_FILE = 2,
  HOSTNAME_DOES_NOT_EXIST = 3

  def __str__(self):
    if self == ErrorCodes.FAILED_TO_READ_INPUT_FILE:
      return "Failed to read input file"
    elif self == ErrorCodes.BAD_INPUT_FILE:
      return "Bad input file"
    elif self == ErrorCodes.HOSTNAME_DOES_NOT_EXIST:
      return "Hostname does not exist"
    else:
      return super().__str__()


class WhoisCrawlerException(Exception):
  def __init__(self, code: ErrorCodes, cause: Exception = None):
    super().__init__(str(code), cause)
    self.message = str(code)
    self.cause = cause
    self.code = code.value
  
  def __str__(self):
    return self.message
