from .models import Notification

def notifications(request):
    """
    Context processor that adds notifications to all templates.
    """
    if request.user.is_authenticated:
        try:
            # Try to access customer - this will work if the user has a customer profile
            customer = request.user.customer
            
            # Get recent notifications
            recent_notifications = Notification.objects.filter(
                customer=customer
            ).order_by('-created_at')[:5]
            
            # Get unread count
            unread_count = Notification.objects.filter(
                customer=customer,
                read=False
            ).count()
            
            # Return the context dictionary
            return {
                'notifications': recent_notifications,
                'unread_notifications_count': unread_count,
            }
        except AttributeError:
            # User doesn't have a customer profile (might be staff)
            pass
    
    # Return empty values for unauthenticated users or users without customer profiles
    return {
        'notifications': [],
        'unread_notifications_count': 0,
    }