from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.data_parser.services import DataExtractor
import jsons,json

class ExtractorApiView(APIView):

    @swagger_auto_schema(
        operation_id ='extract',
        responses={
            200: openapi.Response(
               description='Will return a dictonnary giving you data extracted from filename.',
            ),
        },
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT, 
            properties={
                'text': openapi.Schema(type=openapi.TYPE_STRING, description="global_global-analysis-forecast-phy-001-024_timeseries_salinity_antarctic-circumpolar_anomaly-correlation_0000-0005m.png"),
            }
        )
    )
    def post(self, request, *args, **kwargs):
        #If the request body is empty
        if len(request.body)==0:
	        return HttpResponse("<p> Le body du Json est vide<p>", status=400)
        else:
            payload = json.loads(request.body)
            result = DataExtractor().extract(payload['text'])
            json_to_send = jsons.dump(result)
            return Response(json_to_send)

       
    