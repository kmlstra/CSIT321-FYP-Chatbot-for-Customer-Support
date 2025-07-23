import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, MessageSquare } from 'lucide-react';
import logo from '../img/clever-companion-icon.png';

export const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  useEffect(() => {
    setIsMenuOpen(false);
  }, [location]);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled ? 'bg-white shadow-md py-3' : 'bg-transparent py-5'
      }`}
    >
      <div className="container mx-auto px-5 flex justify-between items-center">
        <Link
          to="/"
          className="flex items-center gap-2 text-xl font-bold"
          aria-label="CleverCompanion Home"
        >
          <img src={logo} alt="CleverCompanion" className="h-8 w-8" />
          <span
            className={`transition-colors duration-300 ${
              isScrolled ? 'text-[#0A74DA]' : 'text-[#0A74DA]'
            }`}
          >
            CleverCompanion
          </span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:block">
          <ul className="flex space-x-8">
            {['Features', 'Pricing', 'FAQ', 'Testimonials', 'Contact Us'].map((item) => (
              <li key={item}>
                <Link
                  to={
                    item === 'Contact Us'
                      ? '/contact'
                      : item === 'Testimonials'
                      ? '/testimonials'
                      : `/${item.toLowerCase()}`
                  }
                  className={`text-base font-medium transition-colors duration-200 hover:text-[#0A74DA] ${
                    isScrolled ? 'text-gray-800' : 'text-gray-800'
                  }`}
                >
                  {item}
                </Link>
                <h1></h1>
              </li>
            ))}
          </ul>
        </nav>

        {/* Mobile Navigation Toggle */}
        <button
          className="md:hidden text-[#0A74DA]"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          aria-label={isMenuOpen ? 'Close Menu' : 'Open Menu'}
        >
          {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>

        {/* Mobile Navigation Menu */}
        {isMenuOpen && (
          <div className="fixed inset-0 top-[60px] bg-white z-40 md:hidden">
            <nav className="container mx-auto px-5 py-5">
              <ul className="flex flex-col space-y-4">
                {['Features', 'Pricing', 'FAQ', 'Testimonials', 'Contact Us'].map((item) => (
                  <li key={item}>
                    <Link
                      to={
                        item === 'Contact Us'
                          ? '/contact'
                          : item === 'Testimonials'
                          ? '/testimonials'
                          : `/${item.toLowerCase()}`
                      }
                      className="text-xl font-medium text-gray-800 hover:text-[#0A74DA] block py-2"
                    >
                      {item}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};
