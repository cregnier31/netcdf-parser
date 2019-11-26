import re
class Informations():

    def __init__(self, filename: str, area: str, product: str, plot_type: str, dataset: str, subarea: str, stat: str, depth: str):
        self.filename = filename
        self.area = area
        self.product = product
        self.plot_type = plot_type
        self.dataset = dataset
        self.subarea = subarea
        self.stat = stat
        self.depth = depth

    @classmethod
    def from_result(cls, filename, splited):
        area = splited[0]
        product = splited[1]
        plot_type = splited[2]
        dataset = splited[3]
        subarea = splited[4]
        stat = splited[5]
        depth = splited[6]
        return cls(filename, area, product, plot_type, dataset, subarea, stat, depth)

class ErrorMsg():

    def __init__(self, filename: str, msg: str):
        self.filename = filename
        self.msg = msg

    @classmethod
    def from_result(cls, filename: str, msg: str):
        return cls(filename, msg)