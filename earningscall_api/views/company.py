"""View module for handling requests about company types"""
from django.http import HttpResponse, HttpResponseServerError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.core.exceptions import ValidationError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers, status
from earningscall_api.models import Company, Appuser, CompanyType
from rest_framework.decorators import action
import json
from nltk import FreqDist
from nltk.tokenize import word_tokenize
from nltk.text import Text
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from django_pandas.io import read_frame
from nltk.corpus import stopwords
from collections import Counter


class AnalyticsView(ViewSet):
    """Dashboard"""

    def create(self, request):
        """Handle POST operations

        Returns:
            Response -- JSON serialized game instance
        """
        # import pdb; pdb.set_trace()
        company = Company()
        company.label = request.data["label"]
        company.value = request.data["value"]
        company.year = request.data["year"]
        company.quarter = request.data["quarter"]
        company.transcript = request.data["transcript"]
        company_type = CompanyType.objects.get(
            pk=request.data["companyTypeId"])
        company.company_type = company_type
        try:
            company.save()
            serializer = CompanySerializer(
                company, context={'request': request})
            return Response(serializer.data)
        except ValidationError as ex:
            return Response({"reason": ex.message}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post', 'delete'], detail=True, permission_classes=[IsAuthenticated])
    def follow(self, request, pk=None):
        """Managing gamers signing up for events"""
        # Django uses the `Authorization` header to determine
        # which user is making the request to sign up
        appuser = Appuser.objects.get(user=request.auth.user)

        try:
            # Handle the case if the client specifies a game
            # that doesn't exist
            company = Company.objects.get(pk=pk)
        except Company.DoesNotExist:
            return Response(
                {'message': 'Company does not exist.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # A gamer wants to sign up for an event
        if request.method == "POST":
            try:
                # Using the attendees field on the event makes it simple to add a gamer to the event
                # .add(gamer) will insert into the join table a new row the gamer_id and the event_id
                company.followers.add(appuser)
                return Response({}, status=status.HTTP_201_CREATED)
            except Exception as ex:
                return Response({'message': ex.args[0]})

        # User wants to leave a previously joined event
        elif request.method == "DELETE":
            try:
                # The many to many relationship has a .remove method that removes the gamer from the attendees list
                # The method deletes the row in the join table that has the gamer_id and event_id
                company.followers.remove(appuser)
                return Response(None, status=status.HTTP_204_NO_CONTENT)
            except Exception as ex:
                return Response({'message': ex.args[0]})

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
            
            df['full_date'] = df['year'].astype(str)+ " Q"+df['quarter'].astype(str)
            date_list =[]
            for i in range(start_year,end_year+1):
                for j in range(1,5):
                    Q = str(i) + ' Q'+str(j)
                    date_list.append(Q)
            
            companies_count =[]
            transcripts=""
            for i in df['label'].unique():
                counts = []
                df_t =df[df['label']==i]
                for j in date_list:
                    df_d = df_t[df_t['full_date']==j]
                    transcript = str(df_d['transcript']).replace("Series([], Name: transcript, dtype: object)"," ")
                    word_token = word_tokenize(transcript)
                    wordcounts_lower = Counter(i.lower() for i in word_token)
                    count = Counter(wordcounts_lower)
                    key_word_count = count[searched_keywords.lower()]
                    counts.append(key_word_count)
                    #counts.append(transcript)
                    transcripts = transcripts+" " + transcript  
                            
                      
                company_count ={'label':i,'data':counts} 
                companies_count.append(company_count)               
            
            trends_json={"labels":date_list,
                         "datasets":companies_count}
############# Top Words Analysis ################
            word_tokens = word_tokenize(transcripts)
            stemed_transcript = [] 
            for w in word_tokens:
                # stemed_transcript.append(ps.stem(w).lower())
                stemed_transcript.append(w.lower())

            new_stopwords = [",", ".", "to", "on",
                             "daily", '%', "'s", "'re", "'"]
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
            for i in range(0, 10):
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
                 'sentimentWords': sentiment_json,
                 'trends': trends_json
                 })
            return HttpResponse(all_charts,
                                status=200, content_type='application/json')

        else:
            serializer = CompanySerializer(
                companies, many=True, context={'request': request})
            return Response(serializer.data)


class CompanyView(ViewSet):

    """Company types"""
    permission_classes = [IsAdminUser]

    def update(self, request, pk=None):
        """Handle POST operations

        Returns:
            Response -- JSON serialized game instance
        """
        company = Company.objects.get(pk=pk)
        company.label = request.data["label"]
        company.value = request.data["value"]
        company.year = request.data["year"]
        company.quarter = request.data["quarter"]
        company.transcript = request.data["transcript"]
        company.company_type = CompanyType.objects.get(
            pk=request.data["companyTypeId"])

        company.save()
        return Response({}, status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):
        """Handle DELETE requests for a single game
        Returns:
            Response -- 200, 404, or 500 status code
        """
        try:
            company = Company.objects.get(pk=pk)
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


class CompanySerializer(serializers.ModelSerializer):
    """JSON serializer for company types

    Arguments:
        serializers
    """
    class Meta:
        model = Company
        fields = ('id', 'label', 'value', 'company_type')


class CompanyTranscriptSerializer(serializers.ModelSerializer):
    """JSON serializer for company types

    Arguments:
        serializers
    """
    class Meta:
        model = Company
        fields = ('id', 'label', 'value', 'company_type',
                  'year', 'quarter', 'transcript', 'followers')
