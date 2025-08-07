import React from 'react';
import React, { useState, useEffect } from 'react';
import { MapPin, Phone, Mail, Clock, Send } from 'lucide-react';
import { getContactInfo } from '../lib/api';

interface ContactInfo {
  id: string;
  type: string;
  label: string;
  value: string;
  icon: string;
  is_active: boolean;
}

const Contact: React.FC = () => {
  const [contactInfo, setContactInfo] = useState<ContactInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchContactInfo();
  }, []);

  const fetchContactInfo = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getContactInfo();
      setContactInfo(data);
    } catch (err: any) {
      console.error('Error fetching contact info:', err);
      setError('Failed to load contact information');
    } finally {
      setLoading(false);
    }
  };

  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'MapPin':
        return <MapPin size={24} className="text-blue-600 flex-shrink-0" />;
      case 'Phone':
        return <Phone size={24} className="text-blue-600 flex-shrink-0" />;
      case 'Mail':
        return <Mail size={24} className="text-blue-600 flex-shrink-0" />;
      case 'Clock':
        return <Clock size={24} className="text-blue-600 flex-shrink-0" />;
      default:
        return <MapPin size={24} className="text-blue-600 flex-shrink-0" />;
    }
  };

  const formatValue = (value: string) => {
    return value.split('\n').map((line, index) => (
      <React.Fragment key={index}>
        {line}
        {index < value.split('\n').length - 1 && <br />}
      </React.Fragment>
    ));
  };

  if (loading) {
    return (
      <div className="pt-20 min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading contact information...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pt-20 min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 text-lg mb-4">{error}</p>
          <button 
            onClick={fetchContactInfo}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="pt-20 min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-800 mb-2">Contact Us</h1>
              <p className="text-gray-600 mb-8">
                We're here to help! Send us a message and we'll get back to you as soon as possible.
              </p>
              
              <form className="space-y-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      First Name
                    </label>
                    <input
                      type="text"
                      className="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter your first name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Last Name
                    </label>
                    <input
                      type="text"
                      className="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter your last name"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    className="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter your email"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    className="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter your phone number"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Subject
                  </label>
                  <select className="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500">
                    <option value="">Select a subject</option>
                    <option value="sales">Sales Inquiry</option>
                    <option value="service">Service Request</option>
                    <option value="parts">Parts Inquiry</option>
                    <option value="finance">Financing Questions</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Message
                  </label>
                  <textarea
                    rows={4}
                    className="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500"
                    placeholder="How can we help you?"
                  ></textarea>
                </div>
                
                <button
                  type="submit"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-md transition-colors flex items-center justify-center gap-2"
                >
                  <Send size={20} />
                  Send Message
                </button>
              </form>
            </div>
            
            <div>
              <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Contact Information</h2>
                <div className="space-y-4">
                  {contactInfo.map((info) => (
                    <div key={info.id} className="flex items-start gap-3">
                      {getIcon(info.icon)}
                      <div>
                        <h3 className="font-medium text-gray-800">{info.label}</h3>
                        <p className="text-gray-600">{formatValue(info.value)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Our Location</h2>
                <div className="aspect-w-16 aspect-h-9 rounded-lg overflow-hidden">
                  <img
                    src="https://images.pexels.com/photos/244133/pexels-photo-244133.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2"
                    alt="EZ Autos Dealership"
                    className="w-full h-full object-cover"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Contact;