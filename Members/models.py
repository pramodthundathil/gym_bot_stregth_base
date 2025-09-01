from django.db import models


# Setting classess 

class Batch_DB(models.Model):
    Batch_Name = models.CharField(max_length=255,choices=(("Morning","Morning"),("Evening","Evening"),("Stoped","Stoped")))
    Batch_Status = models.BooleanField(default=True)
    Batch_Time = models.TimeField(auto_now_add=False)

    def __str__(self):
        return (str(self.Batch_Name) + " " + str(self.Batch_Time))


class TypeSubsription(models.Model):
    Type = models.CharField(max_length=255)
    def __str__(self):
        return self.Type



class Subscription_Period(models.Model):
    Period = models.PositiveIntegerField()
    Category = models.CharField(max_length=255, choices=(("Day","Day"),("Week","Week"),("Month","Month"),("Year","Year")))

    def __str__(self):
        return (str(self.Period) + " " +str(self.Category))
    

class MemberData(models.Model):
    First_Name = models.CharField(max_length=255)
    Last_Name = models.CharField(max_length=255, null= True,blank=True)
    Date_Of_Birth = models.DateField(auto_now_add=False,null= True,blank=True)
    Gender = models.CharField(max_length=255,choices=(("Male","Male"),("Female","Female"),("Other","Other")),default="Male")
    Mobile_Number = models.CharField(max_length=255)
    Discount = models.FloatField(null=True, blank= True)
    Special_Discount = models.BooleanField(default = False)
    Email = models.EmailField(null=True, blank=True)
    Address = models.TextField(max_length=200, null= True,blank=True )
    Medical_History = models.TextField(max_length=2000,null=True,blank=True)
    Registration_Date = models.DateField(auto_now_add=False)
    Photo = models.FileField(upload_to='member_photo', null= True,blank=True)
    Id_Upload = models.FileField(upload_to="member_id", null=True, blank=True)
    Date_Added = models.DateField(auto_now_add=True)
    Active_status = models.BooleanField(default=True)
    Access_status = models.BooleanField(default=False)
    Access_Token_Id = models.CharField(max_length=255,null=True,blank=True)

    

    def save(self, *args, **kwargs):
        if not self.Access_Token_Id:
            self.Access_Token_Id = str(random.randint(1000, 9999))
        super().save(*args, **kwargs)

    def update_active_status(self):
        """
        Check if the member has any unpaid subscriptions.
        If any subscription has Payment_Status=False, set Active_status=False.
        """
        has_unpaid_subscriptions = self.Member_subscription.filter(Payment_Status=False).exists()
        
        if has_unpaid_subscriptions:
            self.Active_status = False
        else:
            self.Active_status = True  # Optionally re-enable if all are paid
        
        self.save()

    def __str__(self):
        if self.Last_Name == None:
            last_name = " "
        else:
            last_name = self.Last_Name
        try:
            return str(self.First_Name) + " " + str(last_name)
        except:
            return str(self.First_Name) + " " + str(self.Mobile_Number)
        

class Subscription(models.Model):
    Member = models.ForeignKey(MemberData, on_delete=models.CASCADE,null=True, blank=True, related_name="Member_subscription")
    Type_Of_Subscription = models.ForeignKey(TypeSubsription,on_delete=models.SET_NULL,null=True,blank=True)
    Period_Of_Subscription = models.ForeignKey(Subscription_Period, on_delete=models.SET_NULL,null=True, blank=True)
    Amount = models.IntegerField()
    Subscribed_Date = models.DateField(auto_now_add=False)
    Subscription_End_Date = models.DateField(auto_now_add=False,null=True,blank=True)
    Batch = models.ForeignKey(Batch_DB, on_delete=models.SET_NULL,null=True, blank=True, related_name="batch_time")
    Batch_Status = models.BooleanField(default=True)
    Payment_Status = models.BooleanField(default=False)
    partial_payment = models.BooleanField(default=False)


    def __str__(self):
        return str(self.Type_Of_Subscription) + " " + str(self.Period_Of_Subscription)
    


from django.core.exceptions import ValidationError
import random

