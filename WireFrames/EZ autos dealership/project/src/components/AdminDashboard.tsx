import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProfile } from '../lib/api';
import {
  Users, MessageSquare, DollarSign, Search, UserPlus,
  FileText, Calendar, Star, BookOpen, History, AlertCircle, Settings
} from 'lucide-react';
import KnowledgeBase from './admin/KnowledgeBase';
import TestDriveBookings from './admin/TestDriveBookings';
import Feedback from './admin/Feedback';
import ChatHistory from './admin/ChatHistory';
import Analytics from './admin/Analytics';
import TeamMembers from './admin/TeamMembers';
import UserManagement from './admin/UserManagement';
import VehicleInventory from './admin/VehicleInventory';

interface User {
  id: string;
  email: string;
  role: string;
  created_at: string;
  status: string;
}

const AdminDashboard: React.FC = () => {
  const [activeSection, setActiveSection] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [accessDenied, setAccessDenied] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    checkAdminAccess();
  }, [navigate]);

  const checkAdminAccess = async () => {
    try {
      const profile = await getProfile();
      if (profile.role !== 'admin') {
        setAccessDenied(true);
        // Don't automatically redirect, show access denied message
      } else {
        setAccessDenied(false);
      }
    } catch (error) {
      console.error('Error checking admin access:', error);
      setAccessDenied(true);
      // Don't automatically redirect, show access denied message
    } finally {
      setLoading(false);
    }
  };

  const navigationItems = [
    { id: 'overview', label: 'Overview', icon: Users },
    { id: 'users', label: 'User Management', icon: UserPlus },
    { id: 'team', label: 'Team Management', icon: UserPlus },
    { id: 'inventory', label: 'Vehicle Inventory', icon: Car },
    { id: 'knowledge', label: 'Knowledge Base', icon: BookOpen },
    { id: 'bookings', label: 'Test Drive Bookings', icon: Calendar },
    { id: 'feedback', label: 'Feedback & Reviews', icon: Star },
    { id: 'chat-history', label: 'Chat History', icon: History },
    { id: 'analytics', label: 'Analytics', icon: DollarSign },
  ];

  const renderContent = () => {
    switch (activeSection) {
      case 'users':
        return <UserManagement />;
      case 'team':
        return <TeamMembers />;
      case 'inventory':
        return <VehicleInventory />;
      case 'knowledge':
        return <KnowledgeBase />;
      case 'bookings':
        return <TestDriveBookings />;
      case 'feedback':
        return <Feedback />;
      case 'chat-history':
        return <ChatHistory />;
      case 'analytics':
      case 'overview':
      default:
        return <Analytics />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 pt-16 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Checking access permissions...</p>
        </div>
      </div>
    );
  }

  if (accessDenied) {
    return (
      <div className="min-h-screen bg-gray-100 pt-16 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-md p-8 max-w-md w-full text-center">
          <div className="text-red-500 mb-4">
            <AlertCircle size={48} className="mx-auto" />
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Access Denied</h2>
          <p className="text-gray-600 mb-6">
            You don't have permission to access the admin dashboard. Please contact an administrator if you believe this is an error.
          </p>
          <div className="space-y-3">
            <button
              onClick={() => navigate('/')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              Go to Home
            </button>
            <button
              onClick={() => navigate('/login')}
              className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-4 rounded-md transition-colors"
            >
              Sign In as Admin
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 pt-16">
      <div className="flex">
        {/* Sidebar */}
        <div className="w-64 bg-white shadow-md min-h-[calc(100vh-4rem)] fixed">
          <div className="p-4">
            <h1 className="text-xl font-bold text-gray-800 truncate">Admin Panel</h1>
          </div>
          <nav className="mt-4">
            {navigationItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={`w-full flex items-center space-x-2 px-4 py-3 text-gray-700 hover:bg-gray-100 ${
                  activeSection === item.id ? 'bg-blue-50 text-blue-600' : ''
                }`}
              >
                <item.icon size={20} />
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Main content */}
        <div className="flex-1 ml-64 p-8">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;