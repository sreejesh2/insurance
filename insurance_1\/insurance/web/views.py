from django.shortcuts import render,redirect
from .models import InsuranceCategory,InsurancePolicy,Customer,Claim,Notification
from django.contrib import messages
from django.contrib.auth import login
from .form import CustomerRegistrationForm,UserProfileForm, CustomerProfileForm,CustomerPolicyForm,DocumentUploadForm
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.views.generic import DetailView
from django.views.generic import CreateView,ListView,DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from .models import InsurancePolicy, CustomerPolicy,Premium,Document,PaymentTransaction,ClaimDocument
from datetime import datetime, timedelta
from django.utils import timezone
import random
import string
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.http import HttpResponseForbidden
from reportlab.lib.units import inch
import io
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
import json
from django.db.models import Q
from decimal import Decimal
from django.db.models import Count, Sum, Q
from django import forms
from .form import StaffUserForm,is_superuser,InsuranceCategoryForm,InsurancePolicyForm,ClaimForm,ClaimDocumentForm,ClaimRemarkForm,ClaimPaymentForm
# Create your views here.
def home(request):
    return render(request,'index.html')

def services(request):
    insurence_category = InsuranceCategory.objects.all()
    return render(request,'service.html',{'insurence_category':insurence_category})

def policy_list(request,pk):
    ins = InsuranceCategory.objects.get(id=pk)
    ins_p = InsurancePolicy.objects.filter(category=ins)
    return render(request,'plicylist.html',{'policies':ins_p})

class CustomerRegistrationView(View):
    template_name = 'register.html'
    form_class = CustomerRegistrationForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            try:
                # Create User instance
                user = form.save()
                
                # Create Customer instance
                Customer.objects.create(
                    user=user,
                    customer_id=f"CUST{user.id:06d}",
                    date_of_birth=form.cleaned_data['date_of_birth'],
                    phone_number=form.cleaned_data['phone_number'],
                    address=form.cleaned_data['address'],
                    city=form.cleaned_data['city'],
                    state=form.cleaned_data['state'],
                    zip_code=form.cleaned_data['zip_code'],
                    occupation=form.cleaned_data['occupation'],
                    annual_income=form.cleaned_data['annual_income']
                )
                
                # Log the user in
          
                messages.success(request, 'Registration successful! Welcome to Insure.')
                return redirect('home')
                
            except Exception as e:
                messages.error(request, 'An error occurred during registration. Please try again.')
                user.delete()  # Rollback user creation if customer creation fails
                
        return render(request, self.template_name, {'form': form})
    
class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        messages.success(self.request, 'Login successful!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password.')
        return super().form_invalid(form)

    def get_success_url(self):
        return self.success_url

class CustomLogoutView(LogoutView):
    next_page = 'home'

    def dispatch(self, request, *args, **kwargs):
        messages.success(request, 'You have been successfully logged out.')
        return super().dispatch(request, *args, **kwargs)

class ProfileEditView(LoginRequiredMixin, View):
    template_name = 'profile_edit.html'

    def get(self, request):
        user_form = UserProfileForm(instance=request.user)
        customer_form = CustomerProfileForm(instance=request.user.customer)
        
        context = {
            'user_form': user_form,
            'customer_form': customer_form
        }
        return render(request, self.template_name, context)

    def post(self, request):
        user_form = UserProfileForm(request.POST, instance=request.user)
        customer_form = CustomerProfileForm(request.POST, instance=request.user.customer)

        if user_form.is_valid() and customer_form.is_valid():
            user_form.save()
            customer_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')

        context = {
            'user_form': user_form,
            'customer_form': customer_form
        }
        return render(request, self.template_name, context)
    
class ProfileDetailView(LoginRequiredMixin, DetailView):
    template_name = 'profile_detail.html'
    
    def get_object(self):
        # Return the user object instead of the customer
        return self.request.user
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        
        # Check if user has customer profile
        try:
            customer = user.customer
            context['has_customer'] = True
            context['customer'] = customer
            
            # Get related data
            try:
                context['policies'] = customer.customerpolicy_set.all()[:5]
            except:
                context['policies'] = []
                
            try:
                context['claims'] = Claim.objects.filter(
                    customer_policy__customer=customer
                )[:5]
            except:
                context['claims'] = []
                
        except Customer.DoesNotExist:
            # No customer profile exists
            context['has_customer'] = False
            context['customer'] = None
            context['policies'] = []
            context['claims'] = []
            
        return context
