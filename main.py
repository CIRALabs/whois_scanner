'''Main executable file'''

import csv
import json
import logging
import os
import sys
from typing import Any, List, Tuple

import jsonschema
from ratelimit import sleep_and_retry, limits
import whois

from error import WhoisScannerException, ErrorCodes
from db import Db

# Basic rate limiting: 5 requests per 20 seconds
RATELIMIT_REQUESTS = 50    # Number of requests to rate limit
RATELIMIT_TIMERANGE = 60   # Amount of time to rate limit
SCHEMA_FILE = "rules.schema.json"
RULES_FILE = "rules.json"
DOMAINS_FILE = "input.csv"
OUTPUT_FORMAT = Db.Format.CSV
OUTPUT_FILE = "output.csv"
ENCODING = "UTF-8"
DB = Db()

LOGLEVEL = os.environ.get('LOGLEVEL', 'ERROR').upper()
logging.basicConfig(level=LOGLEVEL)
log = logging.getLogger(__name__)


# Feature Request: Read from other sources beyond local file system
def read_input(pagenum: int, pagesize: int) -> Tuple[Any, List[str]]:
    '''Read from input files'''
    try:
        with open(RULES_FILE, encoding=ENCODING) as rules_file:
            rules_data = json.load(rules_file)
            parse_input(rules_data)
            terms = extract_terms(rules_data)
    except FileNotFoundError:
        terms = {}
    except IOError as ex:
        raise WhoisScannerException(
            ErrorCodes.FAILED_TO_READ_INPUT_FILE) from ex

    try:
        with open(DOMAINS_FILE, encoding=ENCODING) as domains_file:
            csv_data = csv.DictReader(domains_file)
            domains = extract_domains(csv_data, pagenum, pagesize)
    except IOError as ex:
        raise WhoisScannerException(
            ErrorCodes.FAILED_TO_READ_INPUT_FILE) from ex

    return (terms, domains)


def parse_input(json_data: Any) -> None:
    '''Gather input file data and validate against schema'''
    try:
        with open(SCHEMA_FILE, encoding=ENCODING) as schema_file:
            schema = json.load(schema_file)
            # Will raise exception if invalid
            jsonschema.validate(instance=json_data, schema=schema)
    except jsonschema.exceptions.ValidationError as ex:
        raise WhoisScannerException(ErrorCodes.BAD_INPUT_FILE) from ex


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


def extract_domains(input_data: Any, pagenum: int, pagesize: int) -> List[str]:
    '''Pull domain list out of the input file data'''
    if pagesize is None:
        return input_data
    start = pagesize*pagenum
    stop = pagesize*(pagenum+1)
    specific_rows = [row for idx, row in enumerate(
        input_data) if idx in range(start, stop)]
    return [row["input_url"] for row in specific_rows]


def extract_terms(input_data: Any) -> List[Any]:
    '''Pull terms list out of the input file data'''
    if "terms" in input_data:
        return input_data["terms"]
    return []


def name_privacy_match(terms: List[Any], whois_result: Any) -> str:
    '''Checks name or org fields for privacy indicator'''
    name = None
    if "name" in whois_result:
        name = whois_result["name"]
    if name is None and "org" in whois_result:
        name = whois_result["org"]
    log.debug("Checking %s for privacy flag", name)
    if name is None:
        return None
    if "exact_match" in terms:
        if name in terms["exact_match"]:
            return name
    if "prefix" in terms:
        for term in terms["prefix"]:
            if name.startswith(term):
                return f"prefix:{term}"
    return None


def privacy_match(terms: List[Any], whois_result: Any) -> str:
    '''Determines if this is a value indicating a 'private' registration'''
    name_match = name_privacy_match(terms, whois_result)
    if name_match is not None:
        return name_match
    return None


def main(pagenum: int, pagesize: int) -> int:
    '''Main function. Runs the full process.'''
    try:
        log.info("Processing input data")
        terms, domains = read_input(pagenum, pagesize)
    except WhoisScannerException as whoisexception:
        log.exception(whoisexception)
        return whoisexception.code
    except BaseException as ex:  # pylint: disable=broad-except
        log.exception(ex)
        return -1

    index = 0
    log.info("Begin whois lookup for %d hostnames", len(domains))
    for domain in domains:
        if index % 10 == 0:
            log.info(
                "Processing host [%d of %d] (will output every 10)", index, len(domains))
        try:
            log.debug("Looking up hostname %s", domain)
            whois_result = lookup(domain)
            country = extract_registrant_country(whois_result)
            privacy_term_match = privacy_match(terms, whois_result)
            if privacy_term_match is not None:
                log.debug("# Hostname %s was marked as a privacy flag. Term Match: %s.",
                          domain, privacy_term_match)
                DB.record_flagged(domain, privacy_term_match)
            else:
                log.debug("# Hostname %s was recorded for country %s.",
                          domain, country)
                DB.record_country(domain, country)
            index += 1
        except WhoisScannerException as whoisexception:
            log.debug("# Hostname %s was marked failed. %s",
                      domain, str(whoisexception))
            DB.record_failed(domain, str(whoisexception))
        except whois.parser.PywhoisError as ex:
            log.debug("# Hostname %s was marked failed. %s", domain, str(ex))
            DB.record_failed(domain, str(ex))
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
