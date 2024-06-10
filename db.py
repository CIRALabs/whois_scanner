class Db:
  DB = {}

  def record_country(self, domain, country):
    if country not in self.DB:
      self.DB[country] = []
    self.DB[country].append(domain)

  def __str__(self):
    return str(self.DB)
