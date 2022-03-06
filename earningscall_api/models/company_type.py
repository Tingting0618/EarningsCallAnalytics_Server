from django.db import models

class CompanyType(models.Model):
    """
    Company Types
    """
    label = models.CharField(max_length=50)