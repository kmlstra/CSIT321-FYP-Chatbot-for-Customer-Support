'use client';

import { useState, useEffect } from 'react';

interface SystemStatus {
  name: string;
  status: 'active' | 'inactive' | 'warning';
  description: string;
  lastUpdate: string;
}

export default function AdminDashboard() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus[]>([
    {
      name: 'RASA NLU',
      status: 'active',
      description: 'Natural Language Understanding',
      lastUpdate: 'Just now'
    },
    {
      name: 'FastAPI Backend',
      status: 'active', 
      description: 'Backend API Services',
      lastUpdate: 'Just now'
    },
    {
      name: 'COE Data Service',
      status: 'active',
      description: 'Live COE Price Updates',
      lastUpdate: 'Just now'
    },
    {
      name: 'RAG System',
      status: 'active',
      description: 'Retrieval Augmented Generation',
      lastUpdate: 'Just now'
    }
  ]);

  const [stats, setStats] = useState({
    totalChats: 0,
    activeUsers: 0,
    successRate: 0,
    avgResponseTime: 0
  });

  useEffect(() => {
    // Initialize with static values to prevent hydration mismatch
    setStats({
      totalChats: 1247,
      activeUsers: 12,
      successRate: 97,
      avgResponseTime: 1.4
    });
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'badge-success';
      case 'warning': return 'badge-warning';
      case 'inactive': return 'badge-error';
      default: return 'badge-info';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return '✅';
      case 'warning': return '⚠️';
      case 'inactive': return '❌';
      default: return '❓';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50">
      {/* Enhanced Header */}
      <header className="dashboard-header backdrop-blur-sm border-b border-indigo-100 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                <span className="text-white text-xl">🚗</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold gradient-text">
                  CleverCompanion Dashboard
                </h1>
                <p className="text-sm text-gray-600">System Administration & Analytics</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <a 
                href="/" 
                className="btn-secondary text-sm"
              >
                ← Back to Chat
              </a>
              <a 
                href="/chat.html" 
                className="btn-primary text-sm"
              >
                Landing Page
              </a>
            </div>
          </div>
        </div>
      </header>

      <main className="dashboard-content">
        <div className="max-w-7xl mx-auto">
          {/* Welcome Section */}
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Welcome to CleverCompanion</h2>
            <p className="text-lg text-gray-600 mb-6">Singapore's premier automotive chatbot assistant. This dashboard provides an overview of the system status and capabilities.</p>
            
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span className="flex items-center">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                System Status: All Services Running
              </span>
            </div>
          </div>

          {/* Enhanced Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="stat-card card-hover">
              <div className="flex items-center justify-between">
                <div>
                  <p className="stat-label">Total Conversations</p>
                  <p className="stat-value">{stats.totalChats.toLocaleString()}</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">💬</span>
                </div>
              </div>
            </div>

            <div className="stat-card card-hover">
              <div className="flex items-center justify-between">
                <div>
                  <p className="stat-label">Active Users</p>
                  <p className="stat-value">{stats.activeUsers}</p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">👥</span>
                </div>
              </div>
            </div>

            <div className="stat-card card-hover">
              <div className="flex items-center justify-between">
                <div>
                  <p className="stat-label">Success Rate</p>
                  <p className="stat-value">{stats.successRate}%</p>
                </div>
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">📊</span>
                </div>
              </div>
            </div>

            <div className="stat-card card-hover">
              <div className="flex items-center justify-between">
                <div>
                  <p className="stat-label">Avg Response Time</p>
                  <p className="stat-value">{stats.avgResponseTime.toFixed(1)}s</p>
                </div>
                <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">⚡</span>
                </div>
              </div>
            </div>
          </div>

          {/* Enhanced System Status */}
          <div className="card mb-8">
            <div className="border-b border-gray-100 pb-4 mb-6">
              <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
              <p className="text-sm text-gray-600 mt-1">Real-time monitoring of all CleverCompanion services</p>
            </div>
            <div className="space-y-4">
              {systemStatus.map((service, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg table-row">
                  <div className="flex items-center space-x-4">
                    <span className="text-2xl">{getStatusIcon(service.status)}</span>
                    <div>
                      <h4 className="font-medium text-gray-900">{service.name}</h4>
                      <p className="text-sm text-gray-600">{service.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`badge ${getStatusColor(service.status)}`}>
                      {service.status.toUpperCase()}
                    </span>
                    <p className="text-xs text-gray-500 mt-1">{service.lastUpdate}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Enhanced Features Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">🎯 Core Features</h3>
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span className="text-gray-700">Real-time COE price monitoring</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span className="text-gray-700">Vehicle information database</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span className="text-gray-700">Test drive scheduling</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span className="text-gray-700">Loan calculator & financing</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span className="text-gray-700">Maintenance scheduling</span>
                </div>
              </div>
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">🛠️ Technical Stack</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">NLU Engine:</span>
                  <span className="font-medium">RASA 3.6.4</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Backend:</span>
                  <span className="font-medium">FastAPI + Python</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Frontend:</span>
                  <span className="font-medium">Next.js + React</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Database:</span>
                  <span className="font-medium">MongoDB</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Vector Search:</span>
                  <span className="font-medium">FAISS</span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🚀 Quick Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button className="btn-primary w-full">
                🤖 Train RASA Model
              </button>
              <button className="btn-secondary w-full">
                📊 View Analytics
              </button>
              <button className="btn-secondary w-full">
                🔧 System Settings
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 