import React from 'react';
import { Mail, Phone, MapPin, Send, MessageCircle } from 'lucide-react';
import { useApi } from '../hooks/useApi';

interface ContactInfo {
  _id: string;
  phone: {
    sales: string;
    support: string;
  };
  email: {
    sales: string;
    support: string;
  };
  address: {
    street: string;
    city: string;
    state: string;
    zip: string;
  };
  socialMedia: {
    facebook: string;
    twitter: string;
    linkedin: string;
    instagram: string;
  };
}

const ContactPage: React.FC = () => {
  const { data: contactInfo, loading, error } = useApi<ContactInfo>('/api/contact');

  if (loading) {
    return (
      <div className="pt-20 min-h-screen">
        {/* Hero Section - Always show */}
        <div className="bg-[#0A74DA] text-white py-16">
          <div className="container mx-auto px-5 text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Get in Touch</h1>
            <p className="text-xl max-w-3xl mx-auto">
              We're here to answer your questions and help you get the most out of CleverCompanion.
            </p>
          </div>
        </div>

        {/* Loading State */}
        <div className="py-16">
          <div className="container mx-auto px-5">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
              {/* Contact Form - Always show */}
              <div className="bg-white p-8 rounded-xl shadow-lg">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Send Us a Message</h2>
                
                <form className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-1">
                        First Name
                      </label>
                      <input
                        type="text"
                        id="firstName"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
                        placeholder="John"
                      />
                    </div>
                    <div>
                      <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-1">
                        Last Name
                      </label>
                      <input
                        type="text"
                        id="lastName"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
                        placeholder="Doe"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      id="email"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
                      placeholder="john@yourdealership.com"
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="dealership" className="block text-sm font-medium text-gray-700 mb-1">
                      Dealership Name
                    </label>
                    <input
                      type="text"
                      id="dealership"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
                      placeholder="ABC Motors"
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-1">
                      Subject
                    </label>
                    <select
                      id="subject"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
                    >
                      <option>Select a subject</option>
                      <option>Sales Inquiry</option>
                      <option>Technical Support</option>
                      <option>Billing Question</option>
                      <option>Partnership Opportunity</option>
                      <option>Other</option>
                    </select>
                  </div>
                  
                  <div>
                    <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-1">
                      Message
                    </label>
                    <textarea
                      id="message"
                      rows={5}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
                      placeholder="How can we help you today?"
                    ></textarea>
                  </div>
                  
                  <button
                    type="submit"
                    className="w-full bg-[#0A74DA] text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-600 transition-colors duration-300 flex items-center justify-center gap-2"
                  >
                    Send Message
                    <Send size={18} />
                  </button>
                </form>
              </div>
              
              {/* Contact Information Loading */}
              <div className="flex flex-col justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">Contact Information</h2>
                  
                  <div className="space-y-6 mb-12">
                    <div className="animate-pulse">
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 rounded-full bg-gray-200 flex-shrink-0"></div>
                        <div className="flex-1">
                          <div className="h-5 bg-gray-200 rounded w-1/4 mb-2"></div>
                          <div className="h-4 bg-gray-200 rounded w-3/4 mb-1"></div>
                          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="animate-pulse">
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 rounded-full bg-gray-200 flex-shrink-0"></div>
                        <div className="flex-1">
                          <div className="h-5 bg-gray-200 rounded w-1/4 mb-2"></div>
                          <div className="h-4 bg-gray-200 rounded w-3/4 mb-1"></div>
                          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="animate-pulse">
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 rounded-full bg-gray-200 flex-shrink-0"></div>
                        <div className="flex-1">
                          <div className="h-5 bg-gray-200 rounded w-1/3 mb-2"></div>
                          <div className="h-4 bg-gray-200 rounded w-4/5 mb-1"></div>
                          <div className="h-4 bg-gray-200 rounded w-3/5"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-6 rounded-xl border border-gray-200 mt-6">
                  <div className="animate-pulse">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-full bg-gray-200 flex-shrink-0"></div>
                      <div className="h-5 bg-gray-200 rounded w-1/2"></div>
                    </div>
                    <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
                    <div className="h-10 bg-gray-200 rounded w-full"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Map Section - Always show */}
        <div className="bg-gray-50 py-16">
          <div className="container mx-auto px-5 text-center mb-10">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Visit Our Office</h2>
            <p className="text-gray-600">
              We're located in the heart of San Francisco's tech district.
            </p>
          </div>
          
          <div className="aspect-video max-w-5xl mx-auto bg-gray-200 rounded-xl overflow-hidden">
            <div className="h-full w-full flex items-center justify-center bg-gray-300">
              <p className="text-gray-600 font-medium">Interactive Map Would Be Displayed Here</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pt-20 min-h-screen">
        {/* Hero Section */}
        <div className="bg-[#0A74DA] text-white py-16">
          <div className="container mx-auto px-5 text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Get in Touch</h1>
            <p className="text-xl max-w-3xl mx-auto">
              We're here to answer your questions and help you get the most out of CleverCompanion.
            </p>
          </div>
        </div>

        {/* Error State */}
        <div className="py-16">
          <div className="container mx-auto px-5">
            <div className="max-w-2xl mx-auto text-center">
              <div className="bg-white rounded-xl shadow-lg p-8 border border-red-200">
                <div className="text-red-600 mb-4">
                  <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Unable to Load Contact Information</h3>
                <p className="text-gray-600 mb-4">We're having trouble loading the contact details. Please try again or contact us directly.</p>
                <button 
                  onClick={() => window.location.reload()} 
                  className="bg-[#0A74DA] text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!contactInfo) {
    return (
      <div className="pt-20 min-h-screen">
        {/* Hero Section */}
        <div className="bg-[#0A74DA] text-white py-16">
          <div className="container mx-auto px-5 text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Get in Touch</h1>
            <p className="text-xl max-w-3xl mx-auto">
              We're here to answer your questions and help you get the most out of CleverCompanion.
            </p>
          </div>
        </div>

        {/* No Data State */}
        <div className="py-16">
          <div className="container mx-auto px-5">
            <div className="max-w-2xl mx-auto text-center">
              <div className="bg-white rounded-xl shadow-lg p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Contact Information Unavailable</h3>
                <p className="text-gray-600 mb-4">Please check back later or use the contact form above.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="pt-20">
      {/* Hero Section */}
      <div className="bg-[#0A74DA] text-white py-16">
        <div className="container mx-auto px-5 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">Get in Touch</h1>
          <p className="text-xl max-w-3xl mx-auto">
            We're here to answer your questions and help you get the most out of CleverCompanion.
          </p>
        </div>
      </div>

      {/* Contact Information & Form */}
      <div className="py-16">
        <div className="container mx-auto px-5">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {/* Contact Form */}
            <div className="bg-white p-8 rounded-xl shadow-lg">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Send Us a Message</h2>
              
              <form className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-1">
                      First Name
                    </label>
                    <input
                      type="text"
                      id="firstName"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
                      placeholder="John"
                    />
                  </div>
                  <div>
                    <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-1">
                      Last Name
                    </label>
                    <input
                      type="text"
                      id="lastName"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
                      placeholder="Doe"
                    />
                  </div>
                </div>
                
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    id="email"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
                    placeholder="john@yourdealership.com"
                  />
                </div>
                
                <div>
                  <label htmlFor="dealership" className="block text-sm font-medium text-gray-700 mb-1">
                    Dealership Name
                  </label>
                  <input
                    type="text"
                    id="dealership"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
                    placeholder="ABC Motors"
                  />
                </div>
                
                <div>
                  <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-1">
                    Subject
                  </label>
                  <select
                    id="subject"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
                  >
                    <option>Select a subject</option>
                    <option>Sales Inquiry</option>
                    <option>Technical Support</option>
                    <option>Billing Question</option>
                    <option>Partnership Opportunity</option>
                    <option>Other</option>
                  </select>
                </div>
                
                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-1">
                    Message
                  </label>
                  <textarea
                    id="message"
                    rows={5}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
                    placeholder="How can we help you today?"
                  ></textarea>
                </div>
                
                <button
                  type="submit"
                  className="w-full bg-[#0A74DA] text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-600 transition-colors duration-300 flex items-center justify-center gap-2"
                >
                  Send Message
                  <Send size={18} />
                </button>
              </form>
            </div>
            
            {/* Contact Information */}
            <div className="flex flex-col justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Contact Information</h2>
                
                <div className="space-y-6 mb-12">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                      <Phone className="h-5 w-5 text-[#0A74DA]" />
                    </div>
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">Phone</h3>
                      <p className="text-gray-600">Sales: {contactInfo.phone.sales}</p>
                      <p className="text-gray-600">Support: {contactInfo.phone.support}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                      <Mail className="h-5 w-5 text-[#0A74DA]" />
                    </div>
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">Email</h3>
                      <p className="text-gray-600">{contactInfo.email.sales}</p>
                      <p className="text-gray-600">{contactInfo.email.support}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                      <MapPin className="h-5 w-5 text-[#0A74DA]" />
                    </div>
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">Office Location</h3>
                      <p className="text-gray-600">{contactInfo.address.street}</p>
                      <p className="text-gray-600">{contactInfo.address.city}, {contactInfo.address.state} {contactInfo.address.zip}</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-50 p-6 rounded-xl border border-gray-200 mt-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                    <MessageCircle className="h-5 w-5 text-[#0A74DA]" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900">Live Chat Support</h3>
                </div>
                <p className="text-gray-600 mb-4">
                  Need immediate assistance? Our support team is available for live chat during business hours.
                </p>
                <button className="bg-[#0A74DA] text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-600 transition-colors duration-300 w-full">
                  Start Live Chat
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Map Section */}
      <div className="bg-gray-50 py-16">
        <div className="container mx-auto px-5 text-center mb-10">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Visit Our Office</h2>
          <p className="text-gray-600">
            We're located in the heart of San Francisco's tech district.
          </p>
        </div>
        
        <div className="aspect-video max-w-5xl mx-auto bg-gray-200 rounded-xl overflow-hidden">
          <div className="h-full w-full flex items-center justify-center bg-gray-300">
            <p className="text-gray-600 font-medium">Interactive Map Would Be Displayed Here</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContactPage;