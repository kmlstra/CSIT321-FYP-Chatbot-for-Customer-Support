// API Configuration
// This file centralizes all API endpoint configurations with automatic environment detection

// Environment Detection
const isProduction = process.env.NODE_ENV === 'production';
const isDevelopment = process.env.NODE_ENV === 'development';
const envType = process.env.NEXT_PUBLIC_ENV || 'development';

// Base Domain Configuration with Environment Detection
const getBaseDomain = () => {
  // Check if we're in production build
  if (isProduction || envType === 'production') {
    return process.env.NEXT_PUBLIC_DOMAIN || 'http://54.254.180.103';
  }
  // Default to localhost for development
  return process.env.NEXT_PUBLIC_DOMAIN || 'http://localhost';
};

const DOMAIN = getBaseDomain();

// Port Configuration with Environment Detection
const getPorts = () => {
  if (isProduction || envType === 'production') {
    return {
      FRONTEND: process.env.NEXT_PUBLIC_FRONTEND_PORT || '80',
      BACKEND: process.env.NEXT_PUBLIC_BACKEND_PORT || '8000',
      RASA: process.env.NEXT_PUBLIC_RASA_PORT || '5005'
    };
  }
  return {
    FRONTEND: process.env.NEXT_PUBLIC_FRONTEND_PORT || '3000',
    BACKEND: process.env.NEXT_PUBLIC_BACKEND_PORT || '8000',
    RASA: process.env.NEXT_PUBLIC_RASA_PORT || '5005'
  };
};

const PORTS = getPorts();

// API Configuration with Environment-Aware URLs
export const API_CONFIG = {
  // Environment Info
  ENVIRONMENT: envType,
  IS_PRODUCTION: isProduction,
  IS_DEVELOPMENT: isDevelopment,
  
  // Base Domain
  DOMAIN: DOMAIN,
  
  // Backend API URL
  API_URL: process.env.NEXT_PUBLIC_API_URL || `${DOMAIN}:${PORTS.BACKEND}`,
  
  // RASA API URL
  RASA_URL: process.env.NEXT_PUBLIC_RASA_URL || `${DOMAIN}:${PORTS.RASA}`,
  
  // Widget URL
  WIDGET_URL: process.env.NEXT_PUBLIC_WIDGET_URL || (isProduction ? DOMAIN : `${DOMAIN}:${PORTS.FRONTEND}`),
  
  // Frontend URL
  FRONTEND_URL: process.env.NEXT_PUBLIC_FRONTEND_URL || (isProduction ? DOMAIN : `${DOMAIN}:${PORTS.FRONTEND}`),
  
  // Backend URL
  BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || `${DOMAIN}:${PORTS.BACKEND}`,
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