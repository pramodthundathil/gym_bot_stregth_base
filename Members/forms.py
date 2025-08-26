from django.forms import ModelForm, TextInput, Textarea, FileInput, Select
from .models import MemberData, Subscription, Batch_DB, Subscription_Period, TypeSubsription, Payment
from datetime import datetime

date =  str(datetime.now()).split(" ")[0]


class MemberAddForm(ModelForm):
    class Meta:
        model = MemberData
        fields = [
            "First_Name",
            "Last_Name",
            "Date_Of_Birth",
            "Gender",
            "Mobile_Number",
            "Email",
            "Registration_Date",
            "Access_Token_Id",
            "Photo",
            "Id_Upload",
            "Address",
            "Medical_History",
        ]

        widgets = {
            "First_Name":TextInput(attrs={"class":"form-control"}),
            "Last_Name":TextInput(attrs={"class":"form-control"}),
            "Date_Of_Birth":TextInput(attrs={"class":"form-control","type":"date","max":date}),
            "Gender":Select(attrs={"class":"form-control"}),
            # "Date_Of_Birth":TextInput(attrs={"class":"form-control","type":"date","min":date}),
            "Mobile_Number":TextInput(attrs={"class":"form-control","type":"number"}),
            "Email":TextInput(attrs={"class":"form-control","type":"email"}),
            "Registration_Date":TextInput(attrs={"class":"form-control","type":"date"}),
            # "Address":TextInput(attrs={"class":"form-control",'style': 'height: 3em !importent;'}),
            # "Medical_History":TextInput(attrs={"class":"form-control"}),
            "Photo":FileInput(attrs={"class":"form-control",'accept': 'image/*', 'capture':'camera', "id":"profilePic"}),
            "Id_Upload":FileInput(attrs={"class":"form-control",'accept': 'image/*', 'capture':'camera'}),
            "Access_Token_Id":TextInput(attrs={"class":"form-control"})

        }

class SubscriptionAddForm(ModelForm):
    class Meta:
        model = Subscription
        fields = [
            "Type_Of_Subscription",
            "Period_Of_Subscription",
            "Amount",
            "Subscribed_Date",
            # "Subscription_End_Date",
            "Batch",
        ]

        widgets = {
            "Type_Of_Subscription":Select(attrs={"class":"form-control","required":"required"}),
            "Period_Of_Subscription":Select(attrs={"class":"form-control","required":"required"}),
            "Amount":TextInput(attrs={"class":"form-control","type":"number"}),
            "Subscribed_Date":TextInput(attrs={"class":"form-control","type":"date"}),
            # "Subscription_End_Date":TextInput(attrs={"class":"form-control","type":"date","min":date}),
            "Batch":Select(attrs={"class":"form-control","required":"required"}),

        }

class BatchForm(ModelForm):
    class Meta:
        model = Batch_DB
        fields = ["Batch_Name","Batch_Time"]

        widgets = {
            "Batch_Name":Select(attrs={"class":"form-control"}),
            "Batch_Time":TextInput(attrs={"class":"form-control",'type':"time"}),
        }

class Subscription_PeriodForm(ModelForm):
    class Meta:
        model = Subscription_Period
        fields = ["Period","Category"]

        widgets = {
            "Period":TextInput(attrs={"class":"form-control","type":"number"}),
            "Category":Select(attrs={"class":"form-control"}),
        }

class TypeSubsriptionForm(ModelForm):
    class Meta:
        model = TypeSubsription
        fields = ["Type"]
        widgets = {
           
            "Type":TextInput(attrs={"class":"form-control"}),

        }

class PaymentForm(ModelForm):
    class Meta:
        model = Payment
        fields = ["Member", "Payment_Date","Mode_of_Payment"]

        widgets = {

            "Member":Select(attrs={"class":"form-control"}),
            "Amount":TextInput(attrs={"class":"form-control","type":"number"}),
            "Payment_Date":TextInput(attrs={"class":"form-control","type":"date"}),
            "Mode_of_Payment":Select(attrs={"class":"form-control"})
        }



from django import forms
from .models import MemberData

class MemberBulkUploadForm(forms.Form):
    excel_file = forms.FileField(
        label='Select Excel file',
        help_text='Upload an Excel file (.xlsx) containing member data'
    )




from django import forms
from .models import GymMembership, TermsAndConditions
from datetime import date

