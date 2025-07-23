import React from 'react';
import { Star, Quote } from 'lucide-react';
import { useApi } from '../hooks/useApi';

interface Testimonial {
  _id: string;
  quote: string;
  author: string;
  position: string;
  avatar: string;
  rating: number;
}

const TestimonialsPage: React.FC = () => {
  const { data: testimonials, loading, error } = useApi<Testimonial[]>('/api/testimonials');

  if (loading) {
    return (
      <div className="pt-20 min-h-screen flex items-center justify-center">
        <div className="pt-20">
          {/* Hero Section - Always show */}
          <div className="bg-[#0A74DA] text-white py-20">
            <div className="container mx-auto px-5 text-center">
              <h1 className="text-4xl md:text-5xl font-bold mb-6">
                What Our Customers Say
              </h1>
              <p className="text-xl max-w-3xl mx-auto">
                Discover how CleverCompanion has transformed dealerships across the country.
                Read real stories from real customers who have experienced success with our platform.
              </p>
            </div>
          </div>

          {/* Loading State */}
          <div className="py-20 bg-gray-50">
            <div className="container mx-auto px-5">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {[...Array(6)].map((_, index) => (
                  <div key={index} className="bg-white p-8 rounded-xl shadow-md relative">
                    <div className="animate-pulse">
                      <div className="flex mb-4">
                        {[...Array(5)].map((_, i) => (
                          <div key={i} className="w-4 h-4 bg-gray-200 rounded mr-1"></div>
                        ))}
                      </div>
                      
                      <div className="space-y-2 mb-6">
                        <div className="h-4 bg-gray-200 rounded w-full"></div>
                        <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                        <div className="h-4 bg-gray-200 rounded w-4/6"></div>
                        <div className="h-4 bg-gray-200 rounded w-3/6"></div>
                      </div>
                      
                      <div className="flex items-center">
                        <div className="w-12 h-12 rounded-full bg-gray-200 mr-4"></div>
                        <div className="flex-1">
                          <div className="h-4 bg-gray-200 rounded w-3/4 mb-1"></div>
                          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pt-20 min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error loading testimonials: {error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="bg-[#0A74DA] text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="pt-20">
      {/* Hero Section */}
      <div className="bg-[#0A74DA] text-white py-20">
        <div className="container mx-auto px-5 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            What Our Customers Say
          </h1>
          <p className="text-xl max-w-3xl mx-auto">
            Discover how CleverCompanion has transformed dealerships across the country.
            Read real stories from real customers who have experienced success with our platform.
          </p>
        </div>
      </div>

      {/* Testimonials Grid */}
      <div className="py-20 bg-gray-50">
        <div className="container mx-auto px-5">
          {testimonials && testimonials.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {testimonials.map((testimonial) => (
                <div 
                  key={testimonial._id} 
                  className="bg-white p-8 rounded-xl shadow-md relative hover:shadow-lg transition-shadow duration-300"
                >
                  <div className="absolute top-6 right-8 text-blue-100">
                    <Quote size={56} />
                  </div>
                  
                  <div className="flex mb-4">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Star
                        key={i}
                        size={18}
                        className={i < testimonial.rating ? "text-yellow-400 fill-yellow-400" : "text-gray-300"}
                      />
                    ))}
                  </div>
                  
                  <p className="text-gray-700 mb-6 relative z-10 leading-relaxed">
                    "{testimonial.quote}"
                  </p>
                  
                  <div className="flex items-center">
                    <img
                      src={testimonial.avatar}
                      alt={testimonial.author}
                      className="w-12 h-12 rounded-full mr-4 object-cover"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = 'https://randomuser.me/api/portraits/men/32.jpg';
                      }}
                    />
                    <div>
                      <h4 className="font-semibold text-gray-900">{testimonial.author}</h4>
                      <p className="text-sm text-gray-600">{testimonial.position}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-600 text-lg">No testimonials available at the moment.</p>
            </div>
          )}
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-white py-16">
        <div className="container mx-auto px-5 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Ready to Join Our Success Stories?
          </h2>
          <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
            Start your journey with CleverCompanion today and become our next success story.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="bg-[#0A74DA] text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-600 transition-colors duration-300">
              Start Free Trial
            </button>
            <button className="bg-white text-gray-800 px-8 py-3 rounded-lg font-medium border border-gray-300 hover:bg-gray-100 transition-colors duration-300">
              Schedule a Demo
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestimonialsPage;