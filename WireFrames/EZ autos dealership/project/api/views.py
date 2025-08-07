from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from .models import Profile, VehicleInquiry, NewsletterSubscription
from .serializers import UserSerializer, ProfileSerializer
from .mongodb_models import (
    create_vehicle, get_vehicles, get_vehicle_by_id, update_vehicle, delete_vehicle,
    create_test_drive, get_test_drives, update_test_drive_status,
    save_chat_message, get_chat_history,
    save_feedback, get_feedback,
    create_team_member, get_team_members, update_team_member, delete_team_member,
    vehicles_collection, test_drives_collection, chat_history_collection,
    feedback_collection, team_members_collection
)
from bson import ObjectId
import json
from datetime import datetime, timedelta
from django.db.models import Count
from django.db.models.functions import TruncDate

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    try:
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                'error': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=email).exists():
            return Response({
                'error': 'Email already registered'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        Profile.objects.create(user=user, role='user')

        login(request, user)

        return Response({
            'message': 'User registered successfully',
            'email': user.email,
            'role': 'user'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print(f"Registration error: {str(e)}")
        return Response({
            'error': 'An error occurred during registration'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_user(request):
    try:
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                'error': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=email, password=password)

        if user is not None:
            login(request, user)
            try:
                profile = Profile.objects.get(user=user)
                return Response({
                    'email': user.email,
                    'role': profile.role,
                    'user_id': user.id
                })
            except Profile.DoesNotExist:
                profile = Profile.objects.create(user=user, role='user')
                return Response({
                    'email': user.email,
                    'role': profile.role,
                    'user_id': user.id
                })
        else:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        print(f"Login error: {str(e)}")
        return Response({
            'error': 'An error occurred during login'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def logout_user(request):
    logout(request)
    return Response({'message': 'Logged out successfully'})

@api_view(['GET', 'PUT'])
def get_profile(request):
    if request.method == 'GET':
        print(f"Profile request - User authenticated: {request.user.is_authenticated}")
        print(f"Profile request - User: {request.user}")

        if not request.user.is_authenticated:
            return Response({
                'error': 'Not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)

        try:
            profile = Profile.objects.get(user=request.user)
            return Response({
                'user': {
                    'email': request.user.email,
                    'id': request.user.id,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name
                },
                'role': profile.role,
                'phone': profile.phone,
                'address': profile.address,
                'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None
            })
        except Profile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = Profile.objects.create(user=request.user, role='user')
            return Response({
                'user': {
                    'email': request.user.email,
                    'id': request.user.id,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name
                },
                'role': profile.role,
                'phone': profile.phone,
                'address': profile.address,
                'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None
            })
        except Exception as e:
            print(f"Profile error: {str(e)}")
            return Response({
                'error': 'An error occurred while fetching profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'PUT':
        if not request.user.is_authenticated:
            return Response({
                'error': 'Not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)

        try:
            profile = Profile.objects.get(user=request.user)
            user = request.user

            # Update User model fields
            user.first_name = request.data.get('first_name', user.first_name)
            user.last_name = request.data.get('last_name', user.last_name)
            user.save()

            # Update Profile model fields
            profile.phone = request.data.get('phone', profile.phone)
            profile.address = request.data.get('address', profile.address)

            # Handle date_of_birth
            date_of_birth = request.data.get('date_of_birth')
            if date_of_birth:
                from datetime import datetime
                try:
                    profile.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                except ValueError:
                    pass  # Keep existing value if invalid date format

            profile.save()

            return Response({
                'user': {
                    'email': user.email,
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                },
                'role': profile.role,
                'phone': profile.phone,
                'address': profile.address,
                'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None
            })

        except Profile.DoesNotExist:
            return Response({
                'error': 'Profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Profile update error: {str(e)}")
            return Response({
                'error': 'An error occurred while updating profile'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            profile = Profile.objects.get(user=request.user)
            return profile.role == 'admin'
        except Profile.DoesNotExist:
            return False

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    
    def create(self, request, *args, **kwargs):
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            first_name = request.data.get('first_name', '')
            last_name = request.data.get('last_name', '')
            role = request.data.get('role', 'user')
            phone = request.data.get('phone', '')
            address = request.data.get('address', '')
            is_active = request.data.get('is_active', True)
            
            if User.objects.filter(username=email).exists():
                return Response({
                    'error': 'User with this email already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=is_active
            )
            
            Profile.objects.create(
                user=user,
                role=role,
                phone=phone,
                address=address
            )
            
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            profile = Profile.objects.get(user=user)
            
            # Update User fields
            user.first_name = request.data.get('first_name', user.first_name)
            user.last_name = request.data.get('last_name', user.last_name)
            user.is_active = request.data.get('is_active', user.is_active)
            user.save()
            
            # Update Profile fields
            profile.role = request.data.get('role', profile.role)
            profile.phone = request.data.get('phone', profile.phone)
            profile.address = request.data.get('address', profile.address)
            profile.save()
            
            serializer = self.get_serializer(user)
            return Response(serializer.data)
            
        except Profile.DoesNotExist:
            return Response({
                'error': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAdminUser]

# Analytics endpoint
@api_view(['GET'])
@permission_classes([IsAdminUser])
def analytics_overview(request):
    try:
        # Get time range from query params (default to 30 days)
        days = int(request.GET.get('days', 30))
        start_date = datetime.now() - timedelta(days=days)

        # Django database stats
        total_users = User.objects.count()
        new_users_count = User.objects.filter(date_joined__gte=start_date).count()
        total_inquiries = VehicleInquiry.objects.count()
        pending_inquiries = VehicleInquiry.objects.filter(status='pending').count()
        newsletter_subscribers = NewsletterSubscription.objects.filter(is_active=True).count()

        # User activity over time (last 7 days)
        user_activity = []
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            signups = User.objects.filter(date_joined__date=date.date()).count()
            user_activity.append({
                'date': date_str,
                'signups': signups,
                'visits': signups * 8  # Estimate visits based on signups
            })
        user_activity.reverse()

        # MongoDB stats
        mongodb_stats = {}

        if vehicles_collection is not None:
            total_vehicles = vehicles_collection.count_documents({})
            featured_vehicles = vehicles_collection.count_documents({"featured": True})
            available_vehicles = vehicles_collection.count_documents({"status": "available"})
            mongodb_stats.update({
                'total_vehicles': total_vehicles,
                'featured_vehicles': featured_vehicles,
                'available_vehicles': available_vehicles
            })

        if test_drives_collection is not None:
            total_test_drives = test_drives_collection.count_documents({})
            pending_test_drives = test_drives_collection.count_documents({"status": "pending"})
            approved_test_drives = test_drives_collection.count_documents({"status": "approved"})
            completed_test_drives = test_drives_collection.count_documents({"status": "completed"})
            mongodb_stats.update({
                'total_test_drives': total_test_drives,
                'pending_test_drives': pending_test_drives,
                'approved_test_drives': approved_test_drives,
                'completed_test_drives': completed_test_drives
            })

        if chat_history_collection is not None:
            total_chat_messages = chat_history_collection.count_documents({})
            user_messages = chat_history_collection.count_documents({"sender": "user"})
            bot_messages = chat_history_collection.count_documents({"sender": "bot"})

            # Chat interactions by category (simplified)
            chat_interactions = [
                {"name": "General Inquiries", "value": user_messages // 2},
                {"name": "Test Drive Requests", "value": user_messages // 4},
                {"name": "Financing Questions", "value": user_messages // 5},
                {"name": "Support", "value": user_messages // 8}
            ]

            mongodb_stats.update({
                'total_chat_messages': total_chat_messages,
                'user_messages': user_messages,
                'bot_messages': bot_messages,
                'chat_interactions': chat_interactions
            })

        if feedback_collection is not None:
            total_feedback = feedback_collection.count_documents({})

            # Average rating calculation
            feedback_cursor = feedback_collection.find({}, {"rating": 1})
            ratings = [doc.get('rating', 0) for doc in feedback_cursor]
            average_rating = sum(ratings) / len(ratings) if ratings else 0

            # Rating distribution
            rating_distribution = []
            for rating in range(1, 6):
                count = feedback_collection.count_documents({"rating": rating})
                rating_distribution.append({
                    "rating": rating,
                    "count": count
                })

            mongodb_stats.update({
                'total_feedback': total_feedback,
                'average_rating': round(average_rating, 2),
                'rating_distribution': rating_distribution
            })

        if team_members_collection is not None:
            total_team_members = team_members_collection.count_documents({})
            active_team_members = team_members_collection.count_documents({"status": "active"})
            mongodb_stats.update({
                'total_team_members': total_team_members,
                'active_team_members': active_team_members
            })

        # Calculate estimated revenue (simplified calculation)
        estimated_revenue = completed_test_drives * 45000 if 'completed_test_drives' in mongodb_stats else 0

        return Response({
            'overview_stats': {
                'total_users': total_users,
                'new_users': new_users_count,
                'total_test_drives': mongodb_stats.get('total_test_drives', 0),
                'total_chat_sessions': mongodb_stats.get('user_messages', 0),
                'estimated_revenue': estimated_revenue,
                'newsletter_subscribers': newsletter_subscribers,
                'pending_inquiries': pending_inquiries
            },
            'user_activity': user_activity,
            'mongodb_stats': mongodb_stats,
            'time_range': f"Last {days} days"
        })

    except Exception as e:
        print(f"Analytics error: {str(e)}")
        return Response({
            'error': 'Failed to fetch analytics data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Vehicle endpoints
@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def vehicles_view(request):
    if request.method == 'GET':
        try:
            # Get query parameters for filtering
            make = request.GET.get('make')
            model = request.GET.get('model')
            year = request.GET.get('year')
            min_price = request.GET.get('min_price')
            max_price = request.GET.get('max_price')
            fuel_type = request.GET.get('fuel_type')
            featured = request.GET.get('featured')

            # Build filter query
            filters = {}
            if make:
                filters['make'] = {'$regex': make, '$options': 'i'}
            if model:
                filters['model'] = {'$regex': model, '$options': 'i'}
            if year:
                filters['year'] = int(year)
            if min_price or max_price:
                price_filter = {}
                if min_price:
                    price_filter['$gte'] = int(min_price)
                if max_price:
                    price_filter['$lte'] = int(max_price)
                filters['price'] = price_filter
            if fuel_type:
                filters['fuel_type'] = fuel_type
            if featured:
                filters['featured'] = featured.lower() == 'true'

            vehicles = get_vehicles(filters)

            # Convert ObjectId to string for JSON serialization
            for vehicle in vehicles:
                vehicle['id'] = str(vehicle['_id'])
                del vehicle['_id']

            return Response(vehicles)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'POST':
        # Only admins can create vehicles
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            profile = Profile.objects.get(user=request.user)
            if profile.role != 'admin':
                return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        except Profile.DoesNotExist:
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)

        try:
            result = create_vehicle(request.data)
            return Response({'id': str(result.inserted_id)}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.AllowAny])
def vehicle_detail_view(request, vehicle_id):
    if request.method == 'GET':
        try:
            vehicle = get_vehicle_by_id(vehicle_id)
            if not vehicle:
                return Response({'error': 'Vehicle not found'}, status=status.HTTP_404_NOT_FOUND)

            vehicle['id'] = str(vehicle['_id'])
            del vehicle['_id']
            return Response(vehicle)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method in ['PUT', 'DELETE']:
        # Only admins can update/delete vehicles
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            profile = Profile.objects.get(user=request.user)
            if profile.role != 'admin':
                return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        except Profile.DoesNotExist:
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'PUT':
            try:
                result = update_vehicle(vehicle_id, request.data)
                if result.matched_count == 0:
                    return Response({'error': 'Vehicle not found'}, status=status.HTTP_404_NOT_FOUND)
                return Response({'message': 'Vehicle updated successfully'})
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif request.method == 'DELETE':
            try:
                result = delete_vehicle(vehicle_id)
                if result.deleted_count == 0:
                    return Response({'error': 'Vehicle not found'}, status=status.HTTP_404_NOT_FOUND)
                return Response({'message': 'Vehicle deleted successfully'})
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Test drive endpoints
@api_view(['GET', 'POST'])
def test_drive_view(request):
    if request.method == 'GET':
        # Admins can see all test drives, users can see their own
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.role == 'admin':
                test_drives = get_test_drives()
            else:
                test_drives = get_test_drives({'user_id': str(request.user.id)})

            # Convert ObjectId to string for JSON serialization
            for drive in test_drives:
                drive['id'] = str(drive['_id'])
                del drive['_id']
            return Response(test_drives)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'POST':
        try:
            data = request.data.copy()
            data['user_id'] = str(request.user.id)
            result = create_test_drive(data)
            return Response({'id': str(result.inserted_id)}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_test_drive_view(request, test_drive_id):
    try:
        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)

        result = update_test_drive_status(test_drive_id, new_status)
        if result.matched_count == 0:
            return Response({'error': 'Test drive not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'message': 'Test drive updated successfully'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Chat history endpoints
@api_view(['GET', 'POST'])
def chat_history_view(request):
    if request.method == 'GET':
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.role == 'admin':
                chat_history = get_chat_history()
            else:
                chat_history = get_chat_history({'user_id': str(request.user.id)})

            # Convert ObjectId to string for JSON serialization
            for message in chat_history:
                message['id'] = str(message['_id'])
                del message['_id']
            return Response(chat_history)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'POST':
        try:
            data = request.data.copy()
            if request.user.is_authenticated:
                data['user_id'] = str(request.user.id)
            result = save_chat_message(data)
            return Response({'id': str(result.inserted_id)}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Feedback endpoints
@api_view(['GET', 'POST'])
def feedback_view(request):
    if request.method == 'GET':
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.role == 'admin':
                feedback = get_feedback()
            else:
                feedback = get_feedback({'user_id': str(request.user.id)})

            # Convert ObjectId to string for JSON serialization
            for item in feedback:
                item['id'] = str(item['_id'])
                del item['_id']
            return Response(feedback)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'POST':
        try:
            data = request.data.copy()
            if request.user.is_authenticated:
                data['user_id'] = str(request.user.id)
            result = save_feedback(data)
            return Response({'id': str(result.inserted_id)}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Team members endpoints
@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def team_members_view(request):
    if request.method == 'GET':
        try:
            team_members = get_team_members()
            # Convert ObjectId to string for JSON serialization
            for member in team_members:
                member['id'] = str(member['_id'])
                del member['_id']
            return Response(team_members)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'POST':
        try:
            result = create_team_member(request.data)
            return Response({'id': str(result.inserted_id)}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAdminUser])
def team_member_detail_view(request, member_id):
    if request.method == 'PUT':
        try:
            result = update_team_member(member_id, request.data)
            if result.matched_count == 0:
                return Response({'error': 'Team member not found'}, status=status.HTTP_404_NOT_FOUND)
            return Response({'message': 'Team member updated successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'DELETE':
        try:
            result = delete_team_member(member_id)
            if result.deleted_count == 0:
                return Response({'error': 'Team member not found'}, status=status.HTTP_404_NOT_FOUND)
            return Response({'message': 'Team member deleted successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Enhanced chat bot endpoint for CleverCompanion integration
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@csrf_exempt  # Disable CSRF for this endpoint since it's used by external widget
def chat_bot_view(request):
    try:
        print(f"Chat API called with data: {request.data}")
        print(f"User authenticated: {request.user.is_authenticated}")

        message = request.data.get('message', '')
        session_id = request.data.get('session_id', '')
        sender = request.data.get('sender', 'user')  # 'user' or 'bot'

        if not message or not session_id:
            return Response({
                'error': 'Message and session_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Save the message to chat history
        chat_data = {
            'session_id': session_id,
            'message': message,
            'sender': sender
        }

        # Add user_id if authenticated
        if request.user.is_authenticated:
            chat_data['user_id'] = str(request.user.id)

        print(f"Saving chat data: {chat_data}")

        # Save to MongoDB
        result = save_chat_message(chat_data)

        print(f"Chat message saved with ID: {result.inserted_id}")

        # For CleverCompanion integration, we just save the message
        # The actual bot response comes from CleverCompanion
        return Response({
            'id': str(result.inserted_id),
            'message': 'Message saved successfully',
            'session_id': session_id,
            'success': True
        })

    except Exception as e:
        print(f"Chat bot error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': 'Failed to save chat message',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)