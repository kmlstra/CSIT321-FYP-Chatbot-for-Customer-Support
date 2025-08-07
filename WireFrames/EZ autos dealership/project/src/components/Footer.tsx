import React from 'react';
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Facebook, Twitter, Instagram, Youtube, MapPin, Phone, Mail, Car } from 'lucide-react';
import { getContactInfo } from '../lib/api';

interface ContactInfo {
  id: string;
  type: string;
  label: string;
  value: string;
  icon: string;
  is_active: boolean;
}

const Footer: React.FC = () => {
  const [contactInfo, setContactInfo] = useState<ContactInfo[]>([]);

  useEffect(() => {
    fetchContactInfo();
  }, []);

  const fetchContactInfo = async () => {
    try {
      const data = await getContactInfo();
      setContactInfo(data);
    } catch (error) {
      console.error('Error fetching contact info for footer:', error);
    }
  };

  const getContactValue = (type: string) => {
    const info = contactInfo.find(item => item.type === type);
    return info ? info.value : '';
  };

  const formatBusinessHours = (hours: string) => {
    return hours.split('\n').map((line, index) => (
      <p key={index} className="text-sm">{line}</p>
    ));
  };

  return (
    <footer className="bg-gray-900 text-gray-300">
      {/* Main footer content */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Company info */}
          <div>
            <div className="flex items-center mb-4">
              <Car size={24} className="text-blue-400 mr-2" />
              <h2 className="text-xl font-bold text-white">EZ Autos</h2>
            </div>
            <p className="mb-4">
              Your trusted partner in finding the perfect vehicle. Quality cars, exceptional service, and seamless experience.
            </p>
            <div className="flex space-x-4">
              <a href="https://facebook.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white transition-colors">
                <Facebook size={20} />
              </a>
              <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white transition-colors">
                <Twitter size={20} />
              </a>
              <a href="https://instagram.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white transition-colors">
                <Instagram size={20} />
              </a>
              <a href="https://youtube.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white transition-colors">
                <Youtube size={20} />
              </a>
            </div>
          </div>
          
          {/* Quick links */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Quick Links</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/" className="hover:text-white transition-colors">Home</Link>
              </li>
              <li>
                <Link to="/search" className="hover:text-white transition-colors">Search Inventory</Link>
              </li>
              <li>
                <Link to="/finance" className="hover:text-white transition-colors">Financial Planner</Link>
              </li>
              <li>
                <Link to="/faq" className="hover:text-white transition-colors">FAQ</Link>
              </li>
              <li>
                <Link to="/contact" className="hover:text-white transition-colors">Contact Us</Link>
              </li>
            </ul>
          </div>
          
          {/* Contact information */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Contact Us</h3>
            <ul className="space-y-3">
              <li className="flex items-start">
                <MapPin size={18} className="text-blue-400 mr-2 mt-1 flex-shrink-0" />
                <span>{getContactValue('address') || '123 Auto Boulevard, Car City, CC 12345'}</span>
              </li>
              <li className="flex items-center">
                <Phone size={18} className="text-blue-400 mr-2 flex-shrink-0" />
                <span>{getContactValue('phone') || '(555) 123-4567'}</span>
              </li>
              <li className="flex items-center">
                <Mail size={18} className="text-blue-400 mr-2 flex-shrink-0" />
                <span>{getContactValue('email') || 'info@ezautos.com'}</span>
              </li>
            </ul>
            <div className="mt-4">
              <h4 className="font-medium text-white mb-2">Business Hours</h4>
              {getContactValue('hours') ? 
                formatBusinessHours(getContactValue('hours')) :
                <>
                  <p className="text-sm">Monday - Friday: 9AM - 8PM</p>
                  <p className="text-sm">Saturday: 10AM - 6PM</p>
                  <p className="text-sm">Sunday: 11AM - 5PM</p>
                </>
              }
            </div>
          </div>
          
          {/* Services */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Our Services</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/search" className="hover:text-white transition-colors">New Vehicles</Link>
              </li>
              <li>
                <Link to="/search" className="hover:text-white transition-colors">Pre-owned Vehicles</Link>
              </li>
              <li>
                <Link to="/finance" className="hover:text-white transition-colors">Vehicle Financing</Link>
              </li>
              <li>
                <Link to="/contact" className="hover:text-white transition-colors">Service Center</Link>
              </li>
              <li>
                <Link to="/contact" className="hover:text-white transition-colors">Parts & Accessories</Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
      
      {/* Copyright */}
      <div className="bg-gray-950 py-4">
        <div className="container mx-auto px-4 text-center text-sm">
          <p>&copy; {new Date().getFullYear()} EZ Autos. All rights reserved.</p>
          <div className="mt-2 space-x-4">
            <Link to="/contact" className="hover:text-white transition-colors">Privacy Policy</Link>
            <Link to="/contact" className="hover:text-white transition-colors">Terms of Service</Link>
            <Link to="/contact" className="hover:text-white transition-colors">Cookie Policy</Link>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;