export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold text-gray-900">🤖 CleverCompanion</h1>
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">Admin Dashboard</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                ● Online
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Welcome to CleverCompanion Dashboard</h2>
          <p className="text-lg text-gray-600">Access your automotive chatbot tools and support features</p>
        </div>

        {/* Navigation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* CleverCompanion Chat Widget */}
          <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300 border border-gray-200">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <span className="text-white text-xl font-bold">💬</span>
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-gray-900">CleverCompanion Chat</h3>
                  <p className="text-sm text-gray-500">Interactive automotive assistant</p>
                </div>
              </div>
              <p className="text-gray-600 mb-4">
                Access the main CleverCompanion chatbot interface for customer interactions, COE price queries, and automotive assistance.
              </p>
              <div className="flex space-x-3">
                <a
                  href="/clevercompanion.html"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  🚀 Launch Chat
                </a>
                <a
                  href="/clevercompanion.html"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200 shadow-md hover:shadow-lg transform hover:scale-105"
                >
                  💬 Chat Demo
                </a>
              </div>
            </div>
          </div>

          {/* Chat History Viewer */}
          <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300 border border-gray-200">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-teal-600 rounded-lg flex items-center justify-center">
                    <span className="text-white text-xl font-bold">📋</span>
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-gray-900">Chat History Viewer</h3>
                  <p className="text-sm text-gray-500">Live support dashboard</p>
                </div>
              </div>
              <p className="text-gray-600 mb-4">
                View and manage customer conversation history. Search by conversation ID to access complete chat logs for support purposes.
              </p>
              <div className="flex space-x-3">
                <a
                  href="/conversations"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-gradient-to-r from-green-500 to-teal-600 hover:from-green-600 hover:to-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  🔍 All Conversations
                </a>
                <a
                  href="/chat-history"
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-all duration-200 shadow-md hover:shadow-lg transform hover:scale-105"
                >
                  📄 Individual Search
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">🚀 Quick Access</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">💬</div>
              <div className="text-sm font-medium text-gray-900 mt-2">Chat Interface</div>
              <div className="text-xs text-gray-500">Customer interactions</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">📋</div>
              <div className="text-sm font-medium text-gray-900 mt-2">History Viewer</div>
              <div className="text-xs text-gray-500">Support dashboard</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">🔧</div>
              <div className="text-sm font-medium text-gray-900 mt-2">Admin Tools</div>
              <div className="text-xs text-gray-500">Management panel</div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>CleverCompanion - Singapore Automotive Assistant Platform</p>
          <p className="mt-1">🚗 Powered by RASA, FastAPI & React</p>
        </div>
      </div>
    </div>
  )
}