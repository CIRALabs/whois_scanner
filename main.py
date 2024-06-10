from db import Db
from error import WhoisCrawlerException, ErrorCodes
import whois
import json
import logging

INPUT_FILE = "input.json"
DB = Db()

log = logging.getLogger()


def read_input():
    try:
        with open(INPUT_FILE) as f:
            return json.load(f)
    except Exception as ex:
        raise WhoisCrawlerException(ErrorCodes.FAILED_TO_READ_INPUT_FILE, ex)


def lookup(domain):
    try:
        resp = whois.whois(domain)
        return resp
    except whois.parser.PywhoisError as ex:
        if str(ex).startswith("No match for"):
            raise WhoisCrawlerException(ErrorCodes.HOSTNAME_DOES_NOT_EXIST)
        else:
            raise ex


def extract_registrant_country(whois_result):
    if "country" in whois_result:
        return whois_result["country"]
    else:
        return None


def extract_domains(input_data):
    if "domains" in input_data:
        return input_data["domains"]
    else:
        raise WhoisCrawlerException(ErrorCodes.BAD_INPUT_FILE)


def extract_hostname(domain):
    if "hostname" in domain:
        return domain["hostname"]
    else:
        raise WhoisCrawlerException(ErrorCodes.BAD_INPUT_FILE)


def main():
    try:
        data = read_input()
        domains = extract_domains(data)
    except WhoisCrawlerException as whoisexception:
        log.exception(whoisexception)
        return whoisexception.code
    except BaseException as ex:
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
        except Exception as ex:
            log.exception(ex)
            return -1  # stop processing immediately

    DB.print_results()
    if len(failed_domains) > 0:
        log.error("Failed domains:")
        log.error(failed_domains)
        return 100
    else:
        return 0


if __name__ == "__main__":
    exit(main())
