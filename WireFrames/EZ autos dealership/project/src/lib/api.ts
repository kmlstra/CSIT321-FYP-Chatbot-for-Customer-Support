// API client for EZ Autos
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include CSRF token
api.interceptors.request.use(async (config) => {
  // Get CSRF token from cookies
  const csrfToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1];

  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken;
  }

  return config;
});

// Authentication
export const login = async (email: string, password: string) => {
  const response = await api.post('/auth/login/', { email, password });
  return response.data;
};

export const register = async (email: string, password: string) => {
  const response = await api.post('/auth/register/', { email, password });
  return response.data;
};

export const logout = async () => {
  const response = await api.post('/auth/logout/');
  return response.data;
};

export const getProfile = async () => {
  const response = await api.get('/profile/');
  return response.data;
};

export const updateProfile = async (profileData: any) => {
  const response = await api.put('/profile/', profileData);
  return response.data;
};

// Vehicles
export const getVehicles = async (filters?: any) => {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, String(value));
      }
    });
  }

  const url = params.toString() ? `/vehicles/?${params.toString()}` : '/vehicles/';
  const response = await api.get(url);
  return response.data;
};

export const getVehicleById = async (id: string) => {
  const response = await api.get(`/vehicles/${id}/`);
  return response.data;
};

export const createVehicle = async (vehicleData: any) => {
  const response = await api.post('/vehicles/', vehicleData);
  return response.data;
};

export const updateVehicle = async (id: string, vehicleData: any) => {
  const response = await api.put(`/vehicles/${id}/`, vehicleData);
  return response.data;
};

export const deleteVehicle = async (id: string) => {
  const response = await api.delete(`/vehicles/${id}/`);
  return response.data;
};

// Test Drives
export const getTestDrives = async () => {
  const response = await api.get('/test-drives/');
  return response.data;
};

export const createTestDrive = async (testDriveData: any) => {
  try {
    console.log('API: Creating test drive with data:', testDriveData);
    const response = await api.post('/test-drives/', testDriveData);
    console.log('API: Test drive created successfully:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('API: Error creating test drive:', error);
    console.error('API: Error response:', error.response?.data);
    throw error;
  }
};

export const updateTestDrive = async (id: string, data: any) => {
  const response = await api.put(`/test-drives/${id}/`, data);
  return response.data;
};

// Chat - Updated for CleverCompanion integration
export const getChatHistory = async () => {
  const response = await api.get('/chat-history/');
  return response.data;
};

export const sendChatMessage = async (message: string, sessionId: string, sender: 'user' | 'bot' = 'user') => {
  try {
    console.log('📤 Sending chat message to API:', { message, sessionId, sender });
    const response = await api.post('/chat/', {
      message,
      session_id: sessionId,
      sender
    });
    console.log('✅ Chat message API response:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('❌ Chat message API error:', error);
    console.error('Error response:', error.response?.data);
    throw error;
  }
};

// New function specifically for saving chat messages with sender info
export const saveChatMessage = async (message: string, sessionId: string, sender: 'user' | 'bot') => {
  return sendChatMessage(message, sessionId, sender);
};

// Feedback
export const getFeedback = async () => {
  const response = await api.get('/feedback/');
  return response.data;
};

export const createFeedback = async (feedbackData: any) => {
  const response = await api.post('/feedback/', feedbackData);
  return response.data;
};

// Knowledge Base
export const getKnowledgeBase = async () => {
  const response = await api.get('/knowledge-base/');
  return response.data;
};

export const createKnowledgeBase = async (data: any) => {
  const response = await api.post('/knowledge-base/', data);
  return response.data;
};

export const deleteKnowledgeBase = async (id: string) => {
  const response = await api.delete(`/knowledge-base/${id}/`);
  return response.data;
};

// Chatbot Settings
export const getChatbotSettings = async () => {
  const response = await api.get('/chatbot-settings/');
  return response.data;
};

export const createChatbotSetting = async (data: any) => {
  const response = await api.post('/chatbot-settings/', data);
  return response.data;
};

export const updateChatbotSetting = async (id: string, data: any) => {
  const response = await api.put(`/chatbot-settings/${id}/`, data);
  return response.data;
};

export const deleteChatbotSetting = async (id: string) => {
  const response = await api.delete(`/chatbot-settings/${id}/`);
  return response.data;
};

// Team Members
export const getTeamMembers = async () => {
  const response = await api.get('/team-members/');
  return response.data;
};

export const createTeamMember = async (data: any) => {
  const response = await api.post('/team-members/', data);
  return response.data;
};

export const updateTeamMember = async (id: string, data: any) => {
  const response = await api.put(`/team-members/${id}/`, data);
  return response.data;
};

export const deleteTeamMember = async (id: string) => {
  const response = await api.delete(`/team-members/${id}/`);
  return response.data;
};

// User Management
export const getUsers = async () => {
  const response = await api.get('/users/');
  return response.data;
};

export const createUser = async (userData: any) => {
  const response = await api.post('/users/', userData);
  return response.data;
};

export const updateUser = async (id: string, userData: any) => {
  const response = await api.put(`/users/${id}/`, userData);
  return response.data;
};

export const deleteUser = async (id: string) => {
  const response = await api.delete(`/users/${id}/`);
  return response.data;
};

// Analytics
export const getAnalytics = async (days?: number) => {
  const params = new URLSearchParams();
  if (days !== undefined) {
    params.append('days', String(days));
  }
  
  const url = params.toString() ? `/analytics/?${params.toString()}` : '/analytics/';
  const response = await api.get(url);
  return response.data;
};

// FAQ endpoints
export const getFAQs = async () => {
  const response = await api.get('/faq/');
  return response.data;
};

export const createFAQ = async (faqData: any) => {
  const response = await api.post('/faq/', faqData);
  return response.data;
};

export const updateFAQ = async (id: string, faqData: any) => {
  const response = await api.put(`/faq/${id}/`, faqData);
  return response.data;
};

export const deleteFAQ = async (id: string) => {
  const response = await api.delete(`/faq/${id}/`);
  return response.data;
};

// Contact info endpoints
export const getContactInfo = async () => {
  const response = await api.get('/contact-info/');
  return response.data;
};

export const createContactInfo = async (contactData: any) => {
  const response = await api.post('/contact-info/', contactData);
  return response.data;
};

export const updateContactInfo = async (id: string, contactData: any) => {
  const response = await api.put(`/contact-info/${id}/`, contactData);
  return response.data;
};

export const deleteContactInfo = async (id: string) => {
  const response = await api.delete(`/contact-info/${id}/`);
  return response.data;
};

export default api;