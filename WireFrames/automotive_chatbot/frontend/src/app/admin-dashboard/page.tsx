'use client';

import { useState, useEffect } from 'react';

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
      test_drive_booking: boolean;
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
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showClientDetails, setShowClientDetails] = useState(false);

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
      
      // Fetch clients
      const clientsResponse = await fetch('http://localhost:8000/api/super-admin/clients');
      const clientsData = await clientsResponse.json();
      setClients(Array.isArray(clientsData) ? clientsData : clientsData.clients || []);

      // Fetch metrics
      const metricsResponse = await fetch('http://localhost:8000/api/super-admin/metrics');
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
      
      const response = await fetch(`http://localhost:8000/api/super-admin/clients/${clientId}/${endpoint}`, {
        method: 'POST'
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
        alert('Failed to update client status');
      }
    } catch (error) {
      console.error('Failed to toggle client status:', error);
      alert('Error updating client status');
    }
  };

  const viewClientDetails = (client: Client) => {
    setSelectedClient(client);
    setShowClientDetails(true);
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
    </div>
  );
}