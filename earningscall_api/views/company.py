"""View module for handling requests about company types"""
from django.http import HttpResponse, HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from earningscall_api.models import Company
import json
from nltk import FreqDist
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.text import Text
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from django_pandas.io import read_frame
from nltk.corpus import stopwords


class CompanyView(ViewSet):
    """Company types"""

    def retrieve(self, request, pk=None):
        """Handle GET requests for single Company

        Returns:
            Response -- JSON serialized Company
        """
        try:
            company = Company.objects.get(pk=pk)
            serializer = CompanySerializer(
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

            stop_words = set(stopwords.words('english'))
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
