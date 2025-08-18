'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { API_ENDPOINTS, API_CONFIG, getAuthHeaders } from '@/config/api';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';

function formatToSGTime(timestamp: string) {
  const d = new Date(timestamp); // UTC time
  const sg = new Date(d.getTime() + 8 * 60 * 60 * 1000); // UTC+8 offset

  const hours = sg.getUTCHours();
  const minutes = sg.getUTCMinutes();
  const hour12 = hours % 12 === 0 ? 12 : hours % 12;
  const ampm = hours >= 12 ? 'PM' : 'AM';

  return `${hour12.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')} ${ampm}`;
}

interface DatabaseConfig {
  db_type: string;
  connection_string: string;
  database_name: string;
  collection_name: string;
  chat_collection_name: string;
  additional_collections: string;
  field_mapping: {
    brand: string;
    model: string;
    year: string;
    price: string;
    availability: string;
  };
}

interface Vehicle {
  id: string;
  brand: string;
  model: string;
  year: number;
  price: number;
  availability: string;
  raw_data: Record<string, unknown>;
}

interface ChatConversation {
  _id: string;
  customer_name: string;
  messages: number | any[];
  status: string;
  last_message: string;
  created_at: string;
  total_messages?: number;
  updated_at?: string;
  error?: string;
  timestamp?: string;
  message_count?: number;
  conversation_id?: string;
}

interface BrandingConfig {
  company_name: string;
  primary_color: string;
  secondary_color: string;
  logo_url: string;
}

interface ContactInfo {
  phone: string;
  email: string;
  whatsapp: string;
  address: string;
}

interface DayHours {
  open: string;
  close: string;
  closed: boolean;
}

interface OperatingHours {
  monday: DayHours;
  tuesday: DayHours;
  wednesday: DayHours;
  thursday: DayHours;
  friday: DayHours;
  saturday: DayHours;
  sunday: DayHours;
  public_holidays: DayHours;
}

interface Appointment {
  _id: string;
  appointment_id: string;
  customer_name: string;
  customer_phone: string;
  customer_email?: string;
  service_type: string;
  appointment_datetime: string;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export default function ClientDashboard() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [userData, setUserData] = useState<Record<string, unknown> | null>(null);
  const [clientData, setClientData] = useState<Record<string, unknown> | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [clientId, setClientId] = useState<string>('');
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [chatHistory, setChatHistory] = useState<ChatConversation[]>([]);
  const [filteredChatHistory, setFilteredChatHistory] = useState<ChatConversation[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedConversation, setSelectedConversation] = useState<ChatConversation | null>(null);
  const [showConversationModal, setShowConversationModal] = useState(false);
  
  // Appointment management state
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [filteredAppointments, setFilteredAppointments] = useState<Appointment[]>([]);
  const [appointmentSearchTerm, setAppointmentSearchTerm] = useState('');

  const [updatingAppointmentStatus, setUpdatingAppointmentStatus] = useState<string | null>(null);
  
  // Loading states for different sections
  const [loadingStates, setLoadingStates] = useState({
    vehicles: true,
    appointments: true,
    chatHistory: true,
    dbStatus: true,
    clientInfo: true
  });
  
  // Pagination state for appointments
  const [appointmentCurrentPage, setAppointmentCurrentPage] = useState(1);
  const appointmentItemsPerPage = 20;
  
  // Pagination state for chat history
  const [chatCurrentPage, setChatCurrentPage] = useState(1);
  const chatItemsPerPage = 20;
  
  // Features configuration state
  const [features, setFeatures] = useState({
    coe_prices: true,
    loan_calculator: true,
    appointment_booking: false,  // Default to false, enable based on client configuration
    maintenance_tips: true,
    vehicle_search: true,
    live_support: true
    // business_hours removed as it's now a mandatory function
    // contact_support removed as it's now a core feature, not configurable
  });
  
  const [dbConfig, setDbConfig] = useState<DatabaseConfig>({
    db_type: 'MongoDB',
    connection_string: '',
    database_name: '',
    collection_name: '',
    chat_collection_name: 'chat_history',
    additional_collections: '',
    field_mapping: {
      brand: 'brand',
      model: 'model',
      year: 'year',
      price: 'price',
      availability: 'status'
    }
  });

  const [branding, setBranding] = useState<BrandingConfig>({
    company_name: '',
    primary_color: '#4F46E5',
    secondary_color: '#7C3AED',
    logo_url: ''
  });

  const [contactInfo, setContactInfo] = useState<ContactInfo>({
    phone: '',
    email: '',
    whatsapp: '',
    address: ''
  });

  // Auto-set WhatsApp to phone number when phone changes
  useEffect(() => {
    if (contactInfo.phone && !contactInfo.whatsapp) {
      setContactInfo(prev => ({ ...prev, whatsapp: prev.phone }));
    }
  }, [contactInfo.phone, contactInfo.whatsapp]);

  // Set email from user data when component loads
  useEffect(() => {
    if (userData && userData.email && !contactInfo.email) {
      setContactInfo(prev => ({ ...prev, email: userData.email as string }));
    }
  }, [userData, contactInfo.email]);

  const [operatingHours, setOperatingHours] = useState<OperatingHours>({
    monday: { open: '09:00', close: '18:00', closed: false },
    tuesday: { open: '09:00', close: '18:00', closed: false },
    wednesday: { open: '09:00', close: '18:00', closed: false },
    thursday: { open: '09:00', close: '18:00', closed: false },
    friday: { open: '09:00', close: '18:00', closed: false },
    saturday: { open: '09:00', close: '14:00', closed: false },
    sunday: { open: '10:00', close: '16:00', closed: true },
    public_holidays: { open: '10:00', close: '16:00', closed: true }
  });

  // Analytics state
  const [analyticsPeriod, setAnalyticsPeriod] = useState<'daily' | 'weekly' | 'monthly'>('daily');

  // Colors for charts
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

  const [dbStatus, setDbStatus] = useState({
    connected: false,
    db_type: null,
    database_name: null,
    collection_name: null,
    last_sync: null,
    record_count: 0
  });

  // Custom alert/toast notification state
  const [alerts, setAlerts] = useState<Array<{
    id: string;
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
    duration?: number;
  }>>([]);

  // Removed activeSessionsCount - no longer needed

  // Cancel appointment confirmation modal state
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [appointmentToCancel, setAppointmentToCancel] = useState<string | null>(null);

  // Custom alert function to replace browser alerts
  const showAlert = (message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info', duration: number = 5000) => {
    const id = Date.now().toString();
    const newAlert = { id, message, type, duration };
    setAlerts(prev => [...prev, newAlert]);
    
    if (duration > 0) {
      setTimeout(() => {
        setAlerts(prev => prev.filter(alert => alert.id !== id));
      }, duration);
    }
  };

