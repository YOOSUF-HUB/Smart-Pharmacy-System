from django.db import models

class Student(models.Model):
    sno = models.IntegerField()
    sname = models.CharField(max_length = 50)
    sage = models.IntegerField(default=0)
    sclass = models.IntegerField()
    saddress = models.CharField(max_length = 100)
    sdob = models.DateField(null=True, blank=True)  # Added field for date of birth
    
    def __str__(self):
        return self.sname

