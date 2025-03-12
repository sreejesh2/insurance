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
from .models import InsurancePolicy, CustomerPolicy,Premium,Document
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
from .form import StaffUserForm,is_superuser,InsuranceCategoryForm,InsurancePolicyForm
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
            ['Premium Amount', f"${policy.premium_amount}"],
            ['Payment Frequency', policy.get_premium_payment_frequency_display()],
            ['Coverage Amount', f"${policy.policy.coverage_amount}"],
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
            'text': f"Premium payment of ${premium.amount} received for policy {premium.customer_policy.policy_number}",
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