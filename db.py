'''Data storage and retrieval interface'''
from enum import Enum
from io import TextIOWrapper
import json

SUCCESS_KEY = "succeed_domains"
PRIVACY_KEY = "private_domains"
FAILED_KEY = "failed_domains"


class Db:
    '''Provides an interface to store/retrieve results'''

    class Format(Enum):
        '''Output formats'''
        JSON =  1,
        CSV = 2

    DB = {}

    def record_country(self, domain, country):
        '''Record a result'''
        if SUCCESS_KEY not in self.DB:
            self.DB[SUCCESS_KEY] = {}
        if country not in self.DB[SUCCESS_KEY]:
            self.DB[SUCCESS_KEY][country] = []
        self.DB[SUCCESS_KEY][country].append(domain)

    def record_flagged(self, domain, term):
        '''Record a privacy flagged domain'''
        if PRIVACY_KEY not in self.DB:
            self.DB[PRIVACY_KEY] = {}
        if term not in self.DB[PRIVACY_KEY]:
            self.DB[PRIVACY_KEY][term] = []
        self.DB[PRIVACY_KEY][term].append(domain)

    def record_failed(self, domain, reason):
        '''Record a failed domain lookup'''
        if FAILED_KEY not in self.DB:
            self.DB[FAILED_KEY] = {}
        if reason not in self.DB[FAILED_KEY]:
            self.DB[FAILED_KEY][reason] = []
        self.DB[FAILED_KEY][reason].append(domain)

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
        match fmt:
            case Db.Format.JSON:
                self._output_results_json(output_loc)
            case Db.Format.CSV:
                self._output_results_csv(output_loc)

    def _output_results_json(self, output_loc: TextIOWrapper = None):
        '''Outputs the results stored in the DB to a JSON file'''
        results = json.dumps(self.DB, indent=4)
        if output_loc is None:
            print(results)
        else:
            output_loc.write(results)

    def _output_results_csv(self, output_loc: TextIOWrapper = None):
        '''Outputs the results stored in the DB to a CSV file'''
        pass
