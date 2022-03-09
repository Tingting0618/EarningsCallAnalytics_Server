"""View module for handling requests about company types"""
from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from earningscall_api.models import Company


class CompanyView(ViewSet):
    """Company types"""

    def retrieve(self, request, pk=None):
        """Handle GET requests for single Company

        Returns:
            Response -- JSON serialized Company
        """
        try:
            company = Company.objects.get(pk=pk)
            serializer = CompanySerializer(company, context={'request': request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)


            
    def list(self, request):
        """Handle GET requests to get all company types

        Returns:
            Response -- JSON serialized list of company types
        """
        companies = Company.objects.all()
        searched_co = self.request.query_params.get('symbol', None)
        start_year = self.request.query_params.get('start_year', None)
        end_year = self.request.query_params.get('end_year', None)

        if searched_co and start_year and end_year:
            searched_co = searched_co.split(',')  
            start_year=int(start_year)
            end_year=int(end_year)        
            companies = companies.filter(value__in=searched_co)
            companies = companies.filter(year__gte=start_year)
            companies = companies.filter(year__lte=end_year)
            
            serializer = CompanyTranscriptSerializer(
                companies, many=True, context={'request': request})
            return Response(serializer.data)
        
        else: 
            serializer = CompanySerializer(
            companies, many=True, context={'request': request})
            return Response(serializer.data)

class CompanySerializer(serializers.ModelSerializer):
    """JSON serializer for company types

    Arguments:
        serializers
    """
    class Meta:
        model = Company
        fields = ('id', 'label','value')

class CompanyTranscriptSerializer(serializers.ModelSerializer):
    """JSON serializer for company types

    Arguments:
        serializers
    """
    class Meta:
        model = Company
        fields = ('id', 'label','value', 'company_type',  'year','quarter','transcript','followers' )