class Payment(models.Model):
    Member = models.ForeignKey(MemberData, on_delete=models.CASCADE)
    Subscription_ID = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name="Subscription_payment")
    Amount = models.IntegerField(null=True, blank=True)
    Mode_of_Payment = models.CharField(max_length=255, null=True, blank=True, choices=(("Cash", "Cash"), ("Bank Transfer", "Bank Transfer"), ("Card", "Card")))
    Payment_Date = models.DateField(auto_now_add=False, null=True, blank=True)
    Payment_Balance = models.FloatField(default=0)
    Payment_Status = models.BooleanField(default=False)
    Access_status = models.BooleanField(default=False)
    partial_payment = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # If Payment_Balance is greater than 0, force Payment_Status to False
        if self.Payment_Balance > 0:
            self.Payment_Status = False
        super().save(*args, **kwargs)

    def clean(self):
        # Validation to prevent Payment_Status from being True when Payment_Balance > 0
        if self.Payment_Balance > 0 and self.Payment_Status:
            raise ValidationError({
                'Payment_Status': 'Payment status cannot be True when payment balance is greater than 0.'
            })
        super().clean()

   

class BalancePayment(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="balance_payment")
    Amount = models.FloatField()
    Payment_Date = models.DateField(auto_now_add=True) 

class AccessToGate(models.Model):
    Member = models.ForeignKey(MemberData, on_delete=models.CASCADE)
    Subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    Validity_Date = models.DateField(auto_now_add=False)
    Status = models.BooleanField(default=False)
    Payment_status = models.BooleanField(default=False)

class Discounts(models.Model):
    Discount_Percentage = models.FloatField()
    Till_Date = models.DateField()



from django.db import models
from django.contrib.auth.models import User
import uuid
from django.urls import reverse

class TermsAndConditions(models.Model):
    title = models.CharField(max_length=200, default="Terms and Conditions")
    content = models.TextField()
    version = models.CharField(max_length=10, default="1.0")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Terms and Conditions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - v{self.version}"

