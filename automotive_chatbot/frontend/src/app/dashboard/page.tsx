'use client';

import { useState, useEffect } from 'react';

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
  raw_data: any;
}

interface ChatConversation {
  _id: string;
  customer_name: string;
  messages: number;
  status: string;
  last_message: string;
  created_at: string;
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

export default function ClientDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [isConnected, setIsConnected] = useState(false);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [chatHistory, setChatHistory] = useState<ChatConversation[]>([]);
  const [filteredChatHistory, setFilteredChatHistory] = useState<ChatConversation[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedConversation, setSelectedConversation] = useState<any>(null);
  const [showConversationModal, setShowConversationModal] = useState(false);
  
  // Features configuration state
  const [features, setFeatures] = useState({
    coe_prices: true,
    loan_calculator: true,
    test_drive_booking: true,
    maintenance_tips: true,
    vehicle_search: true,
    contact_support: true,
    business_hours: true
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
    company_name: 'ABC Motors Singapore',
    primary_color: '#4F46E5',
    secondary_color: '#7C3AED',
    logo_url: ''
  });

  const [contactInfo, setContactInfo] = useState<ContactInfo>({
    phone: '+65 6234 5678',
    email: 'sales@abcmotors.com.sg',
    whatsapp: '+65 9876 5432',
    address: '123 Automotive Street, Singapore 123456'
  });

  const [dbStatus, setDbStatus] = useState({
    connected: false,
    db_type: null,
    database_name: null,
    collection_name: null,
    last_sync: null,
    record_count: 0
  });

  useEffect(() => {
    fetchDatabaseStatus();
    fetchVehicles();
    fetchChatHistory();
  }, []);

  useEffect(() => {
    // Filter chat history based on search term
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

  const fetchDatabaseStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/client/database/status');
      if (response.ok) {
        const status = await response.json();
        setDbStatus(status);
        setIsConnected(status.connected);
      }
    } catch (error) {
      console.error('Failed to fetch database status:', error);
    }
  };

