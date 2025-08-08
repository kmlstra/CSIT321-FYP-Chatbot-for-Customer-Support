'use client';

import React, { useState, useMemo } from 'react';
import { Download, Search, MessageCircle, Settings, Clock, Hash, Activity, Table, ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';

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

interface ConversationHistory {
  id: string;
  timestamp: string;
  messageCount: number;
  lastMessage: string;
  participants: string[];
}

type SortField = 'id' | 'timestamp' | 'messageCount' | 'lastMessage';
type SortDirection = 'asc' | 'desc';
type ViewMode = 'single' | 'table';

const ChatHistoryViewer: React.FC = () => {
  const [apiUrl, setApiUrl] = useState('http://localhost:8000/api/conversation');
  const [conversationId, setConversationId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationData, setConversationData] = useState<ConversationData | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [searchedId, setSearchedId] = useState('');
  
  // New state for table view
  const [viewMode, setViewMode] = useState<ViewMode>('single');
  const [conversationHistory, setConversationHistory] = useState<ConversationHistory[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<SortField>('timestamp');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

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

  // New functions for table functionality
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
        const historyData: ConversationHistory[] = data.conversations.map((conv: ConversationData) => {
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

  const selectConversationFromTable = (id: string) => {
    setConversationId(id);
    setViewMode('single');
    // Trigger search for the selected conversation
    const event = { preventDefault: () => {} } as React.FormEvent;
    searchConversation(event);
  };

  const searchConversation = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!conversationId.trim()) {
      setError('Please enter a conversation ID');
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
        setSearchedId(conversationId.trim());
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

  const exportConversation = () => {
    if (!conversationData || !searchedId) {
      alert('No conversation data to export');
      return;
    }

    const exportData = {
      conversationId: searchedId,
      exportedAt: new Date().toISOString(),
      messages: messages
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation_${searchedId}_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const renderInitialState = () => (
    <div className="text-center py-10 text-gray-500">
      <MessageCircle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
      <h3 className="text-lg font-semibold mb-2">Ready to Search</h3>
      <p>Enter a conversation ID above to view the chat history</p>
    </div>
  );

  const renderLoading = () => (
    <div className="text-center py-10 text-gray-500">
      <div className="inline-block w-8 h-8 border-3 border-gray-300 border-t-indigo-600 rounded-full animate-spin mb-4"></div>
      <p>Searching for conversation...</p>
    </div>
  );

  const renderError = () => (
    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-center">
      <strong>❌ Error:</strong> {error}
    </div>
  );

  const renderNoResults = () => (
    <div className="text-center py-10 text-gray-500">
      <Search className="w-12 h-12 mx-auto mb-4 text-gray-400" />
      <h3 className="text-lg font-semibold mb-2">No Conversation Found</h3>
      <p>No conversation found with ID: <strong>{searchedId}</strong></p>
      <p>Please check the ID and try again.</p>
    </div>
  );

  const renderTableView = () => {
    return (
      <>
        {/* Search and Controls */}
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
                {isLoadingHistory ? 'Loading...' : 'Refresh'}
              </button>
            </div>
          </div>
        </div>

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
                {isLoadingHistory ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-4 h-4 border-2 border-gray-300 border-t-indigo-600 rounded-full animate-spin"></div>
                        Loading conversation history...
                      </div>
                    </td>
                  </tr>
                ) : paginatedHistory.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                      {searchTerm ? 'No conversations match your search criteria.' : 'No conversation history found. Click "Refresh" to load conversations.'}
                    </td>
                  </tr>
                ) : (
                  paginatedHistory.map((conv) => (
                    <tr key={conv.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900 font-mono">{conv.id}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-600">
                          {new Date(conv.timestamp).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900 font-medium">{conv.messageCount}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1">
                          {conv.participants.map((participant, idx) => (
                            <span
                              key={idx}
                              className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                            >
                              {participant}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-600 max-w-xs truncate">{conv.lastMessage}</div>
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => selectConversationFromTable(conv.id)}
                          className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1 rounded-md text-xs font-semibold transition-colors"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-6 flex items-center justify-between">
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
                return (
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      currentPage === page
                        ? 'bg-indigo-600 text-white'
                        : 'border border-gray-300 text-gray-600 hover:bg-gray-50'
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
      </>
    );
  };

  const renderConversation = () => {
    const timestamp = conversationData?.timestamp ? new Date(conversationData.timestamp).toLocaleString() : 'Unknown';
    
    return (
      <>
        <div className="bg-gray-50 p-4 rounded-lg mb-6 border-l-4 border-indigo-600">
          <h3 className="text-gray-800 mb-2 text-lg font-semibold flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Conversation Details
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="flex flex-col">
              <span className="text-xs text-gray-600 font-semibold uppercase tracking-wide flex items-center gap-1">
                <Hash className="w-3 h-3" />
                Conversation ID
              </span>
              <span className="text-sm text-gray-800 font-medium mt-1">{searchedId}</span>
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
          <h1 className="text-4xl font-bold mb-3 flex items-center justify-center gap-3 drop-shadow-lg">
            🤖 CleverCompanion Chat History Viewer
          </h1>
          <p className="opacity-95 text-xl font-medium">Live Support Dashboard - View Customer Conversations</p>
          <div className="mt-4 flex justify-center items-center gap-2 text-sm opacity-80">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span>System Online</span>
          </div>
        </div>
      </div>

      {/* Search Section */}
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
        
        {/* View Mode Toggle */}
        <div className="mb-6 flex items-center justify-center">
          <div className="bg-white rounded-xl p-1 shadow-md border border-gray-200">
            <button
              onClick={() => setViewMode('single')}
              className={`px-6 py-3 rounded-lg text-sm font-semibold transition-all duration-300 flex items-center gap-2 ${
                viewMode === 'single'
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-700 text-white shadow-md'
                  : 'text-gray-600 hover:text-indigo-600 hover:bg-gray-50'
              }`}
            >
              <MessageCircle className="w-4 h-4" />
              Single Conversation
            </button>
            <button
              onClick={() => {
                setViewMode('table');
                if (conversationHistory.length === 0) {
                  fetchConversationHistory();
                }
              }}
              className={`px-6 py-3 rounded-lg text-sm font-semibold transition-all duration-300 flex items-center gap-2 ${
                viewMode === 'table'
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-700 text-white shadow-md'
                  : 'text-gray-600 hover:text-indigo-600 hover:bg-gray-50'
              }`}
            >
              <Table className="w-4 h-4" />
              All Conversations
            </button>
          </div>
        </div>
        
        {/* Single Conversation Search Form */}
        {viewMode === 'single' && (
          <form onSubmit={searchConversation} className="flex gap-3 items-center flex-wrap">
            <input 
              type="text" 
              value={conversationId}
              onChange={(e) => setConversationId(e.target.value)}
              className="flex-1 min-w-80 px-5 py-4 border-2 border-gray-300 rounded-xl text-base focus:outline-none focus:border-indigo-600 focus:ring-4 focus:ring-indigo-100 transition-all duration-300 shadow-md hover:shadow-lg"
              placeholder="Enter Conversation ID (e.g., user_1754271933040_qs19m960z)"
              required
            />
            <button 
              type="submit" 
              disabled={isLoading}
              className="bg-gradient-to-r from-indigo-600 to-purple-700 hover:from-indigo-700 hover:to-purple-800 disabled:opacity-60 disabled:cursor-not-allowed text-white px-6 py-3 rounded-xl text-base font-semibold transition-all duration-300 hover:-translate-y-1 disabled:hover:translate-y-0 flex items-center gap-2 shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              <Search className="w-4 h-4" />
              {isLoading ? 'Searching...' : 'Search Conversation'}
            </button>
          </form>
        )}
      </div>

      {/* Results Section */}
      <div className="p-6 min-h-96">
        {viewMode === 'table' ? (
          renderTableView()
        ) : (
          <>
            {isLoading && renderLoading()}
            {error && renderError()}
            {!isLoading && !error && !conversationData && renderInitialState()}
            {!isLoading && !error && conversationData && messages.length === 0 && renderNoResults()}
            {!isLoading && !error && conversationData && renderConversation()}
          </>
        )}
      </div>
    </div>
  );
};

export default ChatHistoryViewer;