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
    except Exception as ex:
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


def extract_registrant_country(whois_result):
    '''Pull rant country out of the whois result'''
    if "country" in whois_result:
        return whois_result["country"]
    return None


def extract_domains(input_data, pagenum, pagesize):
    '''Pull domain list out of the input file data'''
    domains = input_data["domains"]
    if pagesize is None:
        return domains
    return domains[pagesize*pagenum:pagesize*(pagenum+1)]


def extract_hostname(domain):
    '''Pull hostname from input file data'''
    return domain["hostname"]


def main(pagenum, pagesize):
    '''Main function. Runs the full process.'''
    try:
        raw_json = read_input()
        data = parse_input(raw_json)
        domains = extract_domains(data, pagenum, pagesize)
    except WhoisCrawlerException as whoisexception:
        log.exception(whoisexception)
        return whoisexception.code
    except BaseException as ex:  # pylint: disable=broad-except
        log.exception(ex)
        return -1

    failed_domains = []
    for domain in domains:
        try:
            hostname = extract_hostname(domain)
            whois_result = lookup(hostname)
            country = extract_registrant_country(whois_result)
            DB.record_country(hostname, country)
        except WhoisCrawlerException as whoisexception:
            failed_domains.append(
                {"domain": domain, "cause": str(whoisexception)})
            # Continue processing, but record the failure
        except whois.parser.PywhoisError as ex:
            failed_domains.append({"domain": domain, "cause": ex})
            # Continue processing, but record the failure
        except Exception as ex:  # pylint: disable=broad-except
            log.exception(ex)
            return -1  # stop processing immediately

    DB.print_results()
    if len(failed_domains) > 0:
        log.error("Failed domains:")
        log.error(failed_domains)
        return 100
    return 0


if __name__ == "__main__":
    PAGE_NUM = None
    PAGE_SIZE = None
    if len(sys.argv) >= 3:
        PAGE_NUM = int(sys.argv[1])
        PAGE_SIZE = int(sys.argv[2])

    sys.exit(main(PAGE_NUM, PAGE_SIZE))
