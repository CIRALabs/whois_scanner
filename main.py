'''Main executable file'''

import json
import logging
import sys

import jsonschema
import whois

from error import WhoisCrawlerException, ErrorCodes
from db import Db

SCHEMA_FILE = "input.schema.json"
INPUT_FILE = "input.json"
ENCODING = "UTF-8"
DB = Db()

log = logging.getLogger()


# Feature Request: Read from other sources beyond local file system
def read_input():
    '''Read from input file'''
    try:
        with open(INPUT_FILE, encoding=ENCODING) as json_file:
            json_data = json.load(json_file)
            return json_data
    except IOError as ex:
        raise WhoisCrawlerException(ErrorCodes.FAILED_TO_READ_INPUT_FILE) from ex


def parse_input(json_data):
    '''Gather input file data and validate against schema'''
    try:
        with open(SCHEMA_FILE, encoding=ENCODING) as schema_file:
            schema = json.load(schema_file)
            jsonschema.validate(instance=json_data, schema=schema) # Will raise exception if invalid
            return json_data
    except jsonschema.exceptions.ValidationError as ex:
        raise WhoisCrawlerException(ErrorCodes.BAD_INPUT_FILE) from ex


def lookup(domain):
    '''Perform the whois lookup'''
    try:
        resp = whois.whois(domain)
        return resp
    except whois.parser.PywhoisError as ex:
        if str(ex).startswith("No match for"):
            raise WhoisCrawlerException(ErrorCodes.HOSTNAME_DOES_NOT_EXIST) from ex
        raise ex


def extract_registrant_data(whois_result):
    '''Pull rant info out of the whois result'''
    name = None
    country = None
    if "name" in whois_result:
        name = whois_result["name"]
    if "country" in whois_result:
        country = whois_result["country"]
    return (name, country)


def extract_domains(input_data, pagenum, pagesize):
    '''Pull domain list out of the input file data'''
    domains = input_data["domains"]
    if pagesize is None:
        return domains
    return domains[pagesize*pagenum:pagesize*(pagenum+1)]


def extract_terms(input_data):
    '''Pull terms list out of the input file data'''
    if "terms" in input_data:
        return input_data["terms"]
    return []


def extract_hostname(domain):
    '''Pull hostname from input file data'''
    return domain["hostname"]


def country_is_flag(terms, name):
    '''Determines if this is a value indicating a 'private' registration'''
    if name is None:
        return False
    if "exact_match" in terms:
        if name in terms["exact_match"]:
            return True
    if "prefix" in terms:
        for term in terms["prefix"]:
            if term.startswith(name):
                return True
    return False

def main(pagenum, pagesize):
    '''Main function. Runs the full process.'''
    try:
        log.info("Processing input data")
        raw_json = read_input()
        data = parse_input(raw_json)
        domains = extract_domains(data, pagenum, pagesize)
        terms = extract_terms(data)
    except WhoisCrawlerException as whoisexception:
        log.exception(whoisexception)
        return whoisexception.code
    except BaseException as ex:  # pylint: disable=broad-except
        log.exception(ex)
        return -1

    failed_domains = []
    index = 0
    log.info("Begin whois lookup for %d hostnames", len(domains))
    for domain in domains:
        if index % 100 == 0:
            log.info("Processing host (%d of %d)", index, len(domains))
        try:
            hostname = extract_hostname(domain)
            log.debug("Looking up hostname %s", hostname)
            whois_result = lookup(hostname)
            (name, country) = extract_registrant_data(whois_result)
            if country_is_flag(terms, name):
                log.debug("# Hostname %s was marked as a privacy flag. Reason %s.", hostname, name)
                DB.record_flagged(hostname, name)
            else:
                log.debug("# Hostname %s was recorded for country %s.", hostname, country)
                DB.record_country(hostname, country)
            index += 1
        except WhoisCrawlerException as whoisexception:
            failed_domains.append(
                {"domain": domain, "cause": str(whoisexception)})
            # Continue processing, but record the failure
        except whois.parser.PywhoisError as ex:
            failed_domains.append({"domain": domain, "cause": ex})
            # Continue processing, but record the failure
        except Exception as ex:  # pylint: disable=broad-except
            log.exception(ex)
            return -100  # stop processing immediately

    DB.output_results()
    if len(failed_domains) > 0:
        log.error("Failed domains:")
        log.error(failed_domains)
        return len(failed_domains)
    return 0


if __name__ == "__main__":
    PAGE_NUM = None
    PAGE_SIZE = None
    if len(sys.argv) >= 3:
        PAGE_NUM = int(sys.argv[1])
        PAGE_SIZE = int(sys.argv[2])

    sys.exit(main(PAGE_NUM, PAGE_SIZE))