class GymMembershipForm(forms.ModelForm):
    # Override some fields for better UI
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Enter your complete address'
        })
    )
    
    medical_condition_details = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'form-control',
            'placeholder': 'Please specify if you answered Yes above'
        })
    )
    
    medication_details = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'form-control',
            'placeholder': 'Please specify if you answered Yes above'
        })
    )
    
    surgery_injury_details = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'form-control',
            'placeholder': 'Please explain if you answered Yes above'
        })
    )
    
    primary_goal_other = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Please specify if Other is selected'
        })
    )
    
    preferred_training_other = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Please specify if Other is selected'
        })
    )
    
    payment_proof = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,.pdf'
        })
    )
    
    # Digital signature field
    digital_signature = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    # Terms acceptance checkbox
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        error_messages={
            'required': 'You must accept the terms and conditions to proceed.'
        }
    )
    
    # Sleep hours as select dropdown
    SLEEP_CHOICES = [
        ('', 'Select sleep hours'),
        (4, 'Less than 5 hours'),
        (5, '5-6 hours'),
        (6, '6-7 hours'),
        (7, '7-8 hours'),
        (8, '8-9 hours'),
        (9, 'More than 9 hours'),
    ]
    
    sleep_hours = forms.ChoiceField(
        choices=SLEEP_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = GymMembership
        exclude = ['enrollment_id', 'unique_link', 'signature_timestamp', 
                  'created_at', 'updated_at', 'is_active','member','is_member']
        
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter your full name'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 16, 
                'max': 120,
                'readonly': True
            }),
            'gender': forms.RadioSelect(),
            'city_pincode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Mumbai 400001'
            }),
            'mobile_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'pattern': '[0-9]{10}',
                'placeholder': '+91 9876543210'
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'pattern': '[0-9]{10}',
                'placeholder': '+91 9876543210'
            }),
            'email_id': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact person name'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'pattern': '[0-9]{10}',
                'placeholder': '+91 9876543210'
            }),
            'height_cm': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 100, 
                'max': 250,
                'placeholder': '170'
            }),
            'weight_kg': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 30, 
                'max': 300, 
                'step': '0.1',
                'placeholder': '70'
            }),
            'has_medical_condition': forms.RadioSelect(),
            'taking_medication': forms.RadioSelect(),
            'had_surgery_injury': forms.RadioSelect(),
            'smokes_drinks_alcohol': forms.RadioSelect(),
            'family_heart_disease': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'family_diabetes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'family_hypertension': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'family_history_none': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'primary_goal': forms.RadioSelect(),
            'preferred_training': forms.RadioSelect(),
            'training_frequency': forms.RadioSelect(),
            'preferred_workout_time': forms.RadioSelect(),
            'occupation': forms.RadioSelect(),
            'activity_level': forms.RadioSelect(),
            'diet_type': forms.RadioSelect(),
            'plan_chosen': forms.RadioSelect(),
            'personal_trainer_addon': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'nutrition_plan_addon': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'physiotherapy_addon': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'payment_mode': forms.RadioSelect(),
            'terms_version': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get the latest active terms and conditions
        try:
            latest_terms = TermsAndConditions.objects.filter(is_active=True).first()
            if latest_terms:
                self.fields['terms_version'].initial = latest_terms.id
        except TermsAndConditions.DoesNotExist:
            pass
        
        # Make sure all radio fields have proper CSS classes
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.update({'class': 'form-check-input'})
    
    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age and age < 16:
            raise forms.ValidationError("Minimum age requirement is 16 years.")
        return age
    
    def clean_digital_signature(self):
        signature = self.cleaned_data.get('digital_signature')
        if not signature:
            raise forms.ValidationError("Digital signature is required.")
        return signature
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate medical condition details
        if cleaned_data.get('has_medical_condition') and not cleaned_data.get('medical_condition_details'):
            self.add_error('medical_condition_details', "Please specify your medical condition.")
        
        # Validate medication details
        if cleaned_data.get('taking_medication') and not cleaned_data.get('medication_details'):
            self.add_error('medication_details', "Please specify your current medication.")
        
        # Validate surgery/injury details
        if cleaned_data.get('had_surgery_injury') and not cleaned_data.get('surgery_injury_details'):
            self.add_error('surgery_injury_details', "Please explain your surgery/injury history.")
        
        # Validate primary goal other
        if cleaned_data.get('primary_goal') == 'other' and not cleaned_data.get('primary_goal_other'):
            self.add_error('primary_goal_other', "Please specify your primary goal.")
        
        # Validate preferred training other
        if cleaned_data.get('preferred_training') == 'other' and not cleaned_data.get('preferred_training_other'):
            self.add_error('preferred_training_other', "Please specify your preferred training type.")
        
        return cleaned_data