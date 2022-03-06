from django.db import models
from earningscall_api.models.company_type import CompanyType
from earningscall_api.models.appuser import Appuser
class Company(models.Model):
    """
    Company
    """
    label = models.CharField(max_length=50)
    value = models.CharField(max_length=50)
    company_type = models.ForeignKey(CompanyType, on_delete=models.SET_NULL, null=True)
    year = models.IntegerField(null=True)
    quarter = models.IntegerField(null=True)
    transcript = models.TextField(null=True)
    followers = models.ManyToManyField(Appuser,related_name='following')