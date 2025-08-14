'use client';

import { useState, useEffect } from 'react';
import { API_CONFIG } from '../../config/api';

interface Client {
  id: string;
  business_name: string;
  domain: string;
  contact_email: string;
  status: 'pending' | 'active' | 'suspended';
  subscription_plan: {
    plan_type: string;
    price_per_month: number;
  };
  created_at: string;
  current_month_conversations: number;
  total_conversations: number;
  settings: {
    branding: {
      company_name: string;
      primary_color: string;
    };
    features: {
      coe_prices: boolean;
      loan_calculator: boolean;
      appointment_booking: boolean;
      maintenance_tips: boolean;
      vehicle_search: boolean;
      contact_support: boolean;
    };
    contact_info: {
      phone?: string;
      email?: string;
      address?: string;
      whatsapp?: string;
    };
  };
}

interface SystemMetrics {
  total_clients: number;
  active_clients: number;
  pending_approvals: number;
  system_uptime: number;
}

export default function SuperAdminDashboard() {
  const [clients, setClients] = useState<Client[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics>({
    total_clients: 0,
    active_clients: 0,
    pending_approvals: 0,
    system_uptime: 99.9
  });
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  
  // Custom alert/toast notification state
  const [alerts, setAlerts] = useState<Array<{
    id: string;
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
    duration?: number;
  }>>([]);

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
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('super_admin_token');
    if (!token) {
      window.location.href = '/super-admin-login';
      return;
    }

    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setIsRefreshing(true);
      
      const token = localStorage.getItem('super_admin_token');
      const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      };
      
      // Fetch clients
      const clientsResponse = await fetch(`${API_CONFIG.API_URL}/api/super-admin/clients`, {
        headers
      });
      const clientsData = await clientsResponse.json();
      setClients(Array.isArray(clientsData) ? clientsData : clientsData.clients || []);

      // Fetch metrics
      const metricsResponse = await fetch(`${API_CONFIG.API_URL}/api/super-admin/metrics`, {
        headers
      });
      const metricsData = await metricsResponse.json();
      setMetrics(metricsData);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const toggleClientStatus = async (clientId: string, currentStatus: string) => {
    try {
      const newStatus = currentStatus === 'active' ? 'suspended' : 'active';
      const endpoint = newStatus === 'active' ? 'approve' : 'suspend';
      
      const token = localStorage.getItem('super_admin_token');
      const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      };
      
      const response = await fetch(`${API_CONFIG.API_URL}/api/super-admin/clients/${clientId}/${endpoint}`, {
        method: 'POST',
        headers
      });
      
      if (response.ok) {
        // Refresh data to show updated status
        await fetchData();
        
        // Update selected client if it's the one being toggled
        if (selectedClient && selectedClient.id === clientId) {
          const updatedClient = clients.find(c => c.id === clientId);
          if (updatedClient) {
            setSelectedClient(updatedClient);
          }
        }
      } else {
        showAlert('Failed to update client status', 'error');
      }
    } catch (error) {
      console.error('Failed to toggle client status:', error);
      showAlert('Error updating client status', 'error');
    }
  };

  const viewClientDetails = (client: Client) => {
    setSelectedClient(client);
  };

  const logout = () => {
    localStorage.clear();
    window.location.href = '/super-admin-login';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-red-500 to-pink-600 rounded-xl flex items-center justify-center">
                <span className="text-white text-xl">⚡</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-red-600 to-pink-600 bg-clip-text text-transparent">
                  Super Admin Dashboard
                </h1>
                <p className="text-sm text-gray-600">CleverCompanion SaaS Management</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={fetchData}
                disabled={isRefreshing}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {isRefreshing ? 'Refreshing...' : '🔄 Refresh Data'}
              </button>
              <div className="text-sm text-gray-600">
                System Status: <span className="text-green-600 font-medium">All Systems Operational</span>
              </div>
              <button
                onClick={logout}
                className="text-gray-600 hover:text-gray-800"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Metrics Cards - Removed conversations today and revenue */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl p-6 shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Clients</p>
                <p className="text-2xl font-bold text-gray-900">{metrics.total_clients}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <span className="text-2xl">🏢</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Clients</p>
                <p className="text-2xl font-bold text-green-600">{metrics.active_clients}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <span className="text-2xl">✅</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending Approvals</p>
                <p className="text-2xl font-bold text-yellow-600">{metrics.pending_approvals}</p>
              </div>
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                <span className="text-2xl">⏳</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">System Uptime</p>
                <p className="text-2xl font-bold text-blue-600">{metrics.system_uptime}%</p>
                <p className="text-xs text-gray-500 mt-1">Calculated from service start time</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <span className="text-2xl">⚡</span>
              </div>
            </div>
          </div>
        </div>

        {/* Clients Management */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Clients List */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border">
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">All Clients</h3>
                    <p className="text-sm text-gray-600 mt-1">Manage client accounts and status</p>
                  </div>
                  <span className="text-sm text-gray-500">
                    Last updated: {new Date().toLocaleTimeString()}
                  </span>
                </div>
              </div>
              
              <div className="p-6">
                {clients.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No clients registered yet
                  </div>
                ) : (
                  <div className="space-y-4">
                    {clients.map((client) => (
                      <div key={client.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-900">{client.business_name}</h4>
                            <p className="text-sm text-gray-600 mt-1">
                              Domain: {client.domain} | Email: {client.contact_email}
                            </p>
                            <p className="text-sm text-gray-600">
                              Registered: {new Date(client.created_at).toLocaleDateString()}
                            </p>
                            <div className="flex items-center space-x-2 mt-2">
                              <div className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                                client.status === 'active' 
                                  ? 'bg-green-100 text-green-800' 
                                  : client.status === 'pending'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {client.status.toUpperCase()}
                              </div>
                              <span className="text-xs text-gray-500">
                                Plan: {client.subscription_plan?.plan_type || 'N/A'}
                              </span>
                            </div>
                          </div>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => toggleClientStatus(client.id, client.status)}
                              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                                client.status === 'active'
                                  ? 'bg-red-100 text-red-700 hover:bg-red-200'
                                  : 'bg-green-100 text-green-700 hover:bg-green-200'
                              }`}
                            >
                              {client.status === 'active' ? 'Deactivate' : 'Activate'}
                            </button>
                            <button 
                              onClick={() => viewClientDetails(client)}
                              className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 text-sm font-medium"
                            >
                              View Details
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Client Details Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Client Details</h3>
              </div>
              
              <div className="p-6">
                {selectedClient ? (
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">{selectedClient.business_name}</h4>
                      <div className="space-y-2 text-sm">
                        <div><span className="font-medium">Status:</span> 
                          <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
                            selectedClient.status === 'active' ? 'bg-green-100 text-green-800' : 
                            selectedClient.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {selectedClient.status.toUpperCase()}
                          </span>
                        </div>
                        <div><span className="font-medium">Domain:</span> {selectedClient.domain}</div>
                        <div><span className="font-medium">Email:</span> {selectedClient.contact_email}</div>
                        <div><span className="font-medium">Plan:</span> {selectedClient.subscription_plan?.plan_type || 'N/A'}</div>
                        <div><span className="font-medium">Created:</span> {new Date(selectedClient.created_at).toLocaleDateString()}</div>
                      </div>
                    </div>

                    <div className="border-t pt-4">
                      <h5 className="font-medium text-gray-900 mb-2">Contact Information</h5>
                      <div className="space-y-1 text-sm text-gray-600">
                        <div>Phone: {selectedClient.settings.contact_info.phone || 'Not set'}</div>
                        <div>Email: {selectedClient.settings.contact_info.email || 'Not set'}</div>
                        <div>WhatsApp: {selectedClient.settings.contact_info.whatsapp || 'Not set'}</div>
                        <div>Address: {selectedClient.settings.contact_info.address || 'Not set'}</div>
                      </div>
                    </div>

                    <div className="border-t pt-4">
                      <h5 className="font-medium text-gray-900 mb-2">Features Enabled</h5>
                      <div className="space-y-1 text-sm">
                        {Object.entries(selectedClient.settings.features).map(([feature, enabled]) => (
                          <div key={feature} className="flex justify-between">
                            <span className="capitalize">{feature.replace('_', ' ')}</span>
                            <span className={enabled ? 'text-green-600' : 'text-red-600'}>
                              {enabled ? 'ON' : 'OFF'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="border-t pt-4">
                      <h5 className="font-medium text-gray-900 mb-2">Branding</h5>
                      <div className="space-y-2 text-sm text-gray-600">
                        <div>Company: {selectedClient.settings.branding.company_name}</div>
                        <div className="flex items-center space-x-2">
                          <span>Primary Color:</span>
                          <div 
                            className="w-4 h-4 rounded border"
                            style={{ backgroundColor: selectedClient.settings.branding.primary_color }}
                          ></div>
                          <span>{selectedClient.settings.branding.primary_color}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    Select a client to view details
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
      
      {/* Custom Alert/Toast Notifications */}
      {alerts.length > 0 && (
        <div className="fixed top-4 right-4 z-50 space-y-2">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden transform transition-all duration-300 ease-in-out ${
                alert.type === 'success' ? 'border-l-4 border-green-500' :
                alert.type === 'error' ? 'border-l-4 border-red-500' :
                alert.type === 'warning' ? 'border-l-4 border-yellow-500' :
                'border-l-4 border-blue-500'
              }`}
            >
              <div className="p-4">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    {alert.type === 'success' && (
                      <div className="w-5 h-5 text-green-400">✅</div>
                    )}
                    {alert.type === 'error' && (
                      <div className="w-5 h-5 text-red-400">❌</div>
                    )}
                    {alert.type === 'warning' && (
                      <div className="w-5 h-5 text-yellow-400">⚠️</div>
                    )}
                    {alert.type === 'info' && (
                      <div className="w-5 h-5 text-blue-400">ℹ️</div>
                    )}
                  </div>
                  <div className="ml-3 w-0 flex-1">
                    <p className={`text-sm font-medium ${
                      alert.type === 'success' ? 'text-green-900' :
                      alert.type === 'error' ? 'text-red-900' :
                      alert.type === 'warning' ? 'text-yellow-900' :
                      'text-blue-900'
                    }`}>
                      {alert.message}
                    </p>
                  </div>
                  <div className="ml-4 flex-shrink-0 flex">
                    <button
                      className={`inline-flex text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600 transition ease-in-out duration-150`}
                      onClick={() => removeAlert(alert.id)}
                    >
                      <span className="sr-only">Close</span>
                      <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}