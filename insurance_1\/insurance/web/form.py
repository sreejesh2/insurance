from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Customer,Document,InsuranceCategory,InsurancePolicy

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



class StaffUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data

def is_superuser(user):
    return user.is_superuser

class InsuranceCategoryForm(forms.ModelForm):
    class Meta:
        model = InsuranceCategory
        fields = ['name', 'description', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter category description'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control-file'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'is_active': 'Active Status',
        }
        help_texts = {
            'name': 'Enter a unique name for this insurance category',
            'image': 'Upload an image representing this category (optional)',
            'is_active': 'Check if this category should be active',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Check if name already exists (for create view)
        if not self.instance.pk and InsuranceCategory.objects.filter(name=name).exists():
            raise forms.ValidationError("An insurance category with this name already exists.")
        # For update view, check if name exists excluding current instance
        elif self.instance.pk and InsuranceCategory.objects.exclude(pk=self.instance.pk).filter(name=name).exists():
            raise forms.ValidationError("An insurance category with this name already exists.")
        return name
    

class InsurancePolicyForm(forms.ModelForm):
    class Meta:
        model = InsurancePolicy
        fields = ['name', 'category', 'description', 'coverage_amount', 
                  'premium_amount', 'term_length', 'benefits', 
                  'conditions', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter policy name'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide policy description'
            }),
            'coverage_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00'
            }),
            'premium_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00'
            }),
            'term_length': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Months'
            }),
            'benefits': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'List policy benefits'
            }),
            'conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'List policy conditions'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'is_active': 'Active Status',
        }
        help_texts = {
            'coverage_amount': 'Maximum amount covered by this policy',
            'premium_amount': 'Monthly premium to be paid',
            'is_active': 'Uncheck to disable this policy',
        }

    def clean(self):
        cleaned_data = super().clean()
        coverage_amount = cleaned_data.get('coverage_amount')
        premium_amount = cleaned_data.get('premium_amount')
        
        if coverage_amount and premium_amount and premium_amount > coverage_amount:
            raise forms.ValidationError("Premium amount cannot be greater than coverage amount.")
        
        return cleaned_data



from django import forms
from .models import Claim, ClaimDocument

class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = ['incident_date', 'description', 'claim_amount', 'documents']
        widgets = {
            'incident_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'claim_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'documents': forms.FileInput(attrs={'class': 'form-control'})
        }
        
    def clean_incident_date(self):
        incident_date = self.cleaned_data.get('incident_date')
        if incident_date and incident_date > timezone.now().date():
            raise forms.ValidationError("Incident date cannot be in the future.")
        return incident_date
    
    def clean_claim_amount(self):
        claim_amount = self.cleaned_data.get('claim_amount')
        if claim_amount <= 0:
            raise forms.ValidationError("Claim amount must be greater than zero.")
        return claim_amount


class ClaimDocumentForm(forms.ModelForm):
    class Meta:
        model = ClaimDocument
        fields = ['document_type', 'file', 'description']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
        }


class ClaimRemarkForm(forms.Form):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid')
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        required=False
    )        


class ClaimPaymentForm(forms.Form):
    PAYMENT_METHODS = [
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('digital_payment', 'Digital Payment'),
        ('cash', 'Cash')
    ]
    
    transaction_id = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        required=True
    )
    
    claim_amount = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        required=True
    )
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )    