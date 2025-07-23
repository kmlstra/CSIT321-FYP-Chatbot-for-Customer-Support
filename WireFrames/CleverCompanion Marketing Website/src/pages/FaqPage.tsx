import React, { useState } from 'react';
import { ArrowRight, Search, MessageCircle, Phone, Mail } from 'lucide-react';

type FaqCategory = {
  name: string;
  faqs: {
    question: string;
    answer: string;
  }[];
};

const faqCategories: FaqCategory[] = [
  {
    name: 'Getting Started',
    faqs: [
      {
        question: 'How do I sign up for SmartDealer?',
        answer:
          "Signing up for SmartDealer is easy. Simply click the 'Get Started' button on our homepage, fill out the registration form, and follow the instructions to set up your account. Our onboarding team will reach out within 24 hours to guide you through the setup process.",
      },
      {
        question: 'How long does it take to implement SmartDealer?',
        answer:
          'Most dealerships can be fully set up within 24-48 hours. This includes connecting your inventory, customizing chatbot responses, and integrating with your website. Our implementation specialists will work with you to ensure a smooth setup process.',
      },
      {
        question: 'Do I need technical knowledge to use SmartDealer?',
        answer:
          "No technical knowledge is required. Our platform is designed to be user-friendly, and our setup team handles all technical aspects of implementation. You'll receive comprehensive training on how to use the dashboard and manage your settings.",
      },
      {
        question: "Can I customize the chatbot's appearance?",
        answer:
          "Yes, you can fully customize the chatbot's appearance to match your dealership's branding. This includes colors, fonts, logos, and chatbot avatar. The Professional and Enterprise plans also allow for advanced customization options.",
      },
    ],
  },
  {
    name: 'Features & Functionality',
    faqs: [
      {
        question: 'What languages does the chatbot support?',
        answer:
          'SmartDealer currently supports English, Spanish, French, and German. Additional languages can be added for Enterprise customers upon request.',
      },
      {
        question:
          'Can SmartDealer integrate with our existing inventory system?',
        answer:
          'Yes, SmartDealer integrates with most major automotive inventory management systems including vAuto, DealerTrack, CDK, Reynolds & Reynolds, and many others. If you use a custom system, our team can work with you on a custom integration.',
      },
      {
        question: 'How does the AI learn about our specific inventory?',
        answer:
          'SmartDealer connects directly to your inventory management system to access real-time data about vehicle availability, specifications, and pricing. The AI uses this information along with its knowledge base about automotive features to provide accurate responses to customer queries.',
      },
      {
        question: 'Can we track leads generated through the chatbot?',
        answer:
          "Absolutely. SmartDealer provides comprehensive lead tracking and qualification. All customer interactions are logged, and qualified leads are automatically pushed to your CRM system. You'll also receive detailed analytics on conversion rates and lead quality.",
      },
    ],
  },
  {
    name: 'Billing & Subscriptions',
    faqs: [
      {
        question: 'What payment methods do you accept?',
        answer:
          'We accept all major credit cards (Visa, MasterCard, American Express, Discover) as well as ACH bank transfers for annual subscriptions.',
      },
      {
        question: 'Is there a contract or commitment?',
        answer:
          "We offer monthly and annual billing options. While annual plans provide a 20% discount, there's no long-term contract required. You can cancel your subscription at any time.",
      },
      {
        question: 'What happens after my free trial ends?',
        answer:
          "At the end of your 14-day free trial, your account will automatically transition to your selected plan. We'll send you reminders before the trial ends, and you can choose to upgrade, downgrade, or cancel at any time.",
      },
      {
        question: 'Can I change plans later?',
        answer:
          'Yes, you can upgrade or downgrade your plan at any time. If you upgrade, the new pricing takes effect immediately with prorated billing. If you downgrade, the new pricing takes effect at the start of your next billing cycle.',
      },
    ],
  },
  {
    name: 'Technical Support',
    faqs: [
      {
        question: 'What kind of support is included?',
        answer:
          'All plans include email support and access to our knowledge base. The Professional plan adds extended hours phone support, while the Enterprise plan includes 24/7 priority support and a dedicated account manager.',
      },
      {
        question: 'How do I report issues or get help?',
        answer:
          'You can submit support tickets through your dashboard, email support@smartdealer.com, or use the live chat feature on our website. Phone support is available for Professional and Enterprise customers.',
      },
      {
        question: 'Do you provide training for our team?',
        answer:
          'Yes, all plans include initial training during onboarding. Professional and Enterprise plans include additional training sessions and access to advanced webinars and resources.',
      },
      {
        question:
          "What happens if the chatbot can't answer a customer question?",
        answer:
          "If the AI is unable to confidently answer a question, it will gracefully hand off the conversation to a human agent or collect the customer's contact information so your team can follow up. This ensures customers always receive accurate information.",
      },
    ],
  },
];