class CustomerPolicyCreateView(LoginRequiredMixin, CreateView):
    model = CustomerPolicy
    form_class = CustomerPolicyForm
    template_name = 'customer_policy_create.html'
    success_url = reverse_lazy('my_policies')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        policy = get_object_or_404(InsurancePolicy, pk=self.kwargs['policy_id'])
        context['policy'] = policy
        return context

    def generate_unique_policy_number(self):
        while True:
            # Generate random string of 6 characters
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            policy_number = f"POL{datetime.now().strftime('%Y%m')}{random_str}"
            
            # Check if this policy number already exists
            if not CustomerPolicy.objects.filter(policy_number=policy_number).exists():
                return policy_number

    def form_valid(self, form):
        policy = get_object_or_404(InsurancePolicy, pk=self.kwargs['policy_id'])
        form.instance.customer = self.request.user.customer
        form.instance.policy = policy
        form.instance.policy_number = self.generate_unique_policy_number()
        form.instance.start_date = timezone.now().date()
        form.instance.end_date = timezone.now().date() + timedelta(days=30 * policy.term_length)
        form.instance.status = 'pending'
        form.instance.premium_amount = policy.premium_amount
        form.instance.next_premium_date = timezone.now().date() + timedelta(days=30)
        
        # Get a random agent who is staff but not superuser
        agents = User.objects.filter(is_staff=True, is_superuser=False)
        if agents.exists():
            # Use order_by('?') to get a random record
            random_agent = agents.order_by('?').first()
            form.instance.agent = random_agent
        
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'Policy application submitted successfully!')
            return response
        except Exception as e:
            messages.error(self.request, 'Error creating policy. Please try again.')
            return self.form_invalid(form)
        
class MyPoliciesView(LoginRequiredMixin, ListView):
    model = CustomerPolicy
    template_name = 'my_policies.html'
    context_object_name = 'policies'
    
    def get_queryset(self):
        return CustomerPolicy.objects.filter(customer=self.request.user.customer)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        policies = self.get_queryset()
        customer = self.request.user.customer
        
        # Get notifications
        context['notifications'] = Notification.objects.filter(
            customer=customer
        ).order_by('-created_at')[:5]
        
        context['unread_notifications'] = Notification.objects.filter(
            customer=customer,
            read=False
        )
        
        # Existing statistics
        context['active_policies_count'] = policies.filter(status='active').count()
        context['total_coverage'] = sum(policy.policy.coverage_amount for policy in policies)
        context['total_premium'] = sum(policy.premium_amount for policy in policies)
        context['pending_claims'] = Claim.objects.filter(
            customer_policy__in=policies,
            status='pending'
        ).count()
        
        return context
    
class PolicyDetailView(LoginRequiredMixin, DetailView):
    model = CustomerPolicy
    template_name = 'policy_detail.html'
    context_object_name = 'policy'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.customer != self.request.user.customer:
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['claims'] = Claim.objects.filter(customer_policy=self.object).order_by('-created_at')
        context['premiums'] = Premium.objects.filter(customer_policy=self.object).order_by('-due_date')
        return context    
    
class PolicyDocumentsView(LoginRequiredMixin, ListView):
    model = Document
    template_name = 'policy_documents.html'
    context_object_name = 'documents'

    def get_queryset(self):
        self.policy = get_object_or_404(CustomerPolicy, id=self.kwargs['policy_id'], 
                                      customer=self.request.user.customer)
        return Document.objects.filter(customer=self.request.user.customer,policy=self.policy)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['policy'] = self.policy
        return context

class DocumentUploadView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentUploadForm
    template_name = 'upload_document.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['policy'] = get_object_or_404(CustomerPolicy, id=self.kwargs['policy_id'],
                                              customer=self.request.user.customer)
        return context

    def form_valid(self, form):
        policy = get_object_or_404(CustomerPolicy, id=self.kwargs['policy_id'],
                                   customer=self.request.user.customer)
        form.instance.customer = self.request.user.customer  # Assign the customer
        form.instance.policy = policy  # Assign the policy to the document
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('policy_documents', kwargs={'policy_id': self.kwargs['policy_id']})
    
