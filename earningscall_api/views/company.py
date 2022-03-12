"""View module for handling requests about company types"""
from django.forms import ValidationError
from django.http import HttpResponse, HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
from earningscall_api.models import Company
import json

"""DS modules"""
import nltk
from nltk.corpus import stopwords
from django_pandas.io import read_frame
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import PorterStemmer
from nltk import FreqDist


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
            
            df = read_frame(companies, fieldnames = [ "value", "label", "year", "quarter",
            "transcript"])            
            transcript = ""
            for (idx, row)  in df.iterrows(): 
                transcript = transcript+" "+ row.loc['transcript']
            word_tokens = word_tokenize(transcript)
            #ps = PorterStemmer()

            stemed_transcript = []
            for w in word_tokens:
                #stemed_transcript.append(ps.stem(w).lower())
                stemed_transcript.append(w.lower())

            stop_words = set(stopwords.words('english'))
            filtered_transcript = []
            for w in stemed_transcript:
                if w not in stop_words:
                    filtered_transcript.append(w)
            
            fdist = FreqDist(filtered_transcript)
            fd = fdist.most_common(10)
            
            x_val = [x[0] for x in fd]
            y_val = [x[1] for x in fd]

            chart1_json = json.dumps(
                [{'words': x_val, 'freq': y_val} for x_val, y_val in zip(x_val,y_val)])
            
            return HttpResponse(chart1_json,status=200,content_type='application/json')
            # serializer = CompanyTranscriptSerializer(
            #     companies, many=True, context={'request': request})
            # return Response(serializer.data)
        
        else: 
            serializer = CompanySerializer(
            companies, many=True, context={'request': request})
            return Response(serializer.data)
            #return Response({"reason":ValidationError.messages},status=status.HTTP_400_BAD_REQUEST)

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
