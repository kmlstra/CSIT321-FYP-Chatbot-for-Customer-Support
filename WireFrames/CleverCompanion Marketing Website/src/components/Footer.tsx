import React from 'react';
import { Link } from 'react-router-dom';
import { MessageSquare, Facebook, Twitter, Linkedin, Instagram } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-900 text-white py-12">
      <div className="container mx-auto px-5">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="col-span-1">
            <Link to="/" className="flex items-center gap-2 text-xl font-bold mb-4">
              <MessageSquare className="h-7 w-7 text-[#0A74DA]" />
              <span className="text-white">SmartDealer</span>
            </Link>
            <p className="text-gray-400 mb-4">
              Revolutionizing car dealerships with AI-powered customer service solutions.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="text-gray-400 hover:text-[#0A74DA] transition-colors">
                <Facebook size={20} />
              </a>
              <a href="#" className="text-gray-400 hover:text-[#0A74DA] transition-colors">
                <Twitter size={20} />
              </a>
              <a href="#" className="text-gray-400 hover:text-[#0A74DA] transition-colors">
                <Linkedin size={20} />
              </a>
              <a href="#" className="text-gray-400 hover:text-[#0A74DA] transition-colors">
                <Instagram size={20} />
              </a>
            </div>
          </div>
          
          <div className="col-span-1">
            <h3 className="text-lg font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2">
              {['Home', 'Features', 'Pricing', 'FAQ', 'Testimonials'].map((item) => (
                <li key={item}>
                  <Link
                    to={item === 'Home' ? '/' : item === 'Testimonials' ? '/testimonials' : `/${item.toLowerCase()}`}
                    className="text-gray-400 hover:text-[#0A74DA] transition-colors"
                  >
                    {item}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          
          <div className="col-span-1">
            <h3 className="text-lg font-semibold mb-4">Support</h3>
            <ul className="space-y-2">
              {['Contact Us', 'Help Center', 'Privacy Policy', 'Terms of Service'].map((item) => (
                <li key={item}>
                  <Link
                    to={item === 'Contact Us' ? '/contact' : '#'}
                    className="text-gray-400 hover:text-[#0A74DA] transition-colors"
                  >
                    {item}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          
          <div className="col-span-1">
            <h3 className="text-lg font-semibold mb-4">Newsletter</h3>
            <p className="text-gray-400 mb-4">
              Stay updated with our latest news and updates.
            </p>
            <form className="flex flex-col space-y-2">
              <input
                type="email"
                placeholder="Your email address"
                className="bg-gray-800 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0A74DA]"
              />
              <button
                type="submit"
                className="bg-[#0A74DA] text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
              >
                Subscribe
              </button>
            </form>
          </div>
        </div>
        
        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-500">
          <p>© {new Date().getFullYear()} SmartDealer. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};