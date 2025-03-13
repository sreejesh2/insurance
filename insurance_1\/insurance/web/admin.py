from django.contrib import admin

# Register your models here.
from .models import (
    Customer, InsuranceCategory, InsurancePolicy, 
    CustomerPolicy, Claim, Premium, Document, Beneficiary,Notification,PaymentTransaction
)

admin.site.register(Customer)
admin.site.register(InsuranceCategory)
admin.site.register(InsurancePolicy)
admin.site.register(CustomerPolicy)
admin.site.register(Claim)
admin.site.register(Premium)
admin.site.register(Document)
admin.site.register(Beneficiary)
admin.site.register(Notification)
admin.site.register(PaymentTransaction)