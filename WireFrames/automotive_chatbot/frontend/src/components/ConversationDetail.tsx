'use client';

import React, { useState, useEffect } from 'react';
import { Download, MessageCircle, Settings, Clock, Hash, Activity, ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface Message {
  sender: string;
  content: string;
}

interface ConversationData {
  id?: string;
  content: string;
  timestamp?: string;
}

interface ApiResponse {
  success: boolean;
  conversation?: ConversationData[];
}

interface ConversationDetailProps {
  conversationId: string;
}

const ConversationDetail: React.FC<ConversationDetailProps> = ({ conversationId }) => {
  const router = useRouter();
  const [apiUrl, setApiUrl] = useState('http://localhost:8000/api/conversation');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationData, setConversationData] = useState<ConversationData | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);

  const parseConversationContent = (content: string): Message[] => {
    if (!content) return [];
    
    const messages: Message[] = [];
    const lines = content.split('\n').filter(line => line.trim());
    
    lines.forEach(line => {
      line = line.trim();
      if (!line) return;
      
      // Parse different message formats
      if (line.startsWith('User: ')) {
        messages.push({
          sender: 'User',
          content: line.substring(6).trim()
        });
      } else if (line.startsWith('Bot: ')) {
        messages.push({
          sender: 'Bot',
          content: line.substring(5).trim()
        });
      } else if (line.includes(': ')) {
        // Generic format: "Sender: Message"
        const colonIndex = line.indexOf(': ');
        const sender = line.substring(0, colonIndex).trim();
        const content = line.substring(colonIndex + 2).trim();
        
        if (sender && content) {
          messages.push({ sender, content });
        }
      } else {
        // Treat as system message or continuation
        if (messages.length > 0) {
          // Append to last message
          messages[messages.length - 1].content += '\n' + line;
        } else {
          // First message without sender prefix
          messages.push({
            sender: 'System',
            content: line
          });
        }
      }
    });
    
    return messages;
  };

  const formatMessageContent = (content: string): string => {
    if (!content) return '';
    
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>')
      .replace(/https?:\/\/[^\s]+/g, '<a href="$&" target="_blank">$&</a>');
  };

  const fetchConversation = async () => {
    if (!conversationId.trim()) {
      setError('No conversation ID provided');
      return;
    }

    if (!apiUrl.trim()) {
      setError('Please configure the API URL');
      return;
    }

    setIsLoading(true);
    setError(null);
    setConversationData(null);
    setMessages([]);

    try {
      const response = await fetch(`${apiUrl}/history/${conversationId.trim()}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: ApiResponse = await response.json();
      
      if (data.success && data.conversation && data.conversation.length > 0) {
        const conversation = data.conversation[0];
        setConversationData(conversation);
        setMessages(parseConversationContent(conversation.content || ''));
      } else {
        setError(`No conversation found with ID: ${conversationId.trim()}`);
      }
    } catch (error) {
      console.error('Error fetching conversation:', error);
      setError(`Failed to fetch conversation: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (conversationId) {
      fetchConversation();
    }
  }, [conversationId, apiUrl]);

  const exportConversation = () => {
    if (!conversationData || !conversationId) {
      alert('No conversation data to export');
      return;
    }

    const exportData = {
      conversationId: conversationId,
      exportedAt: new Date().toISOString(),
      messages: messages
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation_${conversationId}_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const renderLoading = () => (
    <div className="text-center py-10 text-gray-500">
      <div className="inline-block w-8 h-8 border-3 border-gray-300 border-t-indigo-600 rounded-full animate-spin mb-4"></div>
      <p>Loading conversation...</p>
    </div>
  );

  const renderError = () => (
    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-center">
      <strong>❌ Error:</strong> {error}
    </div>
  );

  const renderNoResults = () => (
    <div className="text-center py-10 text-gray-500">
      <MessageCircle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
      <h3 className="text-lg font-semibold mb-2">No Conversation Found</h3>
      <p>No conversation found with ID: <strong>{conversationId}</strong></p>
      <p>Please check the ID and try again.</p>
    </div>
  );

  const renderConversation = () => {
    const timestamp = conversationData?.timestamp 
      ? new Date(conversationData.timestamp).toLocaleString()
      : 'Unknown';

    return (
      <>
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 p-6 rounded-xl mb-6 shadow-md">
          <h3 className="text-indigo-800 mb-4 font-bold text-lg flex items-center gap-2">
            <Activity className="w-5 h-5" />
            📊 Conversation Details
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="flex flex-col">
              <span className="text-xs text-gray-600 font-semibold uppercase tracking-wide flex items-center gap-1">
                <Hash className="w-3 h-3" />
                Conversation ID
              </span>
              <span className="text-sm text-gray-800 font-medium mt-1 font-mono">{conversationId}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-gray-600 font-semibold uppercase tracking-wide flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Last Updated
              </span>
              <span className="text-sm text-gray-800 font-medium mt-1">{timestamp}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-gray-600 font-semibold uppercase tracking-wide flex items-center gap-1">
                <MessageCircle className="w-3 h-3" />
                Total Messages
              </span>
              <span className="text-sm text-gray-800 font-medium mt-1">{messages.length}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-gray-600 font-semibold uppercase tracking-wide flex items-center gap-1">
                <Activity className="w-3 h-3" />
                Status
              </span>
              <span className="text-sm text-gray-800 font-medium mt-1">Active</span>
            </div>
          </div>
        </div>
        
        <div className="max-h-96 overflow-y-auto border border-gray-300 rounded-lg p-4 bg-gray-50">
          {messages.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No messages found in this conversation.</p>
            </div>
          ) : (
            messages.map((message, index) => {
              const isUser = message.sender.toLowerCase() === 'user';
              const timestamp = new Date().toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit',
                hour12: true 
              });
              
              return (
                <div key={index} className={`mb-4 flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold flex-shrink-0 ${
                    isUser 
                      ? 'bg-gradient-to-br from-indigo-600 to-purple-700 text-white' 
                      : 'bg-gray-300 text-gray-700'
                  }`}>
                    {isUser ? '👤' : '🤖'}
                  </div>
                  <div className={`flex-1 max-w-[70%] ${isUser ? 'text-right' : ''}`}>
                    <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed break-words ${
                      isUser 
                        ? 'bg-gradient-to-br from-indigo-600 to-purple-700 text-white rounded-tr-sm' 
                        : 'bg-white text-gray-800 border border-gray-300 rounded-tl-sm'
                    }`}>
                      <div dangerouslySetInnerHTML={{ __html: formatMessageContent(message.content) }} />
                    </div>
                    <div className={`text-xs mt-1 opacity-70 ${
                      isUser ? 'text-gray-600' : 'text-gray-500'
                    }`}>
                      {timestamp}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
        
        <div className="mt-6 pt-6 border-t border-gray-300 text-center">
          <button 
            onClick={exportConversation}
            className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-6 py-3 rounded-xl text-sm font-semibold transition-all duration-300 flex items-center gap-2 mx-auto shadow-lg hover:shadow-xl transform hover:scale-105 hover:-translate-y-1"
          >
            <Download className="w-4 h-4" />
            Export Conversation
          </button>
        </div>
      </>
    );
  };

  return (
    <div className="max-w-6xl mx-auto bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-purple-700 text-white p-8 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-black opacity-10"></div>
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={() => router.push('/chat-history')}
              className="flex items-center gap-2 text-white hover:text-gray-200 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="text-sm font-medium">Back to All Conversations</span>
            </button>
          </div>
          <h1 className="text-4xl font-bold mb-3 flex items-center justify-center gap-3 drop-shadow-lg">
            🤖 Conversation Details
          </h1>
          <p className="opacity-95 text-xl font-medium">Live Support Dashboard - View Individual Conversation</p>
          <div className="mt-4 flex justify-center items-center gap-2 text-sm opacity-80">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span>System Online</span>
          </div>
        </div>
      </div>

      {/* Configuration Section */}
      <div className="p-8 border-b border-gray-200 bg-gradient-to-br from-gray-50 to-blue-50">
        <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-300 p-6 rounded-xl mb-6 shadow-md">
          <h4 className="text-yellow-800 mb-3 font-bold text-lg flex items-center gap-2">
            <Settings className="w-5 h-5" />
            ⚙️ API Configuration
          </h4>
          <p className="text-yellow-800 text-sm mb-3 font-medium">
            Enter your backend API URL (for Supabase integration, this should point to your conversation API endpoint):
          </p>
          <input 
            type="text" 
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            className="w-full px-4 py-3 border-2 border-yellow-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500 transition-all duration-200 shadow-sm"
            placeholder="http://localhost:8000/api/conversation"
          />
        </div>
      </div>

      {/* Results Section */}
      <div className="p-6 min-h-96">
        {isLoading && renderLoading()}
        {error && renderError()}
        {!isLoading && !error && !conversationData && renderNoResults()}
        {!isLoading && !error && conversationData && renderConversation()}
      </div>
    </div>
  );
};

export default ConversationDetail;