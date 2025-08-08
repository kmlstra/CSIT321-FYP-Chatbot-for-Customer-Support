'use client';

import React from 'react';
import ConversationDetail from '../../../components/ConversationDetail';

interface ConversationPageProps {
  params: Promise<{
    id: string;
  }>;
}

const ConversationPage: React.FC<ConversationPageProps> = ({ params }) => {
  const [conversationId, setConversationId] = React.useState<string>('');

  React.useEffect(() => {
    params.then((resolvedParams) => {
      setConversationId(resolvedParams.id);
    });
  }, [params]);

  if (!conversationId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-100 via-blue-50 to-indigo-100 py-8 px-4 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block w-8 h-8 border-3 border-gray-300 border-t-indigo-600 rounded-full animate-spin mb-4"></div>
          <p>Loading conversation...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 via-blue-50 to-indigo-100 py-8 px-4">
      <ConversationDetail conversationId={conversationId} />
    </div>
  );
};

export default ConversationPage;