  const fetchVehicles = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/client/vehicles');
      if (response.ok) {
        const data = await response.json();
        setVehicles(data.vehicles || []);
        console.log('Fetched vehicles:', data.vehicles?.length || 0);
      }
    } catch (error) {
      console.error('Failed to fetch vehicles:', error);
    }
  };

  const fetchChatHistory = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/client/conversations');
      if (response.ok) {
        const data = await response.json();
        setChatHistory(data.conversations || []);
        setFilteredChatHistory(data.conversations || []);
        console.log('Fetched chat history:', data.conversations?.length || 0);
      }
    } catch (error) {
      console.error('Failed to fetch chat history:', error);
    }
  };

  const testConnection = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/client/database/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dbConfig)
      });
      
      const result = await response.json();
      alert(result.message);
      console.log('Test result:', result);
    } catch (error) {
      alert('Connection test failed');
      console.error('Test error:', error);
    }
  };

  const saveConfiguration = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/client/database/save-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dbConfig)
      });
      
      const result = await response.json();
      if (result.success) {
        setIsConnected(true);
        await fetchDatabaseStatus();
        alert('Configuration saved successfully!');
      } else {
        alert(result.message);
      }
    } catch (error) {
      alert('Failed to save configuration');
      console.error('Save error:', error);
    }
  };

  const syncData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/client/database/sync-data', {
        method: 'POST'
      });
      
      const result = await response.json();
      if (result.success) {
        await fetchVehicles();
        await fetchChatHistory();
        await fetchDatabaseStatus();
        alert(result.message);
      } else {
        alert(result.message);
      }
    } catch (error) {
      alert('Data sync failed');
      console.error('Sync error:', error);
    }
  };

  const saveBranding = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/client/branding', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(branding)
      });
      
      if (response.ok) {
        alert('Branding saved successfully!');
      } else {
        alert('Failed to save branding');
      }
    } catch (error) {
      alert('Failed to save branding');
      console.error('Branding save error:', error);
    }
  };

  const saveContactInfo = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/client/contact-info', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(contactInfo)
      });
      
      if (response.ok) {
        alert('Contact information saved successfully!');
      } else {
        alert('Failed to save contact information');
      }
    } catch (error) {
      alert('Failed to save contact information');
      console.error('Contact save error:', error);
    }
  };

  const saveFeatures = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/client/features', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(features)
      });
      
      if (response.ok) {
        alert('Features configuration saved successfully!');
      } else {
        alert('Failed to save features configuration');
      }
    } catch (error) {
      alert('Failed to save features configuration');
      console.error('Features save error:', error);
    }
  };

  const viewConversationDetails = (conversation: ChatConversation) => {
    setSelectedConversation(conversation);
    setShowConversationModal(true);
  };

  const copyEmbedCode = () => {
    const embedCode = `<!-- CleverCompanion Automotive Chatbot Widget -->
<script>
  window.CleverCompanionConfig = {
    clientId: 'abc_motors_singapore',
    apiUrl: 'https://api.clevercompanion.com/widget',
    branding: {
      company_name: '${branding.company_name}',
      primary_color: '${branding.primary_color}',
      secondary_color: '${branding.secondary_color}',
      logo_url: '${branding.logo_url}'
    },
    features: {
      coe_prices: ${features.coe_prices},
      loan_calculator: ${features.loan_calculator},
      test_drive_booking: ${features.test_drive_booking},
      maintenance_tips: ${features.maintenance_tips},
      vehicle_search: ${features.vehicle_search},
      contact_support: ${features.contact_support},
      business_hours: ${features.business_hours}
    },
    contact_info: {
      phone: '${contactInfo.phone}',
      email: '${contactInfo.email}',
      whatsapp: '${contactInfo.whatsapp}',
      address: '${contactInfo.address}'
    }
  };
</script>
<script src="https://cdn.clevercompanion.com/widget/clevercompanion-widget.js" async></script>
<!-- End CleverCompanion Widget -->`;

    navigator.clipboard.writeText(embedCode).then(() => {
      alert('Embed code copied to clipboard!');
    }).catch(() => {
      alert('Failed to copy embed code');
    });
  };

  const getFeatureDescription = (feature: string): string => {
    const descriptions = {
      coe_prices: 'Real-time COE prices and predictions',
      loan_calculator: 'Vehicle loan calculation and financing options',
      test_drive_booking: 'Schedule test drives for vehicles',
      maintenance_tips: 'Vehicle maintenance guides and tips',
      vehicle_search: 'Search and browse vehicle inventory',
      contact_support: 'Contact information and support',
      business_hours: 'Business hours and operating schedule'
    };
    return descriptions[feature as keyof typeof descriptions] || 'Feature description';
  };

  // Calculate analytics from real data
  const availableVehicles = vehicles.filter(v => 
    v.availability?.toLowerCase() === 'available' || 
    v.availability?.toLowerCase() === 'in stock' ||
    v.availability?.toLowerCase() === 'in_stock'
  ).length;

  const averagePrice = vehicles.length > 0 
    ? Math.round(vehicles.reduce((sum, v) => sum + (v.price || 0), 0) / vehicles.length)
    : 0;

  const tabs = [
    { id: 'overview', name: '📊 Overview', icon: '📊' },
    { id: 'database', name: '🗄️ Database', icon: '🗄️' },
    { id: 'inventory', name: '🚗 Inventory', icon: '🚗' },
    { id: 'chat-history', name: '💬 Chat History', icon: '💬' },
    { id: 'branding', name: '🎨 Branding', icon: '🎨' },
    { id: 'contact', name: '📞 Contact Info', icon: '📞' },
    { id: 'features', name: '⚙️ Features', icon: '⚙️' },
    { id: 'embed', name: '📋 Embed Code', icon: '📋' },
    { id: 'analytics', name: '📈 Analytics', icon: '📈' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                <span className="text-white text-xl">🚗</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  {branding.company_name} Dashboard
                </h1>
                <p className="text-sm text-gray-600">
                  Status: {isConnected ? '✅ Connected' : '❌ Not Connected'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <a href="/" className="text-indigo-600 hover:text-indigo-700 font-medium">
                ← Back to Login
              </a>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 overflow-x-auto">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg p-6 shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Vehicles</p>
                    <p className="text-2xl font-bold text-gray-900">{vehicles.length}</p>
                    <p className="text-xs text-green-600">✅ From your database</p>
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">🚗</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg p-6 shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Available for Sale</p>
                    <p className="text-2xl font-bold text-green-600">{availableVehicles}</p>
                    <p className="text-xs text-green-600">✅ From your database</p>
                  </div>
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">✅</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg p-6 shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Average Price</p>
                    <p className="text-2xl font-bold text-purple-600">${averagePrice.toLocaleString()}</p>
                    <p className="text-xs text-green-600">✅ From your database</p>
                  </div>
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">💰</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg p-6 shadow-sm border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Conversations</p>
                    <p className="text-2xl font-bold text-indigo-600">{chatHistory.length}</p>
                    <p className="text-xs text-green-600">✅ From your database</p>
                  </div>
                  <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">💬</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'database' && (
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
        )}

        {activeTab === 'inventory' && (
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
        )}

        {activeTab === 'chat-history' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Chat History</h3>
              <div className="flex items-center space-x-4">
                <input
                  type="text"
                  placeholder="Search conversations..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-600">
                  {filteredChatHistory.length} of {chatHistory.length} conversations
                </span>
              </div>
            </div>
            
            {filteredChatHistory.length > 0 ? (
              <div className="space-y-4">
                {filteredChatHistory.map((conversation, index) => (
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
                          {conversation.created_at ? new Date(conversation.created_at).toLocaleDateString() : 'Unknown date'}
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
            ) : (
              <div className="text-center py-8 text-gray-500">
                {isConnected ? 'No conversations found' : 'Connect your database to view chat history'}
              </div>
            )}
          </div>
        )}

        {activeTab === 'branding' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Chatbot Branding Configuration</h3>
        {activeTab === 'features' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Chatbot Features Configuration</h3>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div className="space-y-4">
                  <h4 className="font-medium text-gray-900">Enable/Disable Features</h4>
                  
                  {Object.entries(features).map(([feature, enabled]) => (
                    <label key={feature} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                      <div>
                        <span className="font-medium text-gray-900 capitalize">
                          {feature.replace('_', ' ')}
                        </span>
                        <p className="text-sm text-gray-600">
                          {getFeatureDescription(feature)}
                        </p>
                      </div>
                      <div className="relative">
                        <input
                          type="checkbox"
                          checked={enabled}
                          onChange={(e) => setFeatures({
                            ...features,
                            [feature]: e.target.checked
                          })}
                          className="sr-only"
                        />
                        <div
                          className={`w-12 h-6 rounded-full cursor-pointer transition-colors ${
                            enabled ? 'bg-indigo-600' : 'bg-gray-300'
                          }`}
                          onClick={() => setFeatures({
                            ...features,
                            [feature]: !enabled
                          })}
                        >
                          <div
                            className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform ${
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
                  
                  {Object.entries(features).map(([feature, enabled]) => (
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
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Company Name</label>
                  <input
                    type="text"
                    value={branding.company_name}
                    onChange={(e) => setBranding({...branding, company_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="ABC Motors Singapore"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Primary Color</label>
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
                    value={branding.logo_url}
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

              <div className="bg-gray-50 rounded-lg p-6">
                <h4 className="font-medium text-gray-900 mb-4">Chatbot Preview</h4>
                <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
                  <div 
                    className="p-4 text-white"
                    style={{
                      background: `linear-gradient(135deg, ${branding.primary_color} 0%, ${branding.secondary_color} 100%)`
                    }}
                  >
                    <div className="flex items-center space-x-3">
                      {branding.logo_url && (
                        <img 
                          src={branding.logo_url} 
                          alt="Logo" 
                          className="w-8 h-8 rounded"
                          onError={(e) => { e.currentTarget.style.display = 'none'; }}
                        />
                      )}
                      <div>
                        <h3 className="font-semibold">{branding.company_name}</h3>
                        <p className="text-sm opacity-90">Your automotive assistant</p>
                      </div>
                    </div>
                  </div>
                  <div className="p-4">
                    <div className="bg-gray-100 rounded-lg p-3 text-sm">
                      Hello! Welcome to {branding.company_name}. How can I help you today?
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'contact' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Contact Information Configuration</h3>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
                  <input
                    type="tel"
                    value={contactInfo.phone}
                    onChange={(e) => setContactInfo({...contactInfo, phone: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="+65 6234 5678"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                  <input
                    type="email"
                    value={contactInfo.email}
                    onChange={(e) => setContactInfo({...contactInfo, email: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="sales@yourcompany.com"
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

              <div className="bg-gray-50 rounded-lg p-6">
                <h4 className="font-medium text-gray-900 mb-4">Contact Preview</h4>
                <div className="bg-white rounded-lg p-4 border">
                  <h5 className="font-semibold text-gray-900 mb-3">📞 Contact {branding.company_name}</h5>
                  
                  {contactInfo.phone && (
                    <div className="mb-2">
                      <span className="text-sm text-gray-600">📱 Phone: {contactInfo.phone}</span>
                      <div className="mt-1">
                        <button className="px-3 py-1 bg-blue-600 text-white rounded text-xs">
                          📞 Call Now
                        </button>
                      </div>
                    </div>
                  )}

                  {contactInfo.email && (
                    <div className="mb-2">
                      <span className="text-sm text-gray-600">📧 Email: {contactInfo.email}</span>
                      <div className="mt-1">
                        <button className="px-3 py-1 bg-orange-600 text-white rounded text-xs">
                          📧 Email Us
                        </button>
                      </div>
                    </div>
                  )}

                  {contactInfo.whatsapp && (
                    <div className="mb-2">
                      <span className="text-sm text-gray-600">💬 WhatsApp: {contactInfo.whatsapp}</span>
                      <div className="mt-1">
                        <button className="px-3 py-1 bg-green-600 text-white rounded text-xs">
                          💬 WhatsApp
                        </button>
                      </div>
                    </div>
                  )}

                  {contactInfo.address && (
                    <div className="mb-2">
                      <span className="text-sm text-gray-600">📍 Address: {contactInfo.address}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'embed' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Website Embed Code</h3>
            
            <div className="space-y-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-semibold text-blue-800 mb-2">How to Add Chatbot to Your Website</h4>
                <ol className="text-blue-700 text-sm space-y-1">
                  <li>1. Copy the embed code below</li>
                  <li>2. Paste it before the closing &lt;/body&gt; tag on your website</li>
                  <li>3. The chatbot will automatically appear on your site</li>
                  <li>4. Customize appearance in the Branding tab</li>
                </ol>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Embed Code</label>
                <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                  <pre>{`<!-- CleverCompanion Automotive Chatbot Widget -->
<script>
  window.CleverCompanionConfig = {
    clientId: 'abc_motors_singapore',
    apiUrl: 'https://api.clevercompanion.com/widget',
    branding: {
      company_name: '${branding.company_name}',
      primary_color: '${branding.primary_color}',
      secondary_color: '${branding.secondary_color}',
      logo_url: '${branding.logo_url}'
    },
    contact_info: {
      phone: '${contactInfo.phone}',
      email: '${contactInfo.email}',
      whatsapp: '${contactInfo.whatsapp}',
      address: '${contactInfo.address}'
    }
  };
</script>
<script src="https://cdn.clevercompanion.com/widget/clevercompanion-widget.js" async></script>
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
                  <li>• COE Prices & Predictions</li>
                  <li>• Vehicle Search & Recommendations</li>
                  <li>• Loan Calculator</li>
                  <li>• Test Drive Booking</li>
                  <li>• Maintenance Tips</li>
                  <li>• Contact Support</li>
                  <li>• Your Custom Branding & Contact Info</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Analytics Dashboard</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Database Info</h4>
                <div className="space-y-1 text-sm text-gray-600">
                  <p>Database: {dbStatus.database_name || 'Not connected'}</p>
                  <p>Collection: {dbStatus.collection_name || 'Not set'}</p>
                  <p>Records: {dbStatus.record_count || 0}</p>
                  <p>Last Sync: {dbStatus.last_sync ? new Date(dbStatus.last_sync).toLocaleString() : 'Never'}</p>
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
            </div>
          </div>
        )}
      </div>

      {/* Conversation Details Modal */}
      {showConversationModal && selectedConversation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">
                  Conversation Details
                </h3>
                <button
                  onClick={() => setShowConversationModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-96">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Customer:</span>
                    <p className="text-gray-900">{selectedConversation.customer_name || 'Anonymous'}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Status:</span>
                    <p className="text-gray-900">{selectedConversation.status || 'Unknown'}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Messages:</span>
                    <p className="text-gray-900">{selectedConversation.messages || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Date:</span>
                    <p className="text-gray-900">
                      {selectedConversation.created_at ? new Date(selectedConversation.created_at).toLocaleDateString() : 'Unknown'}
                    </p>
                  </div>
                </div>

                <div>
                  <span className="font-medium text-gray-700">Last Message:</span>
                  <p className="text-gray-900 mt-1 p-3 bg-gray-50 rounded-lg">
                    {selectedConversation.last_message || 'No message preview available'}
                  </p>
                </div>

                {selectedConversation.messages && Array.isArray(selectedConversation.messages) && (
                  <div>
                    <span className="font-medium text-gray-700">Full Conversation:</span>
                    <div className="mt-2 space-y-2 max-h-64 overflow-y-auto">
                      {selectedConversation.messages.map((msg: any, index: number) => (
                        <div key={index} className={`p-2 rounded ${
                          msg.role === 'user' ? 'bg-blue-100 text-blue-900' : 'bg-gray-100 text-gray-900'
                        }`}>
                          <div className="text-xs font-medium mb-1">
                            {msg.role === 'user' ? '👤 Customer' : '🤖 Assistant'}
                          </div>
                          <div className="text-sm">{msg.content}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}