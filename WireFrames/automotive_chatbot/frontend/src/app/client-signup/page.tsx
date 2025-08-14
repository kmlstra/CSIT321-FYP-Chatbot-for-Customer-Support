'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { API_CONFIG } from '../../config/api';

export default function ClientSignupPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    business_name: '',
    domain: '',
    contact_email: '',
    admin_user: {
      name: '',
      email: '',
      password: ''
    },
    contact_info: {
      phone: '',
      address: ''
    }
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [registrationResult, setRegistrationResult] = useState<{ client_id: string; message: string; next_steps?: string[] } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_CONFIG.API_URL}/api/client-registration/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(true);
        setRegistrationResult(data);
      } else {
        setError(data.detail || 'Registration failed');
      }
    } catch (err) {
      console.error('Registration error:', err);
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string, nested?: string) => {
    if (nested) {
      setFormData(prev => ({
        ...prev,
        [nested]: {
          ...(prev[nested as keyof typeof prev] as object || {}),
          [field]: value
        }
      }));
    } else {
      setFormData(prev => ({ ...prev, [field]: value }));
    }
  };





  if (success && registrationResult) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100 flex items-center justify-center">
        <div className="max-w-4xl w-full mx-4">
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-2xl">✓</span>
              </div>
              <h1 className="text-3xl font-bold text-green-600">Registration Successful!</h1>
              <p className="text-gray-600 mt-2">{registrationResult.message}</p>
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h3 className="font-semibold text-blue-800 mb-3">Next Steps:</h3>
                <ul className="space-y-2 text-blue-700">
                  {registrationResult.next_steps?.map((step: string, index: number) => (
                    <li key={index} className="flex items-start">
                      <span className="font-bold mr-2">{index + 1}.</span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="font-semibold text-gray-800 mb-3">Account Details:</h3>
                <p className="text-sm text-gray-600 mb-2">
                  <strong>Client ID:</strong> {registrationResult.client_id}
                </p>
                <p className="text-sm text-gray-600 mb-2">
                  <strong>Business:</strong> {formData.business_name}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>Domain:</strong> {formData.domain}
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  Please save these details for your records.
                </p>
              </div>
            </div>

            {/* Payment Notice */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
              <h3 className="font-semibold text-yellow-800 mb-3 flex items-center">
                <span className="text-xl mr-2">💳</span>
                Payment Required
              </h3>
              <p className="text-yellow-700 text-sm mb-4">
                Your account has been created successfully! To activate your chatbot and access the embed code, please complete your payment and setup your profile in the dashboard.
              </p>
              <div className="bg-yellow-100 rounded-lg p-3">
                <p className="text-yellow-800 text-sm font-medium">
                  📋 Complete these steps after login:
                </p>
                <ul className="text-yellow-700 text-sm mt-2 space-y-1">
                  <li>• Complete payment process</li>
                  <li>• Setup your business profile</li>
                  <li>• Configure branding and contact information</li>
                  <li>• Get your personalized embed code</li>
                </ul>
              </div>
            </div>

            <div className="flex space-x-4">
              <button
                onClick={() => router.push('/')}
                className="flex-1 bg-indigo-600 text-white py-3 px-6 rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Go to Login
              </button>
              <button
                onClick={() => {
                  setSuccess(false);
                  setRegistrationResult(null);
                  setFormData({
                    business_name: '',
                    domain: '',
                    contact_email: '',
                    admin_user: { name: '', email: '', password: '' },
                    contact_info: { phone: '', address: '' }
                  });
                }}
                className="flex-1 bg-gray-600 text-white py-3 px-6 rounded-lg hover:bg-gray-700 transition-colors"
              >
                Register Another
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-100 flex items-center justify-center">
      <div className="max-w-2xl w-full mx-4">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4">
            <span className="text-white text-2xl">🚗</span>
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            CleverCompanion
          </h1>
          <p className="text-gray-600 mt-2">Register Your Automotive Business</p>
        </div>

        {/* Registration Form */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Business Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Business Information</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Business Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.business_name}
                  onChange={(e) => handleInputChange('business_name', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Enter your business name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Domain/Website *
                </label>
                <input
                  type="text"
                  required
                  value={formData.domain}
                  onChange={(e) => handleInputChange('domain', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Enter your website domain"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Contact Email *
                </label>
                <input
                  type="email"
                  required
                  value={formData.contact_email}
                  onChange={(e) => handleInputChange('contact_email', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Enter contact email"
                />
              </div>
            </div>

            {/* Admin User */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Admin User Account</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Admin Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.admin_user.name}
                  onChange={(e) => handleInputChange('name', e.target.value, 'admin_user')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Enter admin full name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Admin Email *
                </label>
                <input
                  type="email"
                  required
                  value={formData.admin_user.email}
                  onChange={(e) => handleInputChange('email', e.target.value, 'admin_user')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Enter admin email"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Password *
                </label>
                <input
                  type="password"
                  required
                  value={formData.admin_user.password}
                  onChange={(e) => handleInputChange('password', e.target.value, 'admin_user')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Create a secure password"
                  minLength={8}
                />
              </div>
            </div>

            {/* Contact Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Contact Information</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone Number
                </label>
                <input
                  type="tel"
                  value={formData.contact_info.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value, 'contact_info')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Enter phone number"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Business Address
                </label>
                <textarea
                  value={formData.contact_info.address}
                  onChange={(e) => handleInputChange('address', e.target.value, 'contact_info')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Enter business address"
                  rows={3}
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 px-6 rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </button>

            <div className="text-center">
              <p className="text-sm text-gray-600">
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => router.push('/')}
                  className="text-indigo-600 hover:text-indigo-700 font-medium"
                >
                  Sign in here
                </button>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}