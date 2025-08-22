// API Configuration
// This file centralizes all API endpoint configurations with automatic environment detection

// Hardcoded AWS IP configuration - 硬编码的AWS配置
// 移除环境检测逻辑，直接使用AWS服务器IP地址
const DOMAIN = 'http://13.215.240.173';
const PORTS = {
  FRONTEND: 3000,
  BACKEND: 8000,
  RASA: 5005
};

// API Configuration - 硬编码的API配置
export const API_CONFIG = {
  DOMAIN: 'http://13.215.240.173',
  API_URL: 'http://13.215.240.173:8000',
  RASA_URL: 'http://13.215.240.173:5005',
  WIDGET_URL: 'http://13.215.240.173:3000',
  FRONTEND_URL: 'http://13.215.240.173:3000',
  BACKEND_URL: 'http://13.215.240.173:8000',
  PORTS
};

// Debug logging for development removed
// API Configuration available in API_CONFIG object

// API Endpoints
export const API_ENDPOINTS = {
  // Authentication
  CLIENT_LOGIN: `${API_CONFIG.API_URL}/api/auth/client-login`,
  SUPER_ADMIN_LOGIN: `${API_CONFIG.API_URL}/api/auth/super-admin-login`,
  
  // Client Management
  CLIENT_CONVERSATIONS: (clientId: string) => `${API_CONFIG.API_URL}/api/unified/conversations/client/${clientId}`,
  CLIENT_OPERATING_HOURS: `${API_CONFIG.API_URL}/api/client/operating-hours`,
  CLIENT_DATABASE_STATUS: `${API_CONFIG.API_URL}/api/client/database/status`,
  CLIENT_VEHICLES: `${API_CONFIG.API_URL}/api/client/vehicles`,
  CLIENT_BRANDING: `${API_CONFIG.API_URL}/api/client/branding`,
  CLIENT_CONTACT_INFO: `${API_CONFIG.API_URL}/api/client/contact-info`,
  CLIENT_FEATURES: `${API_CONFIG.API_URL}/api/client/features`,
  CLIENT_DATABASE_TEST: `${API_CONFIG.API_URL}/api/client/database/test-connection`,
  CLIENT_DATABASE_SAVE: `${API_CONFIG.API_URL}/api/client/database/save-connection`,
  CLIENT_DATABASE_SYNC: `${API_CONFIG.API_URL}/api/client/database/sync-data`,
  
  // Appointments
  APPOINTMENTS: `${API_CONFIG.API_URL}/api/appointments/`,
  APPOINTMENT_STATUS: (id: string) => `${API_CONFIG.API_URL}/api/appointments/${id}/status`,
  
  // Super Admin
  SUPER_ADMIN_CLIENTS: `${API_CONFIG.API_URL}/api/super-admin/clients`,
  SUPER_ADMIN_METRICS: `${API_CONFIG.API_URL}/api/super-admin/metrics`,
  SUPER_ADMIN_CLIENT_ACTION: (clientId: string, endpoint: string) => 
    `${API_CONFIG.API_URL}/api/super-admin/clients/${clientId}/${endpoint}`,
  
  // Client Registration
  CLIENT_REGISTRATION: `${API_CONFIG.API_URL}/api/client-registration/register`,
  
  // Widget
  WIDGET_API: `${API_CONFIG.API_URL}/api/widget`,
  WIDGET_CONFIG: (clientId: string) => `${API_CONFIG.API_URL}/api/widget/config/${clientId}`,
  
  // RASA
  RASA_WEBHOOK: `${API_CONFIG.RASA_URL}/webhooks/rest/webhook`,
  
  // Chat
  CHAT: `${API_CONFIG.API_URL}/api/chat`,
  
  // Conversation History
  CONVERSATION_HISTORY: (conversationId: string) => `${API_CONFIG.API_URL}/api/conversation/history/${conversationId}`,
  CONVERSATION_DETAILS: (conversationId: string) => `${API_CONFIG.API_URL}/api/unified/conversations/${conversationId}/history`,
  CONVERSATION_STATS: `${API_CONFIG.API_URL}/api/conversation/stats`,
};

// Widget Configuration
export const WIDGET_CONFIG = {
  SCRIPT_URL: `${API_CONFIG.WIDGET_URL}/clevercompanion-widget.js`,
  API_URL: API_ENDPOINTS.WIDGET_API,
};

// Helper function to get authorization headers
export const getAuthHeaders = () => {
  const token = localStorage.getItem('client_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

// Helper function to get super admin authorization headers
export const getSuperAdminAuthHeaders = () => {
  const token = localStorage.getItem('super_admin_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};