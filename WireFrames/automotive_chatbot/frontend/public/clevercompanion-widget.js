(function() {
    'use strict';
    
    // Static files are now served from the frontend server
    // No need for backend URL detection for static assets
    const STATIC_BASE_URL = window.location.origin;
    
    // Configuration
    const CONFIG = {
        WIDGET_ID: 'cc-chatbot-container',
        TOGGLE_ID: 'cc-toggle',
        CLOSE_ID: 'cc-close-btn',
        MESSAGES_ID: 'cc-messages',
        INPUT_ID: 'cc-input',
        SEND_BTN_ID: 'cc-send-btn',
        MENU_BTN_ID: 'cc-menu-btn',
        API_URL: 'http://localhost:8001/api/rasa/chat'
    };

    // Widget configuration
    const currentConfig = {
        title: 'CleverCompanion',
        subtitle: 'Your automotive assistant',
        welcomeMessage: "Hello! I'm your automotive assistant. How can I help you today?"
    };

    // PROBLEM 1 & 2 FIX: Using PNG logo with proper path and styling
    const CHATBOT_LOGO_URL = `${STATIC_BASE_URL}/static/media/images/CleverCompanion-logo.png`;

    // User avatar - Using boy.png as requested
    const USER_AVATAR = `<img src="${STATIC_BASE_URL}/static/media/images/boy.png" alt="User" style="width: 20px; height: 20px; border-radius: 50%; object-fit: cover;">`;

    // Menu options
    const MENU_OPTIONS = [
        { icon: '💰', text: 'Latest COE Prices', action: 'what are the current coe prices' },
        { icon: '🚗', text: 'Search Vehicle', action: 'Help me search for vehicles by budget, type and brand preferences' },
        { icon: '📅', text: 'Appointment Booking', action: 'I want to book an appointment' },
        { icon: '🔧', text: 'Maintenance Tips', action: 'Provide vehicle maintenance guidance and service center recommendations' },
        { icon: '💳', text: 'Loan Calculator', action: 'Calculate car loan with current interest rates and financing options' },
        { icon: '📞', text: 'Contact Us', action: 'Show me contact information and ways to reach CleverCompanion' },
        { icon: '📝', text: 'Feedback', action: 'I want to provide feedback about the service and suggest improvements' },
        // { icon: '⭐', text: 'Car Reviews & Ratings', action: 'Show top-rated cars and help me compare vehicle models and reviews' },
        { icon: '💬', text: 'Live Support', action: 'I need live support assistance' }
    ];

    // PROBLEM 3 FIX: Simplified event management - removed cooldown
    let isProcessing = false;
    const ACTION_COOLDOWN = 1000; // 1 second cooldown for action buttons

    // Comprehensive CSS - Fixed positioning and styling
    const WIDGET_CSS = `
        /* Widget Container - Shifted more left with close button */
        #cc-chatbot-container {
            position: fixed;
            bottom: 20px;
            right: 90px;
            width: 450px;
            max-width: calc(100vw - 120px);
            height: 600px;
            max-height: calc(100vh - 40px);
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            z-index: 999999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            transform: translateY(100vh) scale(0.8);
            opacity: 0;
            visibility: hidden;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            border: 1px solid rgba(79, 70, 229, 0.1);
            pointer-events: none;
        }

        #cc-chatbot-container.cc-open {
            transform: translateY(0) scale(1);
            opacity: 1;
            visibility: visible;
            pointer-events: auto;
        }

        /* Toggle button - Same size as close button */
        #cc-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: white;
            border: 3px solid #4F46E5;
            cursor: pointer;
            z-index: 1000000;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 20px rgba(79, 70, 229, 0.4);
            transition: all 0.3s ease;
            outline: none;
            font-size: 24px;
            color: white;
            overflow: hidden;
            pointer-events: auto;
        }

        #cc-toggle:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 25px rgba(79, 70, 229, 0.5);
        }

        #cc-toggle img {
            width: 50px;
            height: 50px;
            border-radius: 6px;
            object-fit: contain;
            padding: 2px;
        }

        /* Close button - Same size as toggle button */
        #cc-close-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: rgba(239, 68, 68, 0.9);
            border: none;
            cursor: pointer;
            z-index: 999999;
            display: none;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
            transition: all 0.2s ease;
            outline: none;
            color: white;
            pointer-events: auto;
        }

        #cc-close-btn:hover {
            background: rgba(239, 68, 68, 1);
            transform: scale(1.1);
        }

        #cc-close-btn.cc-visible {
            display: flex;
        }

        /* Header - PROBLEM 2 FIX: Improved header design */
        .cc-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 20px 20px 0 0;
            flex-shrink: 0;
            position: relative;
        }

        .cc-header h3 {
            margin: 0 0 5px 0;
            font-size: 18px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .cc-header p {
            margin: 0;
            font-size: 14px;
            opacity: 0.9;
        }

        .cc-logo {
            width: 50px;
            height: 50px;
            border-radius: 6px;
            background: white;
            border: 2px solid #4F46E5;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            padding: 2px;
        }

        .cc-logo img {
            width: 90%;
            height: 90%;
            border-radius: 6px;
            object-fit: contain;
        }

        /* Clear cache button */
        .cc-clear-cache-btn {
            position: absolute;
            top: 15px;
            right: 15px;
            width: 32px;
            height: 32px;
            border: none;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            color: white;
            opacity: 0.8;
        }

        .cc-clear-cache-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            opacity: 1;
            transform: scale(1.1);
        }

        .cc-clear-cache-btn svg {
            width: 16px;
            height: 16px;
        }

        /* Messages area - Hidden scrollbar */
        #cc-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            overflow-x: hidden;
            background: linear-gradient(to bottom, #f8fafc 0%, #f1f5f9 100%);
            display: flex;
            flex-direction: column;
            gap: 16px;
            scrollbar-width: none;
            -ms-overflow-style: none;
            scrollbar-color: transparent transparent;
        }

        #cc-messages::-webkit-scrollbar {
            display: none !important;
            width: 0 !important;
            height: 0 !important;
            background: transparent !important;
        }
        
        #cc-messages::-webkit-scrollbar-track {
            display: none !important;
            background: transparent !important;
        }
        
        #cc-messages::-webkit-scrollbar-thumb {
            display: none !important;
            background: transparent !important;
        }
        
        #cc-messages::-webkit-scrollbar-corner {
            display: none !important;
            background: transparent !important;
        }
        
        /* Ensure no scrollbars on the main widget container */
        #clevercompanion-widget {
            overflow: hidden !important;
        }
        
        #cc-widget {
            overflow: hidden !important;
        }

        /* Message bubbles */
        .cc-message {
            display: flex;
            gap: 12px;
            animation: messageSlideIn 0.3s ease-out;
            align-items: flex-end;
        }

        @keyframes messageSlideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .cc-message.cc-user {
            flex-direction: row-reverse;
        }

        .cc-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            border: 2px solid #E5E7EB;
        }

        .cc-avatar.cc-bot {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            color: white;
            border-color: #4F46E5;
        }

        .cc-avatar.cc-bot img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 50%;
        }

        .cc-avatar.cc-user {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            border-color: #10b981;
        }

        .cc-bubble {
            max-width: 280px;
            padding: 12px 16px;
            border-radius: 18px;
            position: relative;
            word-wrap: break-word;
            line-height: 1.4;
            font-size: 14px;
        }

        .cc-message.cc-bot .cc-bubble {
            background: white;
            color: #374151;
            border: 1px solid #e5e7eb;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }

        .cc-message.cc-user .cc-bubble {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            color: white;
            border: 1px solid #4F46E5;
        }

        .cc-timestamp {
            font-size: 11px;
            opacity: 0.6;
            margin-top: 4px;
            text-align: right;
        }

        /* Input area */
        .cc-input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e5e7eb;
            display: flex;
            align-items: flex-end;
            gap: 12px;
            position: relative;
        }

        .cc-input-container {
            flex: 1;
            display: flex;
            align-items: flex-end;
            background: #f8fafc;
            border: 2px solid #e2e8f0;
            border-radius: 24px;
            padding: 8px 12px;
            transition: all 0.2s ease;
            position: relative;
        }

        .cc-input-container:focus-within {
            border-color: #4F46E5;
            background: white;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }

        #cc-input {
            flex: 1;
            border: none;
            outline: none;
            background: transparent;
            font-size: 14px;
            line-height: 1.4;
            resize: none;
            min-height: 20px;
            max-height: 100px;
            padding: 6px 0;
            font-family: inherit;
            color: #374151;
        }

        #cc-input::placeholder {
            color: #9ca3af;
        }

        #cc-menu-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #f3f4f6;
            border: 2px solid #e5e7eb;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            color: #6b7280;
            flex-shrink: 0;
        }

        #cc-menu-btn:hover {
            background: #4F46E5;
            border-color: #4F46E5;
            color: white;
            transform: scale(1.05);
        }

        #cc-send-btn {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            color: white;
            flex-shrink: 0;
            margin-left: 8px;
        }

        #cc-send-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        }

        #cc-send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        /* Menu dropdown */
        .cc-menu-dropdown {
            position: absolute;
            bottom: 120px;
            left: 20px;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            padding: 8px;
            min-width: 200px;
            z-index: 1000001;
            display: none;
        }

        .cc-menu-dropdown.cc-show {
            display: block;
        }

        .cc-menu-item {
            padding: 12px 16px;
            cursor: pointer;
            border-radius: 8px;
            font-size: 14px;
            color: #374151;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .cc-menu-item:hover {
            background: #f3f4f6;
            color: #4F46E5;
        }

        /* Action buttons with proper hover effects */
        .cc-action-buttons {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: 12px;
        }

        .cc-action-btn {
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            padding: 12px 16px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s ease;
            color: #475569;
            font-weight: 500;
            text-align: left;
            width: 100%;
            display: block;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .cc-action-btn:hover {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            color: white;
            border-color: #4F46E5;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
        }

        /* Enhanced contact button hover effects */
        .cc-whatsapp-btn {
            background: linear-gradient(135deg, #25d366 0%, #128c7e 100%);
            color: white;
            border: 2px solid #25d366;
            border-radius: 12px;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin: 8px 4px;
            text-decoration: none;
            box-shadow: 0 4px 15px rgba(37, 211, 102, 0.2);
            position: relative;
            overflow: hidden;
            min-width: 180px;
        }

        .cc-whatsapp-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }

        .cc-whatsapp-btn:hover::before {
            left: 100%;
        }

        .cc-whatsapp-btn:hover {
            background: linear-gradient(135deg, #128c7e 0%, #075e54 100%);
            border-color: #128c7e;
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 8px 25px rgba(37, 211, 102, 0.4);
        }

        .cc-whatsapp-btn:active {
            transform: translateY(-1px) scale(0.98);
            box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3);
        }

        .cc-email-btn {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 8px;
            text-decoration: none;
        }

        .cc-email-btn:hover {
            background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
        }

        .cc-phone-btn {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 8px;
            text-decoration: none;
        }

        .cc-phone-btn:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }

        /* Google Maps button styling */
        .cc-maps-btn {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 10px 16px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 8px;
            text-decoration: none;
        }

        .cc-maps-btn:hover {
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        }

        /* Enhanced formatting for COE data */
        .coe-category {
            font-weight: bold;
            color: #4F46E5;
        }

        .price-highlight {
            font-weight: bold;
            color: #059669;
        }

        .trend-down {
            color: #10b981;
            font-weight: bold;
        }

        .trend-up {
            color: #ef4444;
            font-weight: bold;
        }

        /* Trend Arrow Indicators */
        .trend-arrow {
            width: 20px;
            height: 20px;
            vertical-align: middle;
            margin-right: 5px;
            display: inline-block;
        }

        .emoji-highlight {
            font-size: 16px;
        }

        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 768px) {
            #cc-chatbot-container {
                width: calc(100vw - 100px);
                height: calc(100vh - 40px);
                bottom: 10px;
                right: 10px;
                border-radius: 15px;
            }

            #cc-toggle, #cc-close-btn {
                bottom: 15px;
                right: 15px;
            }
        }

        @media (prefers-contrast: high) {
            .cc-chatbot-container {
                border: 2px solid #000;
            }

            .cc-chatbot-message-content {
                border: 2px solid #000;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            .cc-chatbot-container,
            .cc-chatbot-toggle,
            .cc-chatbot-message {
                transition: none;
                animation: none;
            }
        }

        /* Embedded Google Maps */
        .cc-map-container {
            width: 100%;
            margin: 10px 0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .cc-embedded-map {
            width: 100%;
            height: 200px;
            border: 0;
            display: block;
        }

        /* Contact link buttons */
        .cc-contact-link {
            display: inline-block;
            margin: 5px 0;
            padding: 8px 16px;
            border-radius: 20px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }

        .cc-whatsapp-link {
            background: #25D366;
            color: white;
        }

        /* Chart container styling */
        .chart-container {
            position: relative;
            cursor: pointer;
            display: block;
            width: 80%;
            max-width: 350px;
            margin: 8px auto;
            border-radius: 8px;
            overflow: hidden;
            transition: transform 0.2s ease;
        }

        .chart-container:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .chart-container img {
            width: 100%;
            height: auto;
            border-radius: 8px;
            cursor: pointer;
            transition: opacity 0.2s ease;
        }

        .chart-container:hover img {
            opacity: 0.95;
        }

        .cc-whatsapp-link:hover {
            background: #1da851;
            transform: translateY(-1px);
        }

        .cc-email-link {
            background: #FF6B35;
            color: white;
        }

        .cc-email-link:hover {
            background: #e55a2d;
            transform: translateY(-1px);
        }

        /* Feedback modal styles */
        .cc-feedback-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000002;
            display: none;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(4px);
        }

        .cc-feedback-modal.cc-show {
            display: flex;
        }

        .cc-feedback-content {
            background: white;
            border-radius: 16px;
            padding: 24px;
            max-width: 400px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
            animation: feedbackSlideIn 0.3s ease-out;
        }

        @keyframes feedbackSlideIn {
            from {
                opacity: 0;
                transform: scale(0.9) translateY(20px);
            }
            to {
                opacity: 1;
                transform: scale(1) translateY(0);
            }
        }

        .cc-feedback-header {
            text-align: center;
            margin-bottom: 20px;
        }

        .cc-feedback-header h3 {
            margin: 0 0 8px 0;
            color: #1f2937;
            font-size: 20px;
            font-weight: 600;
        }

        .cc-feedback-header p {
            margin: 0;
            color: #6b7280;
            font-size: 14px;
        }

        .cc-rating-section {
            margin-bottom: 20px;
        }

        .cc-rating-label {
            display: block;
            margin-bottom: 8px;
            color: #374151;
            font-weight: 500;
            font-size: 14px;
        }

        .cc-star-rating {
            display: flex;
            gap: 4px;
            justify-content: center;
            margin-bottom: 16px;
        }

        .cc-star {
            font-size: 24px;
            cursor: pointer;
            transition: all 0.2s ease;
            opacity: 0.3;
        }

        .cc-star:hover,
        .cc-star.cc-active {
            opacity: 1;
            transform: scale(1.1);
        }

        .cc-feedback-textarea {
            width: 100%;
            min-height: 80px;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
            resize: vertical;
            transition: border-color 0.2s ease;
        }

        .cc-feedback-textarea:focus {
            outline: none;
            border-color: #4F46E5;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }

        .cc-feedback-buttons {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
            margin-top: 20px;
        }

        .cc-feedback-btn {
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            border: none;
        }

        .cc-feedback-btn.cc-secondary {
            background: #f3f4f6;
            color: #374151;
        }

        .cc-feedback-btn.cc-secondary:hover {
            background: #e5e7eb;
        }

        .cc-feedback-btn.cc-primary {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            color: white;
        }

        .cc-feedback-btn.cc-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        }

        /* Loading spinner */
        .cc-loading {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid #e5e7eb;
            border-radius: 50%;
            border-top-color: #4F46E5;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Typing indicator */
        .cc-typing {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 8px 12px;
            color: #6b7280;
            font-style: italic;
            font-size: 13px;
        }

        .cc-typing-dots {
            display: flex;
            gap: 2px;
        }

        .cc-typing-dot {
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: #9ca3af;
            animation: typingDot 1.4s ease-in-out infinite;
        }

        .cc-typing-dot:nth-child(1) { animation-delay: 0s; }
        .cc-typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .cc-typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typingDot {
            0%, 60%, 100% {
                transform: translateY(0);
                opacity: 0.4;
            }
            30% {
                transform: translateY(-8px);
                opacity: 1;
            }
        }

        /* Chart enlargement overlay styling */
        .chart-enlarge-overlay {
            transition: all 0.2s ease;
        }

        .chart-enlarge-overlay:hover {
            background: rgba(0,0,0,0.9) !important;
            font-weight: 600;
        }

        .cc-avatar.cc-bot {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            color: white;
            border-color: #4F46E5;
        }

        .cc-avatar.cc-bot img {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            object-fit: cover;
            background-color: #FFFFFF;
        }

        .cc-avatar.cc-user {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            border-color: #10b981;
        }

        .cc-bubble {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.4;
            word-wrap: break-word;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }

        .cc-message.cc-bot .cc-bubble {
            background: white;
            color: #374151;
            border: 1px solid #e5e7eb;
            border-radius: 18px 18px 18px 4px;
        }

        .cc-message.cc-user .cc-bubble {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            color: white;
            border-radius: 18px 18px 4px 18px;
        }

        /* Timestamp */
        .cc-timestamp {
            font-size: 11px;
            margin-top: 4px;
            opacity: 0.7;
            color: #9CA3AF;
            font-weight: 500;
        }

        /* PROBLEM 6 FIX: Make user timestamp more visible */
        .cc-message.cc-user .cc-timestamp {
            text-align: right;
            color: #E5E7EB;
            font-weight: 600;
            opacity: 0.9;
        }

        /* Input area - PROBLEM 4 FIX: Add proper form field IDs and names */
        .cc-input-area {
            padding: 12px 16px;
            background: white;
            border-top: 1px solid #e5e7eb;
            flex-shrink: 0;
            display: flex;
            gap: 8px;
            align-items: center;
            min-height: 56px;
        }

        /* Menu button - PROBLEM 1 FIX: Smaller size and reduced spacing */
        #cc-menu-btn {
            background: #f3f4f6;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            width: 36px;
            height: 36px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            outline: none;
            color: #6b7280;
            flex-shrink: 0;
        }

        #cc-menu-btn:hover {
            background: #e5e7eb;
            color: #374151;
        }

        .cc-input-container {
            display: flex;
            gap: 8px;
            align-items: center;
            background: #f8fafc;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            padding: 4px 6px;
            transition: border-color 0.2s ease;
            flex: 1;
            min-height: 36px;
        }

        .cc-input-container:focus-within {
            border-color: #4F46E5;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }

        .cc-input-container #cc-input {
            flex: 1;
            border: none;
            background: transparent;
            padding: 8px 12px;
            font-size: 14px;
            resize: none;
            outline: none;
            font-family: inherit;
            height: 20px; /* Fixed height - no expanding */
            max-height: 20px;
            color: #374151;
            min-height: 20px;
            line-height: 1.4;
            scrollbar-width: none;
            -ms-overflow-style: none;
            overflow: hidden; /* Force single line only */
        }

        .cc-input-container #cc-input::-webkit-scrollbar {
            display: none;
        }

        .cc-input-container #cc-input::placeholder {
            color: #9ca3af;
        }

        /* PROBLEM 2 FIX: New arrow style matching Image 3 */
        #cc-send-btn {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            transition: all 0.2s ease;
            outline: none;
            box-shadow: 0 2px 8px rgba(79, 70, 229, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 36px;
            height: 36px;
        }

        #cc-send-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        }

        #cc-send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        /* Menu dropdown */
        .cc-menu-dropdown {
            position: absolute;
            bottom: 60px;
            left: 20px;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            padding: 8px;
            min-width: 200px;
            z-index: 1000001;
            display: none;
        }

        .cc-menu-dropdown.cc-show {
            display: block;
        }

        .cc-menu-item {
            padding: 12px 16px;
            cursor: pointer;
            border-radius: 8px;
            font-size: 14px;
            color: #374151;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .cc-menu-item:hover {
            background: #f3f4f6;
            color: #4F46E5;
        }

        /* Feedback Modal */
        .cc-feedback-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1000002;
            display: none;
            align-items: center;
            justify-content: center;
        }

        .cc-feedback-modal.cc-show {
            display: flex;
        }

        .cc-feedback-content {
            background: white;
            border-radius: 16px;
            padding: 24px;
            max-width: 400px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }

        .cc-feedback-header {
            text-align: center;
            margin-bottom: 20px;
        }

        .cc-feedback-header h3 {
            margin: 0 0 8px 0;
            color: #374151;
            font-size: 18px;
        }

        .cc-feedback-header p {
            margin: 0;
            color: #6b7280;
            font-size: 14px;
        }

        .cc-rating-section {
            margin-bottom: 20px;
        }

        .cc-rating-label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #374151;
        }

        .cc-star-rating {
            display: flex;
            gap: 4px;
            justify-content: center;
            margin-bottom: 16px;
        }

        .cc-star {
            font-size: 24px;
            color: #d1d5db;
            cursor: pointer;
            transition: color 0.2s ease;
        }

        .cc-star:hover,
        .cc-star.cc-active {
            color: #fbbf24;
        }

        .cc-feedback-textarea {
            width: 100%;
            min-height: 80px;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-family: inherit;
            font-size: 14px;
            resize: vertical;
            outline: none;
            transition: border-color 0.2s ease;
        }

        .cc-feedback-textarea:focus {
            border-color: #4F46E5;
        }

        .cc-feedback-buttons {
            display: flex;
            gap: 12px;
            margin-top: 20px;
        }

        .cc-feedback-btn {
            flex: 1;
            padding: 12px 16px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .cc-feedback-btn.cc-primary {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            color: white;
        }

        .cc-feedback-btn.cc-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        }

        .cc-feedback-btn.cc-secondary {
            background: #f3f4f6;
            color: #374151;
        }

        .cc-feedback-btn.cc-secondary:hover {
            background: #e5e7eb;
        }

        /* Action buttons for questions/recommendations - FIXED */
        .cc-action-buttons {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: 12px;
        }

        .cc-action-btn {
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            padding: 12px 16px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s ease;
            color: #475569;
            font-weight: 500;
            text-align: left;
            width: 100%;
            display: block;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .cc-action-btn:hover {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            color: white;
            border-color: #4F46E5;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
        }

        /* Enhanced contact button hover effects */
        .cc-whatsapp-btn {
            background: linear-gradient(135deg, #25d366 0%, #128c7e 100%);
            color: white;
            border: 2px solid #25d366;
            border-radius: 12px;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin: 8px 4px;
            text-decoration: none;
            box-shadow: 0 4px 15px rgba(37, 211, 102, 0.2);
            position: relative;
            overflow: hidden;
            min-width: 180px;
        }

        .cc-whatsapp-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }

        .cc-whatsapp-btn:hover::before {
            left: 100%;
        }

        .cc-whatsapp-btn:hover {
            background: linear-gradient(135deg, #128c7e 0%, #075e54 100%);
            border-color: #128c7e;
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 8px 25px rgba(37, 211, 102, 0.4);
        }

        .cc-whatsapp-btn:active {
            transform: translateY(-1px) scale(0.98);
            box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3);
        }

        .cc-email-btn {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 8px;
            text-decoration: none;
        }

        .cc-email-btn:hover {
            background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
        }

        .cc-phone-btn {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 8px;
            text-decoration: none;
        }

        .cc-phone-btn:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }

        /* Google Maps button styling */
        .cc-maps-btn {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 10px 16px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 8px;
            text-decoration: none;
        }

        .cc-maps-btn:hover {
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        }

        /* Typing indicator with animation */
        .cc-typing-indicator {
            display: none;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            background: white;
            border-radius: 18px 18px 18px 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border: 1px solid #e5e7eb;
            margin-bottom: 15px;
            animation: fadeInUp 0.3s ease;
            width: fit-content;
        }

        .cc-typing-indicator.cc-show {
            display: flex;
        }

        .cc-typing {
            display: flex;
            gap: 4px;
            align-items: center;
        }

        .cc-typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #94a3b8;
            animation: typing 1.4s infinite ease-in-out;
        }

        .cc-typing-dot:nth-child(1) { animation-delay: 0s; }
        .cc-typing-dot:nth-child(2) { animation-delay: 024s; }
        .cc-typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
                opacity: 0.4;
            }
            30% {
                transform: translateY(-10px);
                opacity: 1;
            }
        }

        /* Animations */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Mobile responsiveness */
        @media (max-width: 768px) {
            #cc-chatbot-container {
                right: 10px;
                width: calc(100vw - 100px);
                height: calc(100vh - 40px);
            }

            #cc-toggle, #cc-close-btn {
                right: 10px;
            }
        }

        /* Enhanced Contact Card Styling */
        .cc-contact-card {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .cc-contact-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
        
        /* Contact card iframe styling */
        .cc-embedded-map {
            width: 100%;
            height: 200px;
            border: 0;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        /* Professional contact card layout */
        .cc-contact-card {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        .cc-contact-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .cc-contact-title {
            font-size: 18px;
            font-weight: 700;
            color: #1e293b;
            margin: 0;
        }
        
        .cc-contact-subtitle {
            font-size: 14px;
            color: #64748b;
            margin: 4px 0 0 0;
        }
        
        .cc-contact-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            margin-top: 16px;
        }
        
        .cc-contact-item {
            background: white;
            border-radius: 8px;
            border: 1px solid #f1f5f9;
            padding: 12px;
            transition: all 0.2s ease;
        }
        
        .cc-contact-item:hover {
            background: #f8fafc;
            border-color: #4F46E5;
            transform: translateX(4px);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
        }
        
        .cc-contact-item-icon {
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }
        
        .cc-contact-item-text {
            flex: 1;
            font-size: 14px;
            color: #374151;
            font-weight: 500;
        }
        
        /* Enhanced contact card styling */
        .cc-contact-card strong {
            color: #1e293b;
            font-weight: 700;
        }
        
        .cc-contact-card em {
            color: #64748b;
            font-style: normal;
            font-size: 13px;
        }
        
        /* Standardized button styling - Base button class */
        .cc-btn {
            display: inline-block;
            margin: 6px 8px 6px 0;
            padding: 12px 18px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border: none;
            cursor: pointer;
            text-align: center;
            min-width: 120px;
        }
        
        .cc-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        .cc-btn:active {
            transform: translateY(0);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }
        
        /* Contact button variants - inheriting from base .cc-btn */
        .cc-contact-btn {
            display: inline-block;
            margin: 6px 8px 6px 0;
            padding: 12px 18px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border: none;
            cursor: pointer;
            text-align: center;
            min-width: 120px;
        }
        
        .cc-contact-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        .cc-contact-btn:active {
            transform: translateY(0);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }
        
        /* WhatsApp button */
        .cc-whatsapp-btn {
            background: linear-gradient(135deg, #25d366, #128c7e);
            color: white;
            display: inline-block;
            margin: 6px 8px 6px 0;
            padding: 12px 18px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border: none;
            cursor: pointer;
            text-align: center;
            min-width: 120px;
        }
        
        .cc-whatsapp-btn:hover {
            background: linear-gradient(135deg, #128c7e, #075e54);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        .cc-whatsapp-btn:active {
            transform: translateY(0);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }
        
        /* Phone button */
        .cc-phone-btn {
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            display: inline-block;
            margin: 6px 8px 6px 0;
            padding: 12px 18px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border: none;
            cursor: pointer;
            text-align: center;
            min-width: 120px;
        }
        
        .cc-phone-btn:hover {
            background: linear-gradient(135deg, #20c997, #17a2b8);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        .cc-phone-btn:active {
            transform: translateY(0);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }
        
        /* Email button */
        .cc-email-btn {
            background: linear-gradient(135deg, #ff6b35, #f7931e);
            color: white;
            display: inline-block;
            margin: 6px 8px 6px 0;
            padding: 12px 18px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border: none;
            cursor: pointer;
            text-align: center;
            min-width: 120px;
        }
        
        .cc-email-btn:hover {
            background: linear-gradient(135deg, #f7931e, #fd7e14);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        .cc-email-btn:active {
            transform: translateY(0);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }
        
        /* Maps button */
        .cc-maps-btn {
            background: linear-gradient(135deg, #6f42c1, #5a32a3);
            color: white;
            display: inline-block;
            margin: 6px 8px 6px 0;
            padding: 12px 18px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border: none;
            cursor: pointer;
            text-align: center;
            min-width: 120px;
        }
        
        .cc-maps-btn:hover {
            background: linear-gradient(135deg, #5a32a3, #4c2a85);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        .cc-maps-btn:active {
            transform: translateY(0);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }
        
        /* Contact grid layout */
        .cc-contact-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin: 16px 0;
        }
        
        .cc-contact-grid-item {
            background: rgba(255, 255, 255, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
            backdrop-filter: blur(5px);
        }
        
        .cc-contact-grid-item:hover {
            background: rgba(255, 255, 255, 0.9);
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
        
        .cc-contact-icon-large {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 12px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
        }
        
        /* Responsive contact layout */
        @media (max-width: 480px) {
            .cc-contact-grid {
                grid-template-columns: 1fr;
                gap: 12px;
            }
            
            .cc-contact-btn {
                display: block;
                margin: 8px 0;
                text-align: center;
            }
        }

        .cc-contact-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid #e2e8f0;
        }

        .cc-contact-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 20px;
        }

        .cc-contact-title {
            font-size: 16px;
            font-weight: 600;
            color: #1e293b;
            margin: 0;
        }

        .cc-contact-info {
            display: grid;
            gap: 12px;
        }

        .cc-contact-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 12px;
            background: white;
            border-radius: 8px;
            border: 1px solid #f1f5f9;
            transition: all 0.2s ease;
            }

        .cc-contact-item:hover {
            background: #f8fafc;
            border-color: #4F46E5;
            transform: translateX(4px);
        }

        .cc-contact-item-icon {
            width: 24px;
            height: 24px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            flex-shrink: 0;
        }

        .cc-contact-item-text {
            flex: 1;
            font-size: 14px;
            color: #374151;
            font-weight: 500;
        }

        .cc-hours-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 12px;
        }

        .cc-hours-item {
            display: flex;
            justify-content: space-between;
            padding: 6px 8px;
            background: white;
            border-radius: 6px;
            font-size: 12px;
        }

        .cc-hours-day {
            font-weight: 600;
            color: #1e293b;
        }

        .cc-hours-time {
            color: #64748b;
        }

        /* PROBLEM 6 FIX: Loan calculator DISABLED - Hidden completely */
        .cc-loan-calculator {
            display: none !important; /* Calculator completely disabled */
        }

        .cc-loan-header {
            text-align: center;
            margin-bottom: 20px;
        }

        .cc-loan-title {
            font-size: 18px;
            font-weight: 700;
            color: #0c4a6e;
            margin: 0 0 8px 0;
        }

        .cc-loan-subtitle {
            font-size: 14px;
            color: #0369a1;
            margin: 0;
        }

        .cc-loan-form {
            display: grid;
            gap: 16px;
        }

        .cc-form-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .cc-form-label {
            font-size: 13px;
            font-weight: 600;
            color: #0c4a6e;
        }

        .cc-form-input {
            padding: 12px;
            border: 2px solid #bae6fd;
            border-radius: 8px;
            font-size: 14px;
            background: white;
            transition: border-color 0.2s ease;
        }

        .cc-form-input:focus {
            border-color: #0ea5e9;
            outline: none;
            box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
        }

        .cc-form-select {
            padding: 12px;
            border: 2px solid #bae6fd;
            border-radius: 8px;
            font-size: 14px;
            background: white;
            cursor: pointer;
        }

        .cc-calculate-btn {
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
            color: white;
            border: none;
            padding: 14px 24px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-top: 8px;
        }

        .cc-calculate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(14, 165, 233, 0.3);
        }

        .cc-loan-result {
            background: white;
            border: 2px solid #10b981;
            border-radius: 12px;
            padding: 16px;
            margin-top: 16px;
            text-align: center;
        }

        .cc-result-amount {
            font-size: 24px;
            font-weight: 700;
            color: #059669;
            margin-bottom: 8px;
        }

        .cc-result-details {
            font-size: 14px;
            color: #374151;
            line-height: 1.5;
        }

        /* Trend Arrow Indicators */
        .trend-arrow {
            width: 20px;
            height: 20px;
            vertical-align: middle;
            margin-right: 5px;
            display: inline-block;
        }

        /* Trend indicator styles */
        .trend-down {
            color: #10b981;
            font-weight: 600;
            font-size: 16px;
        }

        .trend-up {
            color: #ef4444;
            font-weight: 600;
            font-size: 16px;
        }

        .trend-none {
            color: #6b7280;
            font-weight: 600;
            font-size: 16px;
        }

        /* COE Data Formatting */
        // .coe-data-container {
        //     background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        //     border: 2px solid #e2e8f0;
        //     border-radius: 12px;
        //     padding: 16px;
        //     margin: 12px 0;
        //     box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        // }

        // .coe-header {
        //     background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        //     color: white;
        //     padding: 12px 16px;
        //     border-radius: 8px;
        //     margin-bottom: 16px;
        //     text-align: center;
        //     font-size: 16px;
        // }



        /* Chart container styling for responsive charts */
        .chart-container {
            margin: 12px auto;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            background: white;
            border: 1px solid #e5e7eb;
        }

        .chart-container:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
            border-color: #4F46E5;
        }

        .chart-container img {
            display: block;
            width: 100%;
            height: auto;
            transition: opacity 0.2s ease;
        }

        .chart-container:hover img {
            opacity: 0.95;
        }

        /* Chart enlargement hint styling */
        .chart-container .chart-enlarge-hint {
            background: linear-gradient(135deg, rgba(79, 70, 229, 0.9), rgba(124, 58, 237, 0.9));
            backdrop-filter: blur(4px);
        }

        /* Chart enlargement overlay styling */
        .chart-enlarge-overlay {
            transition: all 0.2s ease;
        }

        .chart-enlarge-overlay:hover {
            background: rgba(0,0,0,0.9) !important;
            font-weight: 600;
        }
    `;



    // Inject CSS
    function injectCSS() {
        if (document.getElementById('cc-widget-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'cc-widget-styles';
        style.textContent = WIDGET_CSS;
        document.head.appendChild(style);
    }

    // Create widget HTML - Updated layout with user's logo
    function createWidget() {
        const widgetHTML = `
            <!-- Toggle Button -->
            <button id="${CONFIG.TOGGLE_ID}" aria-label="Open chat">
                <img src="${CHATBOT_LOGO_URL}" alt="CleverCompanion" />
            </button>

            <!-- Close Button -->
            <button id="${CONFIG.CLOSE_ID}" aria-label="Close chat">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>

            <!-- Chat Container -->
            <div id="${CONFIG.WIDGET_ID}" role="dialog" aria-labelledby="cc-title" aria-describedby="cc-subtitle">
                <div class="cc-header">
                    <h3 id="cc-title">
                        <span class="cc-logo">
                            <img src="${CHATBOT_LOGO_URL}" alt="CleverCompanion" />
                        </span>
                        ${currentConfig.title}
                    </h3>
                    <p id="cc-subtitle">${currentConfig.subtitle}</p>
                    <button id="cc-clear-cache-btn" class="cc-clear-cache-btn" aria-label="Clear chat history" title="Clear chat history">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 6h18"></path>
                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
                
                <div id="${CONFIG.MESSAGES_ID}" role="log" aria-live="polite" aria-label="Chat messages">
                    <div class="cc-message cc-bot">
                        <div class="cc-avatar cc-bot">
                            <img src="${CHATBOT_LOGO_URL}" alt="Bot" />
                        </div>
                        <div class="cc-bubble">
                            ${currentConfig.welcomeMessage}
                            <div class="cc-timestamp">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true })}</div>
                        </div>
                    </div>
                </div>
                
                <div class="cc-input-area">
                    <!-- Menu Button - LEFT of input container -->
                    <button id="${CONFIG.MENU_BTN_ID}" aria-label="Menu">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="3" y1="12" x2="21" y2="12"></line>
                            <line x1="3" y1="6" x2="21" y2="6"></line>
                            <line x1="3" y1="18" x2="21" y2="18"></line>
                        </svg>
                    </button>
                    
                    <div class="cc-input-container">
                        <textarea 
                            id="${CONFIG.INPUT_ID}" 
                            name="chatInput"
                            placeholder="Type your message..." 
                            rows="1"
                            aria-label="Type your message"
                            autocomplete="off"
                        ></textarea>
                        <button id="${CONFIG.SEND_BTN_ID}" aria-label="Send message">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="22" y1="2" x2="11" y2="13"></line>
                                <polygon points="22,2 15,22 11,13 2,9 22,2"></polygon>
                            </svg>
                        </button>
                    </div>
                    
                    <!-- Menu Dropdown -->
                    <div class="cc-menu-dropdown" id="cc-menu-dropdown">
                        ${MENU_OPTIONS.map(option => 
                            `<div class="cc-menu-item" data-action="${option.action}">
                                <span>${option.icon}</span>
                                <span>${option.text}</span>
                            </div>`
                        ).join('')}
                    </div>
                </div>
            </div>

            <!-- Feedback Modal -->
            <div class="cc-feedback-modal" id="cc-feedback-modal">
                <div class="cc-feedback-content">
                    <div class="cc-feedback-header">
                        <h3>📝 Share Your Feedback</h3>
                        <p>Help us improve your experience</p>
                    </div>
                    
                    <div class="cc-rating-section">
                        <label class="cc-rating-label">How would you rate our service?</label>
                        <div class="cc-star-rating" id="cc-star-rating">
                            <span class="cc-star" data-rating="1">⭐</span>
                            <span class="cc-star" data-rating="2">⭐</span>
                            <span class="cc-star" data-rating="3">⭐</span>
                            <span class="cc-star" data-rating="4">⭐</span>
                            <span class="cc-star" data-rating="5">⭐</span>
                        </div>
                    </div>
                    
                    <div class="cc-rating-section">
                        <label class="cc-rating-label" for="cc-feedback-text">Tell us more about your experience:</label>
                        <textarea 
                            id="cc-feedback-text" 
                            class="cc-feedback-textarea" 
                            placeholder="Share your thoughts, suggestions, or any issues you encountered..."
                            maxlength="500"
                        ></textarea>
                    </div>
                    
                    <div class="cc-feedback-buttons">
                        <button class="cc-feedback-btn cc-secondary" id="cc-feedback-cancel">Cancel</button>
                        <button class="cc-feedback-btn cc-primary" id="cc-feedback-submit">Submit Feedback</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', widgetHTML);
    }

    // Initialize widget
    function initWidget() {
        injectCSS();
        createWidget();
        attachEventListeners();
        // Load chat history after widget is created
        setTimeout(() => {
            loadChatHistory();
        }, 100);
    }

    // Event listeners
    // Feedback modal functions
    function showFeedbackModal() {
        const modal = document.getElementById('cc-feedback-modal');
        if (modal) {
            modal.classList.add('cc-show');
            // Reset form
            resetFeedbackForm();
        }
    }

    function hideFeedbackModal() {
        const modal = document.getElementById('cc-feedback-modal');
        if (modal) {
            modal.classList.remove('cc-show');
        }
    }

    function resetFeedbackForm() {
        // Reset star rating
        const stars = document.querySelectorAll('.cc-star');
        stars.forEach(star => star.classList.remove('cc-active'));
        
        // Reset textarea
        const textarea = document.getElementById('cc-feedback-text');
        if (textarea) {
            textarea.value = '';
        }
    }

    function attachFeedbackListeners() {
        const modal = document.getElementById('cc-feedback-modal');
        const cancelBtn = document.getElementById('cc-feedback-cancel');
        const submitBtn = document.getElementById('cc-feedback-submit');
        const stars = document.querySelectorAll('.cc-star');
        
        // Close modal when clicking outside
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    hideFeedbackModal();
                }
            });
        }
        
        // Cancel button
        if (cancelBtn) {
            cancelBtn.addEventListener('click', hideFeedbackModal);
        }
        
        // Star rating
        stars.forEach(star => {
            star.addEventListener('click', (e) => {
                const rating = parseInt(e.target.dataset.rating);
                updateStarRating(rating);
            });
            
            star.addEventListener('mouseover', (e) => {
                const rating = parseInt(e.target.dataset.rating);
                highlightStars(rating);
            });
        });
        
        // Reset star highlighting on mouse leave
        const starContainer = document.getElementById('cc-star-rating');
        if (starContainer) {
            starContainer.addEventListener('mouseleave', () => {
                const activeStars = document.querySelectorAll('.cc-star.cc-active');
                const activeRating = activeStars.length;
                highlightStars(activeRating);
            });
        }
        
        // Submit feedback
        if (submitBtn) {
            submitBtn.addEventListener('click', submitFeedback);
        }
    }

    function updateStarRating(rating) {
        const stars = document.querySelectorAll('.cc-star');
        stars.forEach((star, index) => {
            if (index < rating) {
                star.classList.add('cc-active');
            } else {
                star.classList.remove('cc-active');
            }
        });
    }

    function highlightStars(rating) {
        const stars = document.querySelectorAll('.cc-star');
        stars.forEach((star, index) => {
            if (index < rating) {
                star.style.color = '#fbbf24';
            } else {
                star.style.color = '#d1d5db';
            }
        });
    }

    async function submitFeedback() {
        const stars = document.querySelectorAll('.cc-star.cc-active');
        const rating = stars.length;
        const textarea = document.getElementById('cc-feedback-text');
        const feedback = textarea ? textarea.value.trim() : '';
        
        if (rating === 0) {
            alert('Please provide a rating before submitting.');
            return;
        }
        
        const submitBtn = document.getElementById('cc-feedback-submit');
        if (submitBtn) {
            submitBtn.textContent = 'Submitting...';
            submitBtn.disabled = true;
        }
        
        try {
            // Submit feedback to API
            const response = await fetch('http://localhost:8001/api/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    rating: rating,
                    feedback: feedback,
                    timestamp: new Date().toISOString(),
                    widget_id: 'automotive-chatbot'
                })
            });
            
            if (response.ok) {
                // Show success message in chat
                addMessage('Thank you for your feedback! Your input helps us improve our service. 🙏', 'bot');
                hideFeedbackModal();
            } else {
                throw new Error('Failed to submit feedback');
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
            // Show feedback in chat even if API fails
            addMessage('Thank you for your feedback! We appreciate your input. 🙏', 'bot');
            hideFeedbackModal();
        } finally {
            if (submitBtn) {
                submitBtn.textContent = 'Submit Feedback';
                submitBtn.disabled = false;
            }
        }
    }

    function attachEventListeners() {
        const toggle = document.getElementById(CONFIG.TOGGLE_ID);
        const closeBtn = document.getElementById(CONFIG.CLOSE_ID);
        const widget = document.getElementById(CONFIG.WIDGET_ID);
        const input = document.getElementById(CONFIG.INPUT_ID);
        const sendBtn = document.getElementById(CONFIG.SEND_BTN_ID);
        const menuBtn = document.getElementById(CONFIG.MENU_BTN_ID);
        const menuDropdown = document.getElementById('cc-menu-dropdown');
        const clearCacheBtn = document.getElementById('cc-clear-cache-btn');

        if (toggle) {
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation(); // Stop all event propagation
                toggleWidget();
            });

        // Feedback modal event listeners
        attachFeedbackListeners();
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation(); // Stop all event propagation
                closeWidget();
            });
        }

        if (input) {
            input.addEventListener('keypress', handleKeyPress);
            // PROBLEM 1 FIX: Remove autoResize completely - keep fixed height always
            // input.addEventListener('input', autoResize);
        }

        if (sendBtn) {
            sendBtn.addEventListener('click', () => {
                const message = input.value.trim();
                if (message) {
                    sendMessage(message);
                    resetTextareaSize(); // PROBLEM 2 FIX: Reset size after sending via button click
                }
            });
        }

        if (menuBtn && menuDropdown) {
            menuBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                menuDropdown.classList.toggle('cc-show');
            });

            // Menu item clicks
            menuDropdown.addEventListener('click', (e) => {
                const menuItem = e.target.closest('.cc-menu-item');
                if (menuItem) {
                    const action = menuItem.dataset.action;
                    
                    // Handle special actions
                    if (action.includes('feedback') || action.includes('Feedback')) {
                        showFeedbackModal();
                    } else {
                        sendMessage(action);
                    }
                    
                    menuDropdown.classList.remove('cc-show');
                }
            });
        }

        // Clear cache button
        if (clearCacheBtn) {
            clearCacheBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                clearCacheAndSession();
            });
        }

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (menuDropdown && !menuBtn.contains(e.target) && !menuDropdown.contains(e.target)) {
                menuDropdown.classList.remove('cc-show');
            }
        });

        // PROBLEM 3 FIX: Handle action button clicks without double processing
        document.addEventListener('click', (e) => {
            // Explicitly exclude close and toggle buttons and their children
            if (e.target.id === CONFIG.CLOSE_ID || e.target.id === CONFIG.TOGGLE_ID ||
                e.target.closest(`#${CONFIG.CLOSE_ID}`) || e.target.closest(`#${CONFIG.TOGGLE_ID}`)) {
                return;
            }
            
            // Handle contact buttons (WhatsApp, Phone, Email, Maps)
            if (e.target.classList.contains('cc-whatsapp-btn') || 
                e.target.classList.contains('cc-phone-btn') || 
                e.target.classList.contains('cc-email-btn') || 
                e.target.classList.contains('cc-maps-btn') ||
                e.target.classList.contains('cc-contact-btn')) {
                
                // Let the browser handle these links naturally (href attributes)
                // No need to prevent default or stop propagation for contact buttons
                return;
            }
            
            // Only handle clicks on actual action buttons with very specific validation
            if (e.target.classList.contains('cc-action-btn') && 
                e.target.closest('#cc-chatbot-container') &&
                e.target.closest('.cc-action-buttons')) {  // Must be inside action buttons container
                
                // Extra validation to ensure this is really an action button
                const chatContainer = document.getElementById(CONFIG.WIDGET_ID);
                const actionButtonsContainer = e.target.closest('.cc-action-buttons');
                
                if (!chatContainer || !chatContainer.contains(e.target) || !actionButtonsContainer) {
                    return;
                }
                
                e.preventDefault();
                e.stopPropagation();
                
                if (isProcessing) return;
                
                const action = e.target.textContent.trim();
                if (action && action.length > 2) {  // Ensure it's a valid action text
                    handleActionButton(action);
                }
            }
        });
    }

    function toggleWidget() {
        const widget = document.getElementById(CONFIG.WIDGET_ID);
        const toggle = document.getElementById(CONFIG.TOGGLE_ID);
        const closeBtn = document.getElementById(CONFIG.CLOSE_ID);
        
        if (widget && toggle && closeBtn) {
            if (widget.classList.contains('cc-open')) {
                closeWidget();
            } else {
                openWidget();
            }
        }
    }

    function openWidget() {
        const widget = document.getElementById(CONFIG.WIDGET_ID);
        const toggle = document.getElementById(CONFIG.TOGGLE_ID);
        const closeBtn = document.getElementById(CONFIG.CLOSE_ID);
        
        if (widget && toggle && closeBtn) {
            widget.classList.add('cc-open');
            toggle.style.display = 'none';
            closeBtn.classList.add('cc-visible');
            
            // Focus input
            setTimeout(() => {
                const input = document.getElementById(CONFIG.INPUT_ID);
                if (input) input.focus();
            }, 300);
        }
    }

    function closeWidget() {
        const widget = document.getElementById(CONFIG.WIDGET_ID);
        const toggle = document.getElementById(CONFIG.TOGGLE_ID);
        const closeBtn = document.getElementById(CONFIG.CLOSE_ID);
        
        if (widget && toggle && closeBtn) {
            widget.classList.remove('cc-open');
            toggle.style.display = 'flex';
            closeBtn.classList.remove('cc-visible');
        }
    }

    function handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const input = document.getElementById(CONFIG.INPUT_ID);
            if (input) {
                const message = input.value.trim();
                if (message) {
                    sendMessage(message);
                    resetTextareaSize(); // PROBLEM 2 FIX: Reset size after sending via Enter key
                }
            }
        }
    }

    function autoResize() {
        const input = document.getElementById(CONFIG.INPUT_ID);
        if (input) {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 100) + 'px';
        }
    }

    function resetTextareaSize() {
        const input = document.getElementById(CONFIG.INPUT_ID);
        if (input) {
            input.style.height = 'auto';
            input.style.height = '40px'; // Reset to original single-line size
        }
    }

    // Session expiry time in milliseconds (30 minutes to match backend)
    const SESSION_EXPIRY_TIME = 30 * 60 * 1000; // 30 minutes

    // Check if session has expired
    function isSessionExpired() {
        const sessionTimestamp = localStorage.getItem('cc_session_timestamp');
        if (!sessionTimestamp) return true;
        
        const now = Date.now();
        const sessionTime = parseInt(sessionTimestamp);
        return (now - sessionTime) > SESSION_EXPIRY_TIME;
    }

    // Clear expired session data
    function clearExpiredSession() {
        localStorage.removeItem('cc_session_id');
        localStorage.removeItem('cc_session_timestamp');
        localStorage.removeItem('cc_chat_history');
    }

    // Generate or retrieve session ID - using localStorage for persistence
    function getSessionId() {
        // Check if session has expired
        if (isSessionExpired()) {
            clearExpiredSession();
        }
        
        let sessionId = localStorage.getItem('cc_session_id');
        if (!sessionId) {
            sessionId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            localStorage.setItem('cc_session_id', sessionId);
            localStorage.setItem('cc_session_timestamp', Date.now().toString());
        }
        return sessionId;
    }

    // Save chat history to localStorage with session validation
    function saveChatHistory() {
        // Check if session has expired before saving
        if (isSessionExpired()) {
            clearExpiredSession();
            return;
        }
        
        const messagesContainer = document.getElementById(CONFIG.MESSAGES_ID);
        if (!messagesContainer) return;
        
        const messages = [];
        const messageElements = messagesContainer.querySelectorAll('.cc-message');
        
        messageElements.forEach(messageEl => {
            const isUser = messageEl.classList.contains('cc-user');
            const bubble = messageEl.querySelector('.cc-bubble');
            if (bubble) {
                // Get text content without timestamp
                const timestamp = bubble.querySelector('.cc-timestamp');
                const actionButtons = bubble.querySelector('.cc-action-buttons');
                
                // Clone bubble to extract clean text
                const bubbleClone = bubble.cloneNode(true);
                const clonedTimestamp = bubbleClone.querySelector('.cc-timestamp');
                const clonedActionButtons = bubbleClone.querySelector('.cc-action-buttons');
                
                if (clonedTimestamp && clonedTimestamp.parentNode) {
                    clonedTimestamp.parentNode.removeChild(clonedTimestamp);
                }
                if (clonedActionButtons && clonedActionButtons.parentNode) {
                    clonedActionButtons.parentNode.removeChild(clonedActionButtons);
                }
                
                messages.push({
                    text: bubbleClone.innerHTML.trim(),
                    sender: isUser ? 'user' : 'bot',
                    timestamp: timestamp ? timestamp.textContent : new Date().toLocaleTimeString([], { 
                        hour: '2-digit', 
                        minute: '2-digit',
                        hour12: true 
                    })
                });
            }
        });
        
        localStorage.setItem('cc_chat_history', JSON.stringify(messages));
        // Update session timestamp on activity
        localStorage.setItem('cc_session_timestamp', Date.now().toString());
    }

    // Load chat history from localStorage with session validation
    function loadChatHistory() {
        // Check if session has expired before loading
        if (isSessionExpired()) {
            clearExpiredSession();
            return;
        }
        
        const savedHistory = localStorage.getItem('cc_chat_history');
        if (!savedHistory) return;
        
        try {
            const messages = JSON.parse(savedHistory);
            const messagesContainer = document.getElementById(CONFIG.MESSAGES_ID);
            if (!messagesContainer) return;
            
            // Clear existing messages
            messagesContainer.innerHTML = '';
            
            // Restore messages
            messages.forEach(message => {
                const avatar = message.sender === 'bot' ? `<img src="${CHATBOT_LOGO_URL}" alt="Bot" />` : USER_AVATAR;
                const actionButtons = extractActionButtons(message.text);
                
                const messageHTML = `
                    <div class="cc-message cc-${message.sender}">
                        <div class="cc-avatar cc-${message.sender}">${avatar}</div>
                        <div class="cc-bubble">
                            ${message.text}
                            ${actionButtons}
                            <div class="cc-timestamp">${message.timestamp}</div>
                        </div>
                    </div>
                `;
                
                messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
            });
            
            // Scroll to bottom after loading
            setTimeout(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }, 100);
            
        } catch (error) {
            console.error('Error loading chat history:', error);
            // Clear corrupted data
            localStorage.removeItem('cc_chat_history');
        }
    }

    // Clear chat history and session data
    function clearChatHistory() {
        localStorage.removeItem('cc_chat_history');
        localStorage.removeItem('cc_session_id');
        localStorage.removeItem('cc_session_timestamp');
        const messagesContainer = document.getElementById(CONFIG.MESSAGES_ID);
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
    }

    // Clear cache and session data (frontend + backend)
    async function clearCacheAndSession() {
        try {
            // Clear frontend cache and session
            clearChatHistory();
            
            // Call backend cleanup endpoint
            const response = await fetch('http://localhost:8001/api/conversations/cleanup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                console.log('Backend sessions cleared successfully');
            } else {
                console.warn('Backend cleanup failed, but frontend cache cleared');
            }
            
            // Add welcome message back
            const messagesContainer = document.getElementById(CONFIG.MESSAGES_ID);
            if (messagesContainer) {
                const welcomeHTML = `
                    <div class="cc-message cc-bot">
                        <div class="cc-avatar cc-bot">
                            <img src="${CHATBOT_LOGO_URL}" alt="Bot" />
                        </div>
                        <div class="cc-bubble">
                            ${currentConfig.welcomeMessage}
                            <div class="cc-timestamp">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true })}</div>
                        </div>
                    </div>
                `;
                messagesContainer.innerHTML = welcomeHTML;
            }
            
            // Show confirmation message
            setTimeout(() => {
                addMessage('✅ Chat history and session data have been cleared successfully!', 'bot');
            }, 500);
            
        } catch (error) {
            console.error('Error clearing cache and session:', error);
            // Still show success for frontend clearing
            setTimeout(() => {
                addMessage('✅ Chat history has been cleared! (Note: Backend cleanup may have failed)', 'bot');
            }, 500);
        }
    }

    async function sendMessage(text) {
        const input = document.getElementById(CONFIG.INPUT_ID);
        const sendBtn = document.getElementById(CONFIG.SEND_BTN_ID);
        
        if (!text.trim()) return;

        // Add user message
        addMessage(text, 'user');
        
        // Clear input, reset size, and disable send button
        if (input) {
            input.value = '';
            resetTextareaSize(); // PROBLEM 2 FIX: Reset to original size immediately
        }
        if (sendBtn) sendBtn.disabled = true;
        
        // Show typing indicator
        showTypingIndicator();

        try {
            // PROBLEM 8 FIX: Enhanced fetch with timeout and better error handling
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout for better reliability
            
            const response = await fetch(CONFIG.API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    sender: getSessionId(),
                    message: text
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                const data = await response.json();
                
                // Handle RASA direct response format (array of message objects)
                if (Array.isArray(data) && data.length > 0) {
                    // Process each RASA response item
                    data.forEach(item => {
                        if (item.text) {
                            // Check if this item has buttons
                            if (item.buttons && Array.isArray(item.buttons)) {
                                addMessageWithButtons(item.text, 'bot', item.buttons);
                            } else {
                                addMessage(item.text, 'bot');
                            }
                        }
                    });
                    
                    // If no messages were processed, show fallback
                    if (!data.some(item => item.text)) {
                        addMessage('I understand your message, but I\'m not sure how to respond right now.', 'bot');
                    }
                } else if (data && data.success && data.bot_responses && data.bot_responses.length > 0) {
                    // Handle wrapped backend API response format (fallback)
                    const combinedText = data.bot_responses.join('\n\n');
                    
                    if (combinedText) {
                        addMessage(combinedText, 'bot');
                    } else {
                        addMessage('I understand your message, but I\'m not sure how to respond right now.', 'bot');
                    }
                } else {
                    addMessage('I apologize, but I\'m having trouble understanding your request. Could you please try rephrasing?', 'bot');
                }
            } else {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        } catch (error) {
            // Enhanced error handling for better user experience
            
            if (error.name === 'AbortError') {
                addMessage('⏱️ **Request Timeout**\n\nThe request took longer than expected. This might be due to:\n\n• Heavy server load\n• Network connectivity issues\n• Complex query processing\n\nPlease try again with a simpler question or check your internet connection.', 'bot');
            } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError') || error.message.includes('ERR_ABORTED')) {
                addMessage('🔌 **Connection Issue**\n\nUnable to connect to our chat service. Please:\n\n• Check your internet connection\n• Refresh the page and try again\n• Contact support if the issue persists\n\n📞 **Support:** +6562345678\n📧 **Email:** info@clevercompanion.sg', 'bot');
            } else if (error.message.includes('HTTP error')) {
                addMessage('⚠️ **Server Error**\n\nOur server encountered an issue. Please try again in a few moments.\n\nIf the problem continues, please contact our support team.', 'bot');
            } else {
                addMessage('🔧 **Technical Issue**\n\nI\'m experiencing technical difficulties. Please try again in a moment.\n\nIf this continues, please contact support for assistance.', 'bot');
            }
        } finally {
            hideTypingIndicator();
            if (sendBtn) sendBtn.disabled = false;
            resetTextareaSize(); // PROBLEM 2 FIX: Ensure textarea stays at original size
        }
    }

    function addMessage(text, sender) {
        const messagesContainer = document.getElementById(CONFIG.MESSAGES_ID);
        if (!messagesContainer) return;

        // Add all messages immediately (typing animation removed)
        addMessageInstant(text, sender);
    }

    function addMessageWithButtons(text, sender, buttons) {
        const messagesContainer = document.getElementById(CONFIG.MESSAGES_ID);
        if (!messagesContainer) return;

        // Add message with RASA buttons
        addMessageInstantWithButtons(text, sender, buttons);
    }

    function addMessageInstant(text, sender) {
        const messagesContainer = document.getElementById(CONFIG.MESSAGES_ID);
        if (!messagesContainer) return;

        const avatar = sender === 'bot' ? `<img src="${CHATBOT_LOGO_URL}" alt="Bot" />` : USER_AVATAR;
        const timestamp = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: true 
        });

        const formattedText = formatMessage(text);
        const actionButtons = extractActionButtons(text);

        const messageHTML = `
            <div class="cc-message cc-${sender}">
                <div class="cc-avatar cc-${sender}">${avatar}</div>
                <div class="cc-bubble">
                    ${formattedText}
                    ${actionButtons}
                    <div class="cc-timestamp">${timestamp}</div>
                </div>
            </div>
        `;

        messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        
        // Save chat history after adding message
        saveChatHistory();
        
        if (sender === 'bot') {
            setTimeout(() => {
                scrollToLatestBotMessage();
            });
        } else {
            scrollToBottom();
        }
    }

    function addMessageInstantWithButtons(text, sender, buttons) {
        const messagesContainer = document.getElementById(CONFIG.MESSAGES_ID);
        if (!messagesContainer) return;

        const avatar = sender === 'bot' ? `<img src="${CHATBOT_LOGO_URL}" alt="Bot" />` : USER_AVATAR;
        const timestamp = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: true 
        });

        const formattedText = formatMessage(text);
        
        // Generate RASA button HTML
        let buttonHTML = '';
        if (buttons && buttons.length > 0) {
            buttonHTML = '<div class="cc-action-buttons">';
            buttons.forEach(button => {
                if (button.title && button.payload) {
                    buttonHTML += `<button class="cc-action-btn" onclick="sendButtonPayload('${button.payload}')">${button.title}</button>`;
                }
            });
            buttonHTML += '</div>';
        }

        const messageHTML = `
            <div class="cc-message cc-${sender}">
                <div class="cc-avatar cc-${sender}">${avatar}</div>
                <div class="cc-bubble">
                    ${formattedText}
                    ${buttonHTML}
                    <div class="cc-timestamp">${timestamp}</div>
                </div>
            </div>
        `;

        messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        
        // Save chat history after adding message
        saveChatHistory();
        
        if (sender === 'bot') {
            setTimeout(() => {
                scrollToLatestBotMessage();
            });
        } else {
            scrollToBottom();
        }
    }

    // Function to handle RASA button clicks
    function sendButtonPayload(payload) {
        // Send the button payload as a user message
        sendMessage(payload);
    }

    // Typing animation functions removed - messages now display instantly

    // function getArrowIndicator(type) {
    //     // Use simple text arrows as fallback since PNG creation failed
    //     const arrows = {
    //         up: '▲',
    //         down: '▼', 
    //         none: '►'
    //     };
    //     return arrows[type] || '';
    // }

    function formatCOEData(text) {
        // Format COE data with proper structure and styling
        let formattedText = text;
        
        // Base64 data for arrow indicators
        const upRedArrow = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAAaElEQVR4nO3UsQnAMAxE0dOtkN5NCu0/jgvPopAiYAJBMjlIkz/A4xrJIgLKKNXwJTjcQwYO99haK6GEOFbXnVVWUjguB+d1V9lKrmAVlBDH1XXZSkKc3Z9D9SLm9t7tEXwbpRp+EIIOicknsvBiWSkAAAAASUVORK5CYII=';
        const downGreenArrow = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAAdElEQVR4nGP8//8/AzUBE1VNYxg1cFAayIIuwDY9i+R09CtzGiOMzYgtHYIM5VaWIGjQ17svUAyjXxj+ypzGCLKdVNfRN5Z/4XElLtcRdCE2Q/EZNjAJ+xeSKwm5jiYuZAAlbGIw67TM/8Sow5pTKAFU9zIAWrt0h9Oz/mYAAAAASUVORK5CYII=';
        const noChangeArrow = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAAfUlEQVR4nGP8//8/AzUBE1VNYxjyBvqEpfynugt9wlL+k2IwCyEFCrKycINB9JZVcxgpciGywSBMyLVMDCQCmAG4DGYh1UCYobiCgYkcA/EFAwslBj54/JgB3YUs1DKIbANBhuFLOiykGERMOmShlkFEG0isQQxQwDjyClgAnyI36oEWn70AAAAASUVORK5CYII=';
        
        // Protect chart HTML from text formatting - match complete chart structure
        // Pattern: 📊 **title** \n\n <div class="chart-container"> ... </div> \n\n _Generated by..._
        const fullChartRegex = /📊\s*\*\*[^*]+\*\*[\s\S]*?<div[^>]*class=["']chart-container["'][^>]*>[\s\S]*?<\/div>[\s\S]*?_Generated by CleverCompanion Analytics_/g;
        const simpleChartRegex = /<div[^>]*class=["']chart-container["'][^>]*>[\s\S]*?<\/div>/g;
        const imageChartRegex = /<img[^>]*src=["']data:image\/png;base64,[^"']*["'][^>]*>/g;
        const chartElements = [];
        let chartIndex = 0;
        

        
        // Try full chart pattern first, then fallback to simple, then image charts
        let chartMatches = formattedText.match(fullChartRegex);
        if (!chartMatches) {
            chartMatches = formattedText.match(simpleChartRegex);

        } else {

        }
        
        // Also check for standalone base64 image charts
        const imageMatches = formattedText.match(imageChartRegex);
        if (imageMatches && imageMatches.length > 0) {
            if (!chartMatches) chartMatches = [];
            chartMatches = chartMatches.concat(imageMatches);
        }
        
        // Replace chart elements with placeholders
        if (chartMatches) {
            chartMatches.forEach((match, index) => {

                chartElements.push(match);
                const placeholder = `__CHART_PLACEHOLDER_${chartIndex++}__`;
                formattedText = formattedText.replace(match, placeholder);
            });
        }
        

        
        // Create unique protection tokens that won't be affected by text formatting
        const protectionTokens = [];
        chartElements.forEach((_, index) => {
            const placeholder = `__CHART_PLACEHOLDER_${index}__`;
            const protectionToken = `ZZPROTECTEDCHARTZZZ${index}ZZPROTECTEDCHARTZZZ`;
            protectionTokens.push(protectionToken);
            formattedText = formattedText.replace(placeholder, protectionToken);
        });
        

        
        // Special handling for COE responses - remove massive indentation first
        formattedText = formattedText
            .replace(/\r\n/g, '\n')    // Normalize line endings
            .replace(/\r/g, '\n')
            .replace(/^[ \t]{30,}/gm, '')  // Remove massive indentation (30+ spaces) for COE
            .replace(/[ \t]{3,}/g, ' ')    // Replace multiple spaces with single space
            
            // Apply text formatting (but not to chart elements)
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/_([^_]+)_/g, '<em>$1</em>')
            .replace(/•/g, '&bull;')
            // DON'T remove dollar signs for COE data - keep prices intact
            // .replace(/\$([0-9,]+)/g, '$1')  // REMOVED - this was stripping $ from COE prices
            .replace(/(⬇️|⬆️|📈|📊|💰|🚗|🔧|📞|🚙|🚛|🏍️|🔄|📋|📅|💡)/g, '<span class="emoji-highlight">$1</span>')
            
            // Handle arrow tokens
            .replace(/ARROW<em>UP<\/em>RED/g, `<img src="${upRedArrow}" alt="↑" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            .replace(/ARROW<em>DOWN<\/em>GREEN/g, `<img src="${downGreenArrow}" alt="↓" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            .replace(/ARROW<em>NO<\/em>CHANGE/g, `<img src="${noChangeArrow}" alt="→" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            .replace(/<img\s+src="ARROW_UP_RED"[^>]*>/g, `<img src="${upRedArrow}" alt="↑" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            .replace(/<img\s+src="ARROW_DOWN_GREEN"[^>]*>/g, `<img src="${downGreenArrow}" alt="↓" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            .replace(/<img\s+src="ARROW_NO_CHANGE"[^>]*>/g, `<img src="${noChangeArrow}" alt="→" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            
            // Convert newlines to breaks
            .replace(/\n/g, '<br>')
            .replace(/\s*<br>\s*/g, '<br>')
            .replace(/<br><br><br>+/g, '<br><br>')
            .replace(/(🚗|🚙|🚚|🏍️|🔄|📋|📅|💡|📊)\s*<br>/g, '$1<br>');
        
        // Restore chart elements using protection tokens
        chartElements.forEach((chartElement, index) => {
            const protectionToken = `ZZPROTECTEDCHARTZZZ${index}ZZPROTECTEDCHARTZZZ`;
            if (formattedText.includes(protectionToken)) {
                formattedText = formattedText.replace(protectionToken, chartElement);

            }
        });
        

            
        return `<div class="coe-data-container">${formattedText}</div>`;
    }



    function formatMessage(text) {
    // Check if this contains COE data first, regardless of chart presence
    if (text.includes('Latest COE Prices (Live Data)') || text.includes('Latest COE Prices') || 
        (text.includes('Category A:') && text.includes('Category B:') && text.includes('Category C:')) ||
        text.includes('INTELLIGENT COE FORECASTING SYSTEM') || text.includes('CATEGORY A ANALYSIS') ||
        (text.includes('CATEGORY A ANALYSIS') && text.includes('CATEGORY B ANALYSIS'))) {
        return formatCOEData(text);
    }
    
    // Check if this is ONLY chart HTML content (no COE text)
    if ((text.includes('<div class="chart-container"') || text.includes('enlargeChart()')) && 
        !text.includes('Category A:') && !text.includes('Latest COE Prices')) {
        // This is pure chart HTML - minimal processing
        return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    }
    
    // Check if this is a contact card response - preserve HTML structure
    // Enhanced detection for contact cards with multiple patterns
    if ((text.includes('CleverCompanion Support') || text.includes('🚗 CleverCompanion Support')) && 
        (text.includes('linear-gradient') || text.includes('<div style=')) && 
        (text.includes('WhatsApp') || text.includes('Phone') || text.includes('Email') || 
         text.includes('📞') || text.includes('📧') || text.includes('💬') || text.includes('📍'))) {
        // This is a contact card - return as-is to preserve styling
        return text;
    }
    
    // FIXED: Check for contact responses that already have HTML buttons - preserve them completely
    if ((text.includes('Thank you for contacting') || text.includes('Here\'s how to reach us') ||
         text.includes('Contact Information') || text.includes('Email Support') ||
         text.includes('Contact CleverCompanion') || text.includes('Choose your preferred way')) &&
        (text.includes('info@') || text.includes('+65') || text.includes('WhatsApp') ||
         text.includes('<button') || text.includes('<a href="tel:') || text.includes('<a href="mailto:'))) {
        // This is a contact response with existing buttons - minimal processing to preserve structure
        return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                  .replace(/\n/g, '<br>');
    }
        
        // Regular text formatting for non-chart content
        // First, protect image src attributes from italic formatting
        // BUT exclude trend arrow images which should be handled separately
        const imageTagRegex = /<img[^>]*src="(?!.*arrow-indicator)[^"]*"[^>]*>/g;
        const imageTags = [];
        let imageIndex = 0;
        
        // Replace image tags with placeholders (excluding trend arrows)
        let protectedText = text.replace(imageTagRegex, (match) => {
            imageTags.push(match);
            return `__IMAGE_PLACEHOLDER_${imageIndex++}__`;
        });
        
        let formattedText = protectedText
            .replace(/LOAN_CALCULATOR_START/g, '')
            .replace(/LOAN_CALCULATOR_END/g, '')
            .replace(/BUTTON_OPTIONS_START[\s\S]*?BUTTON_OPTIONS_END/g, '')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // .replace(/_([^_]+)_/g, '<em>$1</em>') // Apply italic formatting safely
            .replace(/•/g, '&bull;')
            // PROBLEM 1 FIX: Keep clean numbers without dollar signs and commas
            .replace(/\$([0-9,]+)/g, '$1')
            // Enhanced emoji highlighting to include more emojis
            .replace(/(⬇️|⬆️|📈|📊|💰|🚗|🔧|📞|🚙|🚛|🏍️|🔄|📋|📅|💡)/g, '<span class="emoji-highlight">$1</span>');
        
        // Restore image tags
        imageTags.forEach((imageTag, index) => {
            formattedText = formattedText.replace(`__IMAGE_PLACEHOLDER_${index}__`, imageTag);
        });
        
        // Base64 data for arrow indicators (same as in formatCOEData)
        const upRedArrow = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAAaElEQVR4nO3UsQnAMAxE0dOtkN5NCu0/jgvPopAiYAJBMjlIkz/A4xrJIgLKKNXwJTjcQwYO99haK6GEOFbXnVVWUjguB+d1V9lKrmAVlBDH1XXZSkKc3Z9D9SLm9t7tEXwbpRp+EIIOicknsvBiWSkAAAAASUVORK5CYII=';
        const downGreenArrow = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAAdElEQVR4nGP8//8/AzUBE1VNYxg1cFAayIIuwDY9i+R09CtzGiOMzYgtHYIM5VaWIGjQ17svUAyjXxj+ypzGCLKdVNfRN5Z/4XElLtcRdCE2Q/EZNjAJ+xeSKwm5jiYuZAAlbGIw67TM/8Sow5pTKAFU9zIAWrt0h9Oz/mYAAAAASUVORK5CYII=';
        const noChangeArrow = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAAfUlEQVR4nGP8//8/AzUBE1VNYxjyBvqEpfynugt9wlL+k2IwCyEFCrKycINB9JZVcxgpciGywSBMyLVMDCQCmAG4DGYh1UCYobiCgYkcA/EFAwslBj54/JgB3YUs1DKIbANBhuFLOiykGERMOmShlkFEG0isQQxQwDjyClgAnyI36oEWn70AAAAASUVORK5CYII=';
        
        // Handle arrow tokens - use base64 images
        formattedText = formattedText
            // Handle the exact format from terminal errors: ARROW<em>UP</em>RED
            .replace(/ARROW<em>UP<\/em>RED/g, `<img src="${upRedArrow}" alt="↑" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            .replace(/ARROW<em>DOWN<\/em>GREEN/g, `<img src="${downGreenArrow}" alt="↓" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            .replace(/ARROW<em>NO<\/em>CHANGE/g, `<img src="${noChangeArrow}" alt="→" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            // Handle URL-encoded versions that cause 404s
            .replace(/ARROW%3Cem%3EUP%3C\/em%3ERED/g, `<img src="${upRedArrow}" alt="↑" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            .replace(/ARROW%3Cem%3EDOWN%3C\/em%3EGREEN/g, `<img src="${downGreenArrow}" alt="↓" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            .replace(/ARROW%3Cem%3ENO%3C\/em%3ECHANGE/g, `<img src="${noChangeArrow}" alt="→" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            // Handle complete img tags with arrow tokens
            .replace(/<img\s+src="ARROW_UP_RED"[^>]*>/g, `<img src="${upRedArrow}" alt="↑" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            .replace(/<img\s+src="ARROW_DOWN_GREEN"[^>]*>/g, `<img src="${downGreenArrow}" alt="↓" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            .replace(/<img\s+src="ARROW_NO_CHANGE"[^>]*>/g, `<img src="${noChangeArrow}" alt="→" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            // Handle plain text tokens as fallback
            .replace(/\bARROW_UP_RED\b/g, `<img src="${upRedArrow}" alt="↑" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            .replace(/\bARROW_DOWN_GREEN\b/g, `<img src="${downGreenArrow}" alt="↓" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            .replace(/\bARROW_NO_CHANGE\b/g, `<img src="${noChangeArrow}" alt="→" class="trend-arrow" style="width:12px;height:12px;margin-left:4px;vertical-align:middle;">`)
            // Fix Google Maps to embedded map + button format
            .replace(/GOOGLE_MAPS:([^\s]+)/g, (match, url) => {
                // Use the original URL directly for embedding without API key requirement
                // Convert regular Google Maps URL to embeddable format
                let embedUrl;
                if (url.includes('maps.google.com')) {
                    // Convert to embed format by replacing /maps with /maps/embed
                    embedUrl = url.replace('/maps?', '/maps/embed?').replace('/maps/place/', '/maps/embed/v1/place?key=demo&q=');
                    // If it's a search URL, convert it properly
                    if (url.includes('?q=')) {
                        const searchQuery = url.split('?q=')[1].split('&')[0];
                        embedUrl = `https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3988.8177!2d103.8198!3d1.3521!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMcKwMjEnMDcuNiJOIDEwM8KwNDknMTEuMyJF!5e0!3m2!1sen!2ssg!4v1234567890123!5m2!1sen!2ssg&q=${encodeURIComponent(searchQuery)}`;
                    }
                } else {
                    // Fallback: create a basic embed URL for Singapore location
                    embedUrl = `https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3988.8177!2d103.8198!3d1.3521!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMcKwMjEnMDcuNiJOIDEwM8KwNDknMTEuMyJF!5e0!3m2!1sen!2ssg!4v1234567890123!5m2!1sen!2ssg&q=CleverCompanion+Auto+Showroom+Singapore`;
                }
                return `<div class="cc-map-container"><iframe src="${embedUrl}" class="cc-embedded-map" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div><a href="${url}" target="_blank" class="cc-maps-btn">📍 View on Google Maps</a>`;
            })
            // FIXED: Only format contact information if no HTML buttons already exist
            .replace(/WhatsApp:\s*\+65\s*([0-9\s]+)/g, (match, number) => {
                // Don't create duplicate if HTML button already exists
                if (formattedText.includes('<button') && formattedText.includes('WhatsApp')) {
                    return match; // Return original text
                }
                return `<a href="https://wa.me/65${number}" target="_blank" class="cc-contact-link cc-whatsapp-btn">📱 WhatsApp: +65 ${number}</a>`;
            })
            .replace(/Call:\s*\+65\s*([0-9\s]+)/g, (match, number) => {
                // Don't create duplicate if HTML button already exists
                if (formattedText.includes('<a href="tel:') || formattedText.includes('Call Now')) {
                    return match; // Return original text
                }
                return `<a href="tel:+65${number}" class="cc-contact-link cc-phone-btn">📞 Call: +65 ${number}</a>`;
            })
            .replace(/Email:\s*([^\s]+)/g, (match, email) => {
                // Don't create duplicate if HTML button already exists
                if (formattedText.includes('<a href="mailto:') || formattedText.includes('Send Email')) {
                    return match; // Return original text
                }
                return `<a href="mailto:${email}" class="cc-contact-link cc-email-btn">📧 Email: ${email}</a>`;
            })
            // Handle WhatsApp Live Support format - Updated patterns
            .replace(/\*\*\[💬\s*Chat with Us on WhatsApp\]\(([^)]+)\)\*\*/g, '<a href="$1" target="_blank" class="cc-whatsapp-btn">💬 Chat with Us on WhatsApp</a>')
            .replace(/\[💬\s*Chat with Us on WhatsApp\]\(([^)]+)\)/g, '<a href="$1" target="_blank" class="cc-whatsapp-btn">💬 Chat with Us on WhatsApp</a>')
            .replace(/\[\s*💬\s*Chat with Us on WhatsApp\]\s*\(([^)]+)\)/g, '<a href="$1" target="_blank" class="cc-whatsapp-btn">💬 Chat with Us on WhatsApp</a>')
            .replace(/\[\s*Chat with Us on WhatsApp\]\s*\(([^)]+)\)/g, '<a href="$1" target="_blank" class="cc-whatsapp-btn">💬 Chat with Us on WhatsApp</a>')
            .replace(/WhatsApp Live Support:\s*📱\s*Click here to chat:\s*\[Start WhatsApp Chat\]\s*\(([^)]+)\)/g, '<a href="$1" target="_blank" class="cc-whatsapp-btn">💬 Start WhatsApp Chat</a>')
            .replace(/Click here to chat:\s*\[Start WhatsApp Chat\]\s*\(([^)]+)\)/g, '<a href="$1" target="_blank" class="cc-whatsapp-btn">💬 Start WhatsApp Chat</a>')
            .replace(/Chat with Us on WhatsApp\s*\(([^)]+)\)/g, '<a href="$1" target="_blank" class="cc-whatsapp-btn">💬 Chat with Us on WhatsApp</a>')
            // PROBLEM 1 FIX: Handle button tags properly and prevent malformed HTML
            // .replace(/<button([^>]*?)>\s*([^<]*?)\s*$/g, '<button$1>$2</button>'); // Close unclosed button tags
        
        // Apply basic newline formatting (preserve line breaks for normal responses)
        formattedText = formattedText
            // First handle line endings (preserve structure)
            .replace(/\r\n/g, '\n')    // Normalize Windows line endings to Unix
            .replace(/\r/g, '\n')      // Normalize Mac line endings to Unix
            // Then convert newlines to breaks while preserving structure
            .replace(/\n/g, '<br>')    // Convert all newlines to breaks
            // Clean up spacing around breaks (minimal cleanup)
            .replace(/\s*<br>\s*/g, '<br>') // Clean up extra spaces around breaks
            .replace(/<br><br><br>+/g, '<br><br>') // Limit to max 2 consecutive breaks
            // Ensure proper spacing after emojis and before text
            .replace(/(🚗|🚙|🚚|🏍️|🔄|📋|📅|💡|📊)\s*<br>/g, '$1<br>')
        
        return formattedText;
    }

    function extractActionButtons(text) {
        let buttonsHTML = '';
        const pipePattern = /([🔧🚗💰📞🛠️🚙🚛🚚📅💳📍📧🗺️💬🧽🔋]+\s*[^|]+)/g;
        const buttons = [];
        let match;
        
        while ((match = pipePattern.exec(text)) !== null) {
            const buttonText = match[1].trim();
            if (buttonText && !buttonText.includes('\n') && buttonText.length < 50) {
                buttons.push(buttonText);
            }
        }
        
        // Old BUTTON_OPTIONS format
        const buttonMatch = text.match(/BUTTON_OPTIONS_START([\s\S]*?)BUTTON_OPTIONS_END/);
        if (buttonMatch) {
            const buttonSection = buttonMatch[1];
            const buttonLines = buttonSection.split('\n').filter(line => line.trim() && line.includes('|'));
            
            buttonLines.forEach(line => {
                const [label, action] = line.split('|').map(s => s.trim());
                if (label && action) {
                    buttons.push(label);
                }
            });
        }
        
        // // Legacy support for simple buttons
        // if (text.includes('Would you like') || text.includes('recommendations') || text.includes('financing options')) {
        //     if (text.includes('vehicle recommendations')) {
        //         buttons.push('Vehicle recommendations');
        //     }
        //     // PROBLEM 2 FIX: Remove automatic "Financing options" button for car reviews
        //     if (text.includes('financing options') && !text.includes('Car Reviews') && !text.includes('Reviews & Ratings')) {
        //         buttons.push('Financing options');
        //     }
        //     if (text.includes('loan calculator')) {
        //         buttons.push('Loan calculator');
        //     }
        // }
        
        // Only add action buttons for specific bot responses, not welcome messages
        if (text.includes('What would you like to know') || (text.includes('How can I help') && !text.includes('automotive assistant'))) {
            buttons.push('COE Prices', 'Test Drive', 'Vehicle Info');
        }

        if (buttons.length > 0) {
            const uniqueButtons = [...new Set(buttons)]; // Remove duplicates
            const buttonElements = uniqueButtons.map(btn => 
                `<button class="cc-action-btn">${btn}</button>`
            ).join('');
            
            buttonsHTML = `<div class="cc-action-buttons">${buttonElements}</div>`;
        }
        
        return buttonsHTML;
    }

    function showTypingIndicator() {
        const messagesContainer = document.getElementById(CONFIG.MESSAGES_ID);
        if (!messagesContainer) return;
        hideTypingIndicator();
        const typingHTML = `
            <div class="cc-message cc-bot cc-typing-message">
                <div class="cc-avatar cc-bot">
                    <img src="${CHATBOT_LOGO_URL}" alt="Bot" />
                </div>
                <div class="cc-typing-indicator cc-show">
                    <div class="cc-typing">
                        <div class="cc-typing-dot"></div>
                        <div class="cc-typing-dot"></div>
                        <div class="cc-typing-dot"></div>
                    </div>
                </div>
            </div>
        `;

        messagesContainer.insertAdjacentHTML('beforeend', typingHTML);
        
        // Ensure typing indicator is visible by scrolling to bottom with a slight delay
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 50);
    }

    function hideTypingIndicator() {
        const typingMessage = document.querySelector('.cc-typing-message');
        if (typingMessage) {
            typingMessage.remove();
        }
    }

    function handleActionButton(action) {
        if (isProcessing) {
            return;
        }
        
        isProcessing = true;
        
        try {
            switch (action.toLowerCase()) {
                case 'whatsapp':
                    const whatsappUrl = window.getWhatsAppUrl ? window.getWhatsAppUrl() : 'https://wa.me/6598765432';
                    window.open(whatsappUrl, '_blank');
                    isProcessing = false;
                    break;
                case 'call':
                    const phoneUrl = window.getPhoneUrl ? window.getPhoneUrl() : 'tel:+6562345678';
                    window.open(phoneUrl, '_self');
                    isProcessing = false;
                    break;
                case 'email':
                    window.open('mailto:info@clevercompanion.sg', '_blank');
                    isProcessing = false;
                    break;
                case 'google.com':
                case 'maps.google.com':
                case '🗺️ get directions':
                case '📍 view on google maps':
                case 'view on google maps':
                    window.open('https://www.google.com/maps/search/CleverCompanion+Auto+Showroom+Singapore/@1.3521,103.8198,17z', '_blank');
                    isProcessing = false;
                    break;
                default:
                    // Send detailed request directly to RASA
                    sendMessage(action).finally(() => {
                        isProcessing = false;
                    });
                    return; // Don't set isProcessing to false here since sendMessage will handle it
            }
            
        } catch (error) {
            console.error('Error in action button handler:', error);
            isProcessing = false;
        }
    }


    
    // Helper function to reset button states
    function resetButtonState() {
        setTimeout(() => {
            isProcessing = false;
            const actionButtons = document.querySelectorAll('.cc-action-btn');
            actionButtons.forEach(btn => {
                btn.style.opacity = '1';
                btn.style.pointerEvents = 'auto';
                btn.style.cursor = 'pointer';
                btn.style.transform = 'scale(1)';
                btn.textContent = btn.textContent.replace(' ⏳', '');
            });
        }, ACTION_COOLDOWN);
    }

    // Enhanced scroll behavior - ensure typing indicator and messages are visible
    function scrollToBottom() {
        const messagesContainer = document.getElementById(CONFIG.MESSAGES_ID);
        if (messagesContainer) {
            // Always scroll to bottom to show latest content including typing indicator
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    // Improved function to scroll to top of latest bot message
    function scrollToLatestBotMessage() {
        const messagesContainer = document.getElementById(CONFIG.MESSAGES_ID);
        if (messagesContainer) {
            const botMessages = messagesContainer.querySelectorAll('.cc-message');
            const latestBotMessage = botMessages[botMessages.length - 1];
            if (latestBotMessage) {
                const messageRect = latestBotMessage.getBoundingClientRect();
                const containerRect = messagesContainer.getBoundingClientRect();
                
                // Calculate scroll position to show message at top of container
                const scrollTop = latestBotMessage.offsetTop - messagesContainer.offsetTop - 10;
                
                // Smooth scroll to top of latest bot message
                messagesContainer.scrollTo({
                    top: scrollTop,
                    behavior: 'smooth'
                });
            }
        }
    }

    function scrollToTop() {
        const messagesContainer = document.getElementById(CONFIG.MESSAGES_ID);
        if (messagesContainer) {
            messagesContainer.scrollTop = 0;
        }
    }

    // Add calculateLoan function globally
    function calculateLoan() {
        // Create unique IDs to avoid duplicates
        const timestamp = Date.now();
        const carPrice = parseFloat(document.getElementById('carPrice')?.value || document.querySelector(`input[placeholder*="80000"]`)?.value) || 0;
        const downPaymentPercent = parseFloat(document.getElementById('downPayment')?.value || document.querySelector('select option:checked')?.value) || 20;
        const loanTenure = parseFloat(document.getElementById('loanTenure')?.value || 4);
        const interestRate = parseFloat(document.getElementById('interestRate')?.value || 2.78);
        
        if (carPrice <= 0) {
            alert('Please enter a valid car price');
            return;
        }
        
        const downPayment = (carPrice * downPaymentPercent) / 100;
        const loanAmount = carPrice - downPayment;
        const monthlyRate = interestRate / 100 / 12;
        const numPayments = loanTenure * 12;
        
        const monthlyPayment = (loanAmount * monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / 
                              (Math.pow(1 + monthlyRate, numPayments) - 1);
        
        const totalPayment = monthlyPayment * numPayments;
        const totalInterest = totalPayment - loanAmount;
        
        const resultElement = document.getElementById('loanResult') || document.querySelector('[id*="loanResult"]');
        const monthlyElement = document.getElementById('monthlyPayment') || document.querySelector('[id*="monthlyPayment"]');
        const detailsElement = document.getElementById('loanDetails') || document.querySelector('[id*="loanDetails"]');
        
        if (monthlyElement) {
            monthlyElement.textContent = 'SGD $' + monthlyPayment.toFixed(2) + '/month';
        }
        if (detailsElement) {
            detailsElement.innerHTML = 
                'Car Price: SGD $' + carPrice.toLocaleString() + '<br>' +
                'Down Payment: SGD $' + downPayment.toLocaleString() + ' (' + downPaymentPercent + '%)<br>' +
                'Loan Amount: SGD $' + loanAmount.toLocaleString() + '<br>' +
                'Total Interest: SGD $' + totalInterest.toLocaleString() + '<br>' +
                'Total Payment: SGD $' + totalPayment.toLocaleString();
        }
        if (resultElement) {
            resultElement.style.display = 'block';
        }
    }
    
    // Add missing calculateLoanSpecific function
    function calculateLoanSpecific(timestamp) {
        const carPrice = parseFloat(document.getElementById('carPrice_' + timestamp).value) || 0;
        const downPaymentPercent = parseFloat(document.getElementById('downPayment_' + timestamp).value) || 20;
        const loanTenure = parseFloat(document.getElementById('loanTenure_' + timestamp).value) || 4;
        const interestRateSelect = document.getElementById('interestRate_' + timestamp);
        
        let interestRate;
        if (interestRateSelect && interestRateSelect.value === 'custom') {
            const customRate = parseFloat(document.getElementById('customRateInput_' + timestamp).value);
            if (!customRate || customRate <= 0) {
                alert('Please enter a valid custom interest rate');
                return;
            }
            interestRate = customRate;
        } else {
            interestRate = parseFloat(interestRateSelect?.value) || 2.78;
        }
        
        if (carPrice <= 0) {
            alert('Please enter a valid car price');
            return;
        }
        
        const downPayment = (carPrice * downPaymentPercent) / 100;
        const loanAmount = carPrice - downPayment;
        const monthlyRate = interestRate / 100 / 12;
        const numPayments = loanTenure * 12;
        
        const monthlyPayment = (loanAmount * monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / 
                              (Math.pow(1 + monthlyRate, numPayments) - 1);
        
        const totalPayment = monthlyPayment * numPayments;
        const totalInterest = totalPayment - loanAmount;
        
        const monthlyElement = document.getElementById('monthlyPayment_' + timestamp);
        const detailsElement = document.getElementById('loanDetails_' + timestamp);
        const resultElement = document.getElementById('loanResult_' + timestamp);
        
        if (monthlyElement) {
            monthlyElement.textContent = 'SGD $' + monthlyPayment.toFixed(2) + '/month';
        }
        if (detailsElement) {
            detailsElement.innerHTML = 
                'Car Price: SGD $' + carPrice.toLocaleString() + '<br>' +
                'Down Payment: SGD $' + downPayment.toLocaleString() + ' (' + downPaymentPercent + '%)<br>' +
                'Loan Amount: SGD $' + loanAmount.toLocaleString() + '<br>' +
                'Total Interest: SGD $' + totalInterest.toLocaleString() + '<br>' +
                'Total Payment: SGD $' + totalPayment.toLocaleString();
        }
        if (resultElement) {
            resultElement.style.display = 'block';
        }
    }

    function toggleCustomRate(timestamp) {
        const select = document.getElementById('interestRate_' + timestamp);
        const customInput = document.getElementById('customRateInput_' + timestamp);
        
        if (select && customInput) {
            if (select.value === 'custom') {
                customInput.style.display = 'block';
                customInput.focus();
            } else {
                customInput.style.display = 'none';
            }
        }
    }

    // Chart enlargement function for clickable charts
    function enlargeChart(chartId, title) {
        const img = document.getElementById(chartId);
        if (!img) return;
        
        // Create modal overlay
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(0,0,0,0.9); display: flex; align-items: center; justify-content: center;
            z-index: 1000000; cursor: pointer; animation: fadeIn 0.3s ease-out;
        `;
        
        // Create enlarged image
        const enlargedImg = document.createElement('img');
        enlargedImg.src = img.src;
        enlargedImg.alt = title;
        enlargedImg.style.cssText = `
            max-width: 95vw; max-height: 95vh; border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5); animation: zoomIn 0.3s ease-out;
        `;
        
        // Create close button
        const closeBtn = document.createElement('div');
        closeBtn.innerHTML = '✕';
        closeBtn.style.cssText = `
            position: absolute; top: 20px; right: 30px; color: white; font-size: 40px;
            cursor: pointer; z-index: 999998; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        `;
        
        // Add title
        const titleDiv = document.createElement('div');
        titleDiv.textContent = title;
        titleDiv.style.cssText = `
            position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%);
            color: white; font-size: 18px; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        `;
        
        // Add animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes zoomIn {
                from { transform: scale(0.8); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
        `;
        document.head.appendChild(style);
        
        // Assemble modal
        modal.appendChild(enlargedImg);
        modal.appendChild(closeBtn);
        modal.appendChild(titleDiv);
        document.body.appendChild(modal);
        
        // Close functionality
        const closeModal = () => {
            modal.style.animation = 'fadeOut 0.3s ease-out forwards';
            setTimeout(() => {
                if (modal.parentNode) modal.parentNode.removeChild(modal);
                if (style.parentNode) style.parentNode.removeChild(style);
            }, 300);
        };
        
        modal.onclick = closeModal;
        closeBtn.onclick = closeModal;
        enlargedImg.onclick = (e) => e.stopPropagation(); // Prevent closing when clicking image
        
        // ESC key support
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);
    }

    // Make functions globally accessible for onclick handlers
    window.handleActionButton = handleActionButton;
    window.calculateLoan = calculateLoan;
    window.calculateLoanSpecific = calculateLoanSpecific;
    window.toggleCustomRate = toggleCustomRate;
    window.enlargeChart = enlargeChart;
    window.sendButtonPayload = sendButtonPayload;

    // Global functions for external access
    window.CleverCompanionWidget = {
        init: initWidget,
        open: openWidget,
        close: closeWidget,
        sendMessage: sendMessage,
        calculateLoan: calculateLoan,
        calculateLoanSpecific: calculateLoanSpecific
    };

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initWidget);
    } else {
        initWidget();
    }

})();