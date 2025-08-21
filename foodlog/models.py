# models.py - Add these models to your existing models.py file

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from Members.models import MemberData

class DailyLog(models.Model):
    member = models.ForeignKey(MemberData, on_delete=models.CASCADE, related_name='daily_logs')
    date = models.DateField(default=timezone.now)
    weight = models.FloatField(help_text="Weight in kg", null=True, blank=True)
    notes = models.TextField(max_length=500, blank=True, null=True, help_text="General notes for the day")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('member', 'date')
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.member.First_Name} - {self.date}"

class MealEntry(models.Model):
    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack_morning', 'Morning Snack'),
        ('snack_afternoon', 'Afternoon Snack'),
        ('snack_evening', 'Evening Snack'),
        ('other', 'Other'),
    ]
    
    daily_log = models.ForeignKey(DailyLog, on_delete=models.CASCADE, related_name='meals')
    meal_type = models.CharField(max_length=20, choices=MEAL_CHOICES)
    meal_description = models.TextField(max_length=1000, help_text="Description of meal consumed")
    food_image = models.FileField(upload_to='meal_images/', null=True, blank=True)
    custom_meal_name = models.CharField(max_length=100, blank=True, null=True, help_text="If 'Other' is selected")
    calories_estimate = models.IntegerField(null=True, blank=True, help_text="Estimated calories (optional)")
    time_consumed = models.TimeField(null=True, blank=True, help_text="Time when meal was consumed")
    admin_comment = models.TextField(max_length=1000, blank=True, null=True, help_text="Admin feedback")
    commented_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    comment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['time_consumed', 'created_at']
    
    def get_meal_display_name(self):
        if self.meal_type == 'other' and self.custom_meal_name:
            return self.custom_meal_name
        return self.get_meal_type_display()
    
    def __str__(self):
        return f"{self.daily_log.member.First_Name} - {self.date} - {self.get_meal_display_name()}"

class WeightGoal(models.Model):
    member = models.ForeignKey(MemberData, on_delete=models.CASCADE, related_name='weight_goals')
    target_weight = models.FloatField(help_text="Target weight in kg")
    target_date = models.DateField()
    created_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.member.First_Name} - Target: {self.target_weight}kg by {self.target_date}"
