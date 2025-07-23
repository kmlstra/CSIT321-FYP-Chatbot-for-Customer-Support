import React from 'react';
import { Check, ArrowRight } from 'lucide-react';
import { useApi } from '../hooks/useApi';

interface PricingPlan {
  _id: string;
  planName: string;
  price: number;
  currency: string;
  billingPeriod: string;
  features: string[];
  isActive: boolean;
  isPopular: boolean;
}

const PricingPage: React.FC = () => {
  const { data: pricingPlans, loading, error } = useApi<PricingPlan[]>('/api/pricing');

  if (loading) {
    return (
      <div className="pt-20 min-h-screen">
        {/* Hero Section - Always show */}
        <div className="bg-[#0A74DA] text-white py-20">
          <div className="container mx-auto px-5 text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-6">Simple, Transparent Pricing</h1>
            <p className="text-xl max-w-3xl mx-auto mb-6">
              One plan, all features included. Start your 14-day free trial today.
            </p>
          </div>
        </div>

        {/* Loading State */}
        <div className="py-16 bg-gray-50">
          <div className="container mx-auto px-5">
            <div className="max-w-3xl mx-auto">
              <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
                <div className="p-8">
                  <div className="animate-pulse">
                    <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
                    <div className="h-12 bg-gray-200 rounded w-1/2 mb-4"></div>
                    <div className="h-4 bg-gray-200 rounded w-2/3 mb-6"></div>
                    
                    <div className="space-y-4 mb-8">
                      {[...Array(9)].map((_, index) => (
                        <div key={index} className="flex items-center">
                          <div className="h-5 w-5 bg-gray-200 rounded mr-3"></div>
                          <div className="h-4 bg-gray-200 rounded flex-1"></div>
                        </div>
                      ))}
                    </div>
                    
                    <div className="flex flex-col sm:flex-row gap-4">
                      <div className="h-12 bg-gray-200 rounded flex-1"></div>
                      <div className="h-12 bg-gray-200 rounded flex-1"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* FAQ Section - Always show */}
        <div className="py-16 bg-white">
          <div className="container mx-auto px-5 text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Still have questions?</h2>
            <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
              Our team is here to help you understand how CleverCompanion can work for your dealership.
            </p>
            <button className="bg-[#0A74DA] text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-600 transition-colors duration-300">
              Contact Sales
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pt-20 min-h-screen">
        {/* Hero Section */}
        <div className="bg-[#0A74DA] text-white py-20">
          <div className="container mx-auto px-5 text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-6">Simple, Transparent Pricing</h1>
            <p className="text-xl max-w-3xl mx-auto mb-6">
              One plan, all features included. Start your 14-day free trial today.
            </p>
          </div>
        </div>

        {/* Error State */}
        <div className="py-16 bg-gray-50">
          <div className="container mx-auto px-5">
            <div className="max-w-3xl mx-auto text-center">
              <div className="bg-white rounded-xl shadow-lg p-8 border border-red-200">
                <div className="text-red-600 mb-4">
                  <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Unable to Load Pricing</h3>
                <p className="text-gray-600 mb-4">We're having trouble loading the pricing information. Please try again.</p>
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

  // Use the first active plan
  const activePlan = pricingPlans?.find(plan => plan.isActive);

  if (!activePlan) {
    return (
      <div className="pt-20 min-h-screen">
        {/* Hero Section */}
        <div className="bg-[#0A74DA] text-white py-20">
          <div className="container mx-auto px-5 text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-6">Simple, Transparent Pricing</h1>
            <p className="text-xl max-w-3xl mx-auto mb-6">
              One plan, all features included. Start your 14-day free trial today.
            </p>
          </div>
        </div>

        {/* No Plans Available */}
        <div className="py-16 bg-gray-50">
          <div className="container mx-auto px-5">
            <div className="max-w-3xl mx-auto text-center">
              <div className="bg-white rounded-xl shadow-lg p-8">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No Pricing Plans Available</h3>
                <p className="text-gray-600 mb-4">Please contact us for pricing information.</p>
                <button className="bg-[#0A74DA] text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors">
                  Contact Sales
                </button>
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
      <div className="bg-[#0A74DA] text-white py-20">
        <div className="container mx-auto px-5 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">Simple, Transparent Pricing</h1>
          <p className="text-xl max-w-3xl mx-auto mb-6">
            One plan, all features included. Start your 14-day free trial today.
          </p>
        </div>
      </div>

      {/* Pricing Section */}
      <div className="py-16 bg-gray-50">
        <div className="container mx-auto px-5">
          <div className="max-w-3xl mx-auto">
            <div className={`bg-white rounded-xl shadow-lg overflow-hidden ${activePlan.isPopular ? 'border border-[#0A74DA]' : 'border border-gray-200'}`}>
              {activePlan.isPopular && (
                <div className="bg-[#0A74DA] text-white text-center py-2 text-sm font-medium">
                  Most Popular
                </div>
              )}
              <div className="p-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{activePlan.planName}</h3>
                <div className="flex items-baseline mb-4">
                  <span className="text-4xl font-bold text-gray-900">${activePlan.price}</span>
                  <span className="text-gray-600 ml-1">/{activePlan.billingPeriod}</span>
                </div>
                <p className="text-gray-600 mb-6">Everything you need to transform your dealership</p>
                
                <div className="space-y-4 mb-8">
                  {activePlan.features.map((feature, index) => (
                    <div key={index} className="flex items-center">
                      <Check className="h-5 w-5 text-green-500 mr-3" />
                      <span className="text-gray-700">{feature}</span>
                    </div>
                  ))}
                </div>
                
                <div className="flex flex-col sm:flex-row gap-4">
                  <button className="flex items-center justify-center gap-2 bg-[#0A74DA] text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-600 transition-colors duration-300">
                    Start Free Trial
                    <ArrowRight size={18} />
                  </button>
                  <button className="flex items-center justify-center gap-2 bg-white text-gray-800 px-8 py-3 rounded-lg font-medium border border-gray-300 hover:bg-gray-100 transition-colors duration-300">
                    Schedule Demo
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="py-16 bg-white">
        <div className="container mx-auto px-5 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Still have questions?</h2>
          <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
            Our team is here to help you understand how CleverCompanion can work for your dealership.
          </p>
          <button className="bg-[#0A74DA] text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-600 transition-colors duration-300">
            Contact Sales
          </button>
        </div>
      </div>
    </div>
  );
};

export default PricingPage;