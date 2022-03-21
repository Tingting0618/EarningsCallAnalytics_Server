from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from rest_framework import routers
from earningscall_api.views import register_user, login_user, ProfileView,CompanyTypeView, CompanyView,AnalyticsView

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'companytypes', CompanyTypeView, 'companytype')
router.register(r'companies', CompanyView, 'company')
router.register(r'analyses', AnalyticsView, 'analysis')
router.register(r'profile', ProfileView, 'profile')


urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('register', register_user),
    path('login', login_user),
    path('api-auth', include('rest_framework.urls', namespace='rest_framework')),
]
