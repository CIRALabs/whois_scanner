from error import WhoisCrawlerException, ErrorCodes
import whois
import json
import logging

INPUT_FILE = "input.json"
DB = {}

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

def extract_registrant_country(whois_result):
  if "country" in whois_result:
    return whois_result["country"]
  else:
    return None

def extract_domains(input_data):
  return input_data["domains"] # TODO: Error handling for bad input file?

def extract_hostname(domain):
  return domain["hostname"] # TODO: Error handling for bad input file?

def record_country(domain, country):
  if country not in DB:
    DB[country] = []
  DB[country].append(domain)

def main():
  try:
    data = read_input()
    domains = extract_domains(data)
    for domain in domains:
      hostname = extract_hostname(domain)
      whois_result = lookup(hostname)
      country = extract_registrant_country(whois_result)
      record_country(hostname, country)
    print(DB)
  except WhoisCrawlerException as whoisexception:
    log.exception(whoisexception)
    return whoisexception.code
  except BaseException as ex:
    log.exception(ex)
    return -1

if __name__ == "__main__":
  exit(main())
