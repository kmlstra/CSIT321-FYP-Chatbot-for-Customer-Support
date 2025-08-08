'use client';

export function DemoButton() {
  const scrollToDemo = () => {
    document.getElementById('chat-section')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <button 
      className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-indigo-600 bg-white hover:bg-gray-50 md:py-4 md:text-lg md:px-10"
      onClick={scrollToDemo}
    >
      Try Demo
    </button>
  );
} 