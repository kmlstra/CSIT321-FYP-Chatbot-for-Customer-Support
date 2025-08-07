import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Search } from 'lucide-react';
import { getFAQs } from '../lib/api';

interface FAQItem {
  id: string;
  question: string;
  answer: string;
  category: string;
  status: string;
}

const FAQ: React.FC = () => {
  const [faqs, setFaqs] = useState<FAQItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [openItems, setOpenItems] = useState<number[]>([]);
  const [selectedCategory, setSelectedCategory] = useState('All');

  useEffect(() => {
    fetchFAQs();
  }, []);

  const fetchFAQs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getFAQs();
      setFaqs(data);
    } catch (err: any) {
      console.error('Error fetching FAQs:', err);
      setError('Failed to load FAQ data');
    } finally {
      setLoading(false);
    }
  };

  const categories = ['All', ...Array.from(new Set(faqs.map(faq => faq.category)))];

  const toggleItem = (index: number) => {
    setOpenItems(prev =>
        prev.includes(index)
            ? prev.filter(i => i !== index)
            : [...prev, index]
    );
  };

  const handleChatClick = () => {
    if (window.CleverCompanionWidget) {
      window.CleverCompanionWidget.open();
    } else if (window.startChat) {
      window.startChat();
    } else {
      alert('Chat service is not available at the moment. Please try again later.');
    }
  };

  const filteredFaqs = faqs.filter(faq => {
    const matchesSearch = faq.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
        faq.answer.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || faq.category === selectedCategory;
    const isActive = faq.status === 'active';
    return matchesSearch && matchesCategory && isActive;
  });

  if (loading) {
    return (
      <div className="pt-20 min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading FAQ...</p>
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
            onClick={fetchFAQs}
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
          <div className="max-w-3xl mx-auto">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">Frequently Asked Questions</h1>
            <p className="text-gray-600 mb-8">Find answers to common questions about our vehicles and services</p>

            <div className="mb-8">
              <div className="relative">
                <Search size={20} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                    type="text"
                    placeholder="Search FAQs..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="mb-6 flex flex-wrap gap-2">
              {categories.map(category => (
                  <button
                      key={category}
                      onClick={() => setSelectedCategory(category)}
                      className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                          selectedCategory === category
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                  >
                    {category}
                  </button>
              ))}
            </div>

            <div className="space-y-4">
              {filteredFaqs.map((faq, index) => (
                  <div
                      key={faq.id}
                      className="bg-white rounded-lg shadow-md overflow-hidden"
                  >
                    <button
                        onClick={() => toggleItem(index)}
                        className="w-full px-6 py-4 text-left flex justify-between items-center hover:bg-gray-50"
                    >
                      <span className="font-medium text-gray-800">{faq.question}</span>
                      {openItems.includes(index) ? (
                          <ChevronUp size={20} className="text-gray-500" />
                      ) : (
                          <ChevronDown size={20} className="text-gray-500" />
                      )}
                    </button>

                    {openItems.includes(index) && (
                        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
                          <p className="text-gray-600">{faq.answer}</p>
                        </div>
                    )}
                  </div>
              ))}
            </div>

            <div className="mt-12 p-6 bg-blue-50 rounded-lg">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">Still have questions?</h2>
              <p className="text-gray-600 mb-4">
                Can't find what you're looking for? Feel free to reach out to our customer support team.
              </p>
              <div className="flex gap-4">
                <a
                    href="/contact"
                    className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2 rounded-md transition-colors"
                >
                  Contact Us
                </a>
                <button
                    onClick={handleChatClick}
                    className="inline-block bg-white hover:bg-gray-50 text-gray-700 font-medium px-6 py-2 rounded-md border border-gray-300 transition-colors"
                >
                  Chat with Us
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
  );
};

export default FAQ;