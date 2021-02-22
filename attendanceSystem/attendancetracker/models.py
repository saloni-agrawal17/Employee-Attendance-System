from django.db import models
from django.contrib.auth.models import User


class AttendanceTracker(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.TimeField()
    logout_time = models.TimeField(null=True)
    current_date = models.DateField()
    working_hours_per_day = models.TimeField(null=True)

    #def __str__(self):
     #   return self.user.username

