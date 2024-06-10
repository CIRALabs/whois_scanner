'''Data storage and retrieval interface'''
from pprint import pprint

PRIVACY_KEY = "private_domains"

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

    def __str__(self):
        return str(self.DB)

    # Feature Request: Multiple output locations
    def output_results(self):
        '''Outputs the results stored in the DB'''
        print("Final Results:")
        pprint(self.DB)
