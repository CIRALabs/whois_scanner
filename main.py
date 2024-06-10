from error import WhoisCrawlerException, ErrorCodes
import whois
import json
import logging

INPUT_FILE = "input.jsona"


log = logging.getLogger()

def read_input():
  try:
    with open(INPUT_FILE) as f:
      return json.load(f)
  except Exception as ex:
    raise WhoisCrawlerException(ErrorCodes.FAILED_TO_READ_INPUT_FILE, ex)

def lookup(domain):
  resp = whois.whois(domain)
  return resp

def extract_registrant(whois_result):
  if whois_result.has("country"):
    return whois_result["country"]
  else:
    return None

def main():
  try:
    data = read_input()
    print(data)
  except WhoisCrawlerException as whoisexception:
    log.exception(whoisexception)
    return whoisexception.code
  except BaseException as ex:
    log.exception(ex)
    return -1

if __name__ == "__main__":
  exit(main())
