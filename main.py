'''Main executable file'''

import json
import logging
import os
import sys
from typing import Any, List, Tuple

import jsonschema
import whois

from error import WhoisScannerException, ErrorCodes
from db import Db

SCHEMA_FILE = "input.schema.json"
INPUT_FILE = "input.json"
ENCODING = "UTF-8"
DB = Db()

LOGLEVEL = os.environ.get('LOGLEVEL', 'ERROR').upper()
logging.basicConfig(level=LOGLEVEL)
log = logging.getLogger(__name__)


# Feature Request: Read from other sources beyond local file system
def read_input() -> Any:
    '''Read from input file'''
    try:
        with open(INPUT_FILE, encoding=ENCODING) as json_file:
            json_data = json.load(json_file)
            return json_data
    except IOError as ex:
        raise WhoisScannerException(ErrorCodes.FAILED_TO_READ_INPUT_FILE) from ex


def parse_input(json_data: Any) -> Any:
    '''Gather input file data and validate against schema'''
    try:
        with open(SCHEMA_FILE, encoding=ENCODING) as schema_file:
            schema = json.load(schema_file)
            jsonschema.validate(instance=json_data, schema=schema) # Will raise exception if invalid
            return json_data
    except jsonschema.exceptions.ValidationError as ex:
        raise WhoisScannerException(ErrorCodes.BAD_INPUT_FILE) from ex


def lookup(domain: str) -> Any:
    '''Perform the whois lookup'''
    try:
        resp = whois.whois(domain)
        return resp
    except whois.parser.PywhoisError as ex:
        if str(ex).startswith("No match for"):
            raise WhoisScannerException(ErrorCodes.HOSTNAME_DOES_NOT_EXIST) from ex
        raise ex


def extract_registrant_data(whois_result: Any) -> Tuple[str, str]:
    '''Pull rant info out of the whois result'''
    name = None
    country = None
    if "name" in whois_result:
        name = whois_result["name"]
    if name is None and "org" in whois_result:
        name = whois_result["org"]
    if "country" in whois_result:
        country = whois_result["country"]
    return (name, country)


def extract_domains(input_data: Any, pagenum: int, pagesize: int) -> List[str]:
    '''Pull domain list out of the input file data'''
    domains = input_data["domains"]
    if pagesize is None:
        return domains
    return domains[pagesize*pagenum:pagesize*(pagenum+1)]


def extract_terms(input_data: Any) -> List[Any]:
    '''Pull terms list out of the input file data'''
    if "terms" in input_data:
        return input_data["terms"]
    return []


def extract_hostname(domain: Any) -> str:
    '''Pull hostname from input file data'''
    return domain["hostname"]


def name_privacy_match(terms: List[Any], name: str) -> str:
    '''Determines if this is a value indicating a 'private' registration'''
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

def main(pagenum: int, pagesize: int) -> int:
    '''Main function. Runs the full process.'''
    try:
        log.info("Processing input data")
        raw_json = read_input()
        data = parse_input(raw_json)
        domains = extract_domains(data, pagenum, pagesize)
        terms = extract_terms(data)
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
            log.info("Processing host [%d of %d] (will output every 10)", index, len(domains))
        try:
            hostname = extract_hostname(domain)
            log.debug("Looking up hostname %s", hostname)
            whois_result = lookup(hostname)
            (name, country) = extract_registrant_data(whois_result)
            privacy_term_match = name_privacy_match(terms, name)
            if privacy_term_match is not None:
                log.debug("# Hostname %s was marked as a privacy flag. Term Match: %s.",
                          hostname, privacy_term_match)
                DB.record_flagged(hostname, privacy_term_match)
            else:
                log.debug("# Hostname %s was recorded for country %s.", hostname, country)
                DB.record_country(hostname, country)
            index += 1
        except WhoisScannerException as whoisexception:
            log.debug("# Hostname %s was marked failed. %s", domain, str(whoisexception))
            DB.record_failed(domain, str(whoisexception))
        except whois.parser.PywhoisError as ex:
            log.debug("# Hostname %s was marked failed. %s", domain, str(ex))
            DB.record_failed(domain, str(ex))
        except Exception as ex:  # pylint: disable=broad-except
            log.exception(ex)
            return -100  # stop processing immediately

    DB.output_results()
    return DB.get_failed_domain_count()


if __name__ == "__main__":
    PAGE_NUM = None
    PAGE_SIZE = None
    if len(sys.argv) >= 3:
        PAGE_NUM = int(sys.argv[1])
        PAGE_SIZE = int(sys.argv[2])

    sys.exit(main(PAGE_NUM, PAGE_SIZE))
