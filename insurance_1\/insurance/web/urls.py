
from django.urls import path
from .views import *
urlpatterns = [
  path('',home,name='home'),
  path('servise',services,name='servise'),
  path('policy/list/<int:pk>/',policy_list,name='policy_list'),
  path('register',CustomerRegistrationView.as_view(),name='register'),
     path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
    path('profile/', ProfileDetailView.as_view(), name='profile'),
    path('policy/<int:policy_id>/apply/', CustomerPolicyCreateView.as_view(), name='policy_apply'),
    path('my-policies/', MyPoliciesView.as_view(), name='my_policies'),
    path('policy/<int:pk>/', PolicyDetailView.as_view(), name='policy_details'),
    path('policy/<int:policy_id>/documents/', PolicyDocumentsView.as_view(), name='policy_documents'),
path('policy/<int:policy_id>/documents/upload/', DocumentUploadView.as_view(), name='upload_document'),
path('policy/<int:policy_id>/download/', DownloadPolicyView.as_view(), name='download_policy'),
# urls.py
 
    path('policy/<int:policy_id>/document/<int:pk>/delete/', DocumentDeleteView.as_view(), name='delete_document'),
    path('dashboard',admin_dashboard,name='dashboard'),
    path('agents/', admin_agents, name='admin_agents'),
     path('agents/edit/<int:user_id>/', admin_agent_edit, name='admin_agent_edit'),
    path('agents/delete/<int:user_id>/', admin_agent_delete, name='admin_agent_delete'),
    path('categories/', InsuranceCategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', InsuranceCategoryDetailView.as_view(), name='category_detail'),
    path('categories/create/', InsuranceCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', InsuranceCategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', InsuranceCategoryDeleteView.as_view(), name='category_delete'),

    path('policies/', InsurancePolicyListView.as_view(), name='policy_list'),
    path('policies/create/', InsurancePolicyCreateView.as_view(), name='policy_create'),
    path('policies/<int:pk>/', InsurancePolicyDetailView.as_view(), name='policy_detail'),
    path('policies/<int:pk>/update/',InsurancePolicyUpdateView.as_view(), name='policy_edit'),
    path('policies/<int:pk>/delete/', InsurancePolicyDeleteView.as_view(), name='policy_delete'),
    path('policies/<int:pk>/toggle-status/', toggle_policy_status, name='policy_toggle_status'),
]