'''Main executable file'''

import json
import logging
import sys
import whois

from error import WhoisCrawlerException, ErrorCodes
from db import Db

INPUT_FILE = "input.json"
ENCODING = "UTF-8"
DB = Db()

log = logging.getLogger()


def read_input():
    '''Read from input file'''
    try:
        with open(INPUT_FILE, encoding=ENCODING) as file:
            return json.load(file)
    except Exception as ex:
        raise WhoisCrawlerException(ErrorCodes.FAILED_TO_READ_INPUT_FILE) from ex


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
    if "domains" in input_data:
        domains = input_data["domains"]
        if pagesize is None:
            return domains
        return domains[pagesize*pagenum:pagesize*(pagenum+1)]
    raise WhoisCrawlerException(ErrorCodes.BAD_INPUT_FILE)


def extract_hostname(domain):
    '''Pull hostname from input file data'''
    if "hostname" in domain:
        return domain["hostname"]
    raise WhoisCrawlerException(ErrorCodes.BAD_INPUT_FILE)


def main(pagenum, pagesize):
    '''Main function. Runs the full process.'''
    try:
        data = read_input()
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
