'''Data storage and retrieval interface'''
from pprint import pprint

PRIVACY_KEY = "private_domains"
FAILED_KEY = "failed_domains"

class Db:
    '''Provides an interface to store/retrieve results'''

    DB = {}

    def record_country(self, domain, country):
        '''Record a result'''
        if country not in self.DB:
            self.DB[country] = []
        self.DB[country].append(domain)

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

    # Feature Request: Multiple output locations
    def output_results(self):
        '''Outputs the results stored in the DB'''
        print("Final Results:")
        pprint(self.DB)
