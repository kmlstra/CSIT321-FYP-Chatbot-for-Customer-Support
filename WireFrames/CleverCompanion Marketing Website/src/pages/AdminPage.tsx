import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';
import { 
  Users, 
  MessageSquare, 
  HelpCircle, 
  Phone, 
  DollarSign,
  Plus,
  Edit,
  Trash2,
  Save,
  X
} from 'lucide-react';
import { useApi, useApiMutation } from '../hooks/useApi';

interface Testimonial {
  _id?: string;
  quote: string;
  author: string;
  position: string;
  avatar: string;
  rating: number;
  isActive: boolean;
}

interface FAQ {
  _id?: string;
  question: string;
  answer: string;
  category: string;
  isActive: boolean;
  order: number;
}

interface Contact {
  _id?: string;
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

interface Pricing {
  _id?: string;
  planName: string;
  price: number;
  currency: string;
  billingPeriod: string;
  features: string[];
  isActive: boolean;
  isPopular: boolean;
}

const AdminPage: React.FC = () => {
  const { user, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState('testimonials');
  const [editingItem, setEditingItem] = useState<any>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  const { mutate } = useApiMutation();

  // API hooks
  const { data: testimonials, refetch: refetchTestimonials } = useApi<Testimonial[]>('/api/testimonials/admin', { requireAuth: true });
  const { data: faqs, refetch: refetchFaqs } = useApi<FAQ[]>('/api/faqs/admin', { requireAuth: true });
  const { data: contact, refetch: refetchContact } = useApi<Contact>('/api/contact', { requireAuth: true });
  const { data: pricing, refetch: refetchPricing } = useApi<Pricing[]>('/api/pricing/admin', { requireAuth: true });

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#0A74DA]"></div>
      </div>
    );
  }

  if (!user || user.role !== 'admin') {
    return <Navigate to="/admin/login" replace />;
  }

  const handleSave = async (type: string, data: any) => {
    try {
      if (data._id) {
        // Update existing
        await mutate(`/api/${type}/${data._id}`, {
          method: 'PUT',
          body: data,
          requireAuth: true
        });
      } else {
        // Create new
        await mutate(`/api/${type}`, {
          method: 'POST',
          body: data,
          requireAuth: true
        });
      }

      // Refetch data
      switch (type) {
        case 'testimonials':
          refetchTestimonials();
          break;
        case 'faqs':
          refetchFaqs();
          break;
        case 'contact':
          refetchContact();
          break;
        case 'pricing':
          refetchPricing();
          break;
      }

      setEditingItem(null);
      setShowAddForm(false);
    } catch (error) {
      console.error('Error saving:', error);
      alert('Error saving data. Please try again.');
    }
  };

  const handleDelete = async (type: string, id: string) => {
    if (!confirm('Are you sure you want to delete this item?')) return;

    try {
      await mutate(`/api/${type}/${id}`, {
        method: 'DELETE',
        requireAuth: true
      });

      // Refetch data
      switch (type) {
        case 'testimonials':
          refetchTestimonials();
          break;
        case 'faqs':
          refetchFaqs();
          break;
        case 'pricing':
          refetchPricing();
          break;
      }
    } catch (error) {
      console.error('Error deleting:', error);
      alert('Error deleting item. Please try again.');
    }
  };