class GymMembership(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    GOAL_CHOICES = [
        ('weight_loss', 'Weight Loss'),
        ('muscle_gain', 'Muscle Gain'),
        ('general_fitness', 'General Fitness'),
        ('strength', 'Strength'),
        ('endurance', 'Endurance'),
        ('rehab', 'Rehab'),
        ('other', 'Other'),
    ]
    
    TRAINING_CHOICES = [
        ('personal_training', 'Personal Training'),
        ('group_training', 'Group Training'),
        ('crossfit', 'CrossFit'),
        ('yoga', 'Yoga'),
        ('cardio', 'Cardio'),
        ('weight_training', 'Weight Training'),
        ('other', 'Other'),
    ]
    
    FREQUENCY_CHOICES = [
        ('1-2_days', '1-2 days'),
        ('3-4_days', '3-4 days'),
        ('5-6_days', '5-6 days'),
        ('daily', 'Daily'),
    ]
    
    TIME_CHOICES = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
    ]
    
    OCCUPATION_CHOICES = [
        ('student', 'Student'),
        ('working', 'Working'),
        ('business', 'Business'),
        ('other', 'Other'),
    ]
    
    ACTIVITY_CHOICES = [
        ('sedentary', 'Sedentary'),
        ('moderate', 'Moderate'),
        ('active', 'Active'),
    ]
    
    DIET_CHOICES = [
        ('vegetarian', 'Vegetarian'),
        ('non_veg', 'Non-Vegetarian'),
        ('vegan', 'Vegan'),
        ('eggetarian', 'Eggetarian'),
    ]
    
    PLAN_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('half_yearly', 'Half-Yearly'),
        ('yearly', 'Yearly'),
    ]
    
    PAYMENT_CHOICES = [
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    # Unique identifier
    enrollment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    unique_link = models.CharField(max_length=100, unique=True, blank=True)
    
    # Personal Information
    full_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    address = models.TextField()
    city_pincode = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)
    whatsapp_number = models.CharField(max_length=15)
    email_id = models.EmailField()
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=15)
    
    # Health & Medical History
    height_cm = models.PositiveIntegerField()
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2)
    has_medical_condition = models.BooleanField(default=False)
    medical_condition_details = models.TextField(blank=True, null=True)
    taking_medication = models.BooleanField(default=False)
    medication_details = models.TextField(blank=True, null=True)
    had_surgery_injury = models.BooleanField(default=False)
    surgery_injury_details = models.TextField(blank=True, null=True)
    smokes_drinks_alcohol = models.BooleanField(default=False)
    
    # Family History
    family_heart_disease = models.BooleanField(default=False)
    family_diabetes = models.BooleanField(default=False)
    family_hypertension = models.BooleanField(default=False)
    family_history_none = models.BooleanField(default=False)
    
    # Fitness Goals
    primary_goal = models.CharField(max_length=20, choices=GOAL_CHOICES)
    primary_goal_other = models.CharField(max_length=100, blank=True, null=True)
    preferred_training = models.CharField(max_length=20, choices=TRAINING_CHOICES)
    preferred_training_other = models.CharField(max_length=100, blank=True, null=True)
    training_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    preferred_workout_time = models.CharField(max_length=20, choices=TIME_CHOICES)
    
    # Lifestyle & Habits
    occupation = models.CharField(max_length=20, choices=OCCUPATION_CHOICES)
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)
    sleep_hours = models.PositiveIntegerField()
    diet_type = models.CharField(max_length=20, choices=DIET_CHOICES)
    
    # Membership Selection
    plan_chosen = models.CharField(max_length=20, choices=PLAN_CHOICES)
    personal_trainer_addon = models.BooleanField(default=False)
    nutrition_plan_addon = models.BooleanField(default=False)
    physiotherapy_addon = models.BooleanField(default=False)
    
    # Payment & Agreement
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    payment_proof = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)
    
    # Digital Signature
    digital_signature = models.TextField(blank=True, null=True)  # Base64 encoded signature
    signature_timestamp = models.DateTimeField(blank=True, null=True)
    
    # Terms Agreement
    terms_accepted = models.BooleanField(default=False)
    terms_version = models.ForeignKey(TermsAndConditions, on_delete=models.CASCADE, null=True, blank = True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)


    member = models.ForeignKey(MemberData, on_delete=models.CASCADE, null=True, blank=True, related_name="enrolment_form")
    is_member = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Gym Membership"
        verbose_name_plural = "Gym Memberships"
    
    def save(self, *args, **kwargs):
        if not self.unique_link:
            self.unique_link = str(self.enrollment_id)[:8]
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.full_name} - {self.enrollment_id}"
    
    def get_absolute_url(self):
        return reverse('membership_detail', kwargs={'unique_link': self.unique_link})
    
    @property
    def bmi(self):
        height_m = self.height_cm / 100
        return round(float(self.weight_kg) / (height_m * height_m), 2)
    
    @property
    def bmi_category(self):
        bmi = self.bmi
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Normal weight"
        elif bmi < 30:
            return "Overweight"
        else:
            return "Obese"
        
    def convert_to_member(self):
        """
        Create a MemberData instance from GymMembership data
        and mark this GymMembership as linked (is_member=True).
        """
        if not self.is_member:
            # Create the MemberData record
            member = MemberData.objects.create(
                First_Name=self.full_name.split(" ")[0],
                Last_Name=" ".join(self.full_name.split(" ")[1:]) if len(self.full_name.split(" ")) > 1 else "",
                Date_Of_Birth=self.date_of_birth,
                Gender=self.gender.capitalize(),  # Ensure it matches MemberData choices
                Mobile_Number=self.mobile_number,
                Email=self.email_id,
                Address=self.address,
                Registration_Date=self.created_at.date(),  # or today
                Medical_History=self.medical_condition_details or self.medication_details or self.surgery_injury_details,
                Active_status=True
            )

            # Link to GymMembership
            self.member = member
            self.is_member = True
            self.save()

            return member
        return self.member