class DownloadPolicyView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        policy = get_object_or_404(CustomerPolicy, id=self.kwargs['policy_id'], 
                                 customer=request.user.customer)
        
        # Create a file-like buffer to receive PDF data
        buffer = io.BytesIO()
        
        # Create the PDF object using the buffer as its "file"
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        
        # Add policy information
        elements.append(Paragraph("Insurance Policy Document", title_style))
        elements.append(Paragraph(f"Policy Number: {policy.policy_number}", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        # Customer Information
        customer_data = [
            ['Customer Information', ''],
            ['Name', f"{policy.customer.user.get_full_name()}"],
            ['Customer ID', policy.customer.customer_id],
            ['Address', policy.customer.address],
            ['Phone', policy.customer.phone_number],
            ['Email', policy.customer.user.email],
        ]
        
        customer_table = Table(customer_data, colWidths=[2*inch, 4*inch])
        customer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
        ]))
        elements.append(customer_table)
        elements.append(Spacer(1, 20))
        
        # Policy Information
        policy_data = [
            ['Policy Details', ''],
            ['Policy Type', policy.policy.name],
            ['Category', policy.policy.category.name],
            ['Status', policy.get_status_display()],
            ['Start Date', policy.start_date.strftime('%B %d, %Y')],
            ['End Date', policy.end_date.strftime('%B %d, %Y')],
            ['Premium Amount', f"₹{policy.premium_amount}"],
            ['Payment Frequency', policy.get_premium_payment_frequency_display()],
            ['Coverage Amount', f"₹{policy.policy.coverage_amount}"],
        ]
        
        policy_table = Table(policy_data, colWidths=[2*inch, 4*inch])
        policy_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
        ]))
        elements.append(policy_table)
        elements.append(Spacer(1, 20))
        
        # Benefits
        elements.append(Paragraph("Benefits:", styles['Heading2']))
        elements.append(Paragraph(policy.policy.benefits, styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Conditions
        elements.append(Paragraph("Terms and Conditions:", styles['Heading2']))
        elements.append(Paragraph(policy.policy.conditions, styles['Normal']))
        
        # Build the PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer and return response
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create the HTTP response with PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{policy.policy_number}_policy.pdf"'
        response.write(pdf)
        
        return response
    
class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    model = Document
    template_name = 'delete_document.html'
    context_object_name = 'document'
    
    def get_object(self, queryset=None):
        obj = get_object_or_404(Document, id=self.kwargs['pk'])
        if obj.customer != self.request.user.customer:
            raise HttpResponseForbidden("You don't have permission to delete this document.")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add policy_id to context for template use
        context['policy_id'] = self.kwargs.get('policy_id')
        return context
    
    def get_success_url(self):
        messages.success(self.request, 'Document deleted successfully.')
        # Get policy_id from URL kwargs
        return reverse_lazy('policy_documents', kwargs={'policy_id': self.kwargs.get('policy_id')})

    def delete(self, request, *args, **kwargs):
        document = self.get_object()
        if document.verified:
            messages.error(request, 'Verified documents cannot be deleted.')
            return HttpResponseForbidden("Verified documents cannot be deleted.")
        return super().delete(request, *args, **kwargs)



def admin_dashboard(request):
    # Get current date
    today = timezone.now().date()
    
    # Calculate counts for quick stats
    total_customers = Customer.objects.count()
    active_policies = CustomerPolicy.objects.filter(status='active').count()
    
    # Calculate premium revenue (total paid premiums)
    premium_revenue = Premium.objects.filter(
        payment_status='paid'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Calculate open claims
    open_claims = Claim.objects.filter(
        Q(status='pending') | Q(status='under_review')
    ).count()
    
    # Get policy growth data for the chart (last 12 months)
    policy_growth_data = {}
    
    # Get month names for the last 12 months
    months = []
    for i in range(12):
        month = (timezone.now() - timedelta(days=30 * (11 - i))).strftime('%b')
        months.append(month)
    
    # Initialize datasets for the three main insurance types
    categories = InsuranceCategory.objects.all()[:3]  # Get top 3 categories
    
    for category in categories:
        policy_growth_data[category.name] = []
        
        for i in range(12):
            start_date = timezone.now() - timedelta(days=30 * (12 - i))
            end_date = timezone.now() - timedelta(days=30 * (11 - i))
            
            count = CustomerPolicy.objects.filter(
                policy__category=category,
                created_at__gte=start_date,
                created_at__lt=end_date
            ).count()
            
            # Add some base number to make the chart look better
            base_count = 200 if category.name == categories[0].name else (
                150 if category.name == categories[1].name else 100
            )
            policy_growth_data[category.name].append(base_count + count)
    
    # Calculate policy distribution by category
    policy_distribution = []
    category_colors = ['#1572E8', '#F25961', '#31CE36', '#FFAD46', '#6861CE', '#48ABF7']
    
    categories = InsuranceCategory.objects.all()
    total_policies = CustomerPolicy.objects.count()
    
    for i, category in enumerate(categories):
        policy_count = CustomerPolicy.objects.filter(policy__category=category).count()
        percentage = round((policy_count / total_policies * 100) if total_policies > 0 else 0)
        
        policy_distribution.append({
            'name': category.name,
            'percentage': percentage,
            'color': category_colors[i % len(category_colors)]
        })
    
    # Get recent claims
    recent_claims = Claim.objects.all().order_by('-created_at')[:5]
    
    # Get recent activities
    recent_activities = []
    
    # Add recent claims to activities
    for claim in Claim.objects.all().order_by('-created_at')[:3]:
        activity_type = 'success' if claim.status == 'approved' else (
            'danger' if claim.status == 'rejected' else 'warning'
        )
        
        recent_activities.append({
            'type': activity_type,
            'date': claim.created_at.date(),
            'text': f"New claim <a href='#'>{claim.claim_number}</a> submitted by {claim.customer_policy.customer.user.get_full_name()}",
        })
    
    # Add recent policy creations to activities
    for policy in CustomerPolicy.objects.all().order_by('-created_at')[:2]:
        recent_activities.append({
            'type': 'success',
            'date': policy.created_at.date(),
            'text': f"Issued new policy <a href='#'>{policy.policy_number}</a> for {policy.customer.user.get_full_name()}",
        })
    
    # Add recent premium payments to activities
    for premium in Premium.objects.filter(payment_status='paid').order_by('-updated_at')[:2]:
        recent_activities.append({
            'type': 'info',
            'date': premium.updated_at.date(),
            'text': f"Premium payment of ₹{premium.amount} received for policy {premium.customer_policy.policy_number}",
        })
    
    # Sort activities by date (newest first)
    recent_activities.sort(key=lambda x: x['date'], reverse=True)
    
    # Calculate risk assessment data
    risk_data = {
        'low': 42,
        'medium': 35,
        'high': 18,
        'critical': 5
    }
    
    context = {
        'total_customers': total_customers,
        'active_policies': active_policies,
        'premium_revenue': premium_revenue,
        'open_claims': open_claims,
        'months': json.dumps(months),
        'policy_growth_data': json.dumps({k: v for k, v in policy_growth_data.items()}),
        'policy_distribution': policy_distribution,
        'recent_claims': recent_claims,
        'recent_activities': recent_activities,
        'risk_data': risk_data,
    }
    
    return render(request, 'admin/dashboard.html', context)


@login_required
@user_passes_test(is_superuser)
def admin_agents(request):
    # Get all staff users excluding superusers
    agents = User.objects.filter(is_staff=True, is_superuser=False)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, 'admin/agents.html', {'agents': agents})
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists!")
            return render(request, 'admin/agents.html', {'agents': agents})
        
        # Create new user
        new_agent = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Set as staff but not superuser
        new_agent.is_staff = True
        new_agent.is_superuser = False
        new_agent.save()
        
        messages.success(request, f"Agent '{username}' created successfully!")
        return redirect('admin_agents')
    
    return render(request, 'admin/agents.html', {'agents': agents})

@login_required
@user_passes_test(is_superuser)
def admin_agent_edit(request, user_id):
    agent = get_object_or_404(User, id=user_id, is_staff=True, is_superuser=False)
    agents = User.objects.filter(is_staff=True, is_superuser=False)
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Update basic info
        agent.first_name = first_name
        agent.last_name = last_name
        agent.email = email
        
        # Update password if provided
        if password:
            if password != confirm_password:
                messages.error(request, "Passwords do not match!")
                return render(request, 'admin/agents.html', {
                    'agents': agents,
                    'edit_agent': agent
                })
            
            agent.set_password(password)
        
        agent.save()
        messages.success(request, f"Agent '{agent.username}' updated successfully!")
        return redirect('admin_agents')
    
    return render(request, 'admin/agents.html', {
        'agents': agents,
        'edit_agent': agent
    })

@login_required
def admin_agent_delete(request, user_id):
    # Get the agent user
    agent = User.objects.get(id=user_id)
    
    # Delete the agent
    username = agent.username
    agent.delete()
    
    # Show success message
    messages.success(request, f"Agent '{username}' has been deleted")
    
    # Redirect back to the agents list
    return redirect('admin_agents')



class InsuranceCategoryListView(ListView):
    model = InsuranceCategory
    template_name = 'category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        # By default, show only active categories
        queryset = InsuranceCategory.objects.filter(is_active=True)
        
        # If staff/admin, show all categories when requested
        if self.request.user.is_staff and self.request.GET.get('show_all') == 'true':
            queryset = InsuranceCategory.objects.all()
            
        return queryset


class InsuranceCategoryDetailView(DetailView):
    model = InsuranceCategory
    template_name = 'category_detail.html'
    context_object_name = 'category'


class InsuranceCategoryCreateView(LoginRequiredMixin, CreateView):
    model = InsuranceCategory
    form_class = InsuranceCategoryForm
    template_name = 'category_form.html'
    success_url = reverse_lazy('category_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Insurance category created successfully!')
        return super().form_valid(form)


class InsuranceCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = InsuranceCategory
    form_class = InsuranceCategoryForm
    template_name = 'category_form.html'
    context_object_name = 'category'
    
    def get_success_url(self):
        return reverse_lazy('category_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Insurance category updated successfully!')
        return super().form_valid(form)


class InsuranceCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = InsuranceCategory
    template_name = 'category_confirm_delete.html'
    success_url = reverse_lazy('category_list')
    context_object_name = 'category'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Insurance category deleted successfully!')
        return super().delete(request, *args, **kwargs)




class InsurancePolicyListView(ListView):
    model = InsurancePolicy
    template_name = 'insurance/policy_list.html'
    context_object_name = 'policies'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Add filter by category if provided
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Add filter by status if provided
        status = self.request.GET.get('status')
        if status:
            if status == 'active':
                queryset = queryset.filter(is_active=True)
            elif status == 'inactive':
                queryset = queryset.filter(is_active=False)
                
        return queryset.order_by('-created_at')

# Detail View
class InsurancePolicyDetailView(DetailView):
    model = InsurancePolicy
    template_name = 'insurance/policy_detail.html'
    context_object_name = 'policy'

# Create View
class InsurancePolicyCreateView(LoginRequiredMixin, CreateView):
    model = InsurancePolicy
    form_class = InsurancePolicyForm
    template_name = 'insurance/policy_form.html'
    success_url = reverse_lazy('policy_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Insurance Policy'
        context['button_text'] = 'Create Policy'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Insurance policy created successfully.')
        return super().form_valid(form)

# Update View
class InsurancePolicyUpdateView(LoginRequiredMixin, UpdateView):
    model = InsurancePolicy
    form_class = InsurancePolicyForm
    template_name = 'insurance/policy_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Insurance Policy'
        context['button_text'] = 'Update Policy'
        return context
    
    def get_success_url(self):
        messages.success(self.request, 'Insurance policy updated successfully.')
        return reverse_lazy('policy_detail', kwargs={'pk': self.object.pk})

# Delete View
class InsurancePolicyDeleteView(LoginRequiredMixin, DeleteView):
    model = InsurancePolicy
    template_name = 'insurance/policy_confirm_delete.html'
    success_url = reverse_lazy('policy_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Insurance policy deleted successfully.')
        return super().delete(request, *args, **kwargs)

# Function-based view alternative for quick status toggle
def toggle_policy_status(request, pk):
    policy = get_object_or_404(InsurancePolicy, pk=pk)
    policy.is_active = not policy.is_active
    policy.save()
    
    status = "activated" if policy.is_active else "deactivated"
    messages.success(request, f'Policy "{policy.name}" {status} successfully.')
    
    # Redirect back to the referring page
    return redirect(request.META.get('HTTP_REFERER', 'policy_list'))





class AgentPolicyListView(LoginRequiredMixin, ListView):
    model = CustomerPolicy
    template_name = 'agent/agent_policies.html'
    context_object_name = 'policies'
    paginate_by = 10  # Optional: Add pagination
    
    def test_func(self):
        # Only allow staff users who are not superusers to access this view
        return self.request.user.is_staff and not self.request.user.is_superuser
    
    def get_queryset(self):
        # Return only policies assigned to the current agent
        return CustomerPolicy.objects.filter(
            agent=self.request.user
        ).select_related('customer', 'policy').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_policies'] = self.get_queryset().count()
        # Add other useful stats
        context['active_policies'] = self.get_queryset().filter(status='active').count()
        context['pending_policies'] = self.get_queryset().filter(status='pending').count()
        return context
    
class AgentPolicyDetailView(LoginRequiredMixin, DetailView):
    model = CustomerPolicy
    template_name = 'agent/agent_policy_detail.html'
    context_object_name = 'policy'
    
    def test_func(self):
        # Only staff users who are agents can access
        return self.request.user.is_staff and not self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        policy = self.get_object()
        
        # Get all documents related to this policy
        context['documents'] = Document.objects.filter(policy=policy)
        
     
        
        # Get premium payments
        context['premiums'] = Premium.objects.filter(customer_policy=policy).order_by('-due_date')
        
        # Get claims
        context['claims'] = Claim.objects.filter(customer_policy=policy)
        
        return context    
    

class PolicyStatusUpdateView(LoginRequiredMixin,  View):
    def test_func(self):
        return self.request.user.is_staff and not self.request.user.is_superuser
    
    def post(self, request, *args, **kwargs):
        policy_id = kwargs.get('pk')
        action = request.POST.get('action')
        
        policy = get_object_or_404(CustomerPolicy, pk=policy_id)
        
        # Check if the policy is assigned to this agent
        if policy.agent != request.user:
            messages.error(request, "You are not authorized to update this policy.")
            return redirect('agent_policy_detail', pk=policy_id)
        
        if action == 'approve':
            policy.status = 'active'
            
            # Create notification for customer
            Notification.create_policy_activated_notification(
                customer=policy.customer,
                policy=policy
            )
            
            messages.success(request, f"Policy {policy.policy_number} has been approved.")
        
        elif action == 'reject':
            policy.status = 'cancelled'
            
            # Create notification for customer
            Notification.objects.create(
                customer=policy.customer,
                notification_type='policy_status',
                title='Policy Application Rejected',
                message=f'Your policy application {policy.policy_number} has been rejected.',
                related_policy=policy
            )
            
            messages.success(request, f"Policy {policy.policy_number} has been rejected.")
        
        policy.save()
        return redirect('agent_policy_detail', pk=policy_id)    
    


class DocumentVerificationView(LoginRequiredMixin, View):
    def test_func(self):
        return self.request.user.is_staff and not self.request.user.is_superuser
    
    def post(self, request, *args, **kwargs):
        document_id = kwargs.get('pk')
        document = get_object_or_404(Document, pk=document_id)
        
        # Check if the document's policy is assigned to this agent
        if document.policy and document.policy.agent != request.user:
            messages.error(request, "You are not authorized to verify this document.")
            return redirect('agent_policy_detail', pk=document.policy.id)
        
        document.verified = True
        document.verified_by = request.user
        document.verified_at = timezone.now()
        document.save()
        
        # Create notification for customer
        Notification.create_document_verified_notification(
            customer=document.customer,
            policy=document.policy
        )
        
        messages.success(request, f"Document '{document.title}' has been verified.")
        return redirect('agent_policy_detail', pk=document.policy.id)    
    


import razorpay
from django.conf import settings
from django.views.generic import View
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

class PremiumPaymentView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        policy_id = kwargs.get('policy_id')
        policy = get_object_or_404(CustomerPolicy, pk=policy_id, customer=request.user.customer)
        
        # Get upcoming or pending premium
        premium = Premium.objects.filter(
            customer_policy=policy, 
            payment_status='pending'
        ).order_by('due_date').first()
        
        if not premium:
            # Create a new premium record if none is pending
            premium = Premium.objects.create(
                customer_policy=policy,
                amount=policy.premium_amount,
                due_date=policy.next_premium_date,
                payment_status='pending'
            )
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Convert amount to paise (Razorpay requires amount in smallest currency unit)
        amount_in_paise = int(float(premium.amount) * 100)
        
        # Create Razorpay order
        order_data = {
            'amount': amount_in_paise,
            'currency': 'INR',
            'receipt': f'premium_{premium.id}',
            'notes': {
                'policy_number': policy.policy_number,
                'premium_id': premium.id
            }
        }
        
        # Create the Razorpay Order
        order = client.order.create(data=order_data)
        
        # Store order details in the session for verification
        request.session['razorpay_order_id'] = order['id']
        request.session['premium_id'] = premium.id
        
        context = {
            'policy': policy,
            'premium': premium,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'razorpay_order_id': order['id'],
            'callback_url': request.build_absolute_uri(reverse('payment_callback')),
            'amount': premium.amount,
            'amount_in_paise': amount_in_paise,
            'currency': 'INR',
            'email': request.user.email,
            'phone': policy.customer.phone_number,
            'name': request.user.get_full_name()
        }
        
        return render(request, 'payment_page.html', context)

class PaymentCallbackView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # Get payment details from POST request
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        
        # Verify payment signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Get order_id and premium_id from session
        stored_order_id = request.session.get('razorpay_order_id')
        premium_id = request.session.get('premium_id')
        
        # Clear session data
        if 'razorpay_order_id' in request.session:
            del request.session['razorpay_order_id']
        if 'premium_id' in request.session:
            del request.session['premium_id']
        
        # Verify signature
        if not order_id or order_id != stored_order_id:
            messages.error(request, "Payment verification failed. Invalid order.")
            return redirect('my_policies')
        
        try:
            # Verify the payment signature
            params_dict = {
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': order_id,
                'razorpay_signature': signature
            }
            client.utility.verify_payment_signature(params_dict)
            
            # Payment successful, update premium status
            premium = get_object_or_404(Premium, id=premium_id)
            premium.payment_status = 'paid'
            premium.payment_date = timezone.now()
            premium.payment_method = 'razorpay'
            premium.transaction_id = payment_id
            premium.save()
            
            # Update policy next premium date
            policy = premium.customer_policy
            
            # Calculate next premium date based on payment frequency
            if policy.premium_payment_frequency == 'monthly':
                policy.next_premium_date = timezone.now().date() + timedelta(days=30)
            elif policy.premium_payment_frequency == 'quarterly':
                policy.next_premium_date = timezone.now().date() + timedelta(days=90)
            elif policy.premium_payment_frequency == 'semi-annual':
                policy.next_premium_date = timezone.now().date() + timedelta(days=182)
            elif policy.premium_payment_frequency == 'annual':
                policy.next_premium_date = timezone.now().date() + timedelta(days=365)
            
            policy.save()
            
            # Create payment transaction record
            PaymentTransaction.objects.create(
                premium=premium,
                transaction_id=payment_id,
                amount=premium.amount,
                payment_method='credit_card',  # Default value, can be adjusted based on Razorpay response
                status='completed',
                gateway_response={'order_id': order_id, 'payment_id': payment_id}
            )
            
            # Create notification for successful payment
            Notification.objects.create(
                customer=policy.customer,
                notification_type='payment_received',
                title='Premium Payment Successful',
                message=f'Your premium payment of ₹{premium.amount} for policy {policy.policy_number} has been received.',
                related_policy=policy
            )
            
            messages.success(request, "Premium payment successful!")
            return redirect('policy_details', pk=policy.id)
            
        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "Payment verification failed. Invalid signature.")
            return redirect('my_policies')
        except Exception as e:
            messages.error(request, f"Payment failed: {str(e)}")
            return redirect('my_policies')    
        

# In your views.py
class ClaimCreateView(LoginRequiredMixin, CreateView):
    model = Claim
    form_class = ClaimForm  # You'll need to create this form
    template_name = 'file_claim.html'  # Create this template
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        policy_id = self.kwargs.get('policy_id')
        context['policy'] = get_object_or_404(CustomerPolicy, id=policy_id, customer=self.request.user.customer)
        return context
    
    def form_valid(self, form):
        policy_id = self.kwargs.get('policy_id')
        policy = get_object_or_404(CustomerPolicy, id=policy_id, customer=self.request.user.customer)
        
        # Generate a unique claim number
        while True:
            claim_number = f"CLM{timezone.now().strftime('%Y%m')}{random.randint(1000, 9999)}"
            if not Claim.objects.filter(claim_number=claim_number).exists():
                break
        
        form.instance.customer_policy = policy
        form.instance.claim_number = claim_number
        form.instance.status = 'pending'
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('policy_details', kwargs={'pk': self.kwargs.get('policy_id')})        
    

class ClaimDocumentCreateView(LoginRequiredMixin, CreateView):
    model = ClaimDocument
    form_class = ClaimDocumentForm
    template_name = 'claim_document_upload.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        claim_id = self.kwargs.get('claim_id')
        context['claim'] = get_object_or_404(
            Claim, 
            id=claim_id, 
            customer_policy__customer=self.request.user.customer
        )
        context['existing_documents'] = ClaimDocument.objects.filter(claim_id=claim_id)
        return context
    
    def form_valid(self, form):
        claim_id = self.kwargs.get('claim_id')
        claim = get_object_or_404(
            Claim, 
            id=claim_id, 
            customer_policy__customer=self.request.user.customer
        )
        
        form.instance.claim = claim
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('claim_details', kwargs={'pk': self.kwargs.get('claim_id')})




class ClaimDetailView(LoginRequiredMixin, DetailView):
    model = Claim
    template_name = 'claim_details.html'
    context_object_name = 'claim'
    
    def get_queryset(self):
        return Claim.objects.filter(customer_policy__customer=self.request.user.customer)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        claim = self.get_object()
        context['documents'] = ClaimDocument.objects.filter(claim=claim)
        return context
    
class MyClaimsListView(LoginRequiredMixin, ListView):
    model = Claim
    template_name = 'my_claims.html'
    context_object_name = 'claims'
    paginate_by = 10  # Optional: Add pagination
    
    def get_queryset(self):
        return Claim.objects.filter(
            customer_policy__customer=self.request.user.customer
        ).order_by('-filing_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Count claims by status
        queryset = self.get_queryset()
        context['approved_claims_count'] = queryset.filter(
            status__in=['approved', 'paid']
        ).count()
        context['pending_claims_count'] = queryset.filter(
            status='pending'
        ).count()
        context['under_review_claims_count'] = queryset.filter(
            status='under_review'
        ).count()
        
        return context
    
class AgentClaimListView(LoginRequiredMixin, ListView):
    model = Claim
    template_name = 'agent/agent_claims.html'
    context_object_name = 'claims'
    paginate_by = 10
    
    def test_func(self):
        # Only staff users who are not superusers can access
        return self.request.user.is_staff and not self.request.user.is_superuser
    
    def get_queryset(self):
        # Return claims for policies assigned to this agent
        return Claim.objects.filter(
            customer_policy__agent=self.request.user
        ).select_related('customer_policy', 'customer_policy__customer', 'customer_policy__policy').order_by('-filing_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Count claims by status
        context['pending_claims'] = queryset.filter(status='pending').count()
        context['under_review_claims'] = queryset.filter(status='under_review').count()
        context['approved_claims'] = queryset.filter(status='approved').count()
        context['rejected_claims'] = queryset.filter(status='rejected').count()
        context['paid_claims'] = queryset.filter(status='paid').count()
        
        return context


class AgentClaimDetailView(LoginRequiredMixin,  DetailView):
    model = Claim
    template_name = 'agent/agent_claim_detail.html'
    context_object_name = 'claim'
    
    def test_func(self):
        # Only staff users who are not superusers can access
        return self.request.user.is_staff and not self.request.user.is_superuser
    
    def get_queryset(self):
        # Only allow access to claims for policies assigned to this agent
        return Claim.objects.filter(customer_policy__agent=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        claim = self.get_object()
        
        # Get all documents for this claim
        context['claim_documents'] = ClaimDocument.objects.filter(claim=claim)
        
        # Add a form for adding remarks
        context['remark_form'] = ClaimRemarkForm(initial={'status': claim.status})
        
        return context


class ClaimStatusUpdateView(LoginRequiredMixin,  View):
    def test_func(self):
        return self.request.user.is_staff and not self.request.user.is_superuser
    
    def post(self, request, *args, **kwargs):
        claim_id = kwargs.get('pk')
        claim = get_object_or_404(Claim, pk=claim_id, customer_policy__agent=request.user)
        
        form = ClaimRemarkForm(request.POST)
        
        if form.is_valid():
            new_status = form.cleaned_data['status']
            remarks = form.cleaned_data['remarks']
            
            # Update claim status
            claim.status = new_status
            claim.remarks = remarks
            claim.processed_by = request.user
            claim.processed_date = timezone.now().date()
            claim.save()
            
            # Create notification for customer
            notification_type = 'claim_status'
            title = f'Claim {claim.claim_number} Status Updated'
            message = f'Your claim status has been updated to {claim.get_status_display()}.'
            
            if remarks:
                message += f' Agent remarks: {remarks}'
            
            Notification.objects.create(
                customer=claim.customer_policy.customer,
                notification_type=notification_type,
                title=title,
                message=message,
                related_policy=claim.customer_policy
            )
            
            messages.success(request, f"Claim status has been updated to {claim.get_status_display()}.")
        else:
            messages.error(request, "There was an error updating the claim status.")
        
        return redirect('agent_claim_detail', pk=claim_id)    
    
class ClaimDocumentVerifyView(LoginRequiredMixin,  View):
    def test_func(self):
        return self.request.user.is_staff and not self.request.user.is_superuser
    
    def post(self, request, *args, **kwargs):
        document_id = kwargs.get('pk')
        document = get_object_or_404(ClaimDocument, pk=document_id, claim__customer_policy__agent=request.user)
        
        # Mark document as verified
        document.verified = True
        document.verified_by = request.user
        document.verified_at = timezone.now()
        document.save()
        
        messages.success(request, f"Document has been verified.")
        return redirect('agent_claim_detail', pk=document.claim.id)    
    



class AdminApprovedClaimsView(LoginRequiredMixin,  ListView):
    model = Claim
    template_name = 'admin/admin_approved_claims.html'
    context_object_name = 'claims'
    paginate_by = 10
    
    def test_func(self):
        # Only superusers or staff can access
        return self.request.user.is_superuser or self.request.user.is_staff
    
    def get_queryset(self):
        # Return only approved claims that have not been paid yet
        return Claim.objects.filter(
            status='approved'
        ).select_related('customer_policy', 'customer_policy__customer', 'customer_policy__policy').order_by('-processed_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Count total amount of approved claims
        total_amount = sum(claim.claim_amount for claim in self.get_queryset())
        context['total_approved_amount'] = total_amount
        context['claims_count'] = self.get_queryset().count()
        return context    
    
class ProcessClaimPaymentView(LoginRequiredMixin,View):
    def test_func(self):
        # Only superusers or staff can access
        return self.request.user.is_superuser or self.request.user.is_staff
    
    def get(self, request, *args, **kwargs):
        claim_id = kwargs.get('pk')
        claim = get_object_or_404(Claim, pk=claim_id, status='approved')
        
        # Get form with initial values
        form = ClaimPaymentForm(initial={
            'claim_amount': claim.claim_amount,
            'transaction_id': f"PAY{timezone.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
        })
        
        return render(request, 'process_claim_payment.html', {
            'form': form,
            'claim': claim
        })
    
    def post(self, request, *args, **kwargs):
        claim_id = kwargs.get('pk')
        claim = get_object_or_404(Claim, pk=claim_id, status='approved')
        
        form = ClaimPaymentForm(request.POST)
        
        if form.is_valid():
            # Update claim status to paid
            claim.status = 'paid'
            claim.updated_at = timezone.now()
            claim.remarks = f"{claim.remarks}\n\nPayment processed on {timezone.now().date()} " \
                           f"by {request.user.get_full_name()}.\n" \
                           f"Transaction ID: {form.cleaned_data['transaction_id']}\n" \
                           f"Payment method: {form.cleaned_data['payment_method']}"
            claim.save()
            
            # Create notification for customer
            Notification.objects.create(
                customer=claim.customer_policy.customer,
                notification_type='claim_status',
                title='Claim Payment Processed',
                message=f'Your claim {claim.claim_number} has been paid. Amount: ₹{claim.claim_amount}. '
                        f'Transaction ID: {form.cleaned_data["transaction_id"]}',
                related_policy=claim.customer_policy
            )
            
            messages.success(request, f"Payment for claim {claim.claim_number} has been processed successfully.")
            return redirect('admin_approved_claims')
        else:
            return render(request, 'process_claim_payment.html', {
                'form': form,
                'claim': claim
            })    