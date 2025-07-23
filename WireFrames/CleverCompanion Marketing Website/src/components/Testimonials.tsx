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

export const Testimonials: React.FC = () => {
  const { data: testimonials, loading, error } = useApi<Testimonial[]>('/api/testimonials');

  if (loading) {
    return (
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-5 text-center">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Trusted by Leading Dealerships
            </h2>
            <p className="text-lg text-gray-600">
              Don't just take our word for it. Here's what our partners have to say about CleverCompanion.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[...Array(3)].map((_, index) => (
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
      </section>
    );
  }

  if (error || !testimonials || testimonials.length === 0) {
    return null; // Don't show the section if there's an error or no testimonials
  }

  return (
    <section className="py-20 bg-gray-50">
      <div className="container mx-auto px-5">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Trusted by Leading Dealerships
          </h2>
          <p className="text-lg text-gray-600">
            Don't just take our word for it. Here's what our partners have to say about CleverCompanion.
          </p>
        </div>
        
        <div className={`grid gap-8 ${testimonials.length === 1 ? 'grid-cols-1 max-w-2xl mx-auto' : testimonials.length === 2 ? 'grid-cols-1 md:grid-cols-2 max-w-4xl mx-auto' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'}`}>
          {testimonials.slice(0, 3).map((testimonial) => (
            <div 
              key={testimonial._id} 
              className="bg-white p-8 rounded-xl shadow-md relative"
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
              
              <p className="text-gray-700 mb-6 relative z-10">
                "{testimonial.quote}"
              </p>
              
              <div className="flex items-center">
                <img
                  src={testimonial.avatar}
                  alt={testimonial.author}
                  className="w-12 h-12 rounded-full mr-4"
                />
                <div>
                  <h4 className="font-semibold text-gray-900">{testimonial.author}</h4>
                  <p className="text-sm text-gray-600">{testimonial.position}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-12 text-center">
          <button className="bg-white text-[#0A74DA] border border-[#0A74DA] px-6 py-2 rounded-lg font-medium hover:bg-[#0A74DA] hover:text-white transition-colors duration-300">
            <a href="/testimonials">Read More Success Stories</a>
          </button>
        </div>
      </div>
    </section>
  );
};