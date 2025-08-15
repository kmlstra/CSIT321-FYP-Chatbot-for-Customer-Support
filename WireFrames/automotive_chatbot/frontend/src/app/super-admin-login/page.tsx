'use client';

import { useState } from 'react';
import Link from 'next/link';
import { API_CONFIG } from '../../config/api';

export default function SuperAdminLoginPage() {
  const [formData, setFormData] = useState({
    email: 'admin@clevercompanion.com',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_CONFIG.API_URL}/api/auth/super-admin-login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        }),
      });

      if (response.ok) {
        const result = await response.json();
        
        // Store authentication token
        localStorage.setItem('super_admin_token', result.access_token);
        localStorage.setItem('super_admin_data', JSON.stringify(result.user));
        
        // Simple redirect without router
        window.location.href = '/admin-dashboard';
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Login failed');
      }
    } catch (error) {
      console.error('Super admin login error:', error);
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-100 flex items-center justify-center">
      <div className="max-w-md w-full mx-4">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-r from-red-500 to-pink-600 rounded-xl flex items-center justify-center mx-auto mb-4">
            <span className="text-white text-2xl">⚡</span>
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-red-600 to-pink-600 bg-clip-text text-transparent">
            Super Admin
          </h1>
          <p className="text-gray-600 mt-2">CleverCompanion Platform Management</p>
        </div>

        {/* Login Form */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                placeholder="admin@clevercompanion.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                placeholder="Enter super admin password"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-red-600 to-pink-600 text-white py-3 px-4 rounded-lg font-semibold hover:from-red-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
            >
              {isLoading ? 'Signing In...' : 'Sign In as Super Admin'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600 text-sm">
              For client access, use{' '}
              <Link href="/" className="text-indigo-600 hover:text-indigo-700 font-medium">
                Client Login
              </Link>
            </p>
            <p className="text-gray-500 text-xs mt-2">
              Default super admin credentials for development:
            </p>
            <p className="text-gray-500 text-xs mt-1">
              Email: admin@clevercompanion.com<br/>
              Password: SuperAdmin123!
            </p>
          </div>
        </div>

        {/* Security Notice */}
        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="font-semibold text-yellow-800 mb-2">Security Notice</h3>
          <ul className="text-yellow-700 text-sm space-y-1">
            <li>• Super admin access grants full system control</li>
            <li>• Can approve/suspend all client accounts</li>
            <li>• Access to system-wide analytics and billing</li>
            <li>• Change default credentials in production</li>
          </ul>
        </div>
      </div>
    </div>
  );
}