'''Main executable file'''

import csv
import logging
import os
import re
import sys
from typing import Any, List

from ratelimit import sleep_and_retry, limits
import whois

from error import WhoisScannerException, ErrorCodes
from db import Db

# Basic rate limiting: 5 requests per 20 seconds
RATELIMIT_REQUESTS = 50    # Number of requests to rate limit
RATELIMIT_TIMERANGE = 60   # Amount of time to rate limit
DOMAINS_FILE = "input.csv"
OUTPUT_FORMAT = Db.Format.CSV
OUTPUT_FILE = "output.csv"
ENCODING = "UTF-8"
DB = Db()

PRIVACY_REGEX = re.compile("private|proxy|redacted|privacy", re.IGNORECASE)
LOGLEVEL = os.environ.get('LOGLEVEL', 'ERROR').upper()
logging.basicConfig(level=LOGLEVEL)
log = logging.getLogger(__name__)


# Feature Request: Read from other sources beyond local file system
def read_input(pagenum: int, pagesize: int) -> List[str]:
    '''Read from input file'''
    try:
        with open(DOMAINS_FILE, encoding=ENCODING) as domains_file:
            csv_data = csv.DictReader(domains_file)
            domains = extract_domains(csv_data, pagenum, pagesize)
    except IOError as ex:
        raise WhoisScannerException(
            ErrorCodes.FAILED_TO_READ_INPUT_FILE) from ex

    return domains


# Adding throttling
# This is actually very basic.
# The whois library sends queries to the appropriate NIC servers, so we're overly-throttling here.
# More logic could be added to ask the whois library:
#   WHICH server the domain's request would be sent to, and then throttle per-server.
# This would likely be done by creating a NICClient, then using client.choose_server
@sleep_and_retry
@limits(calls=RATELIMIT_REQUESTS, period=RATELIMIT_TIMERANGE)
def lookup(domain: str) -> Any:
    '''Perform the whois lookup'''
    try:
        resp = whois.whois(domain)
        return resp
    except whois.parser.PywhoisError as ex:
        if str(ex).startswith("No match for"):
            raise WhoisScannerException(
                ErrorCodes.HOSTNAME_DOES_NOT_EXIST) from ex
        raise ex


def extract_registrant_country(whois_result: Any) -> str:
    '''Pull rant info out of the whois result'''
    country = None
    if "country" in whois_result:
        country = whois_result["country"]
    return country


def extract_nameservers(whois_result: Any) -> List[str]:
    '''Pull nameservers info out of the whois result'''
    if "name_servers" in whois_result:
        return whois_result["name_servers"]
    return None


def extract_domains(input_data: Any, pagenum: int, pagesize: int) -> List[str]:
    '''Pull domain list out of the input file data'''
    if pagesize is None:
        return input_data
    start = pagesize*pagenum
    stop = pagesize*(pagenum+1)
    specific_rows = [row for idx, row in enumerate(
        input_data) if idx in range(start, stop)]
    return [row["input_url"] for row in specific_rows]


def privacy_match(whois_result: str) -> bool:
    '''Determines if this is a value indicating a 'private' registration'''
    for key in whois_result:
        if PRIVACY_REGEX.match(str(whois_result[key])) is not None:
            return True
    return False


def main(pagenum: int, pagesize: int) -> int:
    '''Main function. Runs the full process.'''
    try:
        log.info("Processing input data")
        domains = read_input(pagenum, pagesize)
    except WhoisScannerException as whoisexception:
        log.exception(whoisexception)
        return whoisexception.code
    except BaseException as ex:  # pylint: disable=broad-except
        log.exception(ex)
        return -1

    index = 0
    nameserver_list = None
    log.info("Begin whois lookup for %d hostnames", len(domains))
    for domain in domains:
        if index % 10 == 0:
            log.info(
                "Processing host [%d of %d] (will output every 10)", index, len(domains))
        try:
            log.debug("Looking up hostname %s", domain)
            whois_result = lookup(domain)
            country = extract_registrant_country(whois_result)
            nameserver_list = extract_nameservers(whois_result)
            privacy_term_match = privacy_match(whois_result)
            if privacy_term_match:
                log.debug("# Hostname %s was marked as a privacy flag.", domain)
                DB.record_flagged(domain, nameserver_list)
            else:
                log.debug("# Hostname %s was recorded for country %s.",
                          domain, country)
                DB.record_country(domain, country, nameserver_list)
            index += 1
        except WhoisScannerException as whoisexception:
            log.debug("# Hostname %s was marked failed. %s",
                      domain, str(whoisexception))
            DB.record_failed(domain, str(whoisexception), nameserver_list)
        except whois.parser.PywhoisError as ex:
            log.debug("# Hostname %s was marked failed. %s", domain, str(ex))
            DB.record_failed(domain, str(ex), nameserver_list)
        except Exception as ex:  # pylint: disable=broad-except
            log.exception(ex)
            return -100  # stop processing immediately

    with open(OUTPUT_FILE, "w", encoding=ENCODING) as output:
        DB.output_results(output, OUTPUT_FORMAT)
    return DB.get_failed_domain_count()


if __name__ == "__main__":
    PAGE_NUM = None
    PAGE_SIZE = None
    if len(sys.argv) >= 3:
        PAGE_NUM = int(sys.argv[1])
        PAGE_SIZE = int(sys.argv[2])

    sys.exit(main(PAGE_NUM, PAGE_SIZE))