const FaqPage: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState(0);
  const [openFaqs, setOpenFaqs] = useState<number[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const { data: apiData, loading, error } = useApi<FaqCategory[]>('/api/faqs');

  const toggleFaq = (index: number) => {
    if (openFaqs.includes(index)) {
      setOpenFaqs(openFaqs.filter((i) => i !== index));
    } else {
      setOpenFaqs([...openFaqs, index]);
    }
  };

  const filteredFaqs = searchQuery
    ? (apiData || faqCategories).flatMap((category) =>
        category.faqs
          .filter(
            (faq) =>
              faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
              faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
          )
          .map((faq) => ({ ...faq, category: category.name }))
      )
    : [];

  // Use API data if available, otherwise fall back to hardcoded data
  const displayCategories = apiData || faqCategories;

  return (
    <div className="pt-20">
      {/* Hero Section */}
      <div className="bg-[#0A74DA] text-white py-16">
        <div className="container mx-auto px-5 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            Frequently Asked Questions
          </h1>
          <p className="text-xl max-w-3xl mx-auto mb-8">
            Find answers to common questions about SmartDealer's features,
            pricing, and implementation.
          </p>

          <div className="max-w-2xl mx-auto relative">
            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              className="w-full pl-12 pr-4 py-3 rounded-full bg-white text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-white"
              placeholder="Search for answers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* FAQ Content */}
      <div className="py-16 bg-white">
        <div className="container mx-auto px-5">
          {/* Search Results */}
          {searchQuery && (
            <div className="mb-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                Search Results for "{searchQuery}"
              </h2>

              {filteredFaqs.length === 0 ? (
                <div className="text-center py-8 bg-gray-50 rounded-lg">
                  <p className="text-gray-600 mb-4">
                    No results found for your search.
                  </p>
                  <p className="text-gray-600">
                    Try a different search term or browse categories below.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredFaqs.map((faq, index) => (
                    <div
                      key={index}
                      className="border border-gray-200 rounded-lg overflow-hidden"
                    >
                      <button
                        className="flex justify-between items-center w-full p-5 text-left font-medium text-gray-900 bg-gray-50"
                        onClick={() => toggleFaq(index)}
                      >
                        <div>
                          <span className="text-sm font-medium text-[#0A74DA] block mb-1">
                            {faq.category}
                          </span>
                          {faq.question}
                        </div>
                        <span
                          className={`transform transition-transform ${
                            openFaqs.includes(index) ? 'rotate-90' : ''
                          }`}
                        >
                          <ArrowRight className="h-5 w-5" />
                        </span>
                      </button>

                      <div
                        className={`overflow-hidden transition-all duration-300 ${
                          openFaqs.includes(index) ? 'max-h-96' : 'max-h-0'
                        }`}
                      >
                        <div className="p-5 bg-white">
                          <p className="text-gray-600">{faq.answer}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* FAQ Categories */}
          {!searchQuery && (
            <>
              {loading ? (
                <div className="mb-8">
                  <div className="animate-pulse flex space-x-2">
                    {[...Array(4)].map((_, index) => (
                      <div key={index} className="h-10 bg-gray-200 rounded-full w-32"></div>
                    ))}
                  </div>
                </div>
              ) : (
              <div className="mb-8 overflow-x-auto">
                <div className="flex space-x-2 min-w-max">
                  {displayCategories.map((category, index) => (
                    <button
                      key={index}
                      className={`px-5 py-2 rounded-full font-medium whitespace-nowrap transition-colors ${
                        activeCategory === index
                          ? 'bg-[#0A74DA] text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                      onClick={() => setActiveCategory(index)}
                    >
                      {category.name}
                    </button>
                  ))}
                </div>
              </div>
              )}

              {loading ? (
                <div className="space-y-4">
                  {[...Array(4)].map((_, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
                      <div className="animate-pulse p-5 bg-gray-50">
                        <div className="h-5 bg-gray-200 rounded w-3/4"></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  {displayCategories[activeCategory]?.faqs.map((faq, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-lg overflow-hidden"
                  >
                    <button
                      className="flex justify-between items-center w-full p-5 text-left font-medium text-gray-900 bg-gray-50"
                      onClick={() => toggleFaq(index)}
                    >
                      {faq.question}
                      <span
                        className={`transform transition-transform ${
                          openFaqs.includes(index) ? 'rotate-90' : ''
                        }`}
                      >
                        <ArrowRight className="h-5 w-5" />
                      </span>
                    </button>

                    <div
                      className={`overflow-hidden transition-all duration-300 ${
                        openFaqs.includes(index) ? 'max-h-96' : 'max-h-0'
                      }`}
                    >
                      <div className="p-5 bg-white">
                        <p className="text-gray-600">{faq.answer}</p>
                      </div>
                    </div>
                  </div>
                ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Contact Section */}
      <div className="bg-gray-50 py-16">
        <div className="container mx-auto px-5">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Still Have Questions?
            </h2>
            <p className="text-lg text-gray-600">
              Can't find what you're looking for? Our team is here to help.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="bg-white p-6 rounded-xl shadow-sm text-center">
              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-4">
                <MessageCircle className="h-6 w-6 text-[#0A74DA]" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Live Chat
              </h3>
              <p className="text-gray-600 mb-4">
                Chat with our support team during business hours for immediate
                assistance.
              </p>
              <button className="text-[#0A74DA] font-medium hover:underline">
                Start a Chat
              </button>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm text-center">
              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-4">
                <Phone className="h-6 w-6 text-[#0A74DA]" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Call Us
              </h3>
              <p className="text-gray-600 mb-4">
                Speak with a support representative or sales consultant by
                phone.
              </p>
              <button className="text-[#0A74DA] font-medium hover:underline">
                (800) 123-4567
              </button>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm text-center">
              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-4">
                <Mail className="h-6 w-6 text-[#0A74DA]" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Email Us
              </h3>
              <p className="text-gray-600 mb-4">
                Send us an email and we'll get back to you within one business
                day.
              </p>
              <button className="text-[#0A74DA] font-medium hover:underline">
                support@smartdealer.com
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FaqPage;
