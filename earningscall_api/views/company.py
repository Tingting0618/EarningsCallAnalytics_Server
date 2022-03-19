"""View module for handling requests about company types"""
from django.http import HttpResponse, HttpResponseServerError
from django.core.exceptions import ValidationError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
from earningscall_api.models import Company, Appuser, CompanyType
import json
from nltk import FreqDist
from nltk.tokenize import word_tokenize
from nltk.text import Text
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from django_pandas.io import read_frame
from nltk.corpus import stopwords


class CompanyView(ViewSet):
    """Company types"""

    def create(self, request):
        """Handle POST operations

        Returns:
            Response -- JSON serialized game instance
        """
        # # Uses the token passed in the `Authorization` header
        # appuser = Appuser.objects.get(user=request.auth.user)

        # Create a new Python instance of the Company class
        # and set its properties from what was sent in the
        # body of the request from the client.
        company = Company()
        company.label = request.data["label"]
        company.value = request.data["value"]
        company.year = request.data["year"]
        company.quarter = request.data["quarter"]
        company.transcript = request.data["transcript"]
        # Use the Django ORM to get the record from the database
        # whose `id` is what the client passed as the
        # `gameTypeId` in the body of the request.
        company_type = CompanyType.objects.get(pk=request.data["companyTypeId"])
        company.company_type = company_type

        # Try to save the new game to the database, then
        # serialize the game instance as JSON, and send the
        # JSON as a response to the client request
        try:
            company.save()
            serializer = CompanySerializer(company, context={'request': request})
            return Response(serializer.data)

        # If anything went wrong, catch the exception and
        # send a response with a 400 status code to tell the
        # client that something was wrong with its request data
        except ValidationError as ex:
            return Response({"reason": ex.message}, status=status.HTTP_400_BAD_REQUEST)
    def destroy(self, request, pk=None):
        """Handle DELETE requests for a single game
        Returns:
            Response -- 200, 404, or 500 status code
        """
        try:
            company =Company.objects.get(pk=pk)
            company.delete()

            return Response({}, status=status.HTTP_204_NO_CONTENT)

        except Company.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

        except Exception as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)        
    def retrieve(self, request, pk=None):
        """Handle GET requests for single Company

        Returns:
            Response -- JSON serialized Company
        """
        try:
            company = Company.objects.get(pk=pk)
            serializer = CompanyTranscriptSerializer(
                company, context={'request': request})
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
        searched_quar = self.request.query_params.get('quarter', None)
        searched_keywords = self.request.query_params.get('keywords', None)

        if searched_co and start_year and end_year:
            searched_co = searched_co.split(',')
            start_year = int(start_year)
            end_year = int(end_year)
            companies = companies.filter(value__in=searched_co)
            companies = companies.filter(year__gte=start_year)
            companies = companies.filter(year__lte=end_year)
            if searched_quar:
                searched_quar = searched_quar.split(',')
                companies = companies.filter(quarter__in=searched_quar)
            else:
                None
            df = read_frame(companies, fieldnames=["value", "label", "year", "quarter",
                                                   "transcript"])

            transcript = ""
            for (idx, row) in df.iterrows():
                transcript = transcript+" " + row.loc['transcript']
            word_tokens = word_tokenize(transcript)
            #ps = PorterStemmer()

############# Top Words Analysis ################
            stemed_transcript = []
            for w in word_tokens:
                # stemed_transcript.append(ps.stem(w).lower())
                stemed_transcript.append(w.lower())

            new_stopwords = [",", ".", "to", "on", "daily"]
            stop_words = set(stopwords.words('english'))
            stop_words.update(new_stopwords)
            
            filtered_transcript = []
            for w in stemed_transcript:
                if w not in stop_words:
                    filtered_transcript.append(w)

            fdist = FreqDist(filtered_transcript)
            fd = fdist.most_common(10)

            x_val = [x[0] for x in fd]
            y_val = [x[1] for x in fd]

            top_words_json = [{'words': x_val, 'freq': y_val}
                              for x_val, y_val in zip(x_val, y_val)]

############# The sentiment ################
            # word =  'hello'
            textListNLTK = Text(word_tokens)
            sia = SentimentIntensityAnalyzer()
            scores = []
            sentences = []
            for i in range(0,10):
                try:
                    sentence1 = ' '.join(word for word in textListNLTK.concordance_list(
                        searched_keywords, width=50)[i][0])
                    sentence2 = ' '.join(word for word in textListNLTK.concordance_list(
                        searched_keywords, width=50)[i][2])
                    sentence = sentence1+" "+searched_keywords+" "+sentence2
                    score = sia.polarity_scores(sentence)['compound']
                    scores.append(score)
                    sentences.append(sentence)
                except:
                    break
            sentiment_json = [{'sentences': sentences, 'scores': scores}
                              for sentences, scores in zip(sentences, scores)]

            all_charts = json.dumps(
                {'topWords': top_words_json,
                 'sentimentWords': sentiment_json})
            return HttpResponse(all_charts,
                                status=200, content_type='application/json')

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
        fields = ('id', 'label', 'value')


class CompanyTranscriptSerializer(serializers.ModelSerializer):
    """JSON serializer for company types

    Arguments:
        serializers
    """
    class Meta:
        model = Company
        fields = ('id', 'label', 'value', 'company_type',
                  'year', 'quarter', 'transcript', 'followers')
