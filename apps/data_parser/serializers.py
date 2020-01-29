from rest_framework import serializers

from apps.data_parser.models import Area, Subarea, Universe, Variable, Dataset, Product, Depth, Stat, PlotType, Plot, KpiInsitu, KpiSat, KpiScore


class PlotTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlotType
        fields = ['id', 'name']


class StatSerializer(serializers.ModelSerializer):
    plot_types = PlotTypeSerializer(many=True, read_only=True)
    class Meta:
        model = Stat
        fields = ['id', 'name', 'plot_types']


class DepthSerializer(serializers.ModelSerializer):
    stats = StatSerializer(many=True, read_only=True)
    class Meta:
        model = Depth
        fields = ['id', 'name', 'stats']


class SubareaSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        self.context['id_subarea'] = instance.id
        return super().to_representation(instance)
        
    depths = DepthSerializer(many=True, read_only=True)
    class Meta:
        model = Subarea
        fields = ['id', 'name', 'depths']


class FilteredListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = data.filter(area=self.context['area_id'])
        return super(FilteredListSerializer, self).to_representation(data)


class ProductSerializer(serializers.ModelSerializer):
    subareas = SubareaSerializer(many=True, read_only=True)
    
    class Meta:
        list_serializer_class = FilteredListSerializer
        model = Product
        fields = ['id', 'name', 'comment', 'subareas']


class DatasetSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    class Meta:
        model = Dataset
        fields = '__all__'

class VariableSerializer(serializers.ModelSerializer):
    datasets = DatasetSerializer(many=True, read_only=True)
    class Meta:
        model = Variable
        fields = ['id', 'name', 'datasets']


class UniverseSerializer(serializers.ModelSerializer):
    variables = VariableSerializer(many=True, read_only=True)
    class Meta:
        model = Universe
        fields = ['id', 'name', 'variables']


class AreaSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        self.context['area_id'] = instance.id
        return super().to_representation(instance)

    universes = UniverseSerializer(many=True, read_only=True)
    class Meta:
        model = Area
        fields = ['id', 'name', 'fullname', 'universes']


#### Result ###################################################################
class PlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plot
        fields = ['id', 'name']

#### Kpis #####################################################################
class KpiInsituSerializer(serializers.ModelSerializer):
    variable_name = serializers.SerializerMethodField()

    def get_variable_name(self, obj):
        variable = Variable.objects.get(pk=obj.variable_id)
        return variable.name

    class Meta:
        model = KpiInsitu
        fields = ['id', 'what', 'content', 'month', 'year', 'start', 'end', 'variable_name']

class KpiSatSerializer(serializers.ModelSerializer):
    class Meta:
        model = KpiSat
        fields = ['id', 'sat', 'content', 'month', 'year', 'start', 'end']


class KpiScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = KpiScore
        fields = ['id']