  // Remove alert function
  const removeAlert = (id: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== id));
  };

  // Handle cancel appointment confirmation
  const handleCancelAppointment = (appointmentId: string) => {
    setAppointmentToCancel(appointmentId);
    setCancelModalOpen(true);
  };

  // Confirm cancel appointment
  const confirmCancelAppointment = async () => {
    if (appointmentToCancel) {
      await updateAppointmentStatus(appointmentToCancel, 'cancelled');
      setCancelModalOpen(false);
      setAppointmentToCancel(null);
    }
  };

  // Close cancel modal
  const closeCancelModal = () => {
    setCancelModalOpen(false);
    setAppointmentToCancel(null);
  };

  // Authentication functions
  const handleLogout = useCallback(() => {
    localStorage.removeItem('client_token');
    localStorage.removeItem('user_data');
    localStorage.removeItem('client_data');
    setIsAuthenticated(false);
    setUserData(null);
    setClientData(null);
    router.push('/');
  }, [router]);

  const checkAuthentication = useCallback(() => {
    const token = localStorage.getItem('client_token');
    const storedUserData = localStorage.getItem('user_data');
    const storedClientData = localStorage.getItem('client_data');
    
    if (!token || !storedUserData || !storedClientData) {
      router.push('/');
      return false;
    }
    
    try {
      setUserData(JSON.parse(storedUserData));
      setClientData(JSON.parse(storedClientData));
      setIsAuthenticated(true);
      setIsLoading(false);
      return true;
    } catch (error) {
      console.error('Error parsing stored data:', error);
      handleLogout();
      return false;
    }
  }, [router, handleLogout]);


  const fetchChatHistory = useCallback(async () => {
    try {
      setLoadingStates(prev => ({ ...prev, chatHistory: true }));
      const token = localStorage.getItem('client_token');
      if (!token) {
        return;
      }
      
      // Get client_id from stored client data
      const storedClientData = localStorage.getItem('client_data');
      if (!storedClientData) {
        console.error('Client data not found in localStorage');
        return;
      }
      
      const clientData = JSON.parse(storedClientData);
      const clientId = clientData.id;
      if (!clientId) {
        console.error('Client ID not found in client data');
        return;
      }
      
      // Use new unified API endpoint
      const response = await fetch(`${API_CONFIG.API_URL}/api/unified/conversations/client/${clientId}`, {
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const data = await response.json();
        // Transform backend data structure to match frontend expectations
        const transformedConversations = (data.conversations || []).map((conv: any) => ({
          _id: conv.conversation_id || conv._id,
          customer_name: `Customer ${conv.conversation_id?.slice(-8) || 'Unknown'}`, // Generate customer name from conversation ID
          messages: conv.message_count || 0,
          status: conv.status || 'active',
          last_message: `${conv.message_count || 0} messages`, // Show message count as last message info
          created_at: conv.first_message_at || new Date().toISOString(),
          updated_at: conv.last_message_at || new Date().toISOString(),
          total_messages: conv.message_count || 0,
          conversation_id: conv.conversation_id,
          session_id: conv.session_id
        }));
        
        setChatHistory(transformedConversations);
        setFilteredChatHistory(transformedConversations);
      } else {
        console.error('Failed to fetch chat history:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Failed to fetch chat history:', error);
    } finally {
      setLoadingStates(prev => ({ ...prev, chatHistory: false }));
    }
  }, []);

  // Background cache refresh function
  const refreshCacheInBackground = useCallback(async () => {
    try {
      const storedClientData = localStorage.getItem('client_data');
      if (storedClientData) {
        const clientData = JSON.parse(storedClientData);
        const clientId = clientData.id;
        if (clientId) {
          // Silently refresh cache without affecting UI
          await fetch(`${API_CONFIG.API_URL}/cache/warm/${clientId}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            }
          });
          // Background cache refresh completed
        }
      }
    } catch (error) {
      console.warn('Background cache refresh failed:', error);
    }
  }, []);

  // Authentication check on component mount with parallel data loading
  useEffect(() => {
    if (checkAuthentication()) {
      // Load all data in parallel for better performance
      Promise.allSettled([
        fetchClientInfo(),
        fetchDatabaseStatus(),
        fetchVehicles(),
        fetchAppointments(),
        fetchOperatingHours()
      ]).then((results) => {
        // Log any failed requests for debugging
        results.forEach((result, index) => {
          if (result.status === 'rejected') {
            const functionNames = ['fetchClientInfo', 'fetchDatabaseStatus', 'fetchVehicles', 'fetchAppointments', 'fetchOperatingHours'];
            console.warn(`${functionNames[index]} failed:`, result.reason);
          }
        });
        // Dashboard data loading completed
      });

      // Set up background cache refresh every 25 minutes (before 30-minute TTL expires)
      const cacheRefreshInterval = setInterval(refreshCacheInBackground, 25 * 60 * 1000);
      
      // Cleanup interval on component unmount
      return () => {
        clearInterval(cacheRefreshInterval);
      };
    }
  }, [checkAuthentication, refreshCacheInBackground]);

  const fetchOperatingHours = async () => {
    try {
      const token = localStorage.getItem('client_token');
      if (!token) {
        return;
      }
      
      const response = await fetch(API_ENDPOINTS.CLIENT_OPERATING_HOURS, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const data = await response.json();
        if (data.operating_hours) {
          setOperatingHours(data.operating_hours);
        }
      } else {
        console.error('Failed to fetch operating hours:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Failed to fetch operating hours:', error);
    }
  };

  // Fetch chat history when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchChatHistory();
    }
  }, [isAuthenticated, fetchChatHistory]);

  useEffect(() => {
    // Filter chat history based on search term (including conversation_id)
    if (searchTerm.trim() === '') {
      setFilteredChatHistory(chatHistory);
    } else {
      const filtered = chatHistory.filter(conv => 
        conv.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        conv._id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        conv.status?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        conv.last_message?.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredChatHistory(filtered);
    }
  }, [searchTerm, chatHistory]);

  useEffect(() => {
    // Filter appointments based on search term
    let filtered = appointments;
    
    if (appointmentSearchTerm.trim() !== '') {
      filtered = filtered.filter(apt => 
        apt.customer_name?.toLowerCase().includes(appointmentSearchTerm.toLowerCase()) ||
        apt.customer_phone?.toLowerCase().includes(appointmentSearchTerm.toLowerCase()) ||
        apt.appointment_id?.toLowerCase().includes(appointmentSearchTerm.toLowerCase()) ||
        apt.service_type?.toLowerCase().includes(appointmentSearchTerm.toLowerCase())
      );
    }
    
    setFilteredAppointments(filtered);
  }, [appointmentSearchTerm, appointments]);

  const fetchDatabaseStatus = async () => {
    try {
      setLoadingStates(prev => ({ ...prev, dbStatus: true }));
      const token = localStorage.getItem('client_token');
      if (!token) {
        return;
      }
      
      const response = await fetch(API_ENDPOINTS.CLIENT_DATABASE_STATUS, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const status = await response.json();
        setDbStatus(status);
        setIsConnected(status.connected);
      } else {
        console.error('Failed to fetch database status:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Failed to fetch database status:', error);
    } finally {
      setLoadingStates(prev => ({ ...prev, dbStatus: false }));
    }
  };

  const fetchVehicles = async () => {
    try {
      setLoadingStates(prev => ({ ...prev, vehicles: true }));
      const token = localStorage.getItem('client_token');
      if (!token) {
        return;
      }
      
      const response = await fetch(API_ENDPOINTS.CLIENT_VEHICLES, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const data = await response.json();
        setVehicles(data.vehicles || []);

      } else {
        console.error('Failed to fetch vehicles:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Failed to fetch vehicles:', error);
    } finally {
      setLoadingStates(prev => ({ ...prev, vehicles: false }));
    }
  };

  const fetchAppointments = async () => {
    try {
      setLoadingStates(prev => ({ ...prev, appointments: true }));
      const token = localStorage.getItem('client_token');
      if (!token) {
        return;
      }
      
      const response = await fetch(API_ENDPOINTS.APPOINTMENTS, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const data = await response.json();
        
        // Process appointments to ensure consistent field naming
        const processedAppointments = (data.appointments || []).map((appointment: any) => {
          // Ensure appointment_id is available - use _id as fallback if appointment_id is missing
          if (!appointment.appointment_id && appointment._id) {
            appointment.appointment_id = appointment._id;
          }
          
          return appointment;
        });
        setAppointments(processedAppointments);
        setFilteredAppointments(processedAppointments);

      } else {
        console.error('Failed to fetch appointments:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Failed to fetch appointments:', error);
    } finally {
      setLoadingStates(prev => ({ ...prev, appointments: false }));
    }
  };

  // Fetch active sessions count from backend API
  // Removed fetchActiveSessionsCount function - no longer needed

  const updateAppointmentStatus = async (appointmentId: string, newStatus: string) => {
    try {
      setUpdatingAppointmentStatus(appointmentId);
      const token = localStorage.getItem('client_token');
      if (!token) {
        showAlert('Authentication token not found. Please login again.', 'error');
        return;
      }
      
      const response = await fetch(API_ENDPOINTS.APPOINTMENT_STATUS(appointmentId), {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ status: newStatus })
      });
      
      if (response.ok) {
        // Refresh appointments after successful update
        await fetchAppointments();
        showAlert(`Appointment status updated to ${newStatus}`, 'success');
      } else {
        const error = await response.json();
        showAlert(`Failed to update appointment: ${error.error}`, 'error');
      }
    } catch (error) {
      console.error('Failed to update appointment status:', error);
      showAlert('Failed to update appointment status', 'error');
    } finally {
      setUpdatingAppointmentStatus(null);
    }
  };

  const testConnection = async () => {
    try {
      const token = localStorage.getItem('client_token');
      if (!token) {
        showAlert('Authentication token not found. Please login again.', 'error');
        return;
      }
      
      const response = await fetch(API_ENDPOINTS.CLIENT_DATABASE_TEST, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(dbConfig)
      });
      
      const result = await response.json();
      showAlert(result.message, result.success ? 'success' : 'error');
      // Test connection completed
    } catch (error) {
      showAlert('Connection test failed', 'error');
      console.error('Test error:', error);
    }
  };

  const saveConfiguration = async () => {
    try {
      const token = localStorage.getItem('client_token');
      if (!token) {
        showAlert('Authentication token not found. Please login again.', 'error');
        return;
      }
      
      const response = await fetch(API_ENDPOINTS.CLIENT_DATABASE_SAVE, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(dbConfig)
      });
      
      const result = await response.json();
      if (result.success) {
        setIsConnected(true);
        await fetchDatabaseStatus();
        showAlert('Configuration saved successfully!', 'success');
      } else {
        showAlert(result.message, 'error');
      }
    } catch (error) {
      showAlert('Failed to save configuration', 'error');
      console.error('Save error:', error);
    }
  };

  const syncData = async () => {
    try {
      const token = localStorage.getItem('client_token');
      if (!token) {
        showAlert('Authentication token not found. Please login again.', 'error');
        return;
      }
      
      const response = await fetch(API_ENDPOINTS.CLIENT_DATABASE_SYNC, {
        method: 'POST',
        headers: getAuthHeaders()
      });
      
      const result = await response.json();
      if (result.success) {
        await fetchVehicles();
        await fetchChatHistory();
        await fetchDatabaseStatus();
        showAlert(result.message, 'success');
      } else {
        showAlert(result.message, 'error');
      }
    } catch (error) {
      showAlert('Data sync failed', 'error');
      console.error('Sync error:', error);
    }
  };

  const saveBranding = async () => {
    try {
      const token = localStorage.getItem('client_token');
      if (!token) {
        showAlert('Authentication token not found. Please login again.', 'error');
        return;
      }
      
      const response = await fetch(API_ENDPOINTS.CLIENT_BRANDING, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(branding)
      });
      
      if (response.ok) {
        showAlert('Branding saved successfully!', 'success');
      } else {
        showAlert('Failed to save branding', 'error');
      }
    } catch (error) {
      showAlert('Failed to save branding', 'error');
      console.error('Branding save error:', error);
    }
  };

  const saveContactInfo = async () => {
    try {
      const token = localStorage.getItem('client_token');
      if (!token) {
        showAlert('Authentication token not found. Please login again.', 'error');
        return;
      }
      
      const response = await fetch(API_ENDPOINTS.CLIENT_CONTACT_INFO, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(contactInfo)
      });
      
      if (response.ok) {
        showAlert('Contact information saved successfully!', 'success');
      } else {
        showAlert('Failed to save contact information', 'error');
      }
    } catch (error) {
      showAlert('Failed to save contact information', 'error');
      console.error('Contact save error:', error);
    }
  };

  const saveFeatures = async () => {
    try {
      const token = localStorage.getItem('client_token');
      if (!token) {
        showAlert('Authentication token not found. Please login again.', 'error');
        return;
      }
      
      const response = await fetch(API_ENDPOINTS.CLIENT_FEATURES, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(features)
      });
      
      if (response.ok) {
        showAlert('Features configuration saved successfully!', 'success');
      } else {
        showAlert('Failed to save features configuration', 'error');
      }
    } catch (error) {
      showAlert('Failed to save features configuration', 'error');
      console.error('Features save error:', error);
    }
  };

  const saveOperatingHours = async () => {
    try {
      const token = localStorage.getItem('client_token');
      if (!token) {
        showAlert('Authentication token not found. Please login again.', 'error');
        return;
      }
      
      const response = await fetch(API_ENDPOINTS.CLIENT_OPERATING_HOURS, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ operating_hours: operatingHours })
      });
      
      if (response.ok) {
        showAlert('Operating hours saved successfully!', 'success');
      } else {
        showAlert('Failed to save operating hours', 'error');
      }
    } catch (error) {
      showAlert('Failed to save operating hours', 'error');
      console.error('Operating hours save error:', error);
    }
  };

  const viewConversationDetails = async (conversation: ChatConversation) => {
    try {
      // First set the basic conversation data
      setSelectedConversation(conversation);
      setShowConversationModal(true);
      
      // Then fetch detailed conversation messages
      const conversationId = conversation._id;
      if (conversationId) {
        const response = await fetch(API_ENDPOINTS.CONVERSATION_DETAILS(conversationId), {
          headers: getAuthHeaders()
        });
        
        if (response.ok) {
          const data = await response.json();
          // Conversation details response received
          
          // Update the conversation with detailed messages
          if (data.success && data.messages) {
            // Get messages array directly from data and use the role field directly
            const messages = Array.isArray(data.messages) ? data.messages : [];
            
            // Update the selected conversation with messages
            setSelectedConversation({
              ...conversation,
              messages: messages,
              total_messages: data.total_messages || messages.length,
              conversation_id: data.conversation_id
            });
          } else {
            console.warn('No detailed conversation data found for ID:', conversationId);
            // Keep the original conversation but add empty messages array
            setSelectedConversation({
              ...conversation,
              messages: [],
              error: 'No detailed messages found for this conversation'
            });
          }
        } else {
          console.error('Failed to fetch conversation details:', response.status, response.statusText);
          setSelectedConversation({
            ...conversation,
            messages: [],
            error: `Failed to load conversation details (${response.status})`
          });
        }
      } else {
        console.warn('No conversation ID available for fetching details');
        setSelectedConversation({
          ...conversation,
          messages: [],
          error: 'No conversation ID available'
        });
      }
    } catch (error) {
      console.error('Error fetching conversation details:', error);
      setSelectedConversation({
        ...conversation,
        messages: [],
        error: 'Error loading conversation details'
      });
    }
  };

  const fetchClientInfo = async () => {
    try {
      setLoadingStates(prev => ({ ...prev, clientInfo: true }));
      // Get client ID from stored client_data
      const storedClientData = localStorage.getItem('client_data');
      if (storedClientData) {
        const clientData = JSON.parse(storedClientData);
        // Client data stored successfully
        const clientId = clientData.id;
        if (clientId) {
          setClientId(clientId);
          // Fetch all client configuration data in parallel for better performance
          await Promise.allSettled([
            fetchClientBranding(),
            fetchClientContactInfo(),
            fetchClientFeatures()
          ]).then((results) => {
            // Log any failed requests for debugging
            results.forEach((result, index) => {
              if (result.status === 'rejected') {
                const functionNames = ['fetchClientBranding', 'fetchClientContactInfo', 'fetchClientFeatures'];
                console.warn(`${functionNames[index]} failed:`, result.reason);
              }
            });
          });
          return;
        }
      }
      
      console.error('No client data found in localStorage');
      // Don't set fallback - this indicates a real problem
    } catch (error) {
      console.error('Failed to fetch client info:', error);
    } finally {
      setLoadingStates(prev => ({ ...prev, clientInfo: false }));
    }
  };

  const fetchClientBranding = async () => {
    try {
      const token = localStorage.getItem('client_token');
      if (!token) {
        return;
      }
      
      const response = await fetch(API_ENDPOINTS.CLIENT_BRANDING, {
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.branding) {
          setBranding(data.branding);

        }
      } else {
        console.error('Failed to fetch branding:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Failed to fetch branding:', error);
    }
  };

  const fetchClientContactInfo = async () => {
    try {
      const token = localStorage.getItem('client_token');
      if (!token) {
        return;
      }
      
      const response = await fetch(API_ENDPOINTS.CLIENT_CONTACT_INFO, {
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.contact_info) {
          setContactInfo(data.contact_info);

        }
      } else {
        console.error('Failed to fetch contact info:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Failed to fetch contact info:', error);
    }
  };

  const fetchClientFeatures = async () => {
    try {
      const token = localStorage.getItem('client_token');
      if (!token) {
        return;
      }
      
      const response = await fetch(API_ENDPOINTS.CLIENT_FEATURES, {
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.features) {
          setFeatures(data.features);

        }
      } else {
        console.error('Failed to fetch features:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Failed to fetch features:', error);
    }
  };

  const copyEmbedCode = () => {
    if (!clientId) {
      showAlert('Client ID not available. Please refresh the page and try again.', 'error');
      return;
    }
    
    const embedCode = `<!-- CleverCompanion Chatbot Widget -->
<script async>window.CleverCompanionConfig = { clientId: '${clientId}' };</script>
<script async>
    window.DOMAIN = window.DOMAIN || 'http://localhost';
    // Dynamically load scripts with domain configuration and cache-busting
    const timestamp = Date.now();
    const script1 = document.createElement('script');
    script1.src = (window.DOMAIN || 'http://localhost') + ':8000/clevercompanion-widget.js?v=' + timestamp;
    script1.async = true;
    document.head.appendChild(script1);
    
    const script2 = document.createElement('script');
    script2.src = (window.DOMAIN || 'http://localhost') + ':8000/page-interactions.js?v=' + timestamp;
    script2.async = true;
    document.head.appendChild(script2);
</script>
<!-- End CleverCompanion Widget -->`;

    navigator.clipboard.writeText(embedCode).then(() => {
      showAlert('Updated embed code copied to clipboard! The widget will automatically load your branding and settings with dynamic domain configuration.', 'success');
    }).catch(() => {
      showAlert('Failed to copy embed code', 'error');
    });
  };

  const getFeatureDescription = (feature: string): string => {
    const descriptions = {
      coe_prices: 'Real-time COE prices and predictions',
      loan_calculator: 'Vehicle loan calculation and financing options',
      appointment_booking: 'Schedule appointments and test drives',
      maintenance_tips: 'Vehicle maintenance guides and tips',
      vehicle_search: 'Search and browse vehicle inventory',
      live_support: 'Live chat support and assistance'
      // business_hours removed as it's now a mandatory function
      // contact_support removed as it's now a core feature, not configurable
    };
    return descriptions[feature as keyof typeof descriptions] || 'Feature description';
  };

  // Analytics helper functions
  const getAnalyticsData = (type: 'conversations' | 'appointments' | 'daily_users') => {
    const now = new Date();
    const data = [];

    if (analyticsPeriod === 'daily') {
      // Generate data for last 7 days
      for (let i = 6; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        // Ensure consistent date formatting - Fixed for proper 17th date display
        const dateStr = date.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric' 
        });
        
        if (type === 'conversations') {
          const count = chatHistory.filter(conv => {
            const convDate = new Date(conv.created_at || conv.timestamp || new Date());
            return convDate.toDateString() === date.toDateString();
          }).length;
          data.push({ period: dateStr, count });
        } else if (type === 'appointments') {
          const dayAppointments = appointments.filter(apt => {
            const aptDate = new Date(apt.created_at);
            return aptDate.toDateString() === date.toDateString();
          });
          data.push({
            period: dateStr,
            booked: dayAppointments.length,
            completed: dayAppointments.filter(apt => apt.status === 'completed').length,
            cancelled: dayAppointments.filter(apt => apt.status === 'cancelled').length
          });
        } else if (type === 'daily_users') {
          // Calculate unique daily users based on actual chat history
          const dayUsers = chatHistory.filter(conv => {
            const convDate = new Date(conv.created_at || conv.timestamp || new Date());
            return convDate.toDateString() === date.toDateString();
          });
          // Count unique users by customer_name
          const uniqueCustomers = new Set(dayUsers.map(conv => conv.customer_name));
          const uniqueUsers = uniqueCustomers.size;
          data.push({ period: dateStr, users: uniqueUsers });
        }
      }
    } else if (analyticsPeriod === 'weekly') {
      // Generate data for last 4 weeks
      for (let i = 3; i >= 0; i--) {
        const weekStart = new Date(now);
        weekStart.setDate(weekStart.getDate() - (weekStart.getDay() + 7 * i));
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);
        const weekStr = `Week ${weekStart.getDate()}/${weekStart.getMonth() + 1}`;
        
        if (type === 'conversations') {
          const count = chatHistory.filter(conv => {
            const convDate = new Date(conv.created_at || conv.timestamp || new Date());
            return convDate >= weekStart && convDate <= weekEnd;
          }).length;
          data.push({ period: weekStr, count });
        } else if (type === 'appointments') {
          const weekAppointments = appointments.filter(apt => {
            const aptDate = new Date(apt.created_at);
            return aptDate >= weekStart && aptDate <= weekEnd;
          });
          data.push({
            period: weekStr,
            booked: weekAppointments.length,
            completed: weekAppointments.filter(apt => apt.status === 'completed').length,
            cancelled: weekAppointments.filter(apt => apt.status === 'cancelled').length
          });
        } else if (type === 'daily_users') {
          const weekUsers = chatHistory.filter(conv => {
            const convDate = new Date(conv.created_at || conv.timestamp || new Date());
            return convDate >= weekStart && convDate <= weekEnd;
          });
          // Count unique users by customer_name for the week
          const uniqueCustomers = new Set(weekUsers.map(conv => conv.customer_name));
          const uniqueUsers = uniqueCustomers.size;
          data.push({ period: weekStr, users: uniqueUsers });
        }
      }
    } else if (analyticsPeriod === 'monthly') {
      // Generate data for last 6 months
      for (let i = 5; i >= 0; i--) {
        const monthDate = new Date(now);
        monthDate.setMonth(monthDate.getMonth() - i);
        // Ensure consistent month formatting - Fixed for proper date display
        const monthStr = monthDate.toLocaleDateString('en-US', { 
          month: 'short', 
          year: '2-digit' 
        });
        
        if (type === 'conversations') {
          const count = chatHistory.filter(conv => {
            const convDate = new Date(conv.created_at || conv.timestamp || new Date());
            return convDate.getMonth() === monthDate.getMonth() && 
                   convDate.getFullYear() === monthDate.getFullYear();
          }).length;
          data.push({ period: monthStr, count });
        } else if (type === 'appointments') {
          const monthAppointments = appointments.filter(apt => {
            const aptDate = new Date(apt.created_at);
            return aptDate.getMonth() === monthDate.getMonth() && 
                   aptDate.getFullYear() === monthDate.getFullYear();
          });
          data.push({
            period: monthStr,
            booked: monthAppointments.length,
            completed: monthAppointments.filter(apt => apt.status === 'completed').length,
            cancelled: monthAppointments.filter(apt => apt.status === 'cancelled').length
          });
        } else if (type === 'daily_users') {
          const monthUsers = chatHistory.filter(conv => {
            const convDate = new Date(conv.created_at || conv.timestamp || new Date());
            return convDate.getMonth() === monthDate.getMonth() && 
                   convDate.getFullYear() === monthDate.getFullYear();
          });
          // Count unique users by customer_name for the month
          const uniqueCustomers = new Set(monthUsers.map(conv => conv.customer_name));
          const uniqueUsers = uniqueCustomers.size;
          data.push({ period: monthStr, users: uniqueUsers });
        }
      }
    }

    return data;
  };

  // Removed getActiveUsersData function as requested - Active Users graph no longer needed

  // Calculate analytics from real data
  const availableVehicles = vehicles.filter(v => 
    v.availability?.toLowerCase() === 'available' || 
    v.availability?.toLowerCase() === 'in stock' ||
    v.availability?.toLowerCase() === 'in_stock'
  ).length;

  const averagePrice = vehicles.length > 0 
    ? Math.round(vehicles.reduce((sum, v) => sum + (v.price || 0), 0) / vehicles.length)
    : 0;

  // Check if profile is complete
  const isProfileComplete = () => {
    return branding.company_name && 
           branding.primary_color && 
           contactInfo.phone && 
           contactInfo.email && 
           Object.values(operatingHours).some(hours => !hours.closed);
  };

  const tabs = [
    { id: 'overview', name: '📊 Overview', icon: '📊' },
    { id: 'profile', name: '👤 Profile', icon: '👤' },
    { id: 'features', name: '⚙️ Features', icon: '⚙️' },
    { id: 'chat-history', name: '💬 Chat History', icon: '💬' },
    { id: 'appointments', name: '📅 Appointments', icon: '📅' },
    { id: 'appointment-history', name: '📋 Appointment History', icon: '📋' },
    { id: 'embed', name: '📋 Embed Code', icon: '📋' }
    // Hidden sections as requested:
    // { id: 'database', name: '🗄️ Database', icon: '🗄️' },
    // { id: 'inventory', name: '🚗 Inventory', icon: '🚗' },
    // { id: 'analytics', name: '📈 Analytics', icon: '📈' } - Merged into overview
  ];

  // Show loading screen while checking authentication
  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4 animate-pulse">
            <span className="text-white text-2xl">🚗</span>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading Dashboard...</h2>
          <p className="text-gray-600">Verifying your authentication</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-white shadow-lg border-r transition-all duration-300 flex flex-col`}>
        {/* Sidebar Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <div className={`flex items-center space-x-3 ${!sidebarOpen && 'justify-center'}`}>
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                <span className="text-white text-xl">🚗</span>
              </div>
              {sidebarOpen && (
                <div>
                  <h1 className="text-lg font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                    Dashboard
                  </h1>
                  <p className="text-xs text-gray-600">
                    {isConnected ? '✅ Connected' : '❌ Not Connected'}
                  </p>
                </div>
              )}


            </div>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <span className="text-gray-600">{sidebarOpen ? '◀' : '▶'}</span>
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center ${sidebarOpen ? 'space-x-3 px-3' : 'justify-center px-2'} py-2 rounded-lg text-left transition-colors ${
                activeTab === tab.id
                  ? 'bg-indigo-100 text-indigo-700 border border-indigo-200'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`}
              title={!sidebarOpen ? tab.name : ''}
            >
              <span className="text-lg">{tab.icon}</span>
              {sidebarOpen && (
                <span className="font-medium text-sm">{tab.name.replace(/^[^\s]+ /, '')}</span>
              )}
            </button>
          ))}
        </nav>

        {/* Sidebar Footer - Logout moved to header */}
        <div className="p-4 border-t">
          {/* Logout button moved to header */}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Header */}
        <header className="bg-white shadow-sm border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {tabs.find(tab => tab.id === activeTab)?.name.replace(/^[^\s]+ /, '') || 'Dashboard'}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Manage your automotive chatbot settings and data
              </p>
            </div>
            
            {/* User Profile Section */}
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  {branding.company_name || 'Company Name'}
                </p>
                <p className="text-xs text-gray-500">
                  {contactInfo.email || 'No email set'}
                </p>
              </div>
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
                <span className="text-white text-lg font-semibold">
                  {branding.company_name ? branding.company_name.charAt(0).toUpperCase() : '👤'}
                </span>
              </div>
              {/* Logout Button */}
              <button 
                onClick={handleLogout}
                className="flex items-center space-x-2 px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-red-200 hover:border-red-300"
                title="Logout"
              >
                <span className="text-lg">🚪</span>
                <span className="font-medium text-sm">Logout</span>
              </button>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 p-6 overflow-auto">

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Analytics Section */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-gray-900">Analytics Dashboard</h3>
                
                {/* Date Selector */}
                <div className="flex items-center space-x-4">
                  <label className="text-sm font-medium text-gray-700">Period:</label>
                  <select
                    value={analyticsPeriod}
                    onChange={(e) => setAnalyticsPeriod(e.target.value as 'daily' | 'weekly' | 'monthly')}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="daily">Daily (Last 7 days)</option>
                    <option value="weekly">Weekly (Last 4 weeks)</option>
                    <option value="monthly">Monthly (Last 6 months)</option>
                  </select>
                </div>
              </div>

              {/* Analytics Charts Grid - Fixed layout to show all 3 charts properly */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Daily Users Chart */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-4">
                    Daily Users - {analyticsPeriod.charAt(0).toUpperCase() + analyticsPeriod.slice(1)}
                  </h4>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={getAnalyticsData('daily_users')}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="period" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Area 
                          type="monotone" 
                          dataKey="users" 
                          stroke="#f59e0b" 
                          fill="#fbbf24" 
                          name="Daily Users"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Conversations Chart */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-4">
                    Conversations - {analyticsPeriod.charAt(0).toUpperCase() + analyticsPeriod.slice(1)}
                  </h4>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={getAnalyticsData('conversations')}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="period" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line 
                          type="monotone" 
                          dataKey="count" 
                          stroke="#6366f1" 
                          strokeWidth={2}
                          name="Conversations"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Appointments Chart */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-4">
                    Appointments - {analyticsPeriod.charAt(0).toUpperCase() + analyticsPeriod.slice(1)}
                  </h4>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={getAnalyticsData('appointments')}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="period" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="booked" fill="#10b981" name="Booked" />
                        <Bar dataKey="completed" fill="#3b82f6" name="Completed" />
                        <Bar dataKey="cancelled" fill="#ef4444" name="Cancelled" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </div>

            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Commented out as requested by user */}
              {/* <div className="bg-white rounded-lg p-6 shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Vehicles</p>
                    <p className="text-2xl font-bold text-gray-900">{vehicles.length}</p>

                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">🚗</span>
                  </div>
                </div>
              </div> */}

              {/* <div className="bg-white rounded-lg p-6 shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Available for Sale</p>
                    <p className="text-2xl font-bold text-green-600">{availableVehicles}</p>

                  </div>
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">✅</span>
                  </div>
                </div>
              </div> */}

              {/* <div className="bg-white rounded-lg p-6 shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Average Price</p>
                    <p className="text-2xl font-bold text-purple-600">${averagePrice.toLocaleString()}</p>

                  </div>
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">💰</span>
                  </div>
                </div>
              </div> */}

              <div className="bg-white rounded-lg p-6 shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Conversations</p>
                    <p className="text-2xl font-bold text-indigo-600">{chatHistory.length}</p>
                  </div>
                  <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">💬</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg p-6 shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Today's Conversations</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {chatHistory.filter(conv => {
                        const today = new Date();
                        const convDate = new Date(conv.created_at || conv.timestamp || new Date());
                        return convDate.toDateString() === today.toDateString();
                      }).length}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">📊</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg p-6 shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Today's Appointments Booked</p>
                    <p className="text-2xl font-bold text-green-600">
                      {appointments.filter(apt => {
                        const today = new Date();
                        const aptDate = new Date(apt.created_at);
                        return aptDate.toDateString() === today.toDateString();
                      }).length}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">📅</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg p-6 shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Completed Appointments</p>
                    <p className="text-2xl font-bold text-blue-600">{appointments.filter(apt => apt.status === 'completed').length}</p>
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">✅</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg p-6 shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Upcoming Appointments</p>
                    <p className="text-2xl font-bold text-orange-600">
                      {appointments.filter(apt => {
                        const now = new Date();
                        const aptDate = new Date(apt.appointment_datetime);
                        return aptDate > now && apt.status === 'confirmed';
                      }).length}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">⏰</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Database section hidden as requested */}
        {/* {activeTab === 'database' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Database Configuration</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Database Type</label>
                  <select
                    value={dbConfig.db_type}
                    onChange={(e) => setDbConfig({...dbConfig, db_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="MongoDB">MongoDB</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">MongoDB Connection String</label>
                  <textarea
                    value={dbConfig.connection_string}
                    onChange={(e) => setDbConfig({...dbConfig, connection_string: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    rows={3}
                    placeholder="mongodb+srv://username:password@cluster.mongodb.net/..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Database Name</label>
                  <input
                    type="text"
                    value={dbConfig.database_name}
                    onChange={(e) => setDbConfig({...dbConfig, database_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="ezautos"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Vehicle Collection Name</label>
                  <input
                    type="text"
                    value={dbConfig.collection_name}
                    onChange={(e) => setDbConfig({...dbConfig, collection_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="vehicles"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Chat History Collection</label>
                  <input
                    type="text"
                    value={dbConfig.chat_collection_name}
                    onChange={(e) => setDbConfig({...dbConfig, chat_collection_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="chat_history"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Additional Collections (comma-separated)</label>
                  <input
                    type="text"
                    value={dbConfig.additional_collections}
                    onChange={(e) => setDbConfig({...dbConfig, additional_collections: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="test_drives, feedback, financing_applications"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Field Mapping</h4>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Brand Field</label>
                  <input
                    type="text"
                    value={dbConfig.field_mapping.brand}
                    onChange={(e) => setDbConfig({
                      ...dbConfig, 
                      field_mapping: {...dbConfig.field_mapping, brand: e.target.value}
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="brand"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Model Field</label>
                  <input
                    type="text"
                    value={dbConfig.field_mapping.model}
                    onChange={(e) => setDbConfig({
                      ...dbConfig, 
                      field_mapping: {...dbConfig.field_mapping, model: e.target.value}
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="model"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Year Field</label>
                  <input
                    type="text"
                    value={dbConfig.field_mapping.year}
                    onChange={(e) => setDbConfig({
                      ...dbConfig, 
                      field_mapping: {...dbConfig.field_mapping, year: e.target.value}
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="year"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Price Field</label>
                  <input
                    type="text"
                    value={dbConfig.field_mapping.price}
                    onChange={(e) => setDbConfig({
                      ...dbConfig, 
                      field_mapping: {...dbConfig.field_mapping, price: e.target.value}
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="price"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Availability Field</label>
                  <input
                    type="text"
                    value={dbConfig.field_mapping.availability}
                    onChange={(e) => setDbConfig({
                      ...dbConfig, 
                      field_mapping: {...dbConfig.field_mapping, availability: e.target.value}
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="status"
                  />
                </div>
              </div>
            </div>

            <div className="flex space-x-4 mt-6">
              <button
                onClick={testConnection}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                🔍 Test Connection
              </button>
              <button
                onClick={saveConfiguration}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                💾 Save Configuration
              </button>
              <button
                onClick={syncData}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                🔄 Sync Data
              </button>
            </div>
          </div>
        )} */}

        {/* Inventory section hidden as requested */}
        {/* {activeTab === 'inventory' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Vehicle Inventory</h3>
              <p className="text-sm text-gray-600">
                {isConnected ? `✅ Showing ${vehicles.length} vehicles from your database` : '❌ Database not connected'}
              </p>
            </div>
            
            {vehicles.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {vehicles.map((vehicle, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900">
                      {vehicle.brand} {vehicle.model}
                    </h4>
                    <p className="text-sm text-gray-600">Year: {vehicle.year}</p>
                    <p className="text-sm text-gray-600">Price: ${vehicle.price?.toLocaleString() || 'N/A'}</p>
                    <p className="text-sm text-gray-600">Status: {vehicle.availability}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                {isConnected ? 'No vehicles found in database' : 'Connect your database to view inventory'}
              </div>
            )}
          </div>
        )} */}

        {activeTab === 'chat-history' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Chat History</h3>
              <div className="flex items-center space-x-4">
                <input
                  type="text"
                  placeholder="Search by customer name, conversation ID, status, or message..."
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setChatCurrentPage(1); // Reset to first page when searching
                  }}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-600">
                  {filteredChatHistory.length} of {chatHistory.length} conversations
                </span>
              </div>
            </div>
            
            {filteredChatHistory.length > 0 ? (
              <>
                <div className="space-y-4">
                  {filteredChatHistory
                    .slice((chatCurrentPage - 1) * chatItemsPerPage, chatCurrentPage * chatItemsPerPage)
                    .map((conversation, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900">
                            {conversation.customer_name || `Customer ${conversation._id?.slice(-8) || index}`}
                          </h4>
                          <p className="text-sm text-gray-600">
                            Messages: {conversation.messages || 'N/A'} | Status: {conversation.status || 'Unknown'}
                          </p>
                          <p className="text-sm text-gray-500 mt-1">
                            {conversation.last_message || 'No preview available'}
                          </p>
                          <p className="text-xs text-gray-400 mt-2">
                            {conversation.created_at ? new Date(conversation.created_at).toLocaleDateString('en-SG', { 
                              timeZone: 'Asia/Singapore',
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric'
                            }) : 'Unknown date'}
                          </p>
                        </div>
                        <button
                          onClick={() => viewConversationDetails(conversation)}
                          className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 text-sm"
                        >
                          View Details
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Chat History Pagination */}
                {Math.ceil(filteredChatHistory.length / chatItemsPerPage) > 1 && (
                  <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-200">
                    <div className="text-sm text-gray-600">
                      Showing {((chatCurrentPage - 1) * chatItemsPerPage) + 1} to {Math.min(chatCurrentPage * chatItemsPerPage, filteredChatHistory.length)} of {filteredChatHistory.length} conversations
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setChatCurrentPage(prev => Math.max(prev - 1, 1))}
                        disabled={chatCurrentPage === 1}
                        className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <span className="text-sm text-gray-600">
                        Page {chatCurrentPage} of {Math.ceil(filteredChatHistory.length / chatItemsPerPage)}
                      </span>
                      <button
                        onClick={() => setChatCurrentPage(prev => Math.min(prev + 1, Math.ceil(filteredChatHistory.length / chatItemsPerPage)))}
                        disabled={chatCurrentPage === Math.ceil(filteredChatHistory.length / chatItemsPerPage)}
                        className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-8 text-gray-500">
                {isConnected ? 'No conversations found' : 'Connect your database to view chat history'}
              </div>
            )}
          </div>
        )}

        {activeTab === 'appointments' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            {!features.appointment_booking ? (
              <div className="text-center py-12">
                <div className="mb-4">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a1 1 0 011-1h6a1 1 0 011 1v4h3a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9a2 2 0 012-2h3z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Appointment Booking Feature Disabled</h3>
                <p className="text-gray-600 mb-4">To view and manage appointments, please enable the Appointment Booking feature in the Features section.</p>
                <button
                  onClick={() => setActiveTab('features')}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Go to Features
                </button>
              </div>
            ) : (
              <>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-semibold text-gray-900">Active Appointments</h3>
                  <div className="flex items-center space-x-4">
                    <input
                      type="text"
                      placeholder="Search appointments..."
                      value={appointmentSearchTerm}
                      onChange={(e) => {
                        setAppointmentSearchTerm(e.target.value);
                        setAppointmentCurrentPage(1); // Reset to first page when searching
                      }}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-600">
                      {filteredAppointments.filter(apt => apt.status !== 'completed' && apt.status !== 'cancelled').length} active appointments
                    </span>
                  </div>
                </div>
            
            {filteredAppointments.filter(apt => apt.status !== 'completed' && apt.status !== 'cancelled').length > 0 ? (
              <>
                <div className="space-y-4">
                  {filteredAppointments
                    .filter(apt => apt.status !== 'completed' && apt.status !== 'cancelled')
                    .slice((appointmentCurrentPage - 1) * appointmentItemsPerPage, appointmentCurrentPage * appointmentItemsPerPage)
                    .map((appointment, index) => (
                    <div key={appointment.appointment_id || index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900">
                            {appointment.customer_name || 'Unknown Customer'}
                          </h4>
                          <p className="text-sm text-gray-600">
                            Phone: {appointment.customer_phone || 'N/A'} | Service: {appointment.service_type || 'N/A'}
                          </p>
                          <p className="text-sm text-gray-600">
                            Date: {appointment.appointment_datetime ? new Date(appointment.appointment_datetime).toLocaleDateString('en-SG', { 
                              timeZone: 'Asia/Singapore',
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric'
                            }) : 'N/A'}
                          </p>
                          <p className="text-sm text-gray-600">
                            Time: {appointment.appointment_datetime ? new Date(appointment.appointment_datetime).toLocaleTimeString('en-SG', { 
                              timeZone: 'Asia/Singapore',
                              hour: '2-digit', 
                              minute: '2-digit',
                              hour12: true 
                            }) : 'N/A'}
                          </p>
                          <div className="flex items-center space-x-2 mt-2">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              appointment.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                              appointment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              appointment.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                              appointment.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {appointment.status || 'Unknown'}
                            </span>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          {appointment.status === 'pending' && (
                            <button
                              onClick={() => updateAppointmentStatus(appointment.appointment_id || appointment._id, 'cancelled')}
                              disabled={updatingAppointmentStatus === (appointment.appointment_id || appointment._id)}
                              className="px-3 py-1 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm disabled:opacity-50"
                            >
                              {updatingAppointmentStatus === (appointment.appointment_id || appointment._id) ? 'Updating...' : 'Cancel'}
                            </button>
                          )}
                          {appointment.status === 'confirmed' && (
                            <>
                              <button
                                onClick={() => handleCancelAppointment(appointment.appointment_id || appointment._id)}
                                disabled={updatingAppointmentStatus === (appointment.appointment_id || appointment._id)}
                                className="px-3 py-1 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm disabled:opacity-50"
                              >
                                {updatingAppointmentStatus === (appointment.appointment_id || appointment._id) ? 'Updating...' : 'Cancel'}
                              </button>
                              <button
                                onClick={() => updateAppointmentStatus(appointment.appointment_id || appointment._id, 'completed')}
                                disabled={updatingAppointmentStatus === (appointment.appointment_id || appointment._id)}
                                className="px-3 py-1 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 text-sm disabled:opacity-50"
                              >
                                {updatingAppointmentStatus === (appointment.appointment_id || appointment._id) ? 'Updating...' : 'Complete'}
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Appointments Pagination */}
                {Math.ceil(filteredAppointments.length / appointmentItemsPerPage) > 1 && (
                  <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-200">
                    <div className="text-sm text-gray-600">
                      Showing {((appointmentCurrentPage - 1) * appointmentItemsPerPage) + 1} to {Math.min(appointmentCurrentPage * appointmentItemsPerPage, filteredAppointments.length)} of {filteredAppointments.length} appointments
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setAppointmentCurrentPage(prev => Math.max(prev - 1, 1))}
                        disabled={appointmentCurrentPage === 1}
                        className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <span className="text-sm text-gray-600">
                        Page {appointmentCurrentPage} of {Math.ceil(filteredAppointments.length / appointmentItemsPerPage)}
                      </span>
                      <button
                        onClick={() => setAppointmentCurrentPage(prev => Math.min(prev + 1, Math.ceil(filteredAppointments.length / appointmentItemsPerPage)))}
                        disabled={appointmentCurrentPage === Math.ceil(filteredAppointments.length / appointmentItemsPerPage)}
                        className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-8 text-gray-500">
                {appointments.length === 0 ? 'No appointments found' : 'No appointments match your search criteria'}
              </div>
            )}
              </>
            )}
          </div>
        )}

        {activeTab === 'appointment-history' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            {!features.appointment_booking ? (
              <div className="text-center py-12">
                <div className="mb-4">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Appointment Booking Feature Disabled</h3>
                <p className="text-gray-600 mb-4">To view appointment history, please enable the Appointment Booking feature in the Features section.</p>
                <button
                  onClick={() => setActiveTab('features')}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Go to Features
                </button>
              </div>
            ) : (
              <>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-semibold text-gray-900">Appointment History</h3>
                  <div className="flex items-center space-x-4">
                    <input
                      type="text"
                      placeholder="Search history..."
                      value={appointmentSearchTerm}
                      onChange={(e) => {
                        setAppointmentSearchTerm(e.target.value);
                        setAppointmentCurrentPage(1);
                      }}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-600">
                      {filteredAppointments.filter(apt => apt.status === 'completed' || apt.status === 'cancelled').length} historical appointments
                    </span>
                  </div>
                </div>
            
            {filteredAppointments.filter(apt => apt.status === 'completed' || apt.status === 'cancelled').length > 0 ? (
              <>
                <div className="space-y-4">
                  {filteredAppointments
                    .filter(apt => apt.status === 'completed' || apt.status === 'cancelled')
                    .slice((appointmentCurrentPage - 1) * appointmentItemsPerPage, appointmentCurrentPage * appointmentItemsPerPage)
                    .map((appointment, index) => (
                    <div key={appointment.appointment_id || index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900">
                            {appointment.customer_name || 'Unknown Customer'}
                          </h4>
                          <p className="text-sm text-gray-600">
                            Phone: {appointment.customer_phone || 'N/A'} | Service: {appointment.service_type || 'N/A'}
                          </p>
                          <p className="text-sm text-gray-600">
                            Date: {appointment.appointment_datetime ? new Date(appointment.appointment_datetime).toLocaleDateString('en-SG', { 
                              timeZone: 'Asia/Singapore',
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric'
                            }) : 'N/A'}
                          </p>
                          <p className="text-sm text-gray-600">
                            Time: {appointment.appointment_datetime ? new Date(appointment.appointment_datetime).toLocaleTimeString('en-SG', { 
                              timeZone: 'Asia/Singapore',
                              hour: '2-digit', 
                              minute: '2-digit',
                              hour12: true 
                            }) : 'N/A'}
                          </p>
                          {/* Display status timestamp for cancelled or completed appointments */}
                          {appointment.status === 'cancelled' && appointment.cancelled_time && (
                            <p className="text-sm text-red-600">
                              Cancelled: {new Date(appointment.cancelled_time).toLocaleDateString('en-SG', { 
                                timeZone: 'Asia/Singapore',
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric'
                              })} at {new Date(appointment.cancelled_time).toLocaleTimeString('en-SG', { 
                                timeZone: 'Asia/Singapore',
                                hour: '2-digit', 
                                minute: '2-digit',
                                hour12: true 
                              })}
                            </p>
                          )}
                          {appointment.status === 'completed' && appointment.completed_time && (
                            <p className="text-sm text-blue-600">
                              Completed: {new Date(appointment.completed_time).toLocaleDateString('en-SG', { 
                                timeZone: 'Asia/Singapore',
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric'
                              })} at {new Date(appointment.completed_time).toLocaleTimeString('en-SG', { 
                                timeZone: 'Asia/Singapore',
                                hour: '2-digit', 
                                minute: '2-digit',
                                hour12: true 
                              })}
                            </p>
                          )}
                          <div className="flex items-center space-x-2 mt-2">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              appointment.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                              appointment.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {appointment.status || 'Unknown'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* History Pagination */}
                {Math.ceil(filteredAppointments.filter(apt => apt.status === 'completed' || apt.status === 'cancelled').length / appointmentItemsPerPage) > 1 && (
                  <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-200">
                    <div className="text-sm text-gray-600">
                      Showing {((appointmentCurrentPage - 1) * appointmentItemsPerPage) + 1} to {Math.min(appointmentCurrentPage * appointmentItemsPerPage, filteredAppointments.filter(apt => apt.status === 'completed' || apt.status === 'cancelled').length)} of {filteredAppointments.filter(apt => apt.status === 'completed' || apt.status === 'cancelled').length} appointments
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setAppointmentCurrentPage(prev => Math.max(prev - 1, 1))}
                        disabled={appointmentCurrentPage === 1}
                        className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>
                      <span className="text-sm text-gray-600">
                        Page {appointmentCurrentPage} of {Math.ceil(filteredAppointments.filter(apt => apt.status === 'completed' || apt.status === 'cancelled').length / appointmentItemsPerPage)}
                      </span>
                      <button
                        onClick={() => setAppointmentCurrentPage(prev => Math.min(prev + 1, Math.ceil(filteredAppointments.filter(apt => apt.status === 'completed' || apt.status === 'cancelled').length / appointmentItemsPerPage)))}
                        disabled={appointmentCurrentPage === Math.ceil(filteredAppointments.filter(apt => apt.status === 'completed' || apt.status === 'cancelled').length / appointmentItemsPerPage)}
                        className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-8 text-gray-500">
                {appointments.filter(apt => apt.status === 'completed' || apt.status === 'cancelled').length === 0 ? 'No appointment history found' : 'No appointments match your search criteria'}
              </div>
            )}
              </>
            )}
          </div>
        )}

        {activeTab === 'profile' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Profile Configuration</h3>
            
            {/* Profile Completion Status */}
            <div className={`mb-6 p-4 rounded-lg border ${
              isProfileComplete() 
                ? 'bg-green-50 border-green-200' 
                : 'bg-yellow-50 border-yellow-200'
            }`}>
              <div className="flex items-center space-x-2">
                <span className={`text-lg ${
                  isProfileComplete() ? 'text-green-600' : 'text-yellow-600'
                }`}>
                  {isProfileComplete() ? '✅' : '⚠️'}
                </span>
                <h4 className={`font-semibold ${
                  isProfileComplete() ? 'text-green-800' : 'text-yellow-800'
                }`}>
                  Profile {isProfileComplete() ? 'Complete' : 'Incomplete'}
                </h4>
              </div>
              <p className={`text-sm mt-1 ${
                isProfileComplete() ? 'text-green-700' : 'text-yellow-700'
              }`}>
                {isProfileComplete() 
                  ? 'Your profile is complete! You can now access the embed code to add the chatbot to your website.'
                  : 'Please complete all required fields below to unlock the embed code and activate your chatbot.'
                }
              </p>
            </div>

            <div className="space-y-8">
              {/* Branding Section - HIDDEN as per requirements */}
              <div className="border border-gray-200 rounded-lg p-6" style={{display: 'none'}}>
                <h4 className="text-lg font-semibold text-gray-900 mb-4">🎨 Branding</h4>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Company Name *</label>
                      <input
                        type="text"
                        value={branding.company_name}
                        onChange={(e) => setBranding({...branding, company_name: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                        placeholder="ABC Motors Singapore"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Primary Color *</label>
                      <div className="flex space-x-3">
                        <input
                          type="color"
                          value={branding.primary_color}
                          onChange={(e) => setBranding({...branding, primary_color: e.target.value})}
                          className="w-16 h-10 border border-gray-300 rounded-lg"
                        />
                        <input
                          type="text"
                          value={branding.primary_color}
                          onChange={(e) => setBranding({...branding, primary_color: e.target.value})}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                          placeholder="#4F46E5"
                          required
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Secondary Color</label>
                      <div className="flex space-x-3">
                        <input
                          type="color"
                          value={branding.secondary_color}
                          onChange={(e) => setBranding({...branding, secondary_color: e.target.value})}
                          className="w-16 h-10 border border-gray-300 rounded-lg"
                        />
                        <input
                          type="text"
                          value={branding.secondary_color}
                          onChange={(e) => setBranding({...branding, secondary_color: e.target.value})}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                          placeholder="#7C3AED"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Logo URL</label>
                      <input
                        type="url"
                        value={branding.logo_url || ''}
                        onChange={(e) => setBranding({...branding, logo_url: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                        placeholder="https://yourcompany.com/logo.png"
                      />
                    </div>

                    <button
                      onClick={saveBranding}
                      className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                    >
                      💾 Save Branding
                    </button>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <h5 className="font-medium text-gray-900 mb-3">Chatbot Preview</h5>
                    <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
                      <div 
                        className="p-4 text-white"
                        style={{
                          background: `linear-gradient(135deg, ${branding.primary_color} 0%, ${branding.secondary_color} 100%)`
                        }}
                      >
                        <div className="flex items-center space-x-3">
                          {branding.logo_url && branding.logo_url.trim() !== '' && (
                            <Image 
                              src={branding.logo_url} 
                              alt="Logo" 
                              width={24}
                              height={24}
                              className="w-6 h-6 rounded"
                              onError={(e) => { e.currentTarget.style.display = 'none'; }}
                            />
                          )}
                          <div>
                            <h6 className="font-semibold text-sm">{branding.company_name}</h6>
                            <p className="text-xs opacity-90">Your automotive assistant</p>
                          </div>
                        </div>
                      </div>
                      <div className="p-3">
                        <div className="bg-gray-100 rounded-lg p-2 text-xs">
                          Hello! Welcome to {branding.company_name}. How can I help you today?
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Contact Information Section */}
              <div className="border border-gray-200 rounded-lg p-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">📞 Contact Information</h4>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number *</label>
                      <input
                        type="tel"
                        value={contactInfo.phone}
                        onChange={(e) => setContactInfo({...contactInfo, phone: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                        placeholder="+65 6234 5678"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Email Address *</label>
                      <input
                        type="email"
                        value={contactInfo.email || ''}
                        onChange={(e) => setContactInfo({...contactInfo, email: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                        placeholder="sales@yourcompany.com"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">WhatsApp Number</label>
                      <input
                        type="tel"
                        value={contactInfo.whatsapp}
                        onChange={(e) => setContactInfo({...contactInfo, whatsapp: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                        placeholder="+65 9876 5432"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Business Address</label>
                      <textarea
                        value={contactInfo.address}
                        onChange={(e) => setContactInfo({...contactInfo, address: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                        rows={3}
                        placeholder="123 Automotive Street, Singapore 123456"
                      />
                    </div>

                    <button
                      onClick={saveContactInfo}
                      className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                    >
                      💾 Save Contact Information
                    </button>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <h5 className="font-medium text-gray-900 mb-3">Contact Preview</h5>
                    <div className="bg-white rounded-lg p-3 border text-sm">
                      <h6 className="font-semibold text-gray-900 mb-2">📞 Contact {branding.company_name}</h6>
                      
                      {contactInfo.phone && (
                        <div className="mb-2">
                          <span className="text-gray-600">📱 Phone: {contactInfo.phone}</span>
                        </div>
                      )}

                      {contactInfo.email && (
                        <div className="mb-2">
                          <span className="text-gray-600">📧 Email: {contactInfo.email}</span>
                        </div>
                      )}

                      {contactInfo.whatsapp && (
                        <div className="mb-2">
                          <span className="text-gray-600">💬 WhatsApp: {contactInfo.whatsapp}</span>
                        </div>
                      )}

                      {contactInfo.address && (
                        <div className="mb-2">
                          <span className="text-gray-600">📍 Address: {contactInfo.address}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Operating Hours Section */}
              <div className="border border-gray-200 rounded-lg p-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">🕒 Operating Hours</h4>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                      <p className="text-blue-700 text-sm">
                        Configure your business operating hours. At least one day must be open to complete your profile.
                      </p>
                    </div>

                    {Object.entries(operatingHours).map(([day, hours]) => (
                      <div key={day} className="border border-gray-200 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <h5 className="font-medium text-gray-900 capitalize">{day === 'public_holidays' ? 'Public Holidays' : day}</h5>
                          <label className="flex items-center">
                            <input
                              type="checkbox"
                              checked={!hours.closed}
                              onChange={(e) => setOperatingHours({
                                ...operatingHours,
                                [day]: { ...hours, closed: !e.target.checked }
                              })}
                              className="mr-2"
                            />
                            <span className="text-sm text-gray-600">Open</span>
                          </label>
                        </div>
                        
                        {!hours.closed && (
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="block text-xs font-medium text-gray-700 mb-1">Opening</label>
                              <input
                                type="time"
                                value={hours.open}
                                onChange={(e) => setOperatingHours({
                                  ...operatingHours,
                                  [day]: { ...hours, open: e.target.value }
                                })}
                                className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-indigo-500"
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-medium text-gray-700 mb-1">Closing</label>
                              <input
                                type="time"
                                value={hours.close}
                                onChange={(e) => setOperatingHours({
                                  ...operatingHours,
                                  [day]: { ...hours, close: e.target.value }
                                })}
                                className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-indigo-500"
                              />
                            </div>
                          </div>
                        )}
                        
                        {hours.closed && (
                          <div className="text-center py-2">
                            <span className="text-gray-500 text-sm">🚫 Closed</span>
                          </div>
                        )}
                      </div>
                    ))}

                    <button
                      onClick={saveOperatingHours}
                      className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                    >
                      💾 Save Operating Hours
                    </button>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <h5 className="font-medium text-gray-900 mb-3">Hours Preview</h5>
                    <div className="bg-white rounded-lg p-3 border">
                      <h6 className="font-semibold text-gray-900 mb-2 text-sm">🕒 Business Hours</h6>
                      
                      {Object.entries(operatingHours).map(([day, hours]) => (
                        <div key={day} className="flex justify-between items-center py-1 border-b border-gray-100 last:border-b-0">
                          <span className="font-medium text-gray-700 capitalize text-sm">{day === 'public_holidays' ? 'Public Holidays' : day}</span>
                          <span className="text-xs text-gray-600">
                            {hours.closed ? (
                              <span className="text-red-600">Closed</span>
                            ) : (
                              `${hours.open} - ${hours.close}`
                            )}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'features' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Chatbot Features Configuration</h3>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div className="space-y-4">
                  <h4 className="font-medium text-gray-900">Enable/Disable Features</h4>
                  
                  {Object.entries(features).filter(([feature]) => feature !== 'business_hours' && feature !== 'vehicle_search' && feature !== 'contact_support').map(([feature, enabled]) => (
                    <label key={feature} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                      <div>
                        <span className="font-medium text-gray-900 capitalize">
                          {feature.replace('_', ' ')}
                        </span>
                        <p className="text-sm text-gray-600">
                          {getFeatureDescription(feature)}
                        </p>
                      </div>
                      <div className="relative w-12 h-6">
                        <input
                          type="checkbox"
                          checked={enabled}
                          onChange={(e) => setFeatures({
                            ...features,
                            [feature]: e.target.checked
                          })}
                          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
                        />
                        <div
                          className={`w-12 h-6 rounded-full transition-colors duration-200 ${
                            enabled ? 'bg-indigo-600' : 'bg-gray-300'
                          }`}
                        >
                          <div
                            className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform duration-200 ${
                              enabled ? 'translate-x-6' : 'translate-x-0.5'
                            } mt-0.5`}
                          />
                        </div>
                      </div>
                    </label>
                  ))}
                </div>

                <button
                  onClick={saveFeatures}
                  className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  💾 Save Features Configuration
                </button>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <h4 className="font-medium text-gray-900 mb-4">Features Preview</h4>
                <div className="space-y-3">
                  <p className="text-sm text-gray-600 mb-4">
                    These features will be available in your chatbot:
                  </p>
                  
                  {Object.entries(features).filter(([feature]) => feature !== 'business_hours' && feature !== 'vehicle_search' && feature !== 'contact_support').map(([feature, enabled]) => (
                    <div key={feature} className="flex items-center space-x-3">
                      <span className={`w-4 h-4 rounded-full ${enabled ? 'bg-green-500' : 'bg-gray-300'}`} />
                      <span className={`text-sm capitalize ${enabled ? 'text-gray-900' : 'text-gray-400'}`}>
                        {feature.replace('_', ' ')}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'
                      }`}>
                        {enabled ? 'ON' : 'OFF'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}




        {activeTab === 'embed' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Website Embed Code</h3>
            
            {!isProfileComplete() ? (
              <div className="text-center py-12">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 max-w-md mx-auto">
                  <div className="text-yellow-600 text-6xl mb-4">🔒</div>
                  <h4 className="text-xl font-semibold text-yellow-800 mb-3">Profile Setup Required</h4>
                  <p className="text-yellow-700 mb-6">
                    Complete your profile configuration to unlock the embed code and activate your chatbot.
                  </p>
                  <div className="text-left space-y-2 mb-6">
                    <div className="flex items-center space-x-2">
                      <span className={branding.company_name ? '✅' : '❌'}></span>
                      <span className={`text-sm ${branding.company_name ? 'text-green-700' : 'text-red-700'}`}>
                        Company Name
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={branding.primary_color ? '✅' : '❌'}></span>
                      <span className={`text-sm ${branding.primary_color ? 'text-green-700' : 'text-red-700'}`}>
                        Primary Color
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={contactInfo.phone ? '✅' : '❌'}></span>
                      <span className={`text-sm ${contactInfo.phone ? 'text-green-700' : 'text-red-700'}`}>
                        Phone Number
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={contactInfo.email ? '✅' : '❌'}></span>
                      <span className={`text-sm ${contactInfo.email ? 'text-green-700' : 'text-red-700'}`}>
                        Email Address
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={Object.values(operatingHours).some(hours => !hours.closed) ? '✅' : '❌'}></span>
                      <span className={`text-sm ${Object.values(operatingHours).some(hours => !hours.closed) ? 'text-green-700' : 'text-red-700'}`}>
                        At least one operating day
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => setActiveTab('profile')}
                    className="px-6 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
                  >
                    Complete Profile Setup
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-green-600 text-lg">✅</span>
                    <h4 className="font-semibold text-green-800">Profile Complete!</h4>
                  </div>
                  <p className="text-green-700 text-sm">
                    Your chatbot is ready to be embedded on your website.
                  </p>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-semibold text-blue-800 mb-2">How to Add Chatbot to Your Website</h4>
                  <ol className="text-blue-700 text-sm space-y-1">
                    <li>1. Copy the embed code below</li>
                    <li>2. Paste it before the closing &lt;/body&gt; tag on your website</li>
                    <li>3. The chatbot will automatically appear on your site</li>
                    <li>4. Customize appearance in the Profile tab</li>
                  </ol>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Embed Code</label>
                  <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                    <pre>{`<!-- CleverCompanion Chatbot Widget -->
<script async>window.CleverCompanionConfig = { clientId: '${clientId}' };</script>
<script async>
    window.DOMAIN = window.DOMAIN || 'http://localhost';
    // Dynamically load scripts with domain configuration and cache-busting
    const timestamp = Date.now();
    const script1 = document.createElement('script');
    script1.src = (window.DOMAIN || 'http://localhost') + ':8000/clevercompanion-widget.js?v=' + timestamp;
    script1.async = true;
    document.head.appendChild(script1);
    
    const script2 = document.createElement('script');
    script2.src = (window.DOMAIN || 'http://localhost') + ':8000/page-interactions.js?v=' + timestamp;
    script2.async = true;
    document.head.appendChild(script2);
</script>
<!-- End CleverCompanion Widget -->`}</pre>
                  </div>
                  <button
                    onClick={copyEmbedCode}
                    className="mt-3 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    📋 Copy Embed Code
                  </button>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h4 className="font-semibold text-green-800 mb-2">Features Included</h4>
                  <ul className="text-green-700 text-sm space-y-1">
                    <li>• {features.coe_prices ? '✅' : '❌'} COE Prices & Predictions</li>
                    <li>• {features.loan_calculator ? '✅' : '❌'} Loan Calculator</li>
                    <li>• {features.appointment_booking ? '✅' : '❌'} Appointment Booking</li>
                    <li>• ✅ Contact Support (Always Available)</li>
                    <li>• ✅ Operating Hours Configuration (Always Available)</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Analytics section hidden as requested */}
        {/* {activeTab === 'analytics' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Analytics Dashboard</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Database Info</h4>
                <div className="space-y-1 text-sm text-gray-600">
                  <p>Database: {dbStatus.database_name || 'Not connected'}</p>
                  <p>Collection: {dbStatus.collection_name || 'Not set'}</p>
                  <p>Records: {dbStatus.record_count || 0}</p>
                  <p>Last Sync: {dbStatus.last_sync ? new Date(dbStatus.last_sync).toLocaleString('en-SG', { 
                    timeZone: 'Asia/Singapore',
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: true
                  }) : 'Never'}</p>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Vehicle Metrics</h4>
                <div className="space-y-1 text-sm text-gray-600">
                  <p>Total Vehicles: {vehicles.length}</p>
                  <p>Available: {availableVehicles}</p>
                  <p>Average Price: ${averagePrice.toLocaleString()}</p>
                  <p>Data Source: {isConnected ? 'Your Database' : 'Not Connected'}</p>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Chat Metrics</h4>
                <div className="space-y-1 text-sm text-gray-600">
                  <p>Total Conversations: {chatHistory.length}</p>
                  <p>Active Sessions: {chatHistory.filter(c => c.status === 'active').length}</p>
                  <p>Completed: {chatHistory.filter(c => c.status === 'completed').length}</p>
                  <p>Data Source: {isConnected ? 'Your Database' : 'Not Connected'}</p>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Appointment Metrics</h4>
                <div className="space-y-1 text-sm text-gray-600">
                  <p>Total Appointments: {appointments.length}</p>
                  <p>Pending: {appointments.filter(apt => apt.status === 'pending').length}</p>
                  <p>Confirmed: {appointments.filter(apt => apt.status === 'confirmed').length}</p>
                  <p>Completed: {appointments.filter(apt => apt.status === 'completed').length}</p>
                  <p>Cancelled: {appointments.filter(apt => apt.status === 'cancelled').length}</p>
                </div>
              </div>
            </div>
          </div>
        )} */}
        </div>
      </div>

      {/* Full Chatroom View Modal */}
      {showConversationModal && selectedConversation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50">
          <div className="bg-white h-full w-full flex flex-col">
            {/* Header */}
            <div className="bg-indigo-600 text-white p-4 flex justify-between items-center">
              <div className="flex items-center space-x-4">
                <h3 className="text-xl font-semibold">
                  💬 Full Conversation View
                </h3>
                <div className="text-sm opacity-90">
                  ID: {selectedConversation._id || 'N/A'}
                </div>
              </div>
              <button
                onClick={() => setShowConversationModal(false)}
                className="text-white hover:text-gray-200 text-2xl font-bold"
              >
                ✕
              </button>
            </div>
            
            {/* Conversation Info Bar */}
            <div className="bg-gray-50 border-b border-gray-200 p-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Customer:</span>
                  <p className="text-gray-900">{selectedConversation.customer_name || 'Anonymous'}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Status:</span>
                  <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                    selectedConversation.status === 'active' ? 'bg-green-100 text-green-800' :
                    selectedConversation.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {selectedConversation.status || 'Unknown'}
                  </span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Messages:</span>
                  <p className="text-gray-900">{Array.isArray(selectedConversation.messages) ? selectedConversation.messages.length : selectedConversation.message_count || 'N/A'}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Date:</span>
                  <p className="text-gray-900">
                    {selectedConversation.created_at ? new Date(selectedConversation.created_at).toLocaleDateString('en-SG', { 
                      timeZone: 'Asia/Singapore',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    }) : 'Unknown'}
                  </p>
                </div>
              </div>
            </div>

            {/* Chat Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
              {selectedConversation.messages && Array.isArray(selectedConversation.messages) ? (
                <div className="space-y-4 max-w-4xl mx-auto">
                  {selectedConversation.messages.map((msg: { message_type: string; message: string; timestamp?: string }, index: number) => (
                    <div key={index} className={`flex ${
                      msg.message_type === 'user' ? 'justify-end' : 'justify-start'
                    }`}>
                      <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        msg.message_type === 'user' 
                          ? 'bg-indigo-600 text-white rounded-br-none' 
                          : 'bg-white text-gray-900 border border-gray-200 rounded-bl-none'
                      }`}>
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="text-xs font-medium opacity-75">
                            {msg.message_type === 'user' ? '👤 Customer' : '🤖 Assistant'}
                          </span>
                          {msg.timestamp && (
                            <span className="text-xs opacity-50">
                              {formatToSGTime(msg.timestamp)}
                            </span>
                          )}
                        </div>
                        <div className="text-sm whitespace-pre-wrap">{msg.message}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center text-gray-500">
                    <div className="text-6xl mb-4">💬</div>
                    <h4 className="text-lg font-medium mb-2">
                      {(selectedConversation as any)?.error ? 'Error Loading Messages' : 'No detailed messages available'}
                    </h4>
                    <p className="text-sm">
                      {(selectedConversation as any)?.error || 
                       selectedConversation.last_message || 
                       'This conversation may not have detailed message history.'}
                    </p>
                    {(selectedConversation as any)?.error && (
                      <button
                        onClick={() => viewConversationDetails(selectedConversation)}
                        className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm"
                      >
                        🔄 Retry Loading
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Footer with conversation actions */}
            <div className="bg-white border-t border-gray-200 p-4">
              <div className="flex justify-between items-center max-w-4xl mx-auto">
                <div className="text-sm text-gray-600">
                  Conversation ID: <span className="font-mono bg-gray-100 px-2 py-1 rounded">{selectedConversation.conversation_id || selectedConversation._id || 'N/A'}</span>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => {
                      const conversationId = selectedConversation.conversation_id || selectedConversation._id;
                      if (conversationId) {
                        navigator.clipboard.writeText(conversationId);
                        showAlert('Conversation ID copied to clipboard!', 'success');
                      }
                    }}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
                  >
                    📋 Copy ID
                  </button>
                  <button
                    onClick={() => setShowConversationModal(false)}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Cancel Appointment Confirmation Modal */}
      {cancelModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center mr-3">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Cancel Appointment</h3>
            </div>
            <p className="text-gray-600 mb-6">
              Are you sure you want to cancel this appointment? This action cannot be undone.
            </p>
            {appointmentToCancel && (() => {
              const appointment = appointments.find(apt => apt._id === appointmentToCancel || apt.appointment_id === appointmentToCancel);
              return appointment ? (
                <div className="bg-gray-50 rounded-lg p-3 mb-6">
                  <p className="text-sm text-gray-700">
                    <strong>Date:</strong> {new Date(appointment.appointment_datetime).toLocaleDateString('en-SG', { timeZone: 'Asia/Singapore', year: 'numeric', month: '2-digit', day: '2-digit' })}<br/>
                    <strong>Time:</strong> {new Date(appointment.appointment_datetime).toLocaleTimeString('en-SG', { timeZone: 'Asia/Singapore', hour12: false, hour: '2-digit', minute: '2-digit' })}<br/>
                    <strong>Service:</strong> {appointment.service_type || 'General Service'}
                  </p>
                </div>
              ) : null;
            })()}
            <div className="flex justify-end space-x-3">
              <button
                onClick={closeCancelModal}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Keep Appointment
              </button>
              <button
                onClick={confirmCancelAppointment}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Yes, Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Enhanced Custom Alert/Toast Notifications */}
      {alerts.length > 0 && (
        <div className="fixed top-4 right-4 z-50 space-y-3 max-w-sm w-96">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`w-full bg-white shadow-2xl rounded-xl pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden transform transition-all duration-500 ease-out animate-in slide-in-from-right-full ${
                alert.type === 'success' ? 'border-l-4 border-emerald-500' :
                alert.type === 'error' ? 'border-l-4 border-red-500' :
                alert.type === 'warning' ? 'border-l-4 border-amber-500' :
                'border-l-4 border-blue-500'
              }`}
              style={{
                animation: 'slideInRight 0.5s ease-out'
              }}
            >
              <div className={`p-4 ${
                alert.type === 'success' ? 'bg-gradient-to-r from-emerald-50 to-white' :
                alert.type === 'error' ? 'bg-gradient-to-r from-red-50 to-white' :
                alert.type === 'warning' ? 'bg-gradient-to-r from-amber-50 to-white' :
                'bg-gradient-to-r from-blue-50 to-white'
              }`}>
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    {alert.type === 'success' && (
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        'bg-emerald-100 text-emerald-600'
                      }`}>
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                    {alert.type === 'error' && (
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        'bg-red-100 text-red-600'
                      }`}>
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                    {alert.type === 'warning' && (
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        'bg-amber-100 text-amber-600'
                      }`}>
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                    {alert.type === 'info' && (
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        'bg-blue-100 text-blue-600'
                      }`}>
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                  <div className="ml-4 flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className={`text-sm font-semibold ${
                        alert.type === 'success' ? 'text-emerald-800' :
                        alert.type === 'error' ? 'text-red-800' :
                        alert.type === 'warning' ? 'text-amber-800' :
                        'text-blue-800'
                      }`}>
                        {alert.type === 'success' ? 'Success!' :
                         alert.type === 'error' ? 'Error!' :
                         alert.type === 'warning' ? 'Warning!' :
                         'Information'}
                      </h4>
                      <button
                        className={`ml-2 inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-200 ${
                          alert.type === 'success' ? 'text-emerald-500 hover:bg-emerald-100 focus:ring-emerald-600' :
                          alert.type === 'error' ? 'text-red-500 hover:bg-red-100 focus:ring-red-600' :
                          alert.type === 'warning' ? 'text-amber-500 hover:bg-amber-100 focus:ring-amber-600' :
                          'text-blue-500 hover:bg-blue-100 focus:ring-blue-600'
                        }`}
                        onClick={() => removeAlert(alert.id)}
                      >
                        <span className="sr-only">Dismiss</span>
                        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>
                    <p className={`mt-1 text-sm ${
                      alert.type === 'success' ? 'text-emerald-700' :
                      alert.type === 'error' ? 'text-red-700' :
                      alert.type === 'warning' ? 'text-amber-700' :
                      'text-blue-700'
                    }`}>
                      {alert.message}
                    </p>
                  </div>
                </div>
                {/* Progress bar for timed notifications */}
                {alert.duration && alert.duration > 0 && (
                  <div className={`mt-3 w-full bg-gray-200 rounded-full h-1 overflow-hidden`}>
                    <div 
                      className={`h-full rounded-full transition-all ease-linear ${
                        alert.type === 'success' ? 'bg-emerald-500' :
                        alert.type === 'error' ? 'bg-red-500' :
                        alert.type === 'warning' ? 'bg-amber-500' :
                        'bg-blue-500'
                      }`}
                      style={{
                        animation: `shrink ${alert.duration}ms linear forwards`
                      }}
                    ></div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Add custom CSS animations */}
      <style jsx>{`
        @keyframes slideInRight {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        
        @keyframes shrink {
          from {
            width: 100%;
          }
          to {
            width: 0%;
          }
        }
      `}</style>
    </div>
  );
}