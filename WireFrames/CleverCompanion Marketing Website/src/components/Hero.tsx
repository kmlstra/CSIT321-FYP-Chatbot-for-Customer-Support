import React from 'react';
import { ArrowRight } from 'lucide-react';
import logo from '../img/clever-companion-icon.png';
export const Hero: React.FC = () => {
  return (
    <div className="relative overflow-hidden pt-32 pb-16 md:pt-40 md:pb-24">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-white -z-10"></div>

      {/* Decorative circles */}
      <div className="absolute top-1/4 right-0 w-72 h-72 bg-blue-100 rounded-full opacity-20 -z-10 blur-3xl"></div>
      <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-blue-200 rounded-full opacity-20 -z-10 blur-3xl"></div>

      <div className="container mx-auto px-5">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-12">
          <div className="max-w-2xl">
            <div className="inline-block px-4 py-1.5 mb-5 rounded-full bg-blue-100 text-[#0A74DA] font-medium text-sm">
              AI-Powered Car Dealership Solutions
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight mb-6">
              Transform Your Dealership With{' '}
              <span className="text-[#0A74DA]">CleverCompanion</span> AI
              Technology
            </h1>
            <p className="text-lg text-gray-600 mb-8">
              Elevate customer experiences and streamline operations with
              CleverCompanion's AI-powered chatbot customized specifically for
              the automotive industry.
            </p>

          </div>

          <div className="relative w-full lg:w-[45%] aspect-[4/3] bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-100">
            <div className="absolute inset-0">
              <div className="h-12 bg-[#0A74DA] flex items-center px-4">
                <img
                  src={logo}
                  alt="CleverCompanion"
                  className="h-8 w-8 mr-2"
                />
                <div className="text-white text-sm font-medium">
                  CleverCompanion AI Assistant
                </div>
              </div>

              <div className="p-6 h-[calc(100%-3rem)] flex flex-col">
                <div className="flex-grow space-y-4 overflow-y-auto pb-4">
                  <div className="flex items-start gap-3">
                    <img src={logo} alt="CleverCompanion" className="h-8 w-8" />
                    <div className="bg-blue-50 rounded-lg rounded-tl-none p-3 text-sm text-gray-800 max-w-[80%]">
                      Hello! I'm CleverCompanion, your virtual assistant for car
                      information. How can I help you today?
                    </div>
                  </div>

                  <div className="flex items-start justify-end gap-3">
                    <div className="bg-gray-100 rounded-lg rounded-tr-none p-3 text-sm text-gray-800 max-w-[80%]">
                      I'm looking for information about electric vehicles in
                      your inventory.
                    </div>
                    <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center flex-shrink-0 text-xs font-bold text-gray-700">
                      ME
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <img src={logo} alt="CleverCompanion" className="h-8 w-8" />
                    <div className="bg-blue-50 rounded-lg rounded-tl-none p-3 text-sm text-gray-800 max-w-[80%]">
                      I'd be happy to help you find the perfect electric
                      vehicle. Could you tell me your preferred budget range and
                      any specific features you're looking for?
                    </div>
                  </div>
                </div>

                <div className="relative">
                  <input
                    type="text"
                    className="w-full rounded-full py-3 px-5 pr-12 bg-gray-100 focus:outline-none focus:ring-2 focus:ring-[#0A74DA] text-gray-800 placeholder-gray-500"
                    placeholder="Type your message..."
                  />
                  <button className="absolute right-3 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-[#0A74DA] flex items-center justify-center text-white">
                    <ArrowRight size={16} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
