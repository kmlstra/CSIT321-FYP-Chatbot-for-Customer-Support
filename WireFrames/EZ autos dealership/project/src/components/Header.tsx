import React, { useState, useEffect, useRef } from 'react';
import { SearchIcon, DollarSign, HelpCircle, PhoneCall, Car, Menu, X, Home, LogIn, UserCircle, Settings } from 'lucide-react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { NavigationLink } from '../types';
import { getProfile, logout } from '../lib/api';

const Header: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const location = useLocation();

  const navLinks: NavigationLink[] = [
    { name: 'Home', path: '/', icon: 'home' },
    { name: 'Search', path: '/search', icon: 'search' },
    { name: 'Financial Planner', path: '/finance', icon: 'dollar' },
    { name: 'FAQ', path: '/faq', icon: 'help' },
    { name: 'Contact Us', path: '/contact', icon: 'phone' }
  ];

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Check auth on component mount and location changes
  useEffect(() => {
    checkAuth();
  }, [location.pathname]);

  // Also check auth when localStorage changes (for cross-tab updates)
  useEffect(() => {
    const handleStorageChange = () => {
      checkAuth();
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const checkAuth = async () => {
    try {
      console.log('Checking authentication...');
      const profile = await getProfile();
      console.log('Profile received:', profile);

      setUser(profile.user);
      const adminStatus = profile.role === 'admin';
      setIsAdmin(adminStatus);

      console.log('User set to:', profile.user);
      console.log('Admin status set to:', adminStatus);

      // Also update localStorage to keep it in sync
      if (profile.user) {
        localStorage.setItem('isAuthenticated', 'true');
        localStorage.setItem('userRole', profile.role);
        localStorage.setItem('userEmail', profile.user.email);
      }
    } catch (error) {
      console.log('Authentication check failed:', error);
      // User is not authenticated - this is fine, don't redirect
      setUser(null);
      setIsAdmin(false);
      // Clear any stale localStorage data
      localStorage.removeItem('isAuthenticated');
      localStorage.removeItem('userRole');
      localStorage.removeItem('userEmail');
    } finally {
      setAuthChecked(true);
    }
  };

  const handleLogout = async () => {
    console.log('Logout initiated...');

    // Immediately clear UI state
    setUser(null);
    setIsAdmin(false);
    setDropdownOpen(false);
    setMobileMenuOpen(false);

    // Clear all local storage immediately
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('userRole');
    localStorage.removeItem('userEmail');
    localStorage.clear();
    sessionStorage.clear();

    try {
      // Try to call logout API
      console.log('Calling logout API...');
      await logout();
      console.log('Logout API successful');
    } catch (error) {
      console.error('Logout API failed:', error);
      // Continue with logout even if API call fails
    }

    // Force immediate navigation and page reload
    console.log('Redirecting to home...');
    window.location.replace('/');
  };

  const renderIcon = (iconName: string) => {
    switch (iconName) {
      case 'home':
        return <Home size={18} />;
      case 'search':
        return <SearchIcon size={18} />;
      case 'dollar':
        return <DollarSign size={18} />;
      case 'help':
        return <HelpCircle size={18} />;
      case 'phone':
        return <PhoneCall size={18} />;
      default:
        return null;
    }
  };

  // Don't render anything until auth check is complete
  if (!authChecked) {
    return null;
  }

  console.log('Rendering Header - User:', user, 'IsAdmin:', isAdmin);

  return (
      <header
          className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
              isScrolled
                  ? 'bg-white shadow-md py-2'
                  : 'bg-gradient-to-b from-black/70 to-transparent py-4'
          }`}
      >
        <div className="container mx-auto px-4 flex justify-between items-center">
          <Link to="/" className="flex items-center">
            <Car size={28} className={`${isScrolled ? 'text-blue-600' : 'text-white'} mr-2`} />
            <h1 className={`text-2xl font-bold ${isScrolled ? 'text-gray-800' : 'text-white'}`}>
              EZ Autos
            </h1>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            {navLinks.map((link) => (
                <Link
                    key={link.name}
                    to={link.path}
                    className={`flex items-center space-x-1 font-medium transition-colors ${
                        isScrolled
                            ? 'text-gray-700 hover:text-blue-600'
                            : 'text-gray-100 hover:text-white'
                    }`}
                >
                  {renderIcon(link.icon || '')}
                  <span>{link.name}</span>
                </Link>
            ))}

            {user ? (
                <div className="relative" ref={dropdownRef}>
                  <button
                      onClick={() => setDropdownOpen(!dropdownOpen)}
                      className={`flex items-center space-x-2 font-medium ${
                          isScrolled ? 'text-gray-700 hover:text-blue-600' : 'text-gray-100 hover:text-white'
                      }`}
                  >
                    <UserCircle size={20} />
                    <span>{user.email}</span>
                  </button>
                  {dropdownOpen && (
                      <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                        {isAdmin ? (
                            <Link
                                to="/admin"
                                className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                onClick={() => setDropdownOpen(false)}
                            >
                              <Settings size={16} className="mr-2" />
                              Admin Dashboard
                            </Link>
                        ) : (
                           <>
                             <Link
                                 to="/dashboard"
                                 className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                 onClick={() => setDropdownOpen(false)}
                             >
                               <UserCircle size={16} className="mr-2" />
                               My Dashboard
                             </Link>
                            <Link
                                to="/profile"
                                className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                onClick={() => setDropdownOpen(false)}
                            >
                              <UserCircle size={16} className="mr-2" />
                              My Profile
                            </Link>
                           </>
                        )}
                        <button
                            onClick={handleLogout}
                            className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                          <LogIn size={16} className="mr-2" />
                          Sign Out
                        </button>
                      </div>
                  )}
                </div>
            ) : (
                <div className="flex items-center space-x-4">
                  <Link
                      to="/login"
                      className={`flex items-center space-x-1 font-medium ${
                          isScrolled ? 'text-gray-700 hover:text-blue-600' : 'text-gray-100 hover:text-white'
                      }`}
                  >
                    <LogIn size={18} />
                    <span>Sign In</span>
                  </Link>
                  <Link
                      to="/register"
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors"
                  >
                    Register
                  </Link>
                </div>
            )}
          </nav>

          {/* Mobile menu button */}
          <button
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
          >
            {mobileMenuOpen
                ? <X size={24} className={isScrolled ? 'text-gray-800' : 'text-white'} />
                : <Menu size={24} className={isScrolled ? 'text-gray-800' : 'text-white'} />
            }
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
            <div className="md:hidden bg-white shadow-lg">
              <div className="container mx-auto px-4 py-3">
                {navLinks.map((link) => (
                    <Link
                        key={link.name}
                        to={link.path}
                        className="flex items-center space-x-2 py-3 border-b border-gray-200 text-gray-700"
                        onClick={() => setMobileMenuOpen(false)}
                    >
                      {renderIcon(link.icon || '')}
                      <span>{link.name}</span>
                    </Link>
                ))}
                {user ? (
                    <>
                      {isAdmin ? (
                          <Link
                              to="/admin"
                              className="flex items-center space-x-2 py-3 border-b border-gray-200 text-gray-700"
                              onClick={() => setMobileMenuOpen(false)}
                          >
                            <Settings size={18} />
                            <span>Admin Dashboard</span>
                          </Link>
                      ) : (
                          <Link
                              to="/profile"
                              className="flex items-center space-x-2 py-3 border-b border-gray-200 text-gray-700"
                              onClick={() => setMobileMenuOpen(false)}
                          >
                            <UserCircle size={18} />
                            <span>My Profile</span>
                          </Link>
                      )}
                      <button
                          onClick={() => {
                            setMobileMenuOpen(false);
                            handleLogout();
                          }}
                          className="flex items-center space-x-2 py-3 text-gray-700 w-full"
                      >
                        <LogIn size={18} />
                        <span>Sign Out</span>
                      </button>
                    </>
                ) : (
                    <>
                      <Link
                          to="/dashboard"
                          className="flex items-center space-x-2 py-3 border-b border-gray-200 text-gray-700"
                          onClick={() => setMobileMenuOpen(false)}
                      >
                        <UserCircle size={18} />
                        <span>My Dashboard</span>
                      </Link>
                      <Link
                          to="/login"
                          className="flex items-center space-x-2 py-3 border-b border-gray-200 text-gray-700"
                          onClick={() => setMobileMenuOpen(false)}
                      >
                        <LogIn size={18} />
                        <span>Sign In</span>
                      </Link>
                      <Link
                          to="/register"
                          className="flex items-center space-x-2 py-3 text-gray-700"
                          onClick={() => setMobileMenuOpen(false)}
                      >
                        <UserCircle size={18} />
                        <span>Register</span>
                      </Link>
                    </>
                )}
              </div>
            </div>
        )}
      </header>
  );
};

export default Header;