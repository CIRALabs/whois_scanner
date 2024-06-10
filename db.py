'''Data storage and retrieval interface'''

class Db:
    '''Provides an interface to store/retrieve results'''

    DB = {}

    def record_country(self, domain, country):
        '''Record a result'''
        if country not in self.DB:
            self.DB[country] = []
        self.DB[country].append(domain)

    def __str__(self):
        return str(self.DB)

    # Feature Request: Multiple output locations
    def output_results(self):
        '''Outputs the results stored in the DB'''
        print(self)
