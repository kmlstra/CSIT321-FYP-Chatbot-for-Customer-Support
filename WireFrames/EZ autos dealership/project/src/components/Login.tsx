import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, getProfile } from '../lib/api';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [debugInfo, setDebugInfo] = useState<string>('');
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const profile = await getProfile();
        console.log('Already authenticated:', profile);
        // If user is already logged in, redirect based on role
        if (profile.role === 'admin') {
          navigate('/admin');
        } else {
          navigate('/');
        }
      } catch (error) {
        // User is not authenticated - stay on login page
        console.log('Not authenticated, staying on login page');
      }
    };

    checkAuth();
  }, [navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setDebugInfo('');

    try {
      console.log('Attempting login with:', email);
      const data = await login(email, password);
      console.log('Login response:', data);
      setDebugInfo(`Login successful: ${JSON.stringify(data)}`);

      if (data.email) {
        // Store authentication state immediately
        localStorage.setItem('isAuthenticated', 'true');
        localStorage.setItem('userRole', data.role);
        localStorage.setItem('userEmail', data.email);

        console.log('Stored auth data:', {
          role: data.role,
          email: data.email
        });

        // Add a small delay to ensure the API session is properly set
        setTimeout(() => {
          // Force a page reload to update all components with new auth state
          if (data.role === 'admin') {
            console.log('Redirecting admin to dashboard');
            window.location.href = '/admin';
          } else {
            console.log('Redirecting user to home');
            window.location.href = '/';
          }
        }, 100);
      }
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.response?.data?.error || err.message || 'Invalid credentials');
      setDebugInfo(`Error: ${JSON.stringify(err.response?.data || err.message)}`);
      localStorage.clear();
    } finally {
      setLoading(false);
    }
  };

  return (
      <div className="flex justify-center items-center min-h-screen bg-gray-50 pt-16">
        <div className="bg-white shadow-md rounded-lg px-8 pt-6 pb-8 mb-4 w-full max-w-md">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Sign In</h2>

          {error && (
              <div className="bg-red-50 text-red-500 p-3 rounded-md mb-4">
                {error}
              </div>
          )}

          {debugInfo && (
              <div className="bg-blue-50 text-blue-700 p-3 rounded-md mb-4 text-xs">
                Debug: {debugInfo}
              </div>
          )}

          <form onSubmit={handleLogin}>
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="email">
                Email
              </label>
              <input
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
              />
            </div>

            <div className="mb-6">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">
                Password
              </label>
              <input
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
              />
            </div>

            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <input
                    id="remember"
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="remember" className="ml-2 block text-sm text-gray-700">
                  Remember me
                </label>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <button
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full"
                  type="submit"
                  disabled={loading}
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </button>
            </div>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Don't have an account?{' '}
                <a href="/register" className="text-blue-600 hover:text-blue-800 font-medium">
                  Create one
                </a>
              </p>
            </div>

            <div className="mt-4 text-center">
              <p className="text-xs text-gray-500">
                Test admin credentials: admin@example.com / admin
              </p>
            </div>
          </form>
        </div>
      </div>
  );
};

export default Login;