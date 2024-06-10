from enum import Enum


class ErrorCodes(Enum):
  FAILED_TO_READ_INPUT_FILE = 1

  def __str__(self):
    if self == ErrorCodes.FAILED_TO_READ_INPUT_FILE:
      return "Failed to read input file"
    else:
      return super().__str__()


class WhoisCrawlerException(Exception):
  def __init__(self, code: ErrorCodes, cause: BaseException = None):
    super().__init__(str(code), cause)
    self.code = code.value
