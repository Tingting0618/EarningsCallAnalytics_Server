"""View module for handling requests about company types"""
from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from earningscall_api.models import CompanyType


class CompanyTypeView(ViewSet):
    """CompanyType types"""

    def retrieve(self, request, pk=None):
        """Handle GET requests for single CompanyType

        Returns:
            Response -- JSON serialized CompanyType
        """
        try:
            company_type = CompanyType.objects.get(pk=pk)
            serializer = CompanyTypeSerializer(company_type, context={'request': request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

    def list(self, request):
        """Handle GET requests to get all company types

        Returns:
            Response -- JSON serialized list of company types
        """
        company_type = CompanyType.objects.all()

        # Note the addtional `many=True` argument to the
        # serializer. It's needed when you are serializing
        # a list of objects instead of a single object.
        serializer = CompanyTypeSerializer(
            company_type, many=True, context={'request': request})
        return Response(serializer.data)

class CompanyTypeSerializer(serializers.ModelSerializer):
    """JSON serializer for company types

    Arguments:
        serializers
    """
    class Meta:
        model = CompanyType
        fields = ('id', 'label')