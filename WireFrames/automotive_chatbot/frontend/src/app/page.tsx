'use client';

import { useState } from 'react';
import { API_CONFIG } from '../config/api';

export default function ClientLoginPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_CONFIG.API_URL}/api/auth/client-login`, {
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
        localStorage.setItem('client_token', result.access_token);
        localStorage.setItem('client_data', JSON.stringify(result.client));
        localStorage.setItem('user_data', JSON.stringify(result.user));
        
        // Redirect to dashboard
        window.location.href = '/dashboard';
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="max-w-md w-full mx-4">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4">
            <span className="text-white text-2xl">🚗</span>
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            CleverCompanion
          </h1>
          <p className="text-gray-600 mt-2">Client Dashboard Login</p>
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
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="admin@yourcompany.com"
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
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter your password"
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
              className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 px-4 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
            >
              {isLoading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600 text-sm">
              Don&apos;t have an account?{' '}
              <a href="/client-signup" className="text-indigo-600 hover:text-indigo-700 font-medium">
                Sign up here
              </a>
            </p>
          </div>

          <div className="mt-4 text-center">
            <p className="text-gray-500 text-xs">
              Need help? Contact support at{' '}
              <a href="mailto:support@clevercompanion.com" className="text-indigo-600">
                support@clevercompanion.com
              </a>
            </p>
          </div>
        </div>

        {/* Test Credentials */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-800 mb-2">Test Credentials</h3>
          <div className="text-blue-700 text-sm space-y-1">
            <p><strong>Email:</strong> admin@abcmotors.com.sg</p>
            <p><strong>Password:</strong> password123</p>
          </div>
        </div>

        {/* Super Admin Access */}
        <div className="mt-4 text-center">
          <a 
            href="/super-admin-login" 
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            Super Admin Access
          </a>
        </div>
      </div>
    </div>
  );
}