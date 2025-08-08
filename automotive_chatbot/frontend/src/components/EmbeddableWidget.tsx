'use client';

import React, { useState, useEffect, useRef } from 'react';
import { ChatBubbleOvalLeftEllipsisIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

interface WidgetConfig {
  title?: string;
  subtitle?: string;
  primaryColor?: string;
  backgroundColor?: string;
  textColor?: string;
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  apiEndpoint?: string;
  welcomeMessage?: string;
  placeholder?: string;
  height?: string;
  width?: string;
}

interface EmbeddableWidgetProps {
  config?: WidgetConfig;
  onMessage?: (message: string) => void;
}

const defaultConfig: WidgetConfig = {
  title: 'CleverCompanion',
  subtitle: 'How can I help you today?',
  primaryColor: '#3B82F6',
  backgroundColor: '#FFFFFF',
  textColor: '#1F2937',
  position: 'bottom-right',
  apiEndpoint: 'http://localhost:8000/api/chat',
  welcomeMessage: 'Hello! I\'m CleverCompanion, your intelligent assistant. How can I help you today?',
  placeholder: 'Type your message...',
  height: '500px',
  width: '400px',
};

const EmbeddableWidget: React.FC<EmbeddableWidgetProps> = ({ 
  config = {}, 
  onMessage 
}) => {
  const finalConfig = { ...defaultConfig, ...config };
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize with welcome message
  useEffect(() => {
    if (finalConfig.welcomeMessage) {
      setMessages([{
        id: '1',
        text: finalConfig.welcomeMessage,
        sender: 'bot',
        timestamp: new Date(),
      }]);
    }
  }, [finalConfig.welcomeMessage]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (message: string) => {
    if (!message.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: message,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch(finalConfig.apiEndpoint!, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response || 'Sorry, I encountered an error. Please try again.',
        sender: 'bot',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I\'m having trouble connecting. Please try again later.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }

    // Call onMessage callback if provided
    if (onMessage) {
      onMessage(message);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const getPositionStyles = () => {
    const baseStyles = {
      position: 'fixed' as const,
      zIndex: 1000,
    };

    switch (finalConfig.position) {
      case 'bottom-right':
        return { ...baseStyles, bottom: '20px', right: '20px' };
      case 'bottom-left':
        return { ...baseStyles, bottom: '20px', left: '20px' };
      case 'top-right':
        return { ...baseStyles, top: '20px', right: '20px' };
      case 'top-left':
        return { ...baseStyles, top: '20px', left: '20px' };
      default:
        return { ...baseStyles, bottom: '20px', right: '20px' };
    }
  };

  return (
    <div style={getPositionStyles()}>
      {/* Chat Widget */}
      {isOpen && (
        <div
          className="shadow-2xl rounded-lg overflow-hidden mb-4"
          style={{
            backgroundColor: finalConfig.backgroundColor,
            width: finalConfig.width,
            height: finalConfig.height,
            border: `2px solid ${finalConfig.primaryColor}`,
          }}
        >
          {/* Header */}
          <div
            className="p-4 text-white flex justify-between items-center"
            style={{ backgroundColor: finalConfig.primaryColor }}
          >
            <div>
              <h3 className="font-semibold text-lg">{finalConfig.title}</h3>
              <p className="text-sm opacity-90">{finalConfig.subtitle}</p>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-full p-1 transition-all"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Messages */}
          <div
            className="flex-1 overflow-y-auto p-4 space-y-4"
            style={{ 
              height: 'calc(100% - 140px)',
              color: finalConfig.textColor 
            }}
          >
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.sender === 'user'
                      ? 'text-white'
                      : 'bg-gray-100'
                  }`}
                  style={{
                    backgroundColor: message.sender === 'user' 
                      ? finalConfig.primaryColor 
                      : undefined
                  }}
                >
                  <p className="text-sm">{message.text}</p>
                  <p className={`text-xs mt-1 ${
                    message.sender === 'user' ? 'text-white opacity-70' : 'text-gray-500'
                  }`}>
                    {message.timestamp.toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </p>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-4 py-2 rounded-lg">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200">
            <div className="flex space-x-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={finalConfig.placeholder}
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:border-transparent text-sm"
                style={{ 
                  '--tw-ring-color': finalConfig.primaryColor 
                } as React.CSSProperties}
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !inputValue.trim()}
                className="text-white px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm font-medium"
                style={{ backgroundColor: finalConfig.primaryColor }}
              >
                Send
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-14 h-14 rounded-full text-white shadow-lg hover:shadow-xl transition-all transform hover:scale-105"
        style={{ backgroundColor: finalConfig.primaryColor }}
      >
        {isOpen ? (
          <XMarkIcon className="w-6 h-6 mx-auto" />
        ) : (
          <ChatBubbleOvalLeftEllipsisIcon className="w-6 h-6 mx-auto" />
        )}
      </button>
    </div>
  );
};

export default EmbeddableWidget; 