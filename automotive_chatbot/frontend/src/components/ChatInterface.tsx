/**
 * Component: ChatInterface
 * Main chat interface component with HTTP API calls
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';

interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  metadata?: {
    buttons?: Array<{ title: string; payload: string }>;
    quick_replies?: Array<{ title: string; payload: string }>;
  };
}

interface ChatInterfaceProps {
  className?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ className = '' }) => {
  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize with welcome message
  useEffect(() => {
    setMessages([{
      id: 'welcome',
      content: 'Hello! I\'m your automotive assistant. How can I help you today?',
      sender: 'bot',
      timestamp: new Date(),
      metadata: {
        buttons: [
          { title: 'COE Prices', payload: 'COE Prices' },
          { title: 'Test Drive', payload: 'Test Drive' },
          { title: 'Maintenance', payload: 'Maintenance' },
          { title: 'Contact Us', payload: 'Contact Us' }
        ]
      }
    }]);
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim()) return;

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: messageText,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      // Send to RASA backend
      const response = await fetch('http://localhost:5005/webhooks/rest/webhook', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sender: 'user',
          message: messageText
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get response from chatbot');
      }

      const botResponses = await response.json();
      
      // Add bot responses
      if (botResponses && botResponses.length > 0) {
        const botMessages = botResponses.map((resp: any, index: number) => ({
          id: `${Date.now()}-${index}`,
          content: resp.text || 'I received your message, but I\'m not sure how to respond.',
          sender: 'bot' as const,
          timestamp: new Date(),
          metadata: {
            buttons: resp.buttons || [],
            quick_replies: resp.quick_replies || []
          }
        }));
        
        setMessages(prev => [...prev, ...botMessages]);
      } else {
        // Fallback response
        const fallbackMessage: ChatMessage = {
          id: Date.now().toString(),
          content: 'I\'m sorry, I didn\'t receive a proper response. Please try again.',
          sender: 'bot',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, fallbackMessage]);
      }
    } catch (err) {
      setError('Unable to connect to the chatbot service. Please check if the services are running.');
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim() && !isLoading) {
      await sendMessage(inputMessage.trim());
      setInputMessage('');
    }
  };

  const handleButtonClick = async (payload: string, title: string) => {
    await sendMessage(payload);
  };

  const clearChat = () => {
    setMessages([{
      id: 'welcome',
      content: 'Hello! I\'m your automotive assistant. How can I help you today?',
      sender: 'bot',
      timestamp: new Date(),
      metadata: {
        buttons: [
          { title: 'COE Prices', payload: 'COE Prices' },
          { title: 'Test Drive', payload: 'Test Drive' },
          { title: 'Maintenance', payload: 'Maintenance' },
          { title: 'Contact Us', payload: 'Contact Us' }
        ]
      }
    }]);
    setError(null);
  };

  const suggestedQueries = [
    "What are the current COE prices?",
    "How do I book a test drive?", 
    "What maintenance does my car need?"
  ];

  const handleSuggestedQuery = async (query: string) => {
    await sendMessage(query);
  };

  return (
    <div className={`flex flex-col h-full bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="bg-blue-600 text-white p-4 rounded-t-lg">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">Automotive Assistant</h2>
          <button
            onClick={clearChat}
            className="text-blue-200 hover:text-white transition-colors"
            title="Clear Chat"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500">
            <p className="mb-4">Welcome! Ask me anything about automotive maintenance and repairs.</p>
            <div className="space-y-2">
              <p className="text-sm font-medium">Try these questions:</p>
              <div className="grid gap-2">
                {suggestedQueries.slice(0, 3).map((query, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestedQuery(query)}
                    className="text-left p-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm transition-colors"
                  >
                    {query}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onButtonClick={handleButtonClick}
          />
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 rounded-lg p-3 max-w-xs">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type your automotive question..."
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || isLoading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
};

// Message Bubble Component
interface MessageBubbleProps {
  message: ChatMessage;
  onButtonClick: (payload: string, title: string) => void;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onButtonClick }) => {
  const isUser = message.sender === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
        isUser 
          ? 'bg-blue-600 text-white' 
          : 'bg-gray-200 text-gray-800'
      }`}>
        <p className="text-sm">{message.content}</p>
        
        {/* Render buttons if present */}
        {message.metadata?.buttons && message.metadata.buttons.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.metadata.buttons.map((button, index) => (
              <button
                key={index}
                onClick={() => onButtonClick(button.payload, button.title)}
                className="block w-full text-left px-3 py-1 bg-white text-gray-800 rounded border hover:bg-gray-100 transition-colors text-sm"
              >
                {button.title}
              </button>
            ))}
          </div>
        )}

        {/* Render quick replies if present */}
        {message.metadata?.quick_replies && message.metadata.quick_replies.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {message.metadata.quick_replies.map((reply, index) => (
              <button
                key={index}
                onClick={() => onButtonClick(reply.payload, reply.title)}
                className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs hover:bg-blue-200 transition-colors"
              >
                {reply.title}
              </button>
            ))}
          </div>
        )}

        <p className="text-xs opacity-70 mt-1">
          {message.timestamp.toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}; 