# models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class HealthHistory(models.Model):
    # Link to existing member
    member = models.OneToOneField('MemberData', on_delete=models.CASCADE, related_name='health_history')
    
    # MANDATORY FIELDS
    # Emergency Contact Information (Mandatory)
    emergency_contact_name = models.CharField(max_length=255)
    emergency_contact_relationship = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=20)
    emergency_contact_address = models.TextField(max_length=500, null=True, blank=True)
    
    # Current Physical Information (Mandatory)
    current_weight = models.FloatField(validators=[MinValueValidator(0)])
    current_height = models.FloatField(validators=[MinValueValidator(0)])  # in cm
    
    # Fitness Goals (Mandatory)
    FITNESS_GOAL_CHOICES = [
        ('weight_loss', 'Weight Loss'),
        ('weight_gain', 'Weight Gain'),
        ('muscle_building', 'Muscle Building'),
        ('cardiovascular', 'Cardiovascular Fitness'),
        ('strength', 'Strength Training'),
        ('flexibility', 'Flexibility & Mobility'),
        ('sports_specific', 'Sports Specific Training'),
        ('general_fitness', 'General Fitness'),
        ('rehabilitation', 'Rehabilitation'),
        ('other', 'Other'),
    ]
    fitness_goal = models.CharField(max_length=50, choices=FITNESS_GOAL_CHOICES)
    fitness_goal_details = models.TextField(max_length=500, null=True, blank=True)
    
    # PT Session Availability (Mandatory)
    AVAILABILITY_CHOICES = [
        ('morning', 'Morning (6 AM - 12 PM)'),
        ('afternoon', 'Afternoon (12 PM - 6 PM)'),
        ('evening', 'Evening (6 PM - 10 PM)'),
        ('flexible', 'Flexible'),
    ]
    pt_availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES)
    preferred_days = models.CharField(max_length=200, help_text="e.g., Monday, Wednesday, Friday")
    
    # OPTIONAL FIELDS
    # Physician Information
    physician_name = models.CharField(max_length=255, null=True, blank=True)
    physician_phone = models.CharField(max_length=20, null=True, blank=True)
    
    # Current Health Care
    under_medical_care = models.BooleanField(default=False)
    medical_care_reason = models.TextField(max_length=500, null=True, blank=True)
    
    # Medications
    taking_medications = models.BooleanField(default=False)
    
    # Allergies
    allergies = models.TextField(max_length=1000, null=True, blank=True)
    
    # Basic Health Questions
    high_blood_pressure = models.BooleanField(default=False)
    bone_joint_problems = models.BooleanField(default=False)
    over_65 = models.BooleanField(default=False)
    unaccustomed_exercise = models.BooleanField(default=False)
    
    # Medical Conditions - Family History and Personal
    family_asthma = models.BooleanField(default=False)
    personal_asthma = models.TextField(max_length=500, null=True, blank=True)
    
    family_respiratory = models.BooleanField(default=False)
    personal_respiratory = models.TextField(max_length=500, null=True, blank=True)
    
    family_diabetes = models.BooleanField(default=False)
    personal_diabetes_type1 = models.TextField(max_length=200, null=True, blank=True)
    personal_diabetes_type2 = models.TextField(max_length=200, null=True, blank=True)
    diabetes_duration = models.CharField(max_length=100, null=True, blank=True)
    
    family_epilepsy = models.BooleanField(default=False)
    personal_epilepsy_petite = models.TextField(max_length=200, null=True, blank=True)
    personal_epilepsy_grand = models.TextField(max_length=200, null=True, blank=True)
    personal_epilepsy_other = models.TextField(max_length=200, null=True, blank=True)
    
    family_osteoporosis = models.BooleanField(default=False)
    personal_osteoporosis = models.TextField(max_length=500, null=True, blank=True)
    
    # Lifestyle Factors
    STRESS_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    occupational_stress = models.CharField(max_length=10, choices=STRESS_LEVEL_CHOICES, null=True, blank=True)
    
    ENERGY_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    energy_level = models.CharField(max_length=10, choices=ENERGY_LEVEL_CHOICES, null=True, blank=True)
    
    caffeine_daily = models.IntegerField(null=True, blank=True)
    alcohol_weekly = models.IntegerField(null=True, blank=True)
    colds_per_year = models.IntegerField(null=True, blank=True)
    
    anemia = models.TextField(max_length=300, null=True, blank=True)
    gastrointestinal_disorder = models.TextField(max_length=500, null=True, blank=True)
    hypoglycemia = models.TextField(max_length=300, null=True, blank=True)
    thyroid_disorder = models.TextField(max_length=300, null=True, blank=True)
    prenatal_postnatal = models.TextField(max_length=300, null=True, blank=True)
    
    # Cardiovascular
    high_bp_details = models.TextField(max_length=300, null=True, blank=True)
    hypertension_details = models.TextField(max_length=300, null=True, blank=True)
    high_cholesterol = models.TextField(max_length=500, null=True, blank=True)
    hyperlipidemia = models.TextField(max_length=500, null=True, blank=True)
    heart_disease = models.TextField(max_length=500, null=True, blank=True)
    heart_attack = models.TextField(max_length=300, null=True, blank=True)
    stroke = models.TextField(max_length=300, null=True, blank=True)
    angina = models.TextField(max_length=300, null=True, blank=True)
    gout = models.TextField(max_length=300, null=True, blank=True)
    
    # Exercise Restrictions
    exercise_restrictions = models.BooleanField(default=False)
    exercise_restrictions_details = models.TextField(max_length=1000, null=True, blank=True)
    
    chest_pain_exercise = models.BooleanField(default=False)
    chest_pain_details = models.TextField(max_length=500, null=True, blank=True)
    
    # Smoking
    SMOKING_CHOICES = [
        ('non_user', 'Non-user or former user'),
        ('cigar_pipe', 'Cigar and/or pipe'),
        ('1_15', '15 or less cigarettes per day'),
        ('16_25', '16 to 25 cigarettes per day'),
        ('26_35', '26 to 35 cigarettes per day'),
        ('35_plus', 'More than 35 cigarettes per day'),
    ]
    smoking_status = models.CharField(max_length=20, choices=SMOKING_CHOICES, null=True, blank=True)
    smoking_quit_date = models.DateField(null=True, blank=True)
    
    # Musculoskeletal Information
    head_neck_issues = models.TextField(max_length=500, null=True, blank=True)
    upper_back_issues = models.TextField(max_length=500, null=True, blank=True)
    shoulder_clavicle_issues = models.TextField(max_length=500, null=True, blank=True)
    arm_elbow_issues = models.TextField(max_length=500, null=True, blank=True)
    wrist_hand_issues = models.TextField(max_length=500, null=True, blank=True)
    lower_back_issues = models.TextField(max_length=500, null=True, blank=True)
    hip_pelvis_issues = models.TextField(max_length=500, null=True, blank=True)
    thigh_knee_issues = models.TextField(max_length=500, null=True, blank=True)
    arthritis_details = models.TextField(max_length=500, null=True, blank=True)
    hernia_details = models.TextField(max_length=300, null=True, blank=True)
    surgeries_details = models.TextField(max_length=1000, null=True, blank=True)
    other_musculoskeletal = models.TextField(max_length=500, null=True, blank=True)
    
    # Nutritional Information
    on_diet_plan = models.BooleanField(default=False)
    diet_plan_details = models.TextField(max_length=500, null=True, blank=True)
    
    taking_supplements = models.BooleanField(default=False)
    supplements_list = models.TextField(max_length=500, null=True, blank=True)
    
    weight_fluctuations = models.BooleanField(default=False)
    recent_weight_change = models.BooleanField(default=False)
    weight_change_amount = models.CharField(max_length=100, null=True, blank=True)
    weight_change_duration = models.CharField(max_length=100, null=True, blank=True)
    
    caffeine_beverages_daily = models.IntegerField(null=True, blank=True)
    nutritional_habits_description = models.TextField(max_length=1000, null=True, blank=True)
    food_allergies_issues = models.TextField(max_length=500, null=True, blank=True)
    
    # Work and Exercise Habits
    WORK_EXERCISE_CHOICES = [
        ('intense_both', 'Intense occupational and recreational exertion'),
        ('moderate_both', 'Moderate occupational and recreational exertion'),
        ('sedentary_intense', 'Sedentary occupational and intense recreational exertion'),
        ('sedentary_moderate', 'Sedentary occupational and moderate recreational exertion'),
        ('sedentary_light', 'Sedentary occupational and light recreational exertion'),
        ('no_exertion', 'Complete lack of all exertion'),
    ]
    work_exercise_habits = models.CharField(max_length=30, choices=WORK_EXERCISE_CHOICES, null=True, blank=True)
    
    STRESS_LEVEL_CHOICES = [
        ('minimal', 'Minimal'),
        ('moderate', 'Moderate'),
        ('average', 'Average'),
        ('extremely', 'Extremely'),
    ]
    work_stress_level = models.CharField(max_length=15, choices=STRESS_LEVEL_CHOICES, null=True, blank=True)
    home_stress_level = models.CharField(max_length=15, choices=STRESS_LEVEL_CHOICES, null=True, blank=True)
    
    works_over_40_hours = models.BooleanField(default=False)
    additional_comments = models.TextField(max_length=2000, null=True, blank=True)
    
    # Form completion
    date_completed = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Health History"
        verbose_name_plural = "Health Histories"
    
    def __str__(self):
        return f"Health History - {self.member.First_Name} {self.member.Last_Name or ''}"


class Medication(models.Model):
    health_history = models.ForeignKey(HealthHistory, on_delete=models.CASCADE, related_name='medications')
    medication_type = models.CharField(max_length=255)
    dosage_frequency = models.CharField(max_length=255)
    reason_for_taking = models.CharField(max_length=500)
    
    def __str__(self):
        return f"{self.medication_type} - {self.health_history.member.First_Name}"