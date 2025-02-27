
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
    path('policy/<int:pk>/', PolicyDetailView.as_view(), name='policy_detail'),
    path('policy/<int:policy_id>/documents/', PolicyDocumentsView.as_view(), name='policy_documents'),
path('policy/<int:policy_id>/documents/upload/', DocumentUploadView.as_view(), name='upload_document'),
path('policy/<int:policy_id>/download/', DownloadPolicyView.as_view(), name='download_policy'),
# urls.py
 
    path('policy/<int:policy_id>/document/<int:pk>/delete/', DocumentDeleteView.as_view(), name='delete_document'),
]