  const TestimonialForm: React.FC<{ testimonial?: Testimonial; onSave: (data: Testimonial) => void; onCancel: () => void }> = ({ testimonial, onSave, onCancel }) => {
    const [formData, setFormData] = useState<Testimonial>(testimonial || {
      quote: '',
      author: '',
      position: '',
      avatar: 'https://randomuser.me/api/portraits/men/32.jpg',
      rating: 5,
      isActive: true
    });

    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Quote</label>
            <textarea
              value={formData.quote}
              onChange={(e) => setFormData({ ...formData, quote: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
              rows={3}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Author</label>
              <input
                type="text"
                value={formData.author}
                onChange={(e) => setFormData({ ...formData, author: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Position</label>
              <input
                type="text"
                value={formData.position}
                onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Avatar URL</label>
              <input
                type="url"
                value={formData.avatar}
                onChange={(e) => setFormData({ ...formData, avatar: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Rating</label>
              <select
                value={formData.rating}
                onChange={(e) => setFormData({ ...formData, rating: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
              >
                {[1, 2, 3, 4, 5].map(num => (
                  <option key={num} value={num}>{num} Star{num > 1 ? 's' : ''}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.isActive}
                onChange={(e) => setFormData({ ...formData, isActive: e.target.checked })}
                className="mr-2"
              />
              Active
            </label>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => onSave(formData)}
              className="bg-[#0A74DA] text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
            >
              <Save size={16} />
              Save
            </button>
            <button
              onClick={onCancel}
              className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors flex items-center gap-2"
            >
              <X size={16} />
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderTestimonials = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Manage Testimonials</h2>
        <button
          onClick={() => setShowAddForm(true)}
          className="bg-[#0A74DA] text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
        >
          <Plus size={16} />
          Add Testimonial
        </button>
      </div>

      {showAddForm && (
        <TestimonialForm
          onSave={(data) => handleSave('testimonials', data)}
          onCancel={() => setShowAddForm(false)}
        />
      )}

      <div className="grid gap-4">
        {testimonials?.map((testimonial) => (
          <div key={testimonial._id} className="bg-white p-6 rounded-lg border border-gray-200">
            {editingItem?._id === testimonial._id ? (
              <TestimonialForm
                testimonial={testimonial}
                onSave={(data) => handleSave('testimonials', { ...data, _id: testimonial._id })}
                onCancel={() => setEditingItem(null)}
              />
            ) : (
              <div className="flex justify-between items-start">
                <div className="flex-grow">
                  <p className="text-gray-700 mb-2">"{testimonial.quote}"</p>
                  <p className="font-semibold">{testimonial.author}</p>
                  <p className="text-sm text-gray-600">{testimonial.position}</p>
                  <p className="text-sm text-gray-500">Rating: {testimonial.rating}/5</p>
                  <p className="text-sm text-gray-500">Status: {testimonial.isActive ? 'Active' : 'Inactive'}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setEditingItem(testimonial)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <Edit size={16} />
                  </button>
                  <button
                    onClick={() => handleDelete('testimonials', testimonial._id!)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderFaqs = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Manage FAQs</h2>
        <button
          onClick={() => setShowAddForm(true)}
          className="bg-[#0A74DA] text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
        >
          <Plus size={16} />
          Add FAQ
        </button>
      </div>

      <div className="grid gap-4">
        {faqs?.map((faq) => (
          <div key={faq._id} className="bg-white p-6 rounded-lg border border-gray-200">
            <div className="flex justify-between items-start">
              <div className="flex-grow">
                <p className="font-semibold text-gray-900 mb-2">{faq.question}</p>
                <p className="text-gray-700 mb-2">{faq.answer}</p>
                <p className="text-sm text-gray-500">Category: {faq.category}</p>
                <p className="text-sm text-gray-500">Status: {faq.isActive ? 'Active' : 'Inactive'}</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setEditingItem(faq)}
                  className="text-blue-600 hover:text-blue-800"
                >
                  <Edit size={16} />
                </button>
                <button
                  onClick={() => handleDelete('faqs', faq._id!)}
                  className="text-red-600 hover:text-red-800"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderContact = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Manage Contact Information</h2>
      </div>
      
      {contact && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Phone Numbers</h3>
              <p className="text-gray-700">Sales: {contact.phone.sales}</p>
              <p className="text-gray-700">Support: {contact.phone.support}</p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Email Addresses</h3>
              <p className="text-gray-700">Sales: {contact.email.sales}</p>
              <p className="text-gray-700">Support: {contact.email.support}</p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Office Address</h3>
              <p className="text-gray-700">{contact.address.street}</p>
              <p className="text-gray-700">{contact.address.city}, {contact.address.state} {contact.address.zip}</p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Social Media</h3>
              <p className="text-gray-700">Facebook: {contact.socialMedia.facebook}</p>
              <p className="text-gray-700">Twitter: {contact.socialMedia.twitter}</p>
              <p className="text-gray-700">LinkedIn: {contact.socialMedia.linkedin}</p>
              <p className="text-gray-700">Instagram: {contact.socialMedia.instagram}</p>
            </div>
          </div>
          
          <div className="mt-6">
            <button
              onClick={() => setEditingItem(contact)}
              className="bg-[#0A74DA] text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
            >
              <Edit size={16} />
              Edit Contact Information
            </button>
          </div>
        </div>
      )}
    </div>
  );

  const renderPricing = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Manage Pricing Plans</h2>
        <button
          onClick={() => setShowAddForm(true)}
          className="bg-[#0A74DA] text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
        >
          <Plus size={16} />
          Add Pricing Plan
        </button>
      </div>

      <div className="grid gap-4">
        {pricing?.map((plan) => (
          <div key={plan._id} className="bg-white p-6 rounded-lg border border-gray-200">
            <div className="flex justify-between items-start">
              <div className="flex-grow">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{plan.planName}</h3>
                <p className="text-2xl font-bold text-gray-900 mb-2">
                  ${plan.price} <span className="text-sm font-normal text-gray-600">/{plan.billingPeriod}</span>
                </p>
                <div className="mb-4">
                  <h4 className="font-medium text-gray-900 mb-2">Features:</h4>
                  <ul className="list-disc list-inside text-gray-700 space-y-1">
                    {plan.features.map((feature, index) => (
                      <li key={index}>{feature}</li>
                    ))}
                  </ul>
                </div>
                <div className="flex gap-4 text-sm text-gray-500">
                  <span>Status: {plan.isActive ? 'Active' : 'Inactive'}</span>
                  {plan.isPopular && <span className="text-blue-600 font-medium">Popular Plan</span>}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setEditingItem(plan)}
                  className="text-blue-600 hover:text-blue-800"
                >
                  <Edit size={16} />
                </button>
                <button
                  onClick={() => handleDelete('pricing', plan._id!)}
                  className="text-red-600 hover:text-red-800"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const tabs = [
    { id: 'testimonials', label: 'Testimonials', icon: MessageSquare },
    { id: 'faqs', label: 'FAQs', icon: HelpCircle },
    { id: 'contact', label: 'Contact Info', icon: Phone },
    { id: 'pricing', label: 'Pricing', icon: DollarSign },
  ];

  return (
    <div className="pt-20 min-h-screen bg-gray-50">
      <div className="container mx-auto px-5 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
          <p className="text-gray-600">Manage your website content and settings</p>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <div className="lg:w-64">
            <div className="bg-white rounded-lg shadow-sm p-4">
              <nav className="space-y-2">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center gap-3 px-4 py-2 rounded-lg text-left transition-colors ${
                        activeTab === tab.id
                          ? 'bg-[#0A74DA] text-white'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <Icon size={20} />
                      {tab.label}
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            <div className="bg-white rounded-lg shadow-sm p-6">
              {activeTab === 'testimonials' && renderTestimonials()}
              {activeTab === 'faqs' && renderFaqs()}
              {activeTab === 'contact' && renderContact()}
              {activeTab === 'pricing' && renderPricing()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;