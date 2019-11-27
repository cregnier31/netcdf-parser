from django.db import models

#### Zone #####################################################################
class Area(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
        
class Subarea(models.Model):
    name = models.CharField(max_length=50)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

#### Filters ##################################################################
class Univers(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Variable(models.Model):
    name = models.CharField(max_length=50)
    univers = models.ForeignKey(Univers, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Dataset(models.Model):
    name = models.CharField(max_length=50)
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=256)
    comment = models.TextField(null=True)
    datasets = models.ManyToManyField(Dataset)

    def __str__(self):
        return self.name

class Depth(models.Model):
    name = models.CharField(max_length=50)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Stat(models.Model):
    name = models.CharField(max_length=50)
    depth = models.ForeignKey(Depth, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class PlotType(models.Model):
    name = models.CharField(max_length=50)
    stat = models.ForeignKey(Stat, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

#### Result ###################################################################
class Plot(models.Model):
    filename = models.CharField(max_length=256)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    subarea = models.ForeignKey(Subarea, on_delete=models.CASCADE)
    univers = models.ForeignKey(Univers, on_delete=models.CASCADE)
    variable = models.ForeignKey(Variable, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    depth = models.ForeignKey(Depth, on_delete=models.CASCADE)
    stat = models.ForeignKey(Stat, on_delete=models.CASCADE)
    plot_type = models.ForeignKey(PlotType, on_delete=models.CASCADE)


    def __str__(self):
        return self.filename
