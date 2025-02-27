from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Customer,Document

class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control'
    }))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    
    # Customer model fields
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={
        'class': 'form-control',
        'type': 'date'
    }))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    address = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': 3
    }))
    city = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    state = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    zip_code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    occupation = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control'
    }))
    annual_income = forms.DecimalField(widget=forms.NumberInput(attrs={
        'class': 'form-control'
    }))

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'})
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email
    


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['date_of_birth', 'phone_number', 'address', 'city', 
                 'state', 'zip_code', 'occupation', 'annual_income']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'annual_income': forms.NumberInput(attrs={'class': 'form-control'}),
        }    





# forms.py
from django import forms
from .models import CustomerPolicy
from django.utils import timezone

class CustomerPolicyForm(forms.ModelForm):
    class Meta:
        model = CustomerPolicy
        fields = ['premium_payment_frequency']
        widgets = {
            'premium_payment_frequency': forms.Select(attrs={'class': 'form-control'}),
        }


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['document_type', 'title', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, policy=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.policy = policy  # Store the policy for further use

        # Example: If document types are policy-specific, filter them
        if self.policy:
            self.fields['document_type'].queryset = self.policy.get_allowed_document_types()
