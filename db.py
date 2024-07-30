'''Data storage and retrieval interface'''
import csv
from enum import Enum
from io import TextIOWrapper
import json
import sys
from typing import Any, List

SUCCESS_KEY = 'succeed_domains'
PRIVACY_KEY = 'private_domains'
FAILED_KEY = 'failed_domains'
RESULTS_KEY = 'parsed_results'


class Db:
    '''Provides an interface to store/retrieve results'''

    class Format(Enum):
        '''Output formats'''
        JSON = 1
        CSV = 2
        CSV_WHOLE_RESULT = 3

    DB = {}

    def record_country(self, domain, country, nameservers: List[str] = None):
        '''Record a result'''
        if SUCCESS_KEY not in self.DB:
            self.DB[SUCCESS_KEY] = {}
        if country not in self.DB[SUCCESS_KEY]:
            self.DB[SUCCESS_KEY][country] = []
        self.DB[SUCCESS_KEY][country].append(
            {'domain': domain, 'nameservers': nameservers})

    def record_flagged(self, domain: str, nameservers: List[str] = None):
        '''Record a privacy flagged domain'''
        if PRIVACY_KEY not in self.DB:
            self.DB[PRIVACY_KEY] = []
        self.DB[PRIVACY_KEY].append(
            {'domain': domain, 'nameservers': nameservers})

    def record_failed(self, domain, reason, nameservers: List[str] = None):
        '''Record a failed domain lookup'''
        if FAILED_KEY not in self.DB:
            self.DB[FAILED_KEY] = {}
        if reason not in self.DB[FAILED_KEY]:
            self.DB[FAILED_KEY][reason] = []
        self.DB[FAILED_KEY][reason].append(
            {'domain': domain, 'nameservers': nameservers})

    def record_result(self, whois_response: Any) -> None:
        '''Records the whois result to local memory'''

        def domain_to_str(domain):
            if domain is None:
                return ''
            ret_val = None
            if isinstance(domain, list):
                ret_val = domain[0]
            else:
                ret_val = domain
            return ret_val

        def nameservers_to_str(nameservers):
            if nameservers is not None:
                return '|'.join(nameservers)
            return ''

        def date_str(date_val):
            if date_val is None:
                return ''
            ret_val = None
            if isinstance(date_val, list):
                ret_val = date_val[0]
            else:
                ret_val = date_val
            return ret_val.isoformat()

        if RESULTS_KEY not in self.DB:
            self.DB[RESULTS_KEY] = []
        self.DB[RESULTS_KEY].append(
            {
                'domain': domain_to_str(whois_response['domain_name']) if 'domain_name' in whois_response else None,
                'registrar': whois_response['registrar'] if 'registrar' in whois_response else None,
                'registrant_name': whois_response['name'] if 'name' in whois_response else None,
                'registrant_organization': whois_response['org'] if 'org' in whois_response else None,
                'registrant_country': whois_response['country'] if 'country' in whois_response else None,
                'creation_date': date_str(whois_response['creation_date']) if 'creation_date' in whois_response else None,
                'expiration_date': date_str(whois_response['expiration_date']) if 'expiration_date' in whois_response else None,
                'nameservers': nameservers_to_str(whois_response['name_servers']) if 'name_servers' in whois_response else None
            })

    def get_failed_domain_count(self):
        '''Return the number of failed domains recorded'''
        if FAILED_KEY not in self.DB:
            return 0
        count = 0
        for key in self.DB[FAILED_KEY]:
            count += len(self.DB[FAILED_KEY][key])
        return count

    def __str__(self):
        return str(self.DB)

    def output_results(self, output_loc: TextIOWrapper = None, fmt: Format = Format.JSON):
        '''Outputs the results stored in the DB'''
        if fmt == Db.Format.JSON:
            self._output_results_json(output_loc)
        elif fmt == Db.Format.CSV:
            self._output_results_csv(output_loc)
        elif fmt == Db.Format.CSV_WHOLE_RESULT:
            self._output_results_csv_whole_results(output_loc)

    def _output_results_json(self, output_loc: TextIOWrapper = None):
        '''Outputs the results stored in the DB to a JSON file'''
        results = json.dumps(self.DB, indent=4)
        if output_loc is None:
            print(results)
        else:
            output_loc.write(results)

    def _output_results_csv(self, output_loc: TextIOWrapper = None):
        '''Outputs the results stored in the DB to a CSV file'''

        def nameservers_to_str(domain):
            if domain['nameservers'] is not None:
                return '|'.join(domain['nameservers'])
            return ''

        fieldnames = ['domain', 'private', 'country', 'nameservers']
        data = []
        if SUCCESS_KEY in self.DB:
            for country in self.DB[SUCCESS_KEY]:
                for domain in self.DB[SUCCESS_KEY][country]:
                    data.append({
                        'domain': domain['domain'],
                        'private': False,
                        'country': 'N/A' if country is None else country,
                        'nameservers': nameservers_to_str(domain)
                    })
        if PRIVACY_KEY in self.DB:
            for domain in self.DB[PRIVACY_KEY]:
                data.append({'domain': domain['domain'],
                             'private': True,
                             'country': 'Privacy Protected',
                             'nameservers': nameservers_to_str(domain)
                             })
        if FAILED_KEY in self.DB:
            for domain in self.DB[FAILED_KEY]:
                data.append({'domain': domain['domain'],
                             'private': False,
                             'country': 'Failed',
                             'nameservers': nameservers_to_str(domain)
                             })
        writer = csv.DictWriter(output_loc, fieldnames=fieldnames)
        if output_loc is None:
            output_loc = sys.stdout
        writer.writeheader()
        writer.writerows(data)

    def _output_results_csv_whole_results(self, output_loc: TextIOWrapper = None):
        '''Outputs the results stored in the DB to a CSV file'''

        fieldnames = [
            'domain',
            'registrar',
            'registrant_name',
            'registrant_organization',
            'registrant_country',
            'creation_date',
            'expiration_date',
            'nameservers'
        ]
        if output_loc is None:
            output_loc = sys.stdout
        writer = csv.DictWriter(output_loc, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(self.DB[RESULTS_KEY])
