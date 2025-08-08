import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send } from 'lucide-react';
import { toast } from 'sonner';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  isHtml?: boolean;
}

interface ChatWidgetProps {
  title?: string;
  subtitle?: string;
  primaryColor?: string;
  position?: 'bottom-right' | 'bottom-left';
}

const ChatWidget: React.FC<ChatWidgetProps> = ({
  title = "CleverCompanion",
  subtitle = "How can I help you today?",
  primaryColor = "#2563eb",
  position = "bottom-right"
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Initialize with welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        id: 'welcome',
        text: 'Hello! I\'m CleverCompanion, your automotive assistant. How can I help you today?',
        sender: 'bot',
        timestamp: new Date()
      }]);
    }
  }, [messages.length]);

  const handleActionButton = (action: string) => {
    switch (action) {
      case 'whatsapp':
        window.open('https://wa.me/6542848294', '_blank');
        toast.success('Opening WhatsApp...');
        break;
      case 'call':
        window.open('tel:+6562345678', '_blank');
        toast.success('Initiating call...');
        break;
      case 'email':
        window.open('mailto:info@clevercompanion.sg', '_blank');
        toast.success('Opening email client...');
        break;
      case 'view on google maps':
        window.open('https://maps.google.com/?q=CleverCompanion+Singapore', '_blank');
        toast.success('Opening Google Maps...');
        break;
      default:
        console.log('Unknown action:', action);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      text: inputValue,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/rasa/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sender: sessionId,
          message: inputValue,
          metadata: {
            timestamp: new Date().toISOString(),
            source: 'react_widget'
          }
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success && data.bot_responses) {
        data.bot_responses.forEach((botText: string, index: number) => {
          const botMessage: Message = {
            id: `bot-${Date.now()}-${index}`,
            text: botText,
            sender: 'bot',
            timestamp: new Date(),
            isHtml: botText.includes('<')
          };
          
          setTimeout(() => {
            setMessages(prev => [...prev, botMessage]);
          }, index * 500); // Stagger multiple responses
        });
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        text: 'Sorry, I\'m having trouble connecting right now. Please try again later.',
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      toast.error('Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const positionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4'
  };

  return (
    <div className={`fixed ${positionClasses[position]} z-50`}>
      {/* Chat Window */}
      {isOpen && (
        <div className="mb-4 w-96 h-96 bg-white rounded-lg shadow-2xl border border-gray-200 flex flex-col overflow-hidden">
          {/* Header */}
          <div 
            className="p-4 text-white flex items-center justify-between"
            style={{ backgroundColor: primaryColor }}
          >
            <div className="flex items-center space-x-2">
              <MessageCircle className="w-5 h-5" />
              <div>
                <h3 className="font-semibold text-sm">{title}</h3>
                <p className="text-xs opacity-90">{subtitle}</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="hover:bg-white/20 p-1 rounded transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.isHtml ? (
                  <div 
                    className="w-full"
                    dangerouslySetInnerHTML={{ __html: message.text }}
                    onClick={(e) => {
                      const target = e.target as HTMLElement;
                      if (target.tagName === 'BUTTON' && target.onclick) {
                        // Extract action from onclick attribute
                        const onclickStr = target.getAttribute('onclick') || '';
                        const actionMatch = onclickStr.match(/handleActionButton\('([^']+)'\)/);
                        if (actionMatch) {
                          handleActionButton(actionMatch[1]);
                        }
                      }
                    }}
                  />
                ) : (
                  <div
                    className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                      message.sender === 'user'
                        ? 'text-white'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                    style={{
                      backgroundColor: message.sender === 'user' ? primaryColor : undefined
                    }}
                  >
                    {message.text}
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-3 py-2 rounded-lg text-sm text-gray-800">
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
          <div className="p-4 border-t border-gray-200">
            <div className="flex space-x-2">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="px-3 py-2 text-white rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
                style={{ backgroundColor: primaryColor }}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-14 h-14 text-white rounded-full shadow-lg hover:scale-105 transition-transform flex items-center justify-center"
        style={{ backgroundColor: primaryColor }}
      >
        {isOpen ? <X className="w-6 h-6" /> : <MessageCircle className="w-6 h-6" />}
      </button>
    </div>
  );
};

export default ChatWidget;