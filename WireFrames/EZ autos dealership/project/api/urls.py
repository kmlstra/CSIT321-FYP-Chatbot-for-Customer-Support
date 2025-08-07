from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, ProfileViewSet,
    register_user, login_user, logout_user,
    get_profile, vehicles_view, vehicle_detail_view,
    test_drive_view, update_test_drive_view, chat_history_view,
    feedback_view, team_members_view, team_member_detail_view,
    chat_bot_view, analytics_overview
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'profiles', ProfileViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('auth/register/', register_user, name='register'),
    path('auth/login/', login_user, name='login'),
    path('auth/logout/', logout_user, name='logout'),
    path('profile/', get_profile, name='get_profile'),
    
    # Analytics endpoint
    path('analytics/', analytics_overview, name='analytics'),
    
    # Vehicle endpoints
    path('vehicles/', vehicles_view, name='vehicles'),
    path('vehicles/<str:vehicle_id>/', vehicle_detail_view, name='vehicle-detail'),
    
    # Test drive endpoints
    path('test-drives/', test_drive_view, name='test-drives'),
    path('test-drives/<str:test_drive_id>/', update_test_drive_view, name='update-test-drive'),
    
    # Chat endpoints
    path('chat-history/', chat_history_view, name='chat-history'),
    path('chat/', chat_bot_view, name='chat-bot'),
    
    # Feedback endpoints
    path('feedback/', feedback_view, name='feedback'),
    
    # Team management endpoints
    path('team-members/', team_members_view, name='team-members'),
    path('team-members/<str:member_id>/', team_member_detail_view, name='team-member-detail'),
]