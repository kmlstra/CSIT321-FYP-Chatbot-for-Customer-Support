import React from 'react';
import ChatHistoryViewer from '../components/ChatHistoryViewer';

const ChatHistoryViewerPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 via-purple-600 to-purple-800 p-5">
      <ChatHistoryViewer />
    </div>
  );
};

export default ChatHistoryViewerPage;