import re

class Informations:

    def __init__(self, text: str, zone: str, product: str, measure_type: str, hum: str, subzone: str, measure_what: str, deep: str):
        self.zone = zone
        self.product = product
        self.measure_type = measure_type
        self.hum = hum
        self.subzone = subzone
        self.measure_what = measure_what
        self.deep = deep

    @classmethod
    def from_result(cls, text: str, tab):
        return cls(text, tab[0], tab[1], tab[2], tab[3], tab[4], tab[5], tab[6])

class DataExtractor:

    def extract(self,text: str):
        splited = re.split('_', text[:-4])
        try:
            return Informations.from_result(text, splited)
        except:
            return {'error': text+' is an invalid filename'}