class Informations():

    def __init__(self, filename: str, area: str, product: str, plot_type: str, variable: str, subarea: str, stats: str, depths: str, dataset: str):
        self.filename = filename
        self.area = area
        self.product = product
        self.plot_type = plot_type
        self.variable = variable
        self.subarea = subarea
        self.stats = stats
        self.depths = depths
        self.dataset = dataset

    @classmethod
    def from_result(cls, filename: str, tab):
        return cls(filename, tab[0], tab[1], tab[2], tab[3], tab[4], tab[5], tab[6], tab[7])
    
class ErrorMsg():

    def __init__(self, filename: str, msg: str):
        self.filename = filename
        self.msg = msg

    @classmethod
    def from_result(cls, filename: str, msg: str):
        return cls(filename, msg)