import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Calendar, Car, MessageSquare, Star, User, Clock, 
  CheckCircle, XCircle, AlertCircle, Heart, DollarSign,
  Phone, Mail, MapPin
} from 'lucide-react';
import { getProfile, getTestDrives, getFeedback } from '../lib/api';

interface TestDrive {
  id: string;
  vehicle_id: string;
  booking_date: string;
  status: string;
  notes: string;
  created_at: string;
}

interface Feedback {
  id: string;
  vehicle_id?: string;
  rating: number;
  comment: string;
  category: string;
  created_at: string;
}

const UserDashboard: React.FC = () => {
  const [user, setUser] = useState<any>(null);
  const [testDrives, setTestDrives] = useState<TestDrive[]>([]);
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const navigate = useNavigate();

  useEffect(() => {
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    try {
      const profile = await getProfile();
      setUser(profile);

      // Fetch user's test drives and feedback
      const [testDrivesData, feedbackData] = await Promise.all([
        getTestDrives().catch(() => []),
        getFeedback().catch(() => [])
      ]);

      setTestDrives(testDrivesData);
      setFeedback(feedbackData);
    } catch (error) {
      console.error('Error fetching user data:', error);
      navigate('/login');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="text-green-500" size={20} />;
      case 'completed':
        return <CheckCircle className="text-blue-500" size={20} />;
      case 'cancelled':
      case 'rejected':
        return <XCircle className="text-red-500" size={20} />;
      default:
        return <Clock className="text-yellow-500" size={20} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      case 'cancelled':
      case 'rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const renderStars = (rating: number) => {
    return Array(5).fill(0).map((_, index) => (
      <Star
        key={index}
        size={16}
        className={index < rating ? 'text-yellow-400 fill-current' : 'text-gray-300'}
      />
    ));
  };

  if (loading) {
    return (
      <div className="pt-20 min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="pt-20 min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="mx-auto text-red-500 mb-4" size={48} />
          <p className="text-red-600 text-lg mb-4">Unable to load dashboard</p>
          <button
            onClick={() => navigate('/login')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md"
          >
            Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="pt-20 min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="bg-blue-600 p-3 rounded-full">
                  <User className="text-white" size={24} />
                </div>
                <div className="ml-4">
                  <h1 className="text-2xl font-bold text-gray-800">
                    Welcome back, {user.user.first_name || user.user.email}!
                  </h1>
                  <p className="text-gray-600">Manage your vehicle interests and bookings</p>
                </div>
              </div>
              <button
                onClick={() => navigate('/profile')}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md transition-colors"
              >
                Edit Profile
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="bg-white rounded-lg shadow-md mb-8">
            <div className="border-b border-gray-200">
              <nav className="flex space-x-8 px-6">
                {[
                  { id: 'overview', label: 'Overview', icon: User },
                  { id: 'test-drives', label: 'Test Drives', icon: Calendar },
                  { id: 'feedback', label: 'My Reviews', icon: Star },
                  { id: 'favorites', label: 'Favorites', icon: Heart }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-2 py-4 border-b-2 font-medium text-sm ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    <tab.icon size={18} />
                    <span>{tab.label}</span>
                  </button>
                ))}
              </nav>
            </div>

            <div className="p-6">
              {/* Overview Tab */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  {/* Quick Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-blue-50 p-6 rounded-lg">
                      <div className="flex items-center">
                        <Calendar className="text-blue-600" size={24} />
                        <div className="ml-4">
                          <p className="text-sm text-gray-600">Test Drives</p>
                          <p className="text-2xl font-bold text-gray-800">{testDrives.length}</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-green-50 p-6 rounded-lg">
                      <div className="flex items-center">
                        <Star className="text-green-600" size={24} />
                        <div className="ml-4">
                          <p className="text-sm text-gray-600">Reviews Given</p>
                          <p className="text-2xl font-bold text-gray-800">{feedback.length}</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-purple-50 p-6 rounded-lg">
                      <div className="flex items-center">
                        <Heart className="text-purple-600" size={24} />
                        <div className="ml-4">
                          <p className="text-sm text-gray-600">Favorites</p>
                          <p className="text-2xl font-bold text-gray-800">0</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Recent Activity */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Activity</h3>
                    <div className="space-y-4">
                      {testDrives.slice(0, 3).map((drive) => (
                        <div key={drive.id} className="flex items-center p-4 bg-gray-50 rounded-lg">
                          <div className="flex items-center">
                            {getStatusIcon(drive.status)}
                            <div className="ml-3">
                              <p className="text-sm font-medium text-gray-800">
                                Test drive scheduled for {new Date(drive.booking_date).toLocaleDateString()}
                              </p>
                              <p className="text-xs text-gray-500">
                                Status: {drive.status} • {new Date(drive.created_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                      
                      {testDrives.length === 0 && (
                        <div className="text-center py-8">
                          <Calendar className="mx-auto text-gray-400 mb-4" size={48} />
                          <p className="text-gray-600">No recent activity</p>
                          <button
                            onClick={() => navigate('/search')}
                            className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md"
                          >
                            Browse Vehicles
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800 mb-4">Quick Actions</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      <button
                        onClick={() => navigate('/search')}
                        className="flex items-center justify-center p-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        <Car className="mr-2" size={20} />
                        Browse Vehicles
                      </button>
                      
                      <button
                        onClick={() => navigate('/finance')}
                        className="flex items-center justify-center p-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        <DollarSign className="mr-2" size={20} />
                        Finance Calculator
                      </button>
                      
                      <button
                        onClick={() => navigate('/contact')}
                        className="flex items-center justify-center p-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                      >
                        <Phone className="mr-2" size={20} />
                        Contact Us
                      </button>
                      
                      <button
                        onClick={() => window.startChat && window.startChat()}
                        className="flex items-center justify-center p-4 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
                      >
                        <MessageSquare className="mr-2" size={20} />
                        Chat Support
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Test Drives Tab */}
              {activeTab === 'test-drives' && (
                <div>
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-semibold text-gray-800">My Test Drives</h3>
                    <button
                      onClick={() => navigate('/search')}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
                    >
                      Book New Test Drive
                    </button>
                  </div>
                  
                  {testDrives.length === 0 ? (
                    <div className="text-center py-12">
                      <Calendar className="mx-auto text-gray-400 mb-4" size={48} />
                      <p className="text-gray-600 text-lg mb-4">No test drives booked yet</p>
                      <button
                        onClick={() => navigate('/search')}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md"
                      >
                        Browse Vehicles
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {testDrives.map((drive) => (
                        <div key={drive.id} className="border rounded-lg p-6">
                          <div className="flex justify-between items-start">
                            <div>
                              <div className="flex items-center mb-2">
                                {getStatusIcon(drive.status)}
                                <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(drive.status)}`}>
                                  {drive.status.charAt(0).toUpperCase() + drive.status.slice(1)}
                                </span>
                              </div>
                              <p className="font-medium text-gray-800">
                                Scheduled: {new Date(drive.booking_date).toLocaleString()}
                              </p>
                              <p className="text-sm text-gray-600 mt-1">
                                Vehicle ID: {drive.vehicle_id}
                              </p>
                              {drive.notes && (
                                <p className="text-sm text-gray-600 mt-2">
                                  Notes: {drive.notes}
                                </p>
                              )}
                            </div>
                            <div className="text-right">
                              <p className="text-xs text-gray-500">
                                Booked: {new Date(drive.created_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Feedback Tab */}
              {activeTab === 'feedback' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-6">My Reviews</h3>
                  
                  {feedback.length === 0 ? (
                    <div className="text-center py-12">
                      <Star className="mx-auto text-gray-400 mb-4" size={48} />
                      <p className="text-gray-600 text-lg mb-4">No reviews submitted yet</p>
                      <p className="text-gray-500 text-sm">
                        After your test drive or purchase, you can leave a review to help other customers.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {feedback.map((review) => (
                        <div key={review.id} className="border rounded-lg p-6">
                          <div className="flex justify-between items-start mb-3">
                            <div className="flex items-center">
                              {renderStars(review.rating)}
                              <span className="ml-2 text-sm text-gray-600">
                                {review.rating}/5 stars
                              </span>
                            </div>
                            <span className="text-xs text-gray-500">
                              {new Date(review.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          
                          <div className="mb-3">
                            <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                              {review.category}
                            </span>
                          </div>
                          
                          <p className="text-gray-700">{review.comment}</p>
                          
                          {review.vehicle_id && (
                            <p className="text-xs text-gray-500 mt-2">
                              Vehicle ID: {review.vehicle_id}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Favorites Tab */}
              {activeTab === 'favorites' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-6">Favorite Vehicles</h3>
                  
                  <div className="text-center py-12">
                    <Heart className="mx-auto text-gray-400 mb-4" size={48} />
                    <p className="text-gray-600 text-lg mb-4">No favorite vehicles yet</p>
                    <p className="text-gray-500 text-sm mb-6">
                      Click the heart icon on any vehicle to add it to your favorites.
                    </p>
                    <button
                      onClick={() => navigate('/search')}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md"
                    >
                      Browse Vehicles
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserDashboard;