'use client';

import React, { useState, useMemo } from 'react';
import { Search, MessageCircle, Settings, Clock, Hash, Activity, ChevronUp, ChevronDown, ChevronLeft, ChevronRight, Eye } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface Message {
  sender: string;
  content: string;
}



interface ConversationHistory {
  id: string;
  timestamp: string;
  messageCount: number;
  lastMessage: string;
  participants: string[];
}

type SortField = 'id' | 'timestamp' | 'messageCount' | 'lastMessage';
type SortDirection = 'asc' | 'desc';

const ConversationsList: React.FC = () => {
  const router = useRouter();
  const [apiUrl, setApiUrl] = useState('http://localhost:8000/api/conversation');
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationHistory, setConversationHistory] = useState<ConversationHistory[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<SortField>('timestamp');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

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

  const fetchConversationHistory = async () => {
    if (!apiUrl.trim()) {
      setError('Please configure the API URL');
      return;
    }

    setIsLoadingHistory(true);
    setError(null);

    try {
      const response = await fetch(`${apiUrl}/history`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.success && data.conversations) {
        const historyData: ConversationHistory[] = data.conversations.map((conv: { id?: string; content: string; timestamp?: string }) => {
          const messages = parseConversationContent(conv.content || '');
          return {
            id: conv.id || 'Unknown',
            timestamp: conv.timestamp || new Date().toISOString(),
            messageCount: messages.length,
            lastMessage: messages.length > 0 ? messages[messages.length - 1].content.substring(0, 100) + '...' : 'No messages',
            participants: [...new Set(messages.map(m => m.sender || 'unknown').filter(sender => sender !== 'unknown'))]
          };
        });
        setConversationHistory(historyData);
      } else {
        setError('No conversation history found');
      }
    } catch (error) {
      console.error('Error fetching conversation history:', error);
      setError(`Failed to fetch conversation history: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
    setCurrentPage(1);
  };

  const filteredAndSortedHistory = useMemo(() => {
    const filtered = conversationHistory.filter(conv => 
      conv.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      conv.lastMessage.toLowerCase().includes(searchTerm.toLowerCase()) ||
      conv.participants.some(p => p.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    filtered.sort((a, b) => {
      let aValue: string | number | Date = a[sortField];
      let bValue: string | number | Date = b[sortField];

      if (sortField === 'timestamp') {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      } else if (sortField === 'messageCount') {
        aValue = Number(aValue);
        bValue = Number(bValue);
      } else {
        aValue = String(aValue).toLowerCase();
        bValue = String(bValue).toLowerCase();
      }

      if (sortDirection === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

    return filtered;
  }, [conversationHistory, searchTerm, sortField, sortDirection]);

  const paginatedHistory = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredAndSortedHistory.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredAndSortedHistory, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(filteredAndSortedHistory.length / itemsPerPage);

  const handlePageChange = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  const selectConversation = (id: string) => {
    router.push(`/conversation/${id}`);
  };

  const renderError = () => (
    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-center">
      <strong>❌ Error:</strong> {error}
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-purple-700 text-white p-8 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-black opacity-10"></div>
        <div className="relative z-10">
          <h1 className="text-4xl font-bold mb-3 flex items-center justify-center gap-3 drop-shadow-lg">
            🤖 All Conversations
          </h1>
          <p className="opacity-95 text-xl font-medium">Live Support Dashboard - View All Customer Conversations</p>
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

      {/* Search and Controls */}
      <div className="p-6">
        <div className="mb-6 space-y-4">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border-2 border-gray-300 rounded-xl text-sm focus:outline-none focus:border-indigo-600 focus:ring-4 focus:ring-indigo-100 transition-all duration-300"
                placeholder="Search conversations by ID, message content, or participants..."
              />
            </div>
            <div className="flex gap-2 items-center">
              <select
                value={itemsPerPage}
                onChange={(e) => setItemsPerPage(Number(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-indigo-600"
              >
                <option value={5}>5 per page</option>
                <option value={10}>10 per page</option>
                <option value={25}>25 per page</option>
                <option value={50}>50 per page</option>
              </select>
              <button
                onClick={fetchConversationHistory}
                disabled={isLoadingHistory}
                className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:opacity-60 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 flex items-center gap-2"
              >
                <Activity className="w-4 h-4" />
                {isLoadingHistory ? 'Loading...' : 'Load Conversations'}
              </button>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && renderError()}

        {/* Table */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left">
                    <button
                      onClick={() => handleSort('id')}
                      className="flex items-center gap-2 text-xs font-semibold text-gray-600 uppercase tracking-wide hover:text-indigo-600 transition-colors"
                    >
                      Conversation ID
                      {sortField === 'id' && (
                        sortDirection === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-4 text-left">
                    <button
                      onClick={() => handleSort('timestamp')}
                      className="flex items-center gap-2 text-xs font-semibold text-gray-600 uppercase tracking-wide hover:text-indigo-600 transition-colors"
                    >
                      Last Updated
                      {sortField === 'timestamp' && (
                        sortDirection === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-4 text-left">
                    <button
                      onClick={() => handleSort('messageCount')}
                      className="flex items-center gap-2 text-xs font-semibold text-gray-600 uppercase tracking-wide hover:text-indigo-600 transition-colors"
                    >
                      Messages
                      {sortField === 'messageCount' && (
                        sortDirection === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-4 text-left">
                    <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Participants</span>
                  </th>
                  <th className="px-6 py-4 text-left">
                    <button
                      onClick={() => handleSort('lastMessage')}
                      className="flex items-center gap-2 text-xs font-semibold text-gray-600 uppercase tracking-wide hover:text-indigo-600 transition-colors"
                    >
                      Last Message
                      {sortField === 'lastMessage' && (
                        sortDirection === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-4 text-left">
                    <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {paginatedHistory.map((conversation) => (
                  <tr key={conversation.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Hash className="w-4 h-4 text-gray-400" />
                          <span className="text-sm font-medium text-gray-900 font-mono">{conversation.id}</span>
                        </div>
                        <button
                          onClick={() => router.push(`/conversation/${conversation.id}`)}
                          className="ml-2 inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
                          title="View conversation details"
                        >
                          <Eye className="w-3 h-3 mr-1" />
                          View
                        </button>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-600">
                          {new Date(conversation.timestamp).toLocaleString()}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <MessageCircle className="w-4 h-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-900">{conversation.messageCount}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {conversation.participants.map((participant, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                          >
                            {participant}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm text-gray-600 truncate max-w-xs">{conversation.lastMessage}</p>
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => selectConversation(conversation.id)}
                        className="bg-gradient-to-r from-indigo-600 to-purple-700 hover:from-indigo-700 hover:to-purple-800 text-white px-3 py-1 rounded-lg text-xs font-semibold transition-all duration-300 hover:shadow-md"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, filteredAndSortedHistory.length)} of {filteredAndSortedHistory.length} conversations
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="p-2 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const page = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
                  if (page > totalPages) return null;
                  
                  return (
                    <button
                      key={page}
                      onClick={() => handlePageChange(page)}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        currentPage === page
                          ? 'bg-indigo-600 text-white'
                          : 'text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      {page}
                    </button>
                  );
                })}
                
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="p-2 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Empty State */}
        {!isLoadingHistory && conversationHistory.length === 0 && !error && (
          <div className="text-center py-10 text-gray-500">
            <MessageCircle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-semibold mb-2">No Conversations Found</h3>
            <p>Click &quot;Load Conversations&quot; to fetch conversation history from the API.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConversationsList;