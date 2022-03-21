"""View module for handling requests about park areas"""
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from earningscall_api.models import Company,Appuser
from django.contrib.auth import get_user_model
User = get_user_model()

class ProfileView(ViewSet):
    """Gamer can see profile information"""

    def list(self, request):
        """Handle GET requests to profile resource
        Returns:
            Response -- JSON representation of user info and events
        """
        appuser = Appuser.objects.get(user=request.auth.user)

        companies = Company.objects.filter(followers=appuser)

        companies = CompanySerializer(
            companies, many=True, context={'request': request})
        appuser = AppUserSerializer(
            appuser, many=False, context={'request': request})

        # Manually construct the JSON structure you want in the response
        profile = {}
        profile["appuser"] = appuser.data
        profile["companies"] = companies.data

        return Response(profile)

class UserSerializer(serializers.ModelSerializer):
    """JSON serializer for gamer's related Django user"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username','is_staff')


class AppUserSerializer(serializers.ModelSerializer):
    """JSON serializer for gamers"""
    user = UserSerializer(many=False)

    class Meta:
        model = Appuser
        fields = ('user', 'bio')


class CompanySerializer(serializers.ModelSerializer):
    """JSON serializer for games"""
    class Meta:
        model = Company
        fields = ('value','label','followers')
