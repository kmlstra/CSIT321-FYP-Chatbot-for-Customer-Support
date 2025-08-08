'use client';

import React from 'react';
import ConversationsList from '../../components/ConversationsList';

const ConversationsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 via-blue-50 to-indigo-100 py-8 px-4">
      <ConversationsList />
    </div>
  );
};

export default ConversationsPage;