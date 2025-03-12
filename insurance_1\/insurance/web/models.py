from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='customer')
    customer_id = models.CharField(max_length=10, unique=True)
    date_of_birth = models.DateField()
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    occupation = models.CharField(max_length=100)
    annual_income = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.customer_id}"

class InsuranceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='image')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Insurance Categories"

    def __str__(self):
        return self.name

class InsurancePolicy(models.Model):
    POLICY_STATUS_CHOICES = [
        ('active', 'Active'),
        ('processed', 'Processed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending Approval')
    ]

    name = models.CharField(max_length=200)
    category = models.ForeignKey(InsuranceCategory, on_delete=models.CASCADE)
    description = models.TextField()
    coverage_amount = models.DecimalField(max_digits=12, decimal_places=2)
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2)
    term_length = models.IntegerField(help_text="Term length in months")
    benefits = models.TextField()
    conditions = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Insurance Policies"

    def __str__(self):
        return f"{self.name} - {self.category.name}"

class CustomerPolicy(models.Model):
    PAYMENT_FREQUENCY = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi-annual', 'Semi-Annual'),
        ('annual', 'Annual')
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    policy = models.ForeignKey(InsurancePolicy, on_delete=models.CASCADE)
    policy_number = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=InsurancePolicy.POLICY_STATUS_CHOICES)
    premium_payment_frequency = models.CharField(max_length=20, choices=PAYMENT_FREQUENCY)
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2)
    next_premium_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    agent= models.ForeignKey(User,on_delete=models.CASCADE,related_name='policy_agent',null=True,blank= True)

    class Meta:
        verbose_name_plural = "Customer Policies"

    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.policy_number}"

class Claim(models.Model):
    CLAIM_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid')
    ]

    customer_policy = models.ForeignKey(CustomerPolicy, on_delete=models.CASCADE)
    claim_number = models.CharField(max_length=20, unique=True)
    incident_date = models.DateField()
    filing_date = models.DateField(auto_now_add=True)
    description = models.TextField()
    claim_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=CLAIM_STATUS_CHOICES, default='pending')
    documents = models.FileField(upload_to='claim_documents/')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    processed_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.claim_number} - {self.customer_policy.policy_number}"

class Premium(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]

    customer_policy = models.ForeignKey(CustomerPolicy, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES)
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
  

    def __str__(self):
        return f"{self.customer_policy.policy_number} - {self.due_date}"

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('id_proof', 'ID Proof'),
        ('address_proof', 'Address Proof'),
        ('income_proof', 'Income Proof'),
        ('policy_document', 'Policy Document'),
        ('claim_related', 'Claim Related'),
        ('other', 'Other')
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    policy = models.ForeignKey(CustomerPolicy,on_delete=models.CASCADE,null=True,blank=True)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='customer_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.document_type}"

    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.document_type}"

class Beneficiary(models.Model):
    customer_policy = models.ForeignKey(CustomerPolicy, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    percentage_share = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Beneficiaries"

    def __str__(self):
        return f"{self.name} - {self.customer_policy.policy_number}"
    

class PaymentTransaction(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('net_banking', 'Net Banking'),
        ('upi', 'UPI'),
        ('wallet', 'Digital Wallet')
    ]
    
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]
    
    premium = models.ForeignKey(Premium, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    payment_date = models.DateTimeField(auto_now_add=True)
    gateway_response = models.JSONField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.transaction_id} - {self.amount}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('document_upload', 'Document Upload Required'),
        ('document_verified', 'Document Verified'),
        ('payment_pending', 'Payment Pending'),
        ('payment_received', 'Payment Received'),
        ('policy_activated', 'Policy Activated'),
        ('policy_expiring', 'Policy Expiring Soon'),
        ('claim_status', 'Claim Status Update'),
        ('premium_due', 'Premium Due'),
    ]

    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_policy = models.ForeignKey('CustomerPolicy', on_delete=models.CASCADE, null=True, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.get_notification_type_display()}"

    @classmethod
    def create_document_upload_notification(cls, customer, policy):
        return cls.objects.create(
            customer=customer,
            notification_type='document_upload',
            title='Document Upload Required',
            message=f'Please upload required documents for policy {policy.policy_number}',
            related_policy=policy
        )

    @classmethod
    def create_document_verified_notification(cls, customer, policy):
        return cls.objects.create(
            customer=customer,
            notification_type='document_verified',
            title='Documents Verified',
            message=f'Your documents for policy {policy.policy_number} have been verified',
            related_policy=policy
        )

    @classmethod
    def create_payment_notification(cls, customer, policy, amount):
        return cls.objects.create(
            customer=customer,
            notification_type='payment_pending',
            title='Payment Required',
            message=f'Please complete payment of ₹{amount} for policy {policy.policy_number}',
            related_policy=policy
        )

    @classmethod
    def create_policy_activated_notification(cls, customer, policy):
        return cls.objects.create(
            customer=customer,
            notification_type='policy_activated',
            title='Policy Activated',
            message=f'Your policy {policy.policy_number} has been activated successfully',
            related_policy=policy
        )

    @classmethod
    def create_premium_due_notification(cls, customer, policy, due_date):
        return cls.objects.create(
            customer=customer,
            notification_type='premium_due',
            title='Premium Due',
            message=f'Premium payment of ₹{policy.premium_amount} is due on {due_date}',
            related_policy=policy,
            expires_at=due_date
        )

    def mark_as_read(self):
        self.read = True
        self.save()

    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def time_since_created(self):
        now = timezone.now()
        diff = now - self.created_at

        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"

class ClaimDocument(models.Model):
    DOCUMENT_TYPES = [
        ('medical_report', 'Medical Report'),
        ('police_report', 'Police Report'),
        ('bills', 'Bills/Invoices'),
        ('photos', 'Photographs'),
        ('other', 'Other Supporting Documents')
    ]
    
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='claim_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.claim.claim_number} - {self.document_type}"

class PolicyRenewalHistory(models.Model):
    customer_policy = models.ForeignKey(CustomerPolicy, on_delete=models.CASCADE)
    previous_end_date = models.DateField()
    new_start_date = models.DateField()
    new_end_date = models.DateField()
    renewal_date = models.DateTimeField(auto_now_add=True)
    renewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2)
    remarks = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.customer_policy.policy_number} - {self.renewal_date}"





