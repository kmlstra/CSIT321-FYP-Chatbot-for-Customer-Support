/**
 * CleverCompanion Multi-tenant Widget
 * Dynamically configures based on client settings
 * Enhanced with full feature set from single-tenant version
 */

(function() {
    'use strict';

    class MultiTenantChatWidget {
        constructor() {
            // Simplified configuration - only requires client_id
            this.config = window.CleverCompanionConfig || {};
            this.clientId = this.config.clientId || this.detectClientId();
            this.apiUrl = this.config.apiUrl || (window.CLEVERCOMPANION_BACKEND_URL || window.BACKEND_URL || window.DOMAIN + ':8000' || 'http://localhost:8000') + '/api/widget';
            this.sessionId = this.generateSessionId();
            this.isOpen = false;
            this.messages = [];
            this.isProcessing = false;
            this.isProcessingButton = false; // 防止按钮重复点击的标志
            this.lastButtonClickTime = 0; // 上次按钮点击时间戳
            this.menuOpen = false;
            this.lastInteractionTime = new Date().toISOString();
            
            // Default configuration (will be overridden by client config)
            this.defaultConfig = {
                title: 'CleverCompanion',
                subtitle: 'Your automotive assistant',
                welcomeMessage: "Hello! I'm CleverCompanion, your automotive assistant. How can I help you today?",
                branding: {
                    primary_color: '#4F46E5',
                    company_name: 'CleverCompanion',
                    logo_url: '/static/media/images/CleverCompanion-logo.png'
                },
                features: {
                    menu_enabled: true,
                    loan_calculator: true,
                    coe_prices: true,
                    contact_info: true
                }
            };
            
            if (!this.clientId) {
                console.error('CleverCompanion: No valid client ID found. Please provide clientId in CleverCompanionConfig.');
                return;
            }
            
            this.init();
        }
        
        detectClientId() {
            // Try multiple methods to detect client ID in order of priority
            
            // Method 1: From window.CleverCompanionConfig (highest priority)
            if (this.config.clientId && this.isValidClientId(this.config.clientId)) {
                // Client ID detected from config
                this.storeClientId(this.config.clientId);
                return this.config.clientId;
            }
            
            // Method 2: URL parameter
            const urlParams = new URLSearchParams(window.location.search);
            const urlClientId = urlParams.get('client_id') || urlParams.get('clientId') || urlParams.get('client');
            if (urlClientId && this.isValidClientId(urlClientId)) {
                // Client ID detected from URL
                this.storeClientId(urlClientId);
                return urlClientId;
            }
            
            // Method 3: Script tag data attribute
            const scriptTags = document.querySelectorAll('script[src*="clevercompanion-widget.js"], script[src*="multi-tenant-widget.js"]');
            for (const scriptTag of scriptTags) {
                const scriptClientId = scriptTag.getAttribute('data-client-id') || 
                                     scriptTag.getAttribute('data-client') ||
                                     scriptTag.getAttribute('client-id') ||
                                     scriptTag.dataset.clientId;
                if (scriptClientId && this.isValidClientId(scriptClientId)) {
                    // Client ID detected from script tag
                    this.storeClientId(scriptClientId);
                    return scriptClientId;
                }
            }
            
            // Method 4: Meta tag
            const metaTag = document.querySelector('meta[name="clevercompanion-client-id"], meta[name="cc-client-id"]');
            if (metaTag) {
                const metaClientId = metaTag.getAttribute('content');
                if (metaClientId && this.isValidClientId(metaClientId)) {
                    // Client ID detected from meta tag
                    this.storeClientId(metaClientId);
                    return metaClientId;
                }
            }
            
            // Method 5: Global variable
            const globalClientId = window.CLEVERCOMPANION_CLIENT_ID || 
                                 window.CC_CLIENT_ID || 
                                 window.clevercompanionClientId;
            if (globalClientId && this.isValidClientId(globalClientId)) {
                // Client ID detected from global variable
                this.storeClientId(globalClientId);
                return globalClientId;
            }
            
            // Method 6: Local storage
            try {
                const storageClientId = localStorage.getItem('cc_client_id') || 
                                      localStorage.getItem('clevercompanion_client_id');
                if (storageClientId && this.isValidClientId(storageClientId)) {
                    // Client ID detected from local storage
                    return storageClientId;
                }
            } catch (e) {
                // console.warn('Local storage access failed:', e);
            }
            
            // Method 7: Domain mapping (fallback)
            const hostname = window.location.hostname;
            const domainMapping = {
                'localhost': 'demo-client',
                '127.0.0.1': 'demo-client',
                'demo.clevercompanion.com': 'demo-client',
                'test.clevercompanion.com': 'test-client',
                // Add more domain mappings as needed
            };
            
            if (domainMapping[hostname]) {
                // Client ID detected from domain mapping
                this.storeClientId(domainMapping[hostname]);
                return domainMapping[hostname];
            }
            
            // Method 8: Extract from subdomain
            const subdomainMatch = hostname.match(/^([^.]+)\.(clevercompanion|cc)\.(com|net|org)$/);
            if (subdomainMatch && subdomainMatch[1] !== 'www') {
                const subdomainClientId = subdomainMatch[1];
                if (this.isValidClientId(subdomainClientId)) {
                    // Client ID detected from subdomain
                    this.storeClientId(subdomainClientId);
                    return subdomainClientId;
                }
            }
            
            // console.warn('No valid client ID detected, using default');
            return 'default';
        }
        
        isValidClientId(clientId) {
            // Validate client ID format
            if (!clientId || typeof clientId !== 'string') {
                return false;
            }
            
            // Remove whitespace
            clientId = clientId.trim();
            
            // Check length (3-50 characters)
            if (clientId.length < 3 || clientId.length > 50) {
                return false;
            }
            
            // Check format: alphanumeric, hyphens, underscores only
            const validFormat = /^[a-zA-Z0-9_-]+$/.test(clientId);
            if (!validFormat) {
                return false;
            }
            
            // Exclude common invalid values
            const invalidValues = ['null', 'undefined', 'test', 'example', 'sample', 'placeholder'];
            if (invalidValues.includes(clientId.toLowerCase())) {
                return false;
            }
            
            return true;
        }
        
        storeClientId(clientId) {
            // Store client ID for future use
            try {
                localStorage.setItem('cc_client_id', clientId);
            } catch (e) {
                // console.warn('Failed to store client ID in local storage:', e);
            }
        }

        async init() {
            // Create widget immediately with default config to prevent delay
            this.clientConfig = this.defaultConfig;
            this.createWidget();
            
            // Add welcome message immediately with default config
            this.addWelcomeMessage();
            
            // Load client configuration and preload cache in parallel for better performance
            const configPromise = this.loadClientConfig().then(() => {
                this.updateWidgetWithConfig();
                this.applyBranding();
                // Update welcome message with client-specific config if different
                if (this.clientConfig.welcomeMessage !== this.defaultConfig.welcomeMessage) {
                    this.addWelcomeMessage();
                }
            }).catch((error) => {
                // console.warn('Failed to load client config, using defaults:', error);
                // Still apply branding with defaults
                this.applyBranding();
            });
            
            // Preload client cache in background for faster chat responses
            const cachePromise = this.preloadClientCache();
            
            // Wait for both operations to complete (but don't block widget initialization)
            Promise.all([configPromise, cachePromise]).then(() => {
                // Widget initialization and cache preloading completed
            }).catch((error) => {
                // console.warn('Some initialization tasks failed, but widget is ready:', error);
            });
        }
        
        updateWidgetWithConfig() {
            // Update widget elements with loaded configuration
            const titleElement = document.getElementById('cc-title');
            const logoElements = document.querySelectorAll('#cc-toggle img, .cc-logo img');
            const menuDropdown = document.getElementById('cc-menu-dropdown');
            
            if (titleElement) {
                const logoUrl = this.clientConfig.branding?.logo_url || '/static/media/images/CleverCompanion-logo.png';
                titleElement.innerHTML = `
                    <span class="cc-logo">
                        <img src="${logoUrl}" alt="CleverCompanion" />
                    </span>
                    CleverCompanion
                `;
            }
            
            // Update logo in toggle button
            logoElements.forEach(img => {
                const logoUrl = this.clientConfig.branding?.logo_url || '/static/media/images/CleverCompanion-logo.png';
                img.src = logoUrl;
                img.alt = 'CleverCompanion';
            });
            
            // Update menu items
            if (menuDropdown) {
                menuDropdown.innerHTML = this.generateMenuItems();
            }
            
            // Safely update CSS with improved injection mechanism
            this.updateWidgetCSS();
        }

        // Session management with expiry (30 minutes to match backend)
        getSessionExpiryTime() {
            return 30 * 60 * 1000; // 30 minutes
        }

        isSessionExpired() {
            const sessionTimestamp = localStorage.getItem('cc_session_timestamp');
            if (!sessionTimestamp) return true;
            
            const now = Date.now();
            const sessionTime = parseInt(sessionTimestamp);
            return (now - sessionTime) > this.getSessionExpiryTime();
        }

        clearExpiredSession() {
            localStorage.removeItem('cc_session_id');
            localStorage.removeItem('cc_session_timestamp');
            localStorage.removeItem('cc_chat_history');
        }

        generateSessionId() {
            // Simplified session generation - backend handles session validation
            let sessionId = localStorage.getItem('cc_session_id');
            if (!sessionId || this.isSessionExpired()) {
                // Clear expired session and generate new one
                this.clearExpiredSession();
                sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                localStorage.setItem('cc_session_id', sessionId);
                localStorage.setItem('cc_session_timestamp', Date.now().toString());
            }
            return sessionId;
        }

        updateSessionTimestamp() {
            // Simplified timestamp update - backend manages session lifecycle
            localStorage.setItem('cc_session_timestamp', Date.now().toString());
        }

        loadClientConfig() {
            // Load client configuration directly from database instead of API endpoint
            return this.getClientConfigFromDB(this.clientId)
                .then(clientConfig => {
                    // Merge with default config
                    this.clientConfig = { ...this.defaultConfig, ...clientConfig };
                })
                .catch(error => {
                    // console.warn('Error loading client config:', error);
                    this.clientConfig = this.defaultConfig;
                });
        }

        // Get client configuration directly from database
        async getClientConfigFromDB(clientId) {
            try {
                // Use the backend API to get client config
                const response = await fetch(`${this.apiUrl}/config/${clientId}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Client-Domain': window.location.hostname
                    }
                });
                
                if (response.ok) {
                    return await response.json();
                } else {
                    console.warn('Failed to load client config, using defaults');
                    return this.defaultConfig;
                }
            } catch (error) {
                console.warn('Error loading client config:', error);
                return this.defaultConfig;
            }
        }

        preloadClientCache() {
            // Preload client data into cache to speed up first chat response
            // Use the correct API endpoint structure
            const cacheApiUrl = this.apiUrl.replace('/api/widget', '/api/cache');
            return fetch(`${cacheApiUrl}/warm/${this.clientId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Client-Domain': window.location.hostname
                }
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    // console.warn('Failed to preload client cache, but widget will still work');
                    return null;
                }
            })
            .then(result => {
                if (result) {
                    // Cache preloaded successfully
                }
            })
            .catch(error => {
                // Error preloading client cache
                // Don't throw error - widget should still work without cache preloading
            });
        }

        createWidget() {
            // Inject CSS
            this.injectCSS();
            
            // Create widget HTML
            const widgetHTML = this.generateWidgetHTML();
            document.body.insertAdjacentHTML('beforeend', widgetHTML);
            
            // Attach event listeners
            this.attachEventListeners();
        }

        injectCSS() {
            if (document.getElementById('cc-widget-styles')) return;
            
            const style = document.createElement('style');
            style.id = 'cc-widget-styles';
            style.setAttribute('data-widget-version', '1.0');
            style.textContent = this.getWidgetCSS();
            document.head.appendChild(style);
        }

        // New method for safely updating CSS without losing styles
        updateWidgetCSS() {
            const existingStyle = document.getElementById('cc-widget-styles');
            if (existingStyle) {
                // Create a temporary style element to test the new CSS
                const tempStyle = document.createElement('style');
                tempStyle.id = 'cc-widget-styles-temp';
                tempStyle.setAttribute('data-widget-version', '1.0');
                tempStyle.textContent = this.getWidgetCSS();
                
                // Insert the temporary style after the existing one
                existingStyle.parentNode.insertBefore(tempStyle, existingStyle.nextSibling);
                
                // Use requestAnimationFrame to ensure smooth transition
                requestAnimationFrame(() => {
                    // Remove the old style
                    if (existingStyle.parentNode) {
                        existingStyle.remove();
                    }
                    
                    // Rename the temporary style to the permanent ID
                    tempStyle.id = 'cc-widget-styles';
                    
                    // Clean up any duplicate styles
                    this.ensureSingleWidgetStyle();
                });
            } else {
                // If no existing style, inject normally
                this.injectCSS();
            }
        }

        // Prevent CSS conflicts by ensuring only one widget style exists
        ensureSingleWidgetStyle() {
            const existingStyles = document.querySelectorAll('style[id^="cc-widget-styles"]');
            if (existingStyles.length > 1) {
                // Keep only the most recent style element
                for (let i = 0; i < existingStyles.length - 1; i++) {
                    if (existingStyles[i].parentNode) {
                        existingStyles[i].remove();
                    }
                }
            }
        }

        generateWidgetHTML() {
            const config = this.clientConfig;
            const logoUrl = config.branding?.logo_url || '/static/media/images/CleverCompanion-logo.png';
            
            return `
                <!-- Toggle Button -->
                <button id="cc-toggle" aria-label="Open chat">
                    <img src="${logoUrl}" alt="CleverCompanion" />
                </button>

                <!-- Close Button -->
                <button id="cc-close-btn" aria-label="Close chat">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>

                <!-- Chat Container -->
                <div id="cc-chatbot-container" role="dialog" aria-labelledby="cc-title" aria-describedby="cc-subtitle">
                    <div class="cc-header">
                        <h3 id="cc-title">
                            <span class="cc-logo">
                                <img src="${logoUrl}" alt="CleverCompanion" />
                            </span>
                            CleverCompanion
                        </h3>
                        <p id="cc-subtitle">How can I help you today?</p>
                    </div>
                    
                    <div id="cc-messages" role="log" aria-live="polite" aria-label="Chat messages">
                        <!-- Messages will be added here -->
                    </div>
                    
                    <div class="cc-input-area">
                        <button id="cc-menu-btn" aria-label="Menu">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="3" y1="12" x2="21" y2="12"></line>
                                <line x1="3" y1="6" x2="21" y2="6"></line>
                                <line x1="3" y1="18" x2="21" y2="18"></line>
                            </svg>
                        </button>
                        
                        <div class="cc-input-container">
                            <textarea 
                                id="cc-input" 
                                name="chatInput"
                                placeholder="Type your message..." 
                                rows="1"
                                aria-label="Type your message"
                                autocomplete="off"
                            ></textarea>
                            <button id="cc-send-btn" aria-label="Send message">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="22" y1="2" x2="11" y2="13"></line>
                                    <polygon points="22,2 15,22 11,13 2,9 22,2"></polygon>
                                </svg>
                            </button>
                        </div>
                        
                        <div class="cc-menu-dropdown" id="cc-menu-dropdown">
                            ${this.generateMenuItems()}
                        </div>
                    </div>
                </div>
            `;
        }

        generateMenuItems() {
            const menuOptions = [
                { icon: '💰', text: 'Latest COE Prices', action: 'what are the current coe prices', enabled: this.clientConfig.features?.coe_prices },
                // { icon: '🚗', text: 'Search Vehicle', action: 'Help me search for vehicles by budget, type and brand preferences', enabled: true },
                { icon: '📅', text: 'Appointment Booking', action: 'I want to book an appointment', enabled: this.clientConfig.features?.appointment_booking },
                // { icon: '🔧', text: 'Maintenance Tips', action: 'Provide vehicle maintenance guidance and service center recommendations', enabled: true },
                { icon: '💳', text: 'Loan Calculator', action: 'Calculate car loan with current interest rates and financing options', enabled: this.clientConfig.features?.loan_calculator },
                { icon: '📞', text: 'Contact Us', action: 'Show me contact information and ways to reach us', enabled: true }, // Contact Us is always available as core feature
                // { icon: '📝', text: 'Feedback', action: 'I want to provide feedback about the service and suggest improvements', enabled: true },
                { icon: '💬', text: 'Live Support', action: 'I need live support assistance', enabled: this.clientConfig.features?.live_support } // Live Support can be disabled
            ];

            // 只显示明确启用的功能按钮 (enabled === true)
            return menuOptions
                .filter(option => option.enabled === true)
                .map(option => 
                    `<div class="cc-menu-item" data-action="${option.action}">
                        <span>${option.icon}</span>
                        <span>${option.text}</span>
                    </div>`
                ).join('');
        }

        getWidgetCSS() {
            const primaryColor = this.clientConfig.branding?.primary_color || '#4F46E5';
            return `
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
            background: transparent;
            border: 2px solid #4F46E5;
            border-radius: 12px;
            padding: 12px 16px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s ease;
            color: #4F46E5;
            font-weight: 500;
            text-align: left;
            width: 100%;
            display: block;
            box-shadow: none;
        }

        .cc-action-btn:hover {
            background: rgba(79, 70, 229, 0.1);
            color: #4F46E5;
            border-color: #4F46E5;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
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

        /* FIXED: Enhanced contact button styling to match WhatsApp button */
        .cc-email-btn {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            border: 2px solid #f59e0b;
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
            box-shadow: 0 4px 15px rgba(245, 158, 11, 0.2);
            position: relative;
            overflow: hidden;
            min-width: 180px;
        }

        .cc-email-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }

        .cc-email-btn:hover::before {
            left: 100%;
        }

        .cc-email-btn:hover {
            background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
            border-color: #d97706;
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 8px 25px rgba(245, 158, 11, 0.4);
        }

        .cc-email-btn:active {
            transform: translateY(-1px) scale(0.98);
            box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);
        }

        .cc-phone-btn {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white;
            border: 2px solid #3b82f6;
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
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2);
            position: relative;
            overflow: hidden;
            min-width: 180px;
        }

        .cc-phone-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }

        .cc-phone-btn:hover::before {
            left: 100%;
        }

        .cc-phone-btn:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
            border-color: #1d4ed8;
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
        }

        .cc-phone-btn:active {
            transform: translateY(-1px) scale(0.98);
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
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

        /* FIXED: Reduced Google Maps size */
        .cc-map-container {
            width: 100%;
            max-width: 280px;
            margin: 10px auto;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .cc-embedded-map {
            width: 100%;
            height: 150px;
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

        /* Chart container styling - FIXED: Proper sizing and modal hint */
        .chart-container {
            position: relative;
            cursor: pointer;
            display: block;
            width: 100%;
            max-width: 280px;
            margin: 12px auto;
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.3s ease;
            border: 2px solid #e5e7eb;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .chart-container:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 8px 25px rgba(79, 70, 229, 0.15);
            border-color: #4F46E5;
        }

        .chart-container img {
            width: 100%;
            height: auto;
            max-height: 200px;
            object-fit: contain;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .chart-container:hover img {
            opacity: 0.9;
        }

        .chart-container::after {
            content: '🔍 Click to enlarge';
            position: absolute;
            bottom: 8px;
            right: 8px;
            background: rgba(79, 70, 229, 0.9);
            color: white;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 11px;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        }

        .chart-container:hover::after {
            opacity: 1;
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
        .cc-typing-dot:nth-child(2) { animation-delay: 0.2s; }
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
        
        /* Chat buttons for Rasa responses */
        .cc-chat-buttons {
            margin: 12px 0;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .cc-chat-button {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 16px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(79, 70, 229, 0.2);
            text-align: left;
            width: 100%;
            min-height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .cc-chat-button:hover {
            background: linear-gradient(135deg, #3730A3 0%, #6D28D9 100%);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
        }
        
        .cc-chat-button:active {
            transform: translateY(0);
            box-shadow: 0 2px 8px rgba(79, 70, 229, 0.2);
        }
        
        .cc-chat-button:disabled {
            background: #9CA3AF;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        /* Enhanced appointment booking buttons */
        .cc-buttons {
            margin: 16px 0 8px 0;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .cc-button {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            color: white;
            border: none;
            border-radius: 16px;
            padding: 14px 20px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
            text-align: center;
            width: 100%;
            min-height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
            border: 2px solid transparent;
        }
        
        .cc-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.6s ease;
        }
        
        .cc-button:hover::before {
            left: 100%;
        }
        
        .cc-button:hover {
            background: linear-gradient(135deg, #3730A3 0%, #6D28D9 100%);
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 8px 25px rgba(79, 70, 229, 0.4);
            border-color: rgba(255, 255, 255, 0.2);
        }
        
        .cc-button:active {
            transform: translateY(-1px) scale(0.98);
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
        }
        
        .cc-button:focus {
            outline: none;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25), 0 0 0 3px rgba(79, 70, 229, 0.1);
        }
        
        .cc-button:disabled {
            background: linear-gradient(135deg, #9CA3AF 0%, #6B7280 100%);
            cursor: not-allowed;
            transform: none;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            border-color: transparent;
        }
        
        .cc-button:disabled::before {
            display: none;
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
            
            .cc-chat-buttons {
                gap: 6px;
            }
            
            .cc-chat-button {
                padding: 10px 14px;
                font-size: 13px;
                min-height: 40px;
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

        /* Loan calculator styling */
        .cc-loan-calculator {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border: 2px solid #0ea5e9;
            border-radius: 16px;
            padding: 20px;
            margin: 16px 0;
            box-shadow: 0 4px 12px rgba(14, 165, 233, 0.15);
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
        }

        applyBranding() {
            // Additional branding customizations can be applied here
            // This method can be extended to apply more specific styling based on client config
        }

        addWelcomeMessage() {
            const config = this.clientConfig;
            const logoUrl = config.branding?.logo_url || '/static/media/images/CleverCompanion-logo.png';
            
            const welcomeHTML = `
                <div class="cc-message cc-bot">
                    <div class="cc-avatar cc-bot">
                        <img src="${logoUrl}" alt="Bot" />
                    </div>
                    <div class="cc-bubble">
                        ${config.welcomeMessage}
                        <div class="cc-timestamp">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true })}</div>
                    </div>
                </div>
            `;
            
            const messagesContainer = document.getElementById('cc-messages');
            if (messagesContainer) {
                messagesContainer.innerHTML = welcomeHTML;
            }
        }

        attachEventListeners() {
            const toggle = document.getElementById('cc-toggle');
            const closeBtn = document.getElementById('cc-close-btn');
            const input = document.getElementById('cc-input');
            const sendBtn = document.getElementById('cc-send-btn');
            const menuBtn = document.getElementById('cc-menu-btn');
            const menuDropdown = document.getElementById('cc-menu-dropdown');


            if (toggle) {
                toggle.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.toggleWidget();
                });
            }

            if (closeBtn) {
                closeBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.closeWidget();
                });
            }

            if (input) {
                input.addEventListener('keypress', (e) => this.handleKeyPress(e));
            }

            if (sendBtn) {
                sendBtn.addEventListener('click', () => {
                    const message = input.value.trim();
                    if (message) {
                        this.sendMessage(message);
                    }
                });
            }

            if (menuBtn && menuDropdown) {
                menuBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    menuDropdown.classList.toggle('cc-show');
                });

                menuDropdown.addEventListener('click', (e) => {
                    const menuItem = e.target.closest('.cc-menu-item');
                    if (menuItem) {
                        const action = menuItem.dataset.action;
                        this.sendMessage(action);
                        menuDropdown.classList.remove('cc-show');
                    }
                });
            }



            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (menuDropdown && menuBtn && !menuBtn.contains(e.target) && !menuDropdown.contains(e.target)) {
                    menuDropdown.classList.remove('cc-show');
                }
            });
        }

        toggleWidget() {
            if (this.isOpen) {
                this.closeWidget();
            } else {
                this.openWidget();
            }
        }

        openWidget() {
            const widget = document.getElementById('cc-chatbot-container');
            const toggle = document.getElementById('cc-toggle');
            const closeBtn = document.getElementById('cc-close-btn');
            
            if (widget && toggle && closeBtn) {
                widget.classList.add('cc-open');
                toggle.style.display = 'none';
                closeBtn.classList.add('cc-visible');
                this.isOpen = true;
                
                // Load chat history when widget opens (non-blocking)
                this.loadChatHistory();
                
                // Focus input
                setTimeout(() => {
                    const input = document.getElementById('cc-input');
                    if (input) input.focus();
                }, 300);
            }
        }

        closeWidget() {
            const widget = document.getElementById('cc-chatbot-container');
            const toggle = document.getElementById('cc-toggle');
            const closeBtn = document.getElementById('cc-close-btn');
            
            if (widget && toggle && closeBtn) {
                widget.classList.remove('cc-open');
                toggle.style.display = 'flex';
                closeBtn.classList.remove('cc-visible');
                this.isOpen = false;
            }
        }

        handleKeyPress(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const input = document.getElementById('cc-input');
                if (input) {
                    const message = input.value.trim();
                    if (message) {
                        this.sendMessage(message);
                    }
                }
            }
        }

        sendMessage(text) {
            const input = document.getElementById('cc-input');
            const sendBtn = document.getElementById('cc-send-btn');
            
            if (!text.trim()) return;

            // Unified session management - backend handles session validation and storage
            this.sessionId = this.generateSessionId();
            this.updateSessionTimestamp();

            // Add user message (non-blocking)
            this.addMessage(text, 'user');
            
            // Clear input and disable send button
            if (input) input.value = '';
            if (sendBtn) sendBtn.disabled = true;

            // Check if this is an appointment-related message
            const appointmentKeywords = ['appointment', 'book', 'schedule', 'service', 'test drive', 'consultation', 'trade-in'];
            const isAppointmentMessage = appointmentKeywords.some(keyword => 
                text.toLowerCase().includes(keyword)
            );
            
            // Route appointment messages directly to Rasa
            if (isAppointmentMessage) {
                this.sendMessageToRasa(text);
                if (sendBtn) sendBtn.disabled = false;
                return;
            }

            // Use unified chat API endpoint with automatic conversation storage
            this.showTypingIndicator();
            
            fetch(`${this.apiUrl.replace('/api/widget', '/api')}/chat/unified`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Client-Domain': window.location.hostname
                },
                body: JSON.stringify({
                    client_id: this.clientId,
                    session_id: this.sessionId,
                    message: text,
                    timestamp: new Date().toISOString()
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Chat request failed: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                this.hideTypingIndicator();
                
                if (data.response) {
                    this.addMessage(data.response, 'bot');
                } else if (data.error) {
                    this.addMessage(data.error, 'bot');
                } else {
                    this.addMessage('I apologize, but I\'m having trouble understanding your request. Could you please try rephrasing?', 'bot');
                }
            })
            .catch(error => {
                console.error('Error in unified chat:', error);
                this.hideTypingIndicator();
                
                // Fallback to legacy endpoint for backward compatibility
                this.sendMessageFallback(text);
            })
            .finally(() => {
                if (sendBtn) sendBtn.disabled = false;
                // Save chat history after message exchange (local backup)
                this.saveChatHistory();
            });
        }

        // Fallback method for backward compatibility with legacy endpoints
        sendMessageFallback(text) {
            this.showTypingIndicator();
            
            // Try legacy endpoint for backward compatibility
            fetch(`${this.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Client-Domain': window.location.hostname
                },
                body: JSON.stringify({
                    client_id: this.clientId,
                    session_id: this.sessionId,
                    message: text,
                    timestamp: new Date().toISOString()
                })
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            })
            .then(data => {
                // Handle the ChatResponse structure from backend
                if (data.response) {
                    this.addMessage(data.response, 'bot');
                } else if (data.responses && data.responses.length > 0) {
                    for (const responseText of data.responses) {
                        this.addMessage(responseText, 'bot');
                    }
                } else {
                    this.addMessage('I apologize, but I\'m having trouble understanding your request. Could you please try rephrasing?', 'bot');
                }
            })
            .catch(error => {
                console.error('Error in fallback chat:', error);
                this.addMessage('I\'m experiencing technical difficulties. Please try again in a moment.', 'bot');
            });
        }

        addMessage(text, sender) {
            const messagesContainer = document.getElementById('cc-messages');
            if (!messagesContainer) return;

            const config = this.clientConfig;
            const logoUrl = config.branding?.logo_url || '/static/media/images/CleverCompanion-logo.png';
            
            // Use cached profile picture URL or initialize cache
            if (!this.cachedUserAvatarUrl) {
                // Set default fallback URL
                this.cachedUserAvatarUrl = `${window.DOMAIN || 'http://localhost'}:${window.BACKEND_PORT || '8000'}/static/boy.png`;
                
                // Fetch environment config asynchronously and cache the result (non-blocking)
                fetch(`${this.apiUrl.replace('/api/widget', '/api/config/env')}`)
                    .then(response => {
                        if (response.ok) {
                            return response.json();
                        }
                        throw new Error('Failed to fetch env config');
                    })
                    .then(envConfig => {
                        this.cachedUserAvatarUrl = envConfig.PROFILE_PICTURE_URL || this.cachedUserAvatarUrl;
                        // Update existing user avatars with the correct URL
                        const userAvatars = document.querySelectorAll('.cc-avatar.cc-user img');
                        userAvatars.forEach(img => {
                            img.src = this.cachedUserAvatarUrl;
                        });
                    })
                    .catch(error => {
                        // console.warn('Failed to load environment config for profile picture:', error);
                    });
            }
            
            const avatar = sender === 'bot' ? `<img src="${logoUrl}" alt="Bot" />` : `<img src="${this.cachedUserAvatarUrl}" alt="User" style="width: 20px; height: 20px; border-radius: 50%; object-fit: cover;" />`;
            // Generate timestamp in Singapore timezone
            const now = new Date();
            const timestamp = now.toLocaleTimeString('en-SG', { 
                hour: '2-digit', 
                minute: '2-digit',
                hour12: true,
                timeZone: 'Asia/Singapore'
            });

            const messageHTML = `
                <div class="cc-message cc-${sender}">
                    <div class="cc-avatar cc-${sender}">${avatar}</div>
                    <div class="cc-bubble">
                        ${this.formatMessage(text)}
                        <div class="cc-timestamp">${timestamp}</div>
                    </div>
                </div>
            `;

            // Insert message at the end and scroll to show the latest message
            messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
            this.scrollToLatestMessage(); // Scroll to show the beginning of the latest message
        }

        // Add message with buttons support
        addMessageWithButtons(text, sender, buttons = []) {
            const messagesContainer = document.getElementById('cc-messages');
            if (!messagesContainer) return;

            const config = this.clientConfig;
            const logoUrl = config.branding?.logo_url || '/static/media/images/CleverCompanion-logo.png';
            
            // Use cached profile picture URL or initialize cache
            if (!this.cachedUserAvatarUrl) {
                this.cachedUserAvatarUrl = `${window.DOMAIN || 'http://localhost'}:${window.BACKEND_PORT || '8000'}/static/boy.png`;
            }
            
            const avatar = sender === 'bot' ? `<img src="${logoUrl}" alt="Bot" />` : `<img src="${this.cachedUserAvatarUrl}" alt="User" style="width: 20px; height: 20px; border-radius: 50%; object-fit: cover;" />`;
            // Generate timestamp in Singapore timezone
            const now = new Date();
            const timestamp = now.toLocaleTimeString('en-SG', { 
                hour: '2-digit', 
                minute: '2-digit',
                hour12: true,
                timeZone: 'Asia/Singapore'
            });

            // Generate buttons HTML if buttons exist
            let buttonsHTML = '';
            if (buttons && buttons.length > 0) {
                buttonsHTML = '<div class="cc-buttons">';
                buttons.forEach((button, index) => {
                    const buttonTitle = button.title || button.text || 'Button';
                    const buttonPayload = button.payload || button.title || button.text;
                    buttonsHTML += `<button class="cc-button" onclick="window.cleverCompanionWidget.sendButtonPayload('${buttonPayload}')">${buttonTitle}</button>`;
                });
                buttonsHTML += '</div>';
            }

            const messageHTML = `
                <div class="cc-message cc-${sender}">
                    <div class="cc-avatar cc-${sender}">${avatar}</div>
                    <div class="cc-bubble">
                        ${this.formatMessage(text)}
                        ${buttonsHTML}
                        <div class="cc-timestamp">${timestamp}</div>
                    </div>
                </div>
            `;

            // Insert message at the end and scroll to show the latest message
            messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
            this.scrollToLatestMessage();
        }

        // Handle button click and send payload with enhanced anti-double-click protection
        sendButtonPayload(payload) {
            // Enhanced double-click prevention with timestamp tracking
            const now = Date.now();
            const minClickInterval = 1000; // Minimum 1 second between clicks
            
            // Check if we're already processing or if click is too soon
            if (this.isProcessingButton || (this.lastButtonClickTime && (now - this.lastButtonClickTime) < minClickInterval)) {
                console.log('[ANTI-SPAM] Button click ignored - too frequent or already processing');
                return;
            }
            
            // Update last click timestamp and set processing flag
            this.lastButtonClickTime = now;
            this.isProcessingButton = true;
            
            // Check if payload is for auto-fill functionality
            if (payload.startsWith('autofill:')) {
                // Extract the text to auto-fill
                const autoFillText = payload.replace('autofill:', '');
                
                // Get the input element and set its value
                const input = document.getElementById('cc-input');
                if (input) {
                    input.value = autoFillText;
                    input.focus(); // Focus on the input for user convenience
                }
                
                // Reset processing flag with delay to prevent rapid auto-fill clicks
                setTimeout(() => {
                    this.isProcessingButton = false;
                }, 500);
                // Don't send this as a message to Rasa
                return;
            }
            
            // Disable all buttons immediately with visual feedback
            const buttons = document.querySelectorAll('.cc-button');
            buttons.forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.4';
                btn.style.pointerEvents = 'none'; // Extra protection
                btn.style.cursor = 'not-allowed';
            });
            
            // Add user message showing the selected option
            this.addMessage(payload, 'user');
            
            // Send the payload to Rasa through proxy with timeout protection
            const sendPromise = this.sendMessageToRasa(payload);
            
            // Set a maximum timeout for the request
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Request timeout')), 30000); // 30 second timeout
            });
            
            Promise.race([sendPromise, timeoutPromise])
                .catch(error => {
                    console.error('Error or timeout in sendMessageToRasa:', error);
                    this.addMessage('Request timed out. Please try again.', 'bot');
                })
                .finally(() => {
                    // Reset processing flag and re-enable buttons after response
                    setTimeout(() => {
                        this.isProcessingButton = false;
                        buttons.forEach(btn => {
                            btn.disabled = false;
                            btn.style.opacity = '1';
                            btn.style.pointerEvents = 'auto';
                            btn.style.cursor = 'pointer';
                        });
                    }, 500); // Additional 500ms delay to prevent rapid re-clicking
                });
        }

        // Send message through integrated multi-tenant chat handler
        sendMessageToRasa(text) {
            this.showTypingIndicator();
            
            // Process chat request directly instead of using proxy
            this.processChatRequest(text)
                .then(responses => {
                    this.hideTypingIndicator();
                    this.handleChatResponse(responses);
                })
                .catch(error => {
                    this.hideTypingIndicator();
                    console.error('Error processing chat request:', error);
                    this.addMessage('I\'m experiencing technical difficulties. Please try again in a moment.', 'bot');
                });
        }

        // Process chat request directly (replaces multi_tenant_chat.py functionality)
        async processChatRequest(message) {
            try {
                // Determine client context
                const clientContext = await this.determineClientContext();
                
                // Send request to RASA
                const rasaResponse = await this.sendToRasa(message, clientContext);
                
                // Process RASA response
                const processedResponse = await this.processRasaResponse(rasaResponse, clientContext);
                
                // Store conversation
                await this.storeConversation(message, processedResponse);
                
                return processedResponse;
            } catch (error) {
                console.error('Error in processChatRequest:', error);
                throw error;
            }
        }

        // Determine client context for chat processing
        async determineClientContext() {
            return {
                client_id: this.clientId,
                domain: window.location.hostname,
                session_id: this.sessionId,
                config: this.clientConfig
            };
        }

        // Send message directly to RASA
        async sendToRasa(message, clientContext) {
            const rasaPayload = {
                sender: clientContext.session_id,
                message: message,
                metadata: {
                    client_id: clientContext.client_id,
                    domain: clientContext.domain,
                    timestamp: new Date().toISOString()
                }
            };

            const response = await fetch('http://localhost:5005/webhooks/rest/webhook', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(rasaPayload)
            });

            if (!response.ok) {
                throw new Error(`RASA request failed: ${response.status}`);
            }

            return await response.json();
        }

        // Process RASA response with client-specific information
        async processRasaResponse(rasaResponse, clientContext) {
            const processedResponses = [];
            
            for (const response of rasaResponse) {
                let processedResponse = { ...response };
                
                // Replace dynamic information with client-specific data
                if (response.text) {
                    processedResponse.text = await this.replaceDynamicInfo(response.text, clientContext);
                }
                
                processedResponses.push(processedResponse);
            }
            
            return processedResponses;
        }

        // Replace dynamic information in responses
        async replaceDynamicInfo(text, clientContext) {
            let processedText = text;
            
            // Replace client-specific placeholders
            const replacements = {
                '{company_name}': clientContext.config.branding?.title || 'Our Company',
                '{contact_phone}': clientContext.config.contact?.phone || 'N/A',
                '{contact_email}': clientContext.config.contact?.email || 'N/A',
                '{website_url}': clientContext.config.contact?.website || window.location.origin
            };
            
            for (const [placeholder, value] of Object.entries(replacements)) {
                processedText = processedText.replace(new RegExp(placeholder, 'g'), value);
            }
            
            return processedText;
        }

        // Handle processed chat response
        handleChatResponse(responses) {
            if (!Array.isArray(responses)) {
                responses = [responses];
            }
            
            responses.forEach(response => {
                if (typeof response === 'string') {
                    // Old format - just text
                    this.addMessage(response, 'bot');
                } else if (typeof response === 'object') {
                    // New format - object with text, buttons, and custom fields
                    const text = response.text || '';
                    const buttons = response.buttons || [];
                    const custom = response.custom || {};
                    
                    // Handle autofill functionality
                    if (custom.autofill) {
                        const inputElement = document.getElementById('cc-input');
                        if (inputElement) {
                            inputElement.value = custom.autofill;
                            inputElement.focus();
                        }
                    }
                    
                    if (buttons.length > 0) {
                        // Message with buttons
                        this.addMessageWithButtons(text, 'bot', buttons);
                    } else if (text) {
                        // Regular message
                        this.addMessage(text, 'bot');
                    }
                }
            });
        }

        // Store conversation using unified backend session management
        async storeConversation(userMessage, botResponses) {
            try {
                // Store user message first
                await this.storeMessage(userMessage, 'user');
                
                // Store each bot response separately
                if (Array.isArray(botResponses)) {
                    for (const response of botResponses) {
                        const responseText = typeof response === 'string' ? response : response.text || '';
                        if (responseText) {
                            await this.storeMessage(responseText, 'bot');
                        }
                    }
                } else if (botResponses) {
                    const responseText = typeof botResponses === 'string' ? botResponses : botResponses.text || '';
                    if (responseText) {
                        await this.storeMessage(responseText, 'bot');
                    }
                }
            } catch (error) {
                console.error('Error storing conversation:', error);
                // Don't throw error as this shouldn't break the chat flow
            }
        }
        
        // Store individual message with correct format for unified API
        async storeMessage(message, messageType) {
            try {
                const messageData = {
                    session_id: this.sessionId,
                    message: message,
                    message_type: messageType, // 'user' or 'bot'
                    metadata: {
                        client_id: this.clientId,
                        domain: window.location.hostname,
                        timestamp: new Date().toISOString()
                    }
                };
                
                // Use new unified conversation API endpoint
                await fetch(`${this.apiUrl.replace('/api/widget', '/api')}/unified/conversations/store`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Client-Domain': window.location.hostname
                    },
                    body: JSON.stringify(messageData)
                });
            } catch (error) {
                console.error('Error storing message:', error);
                // Fallback to legacy endpoint for backward compatibility
                try {
                    const legacyData = {
                        client_id: this.clientId,
                        session_id: this.sessionId,
                        message: message,
                        sender: messageType,
                        timestamp: new Date().toISOString(),
                        domain: window.location.hostname
                    };
                    
                    await fetch(`${this.apiUrl}/conversations/store`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(legacyData)
                    });
                } catch (fallbackError) {
                    console.error('Fallback message storage also failed:', fallbackError);
                    // Don't throw error as this shouldn't break the chat flow
                }
            }
        }

        formatMessage(text) {
            const result = text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/_(.*?)_/g, '<em>$1</em>')
                .replace(/\n\n/g, '<br><br>') // Handle double newlines for empty lines
                .replace(/\n/g, '<br>'); // Handle single newlines
            
            return result;
        }

        showTypingIndicator() {
            const messagesContainer = document.getElementById('cc-messages');
            if (!messagesContainer) return;
            
            this.hideTypingIndicator();
            
            const config = this.clientConfig;
            const logoUrl = config.branding?.logo_url || '/static/media/images/CleverCompanion-logo.png';
            
            const typingHTML = `
                <div class="cc-message cc-bot cc-typing-message">
                    <div class="cc-avatar cc-bot">
                        <img src="${logoUrl}" alt="Bot" />
                    </div>
                    <div class="cc-bubble">
                        <div class="cc-typing">
                            <div class="cc-typing-dot"></div>
                            <div class="cc-typing-dot"></div>
                            <div class="cc-typing-dot"></div>
                        </div>
                    </div>
                </div>
            `;

            messagesContainer.insertAdjacentHTML('beforeend', typingHTML);
            this.scrollToLatestMessage(); // Scroll to show the latest message
        }

        hideTypingIndicator() {
            const typingMessage = document.querySelector('.cc-typing-message');
            if (typingMessage) {
                typingMessage.remove();
            }
        }

        scrollToBottom() {
            const messagesContainer = document.getElementById('cc-messages');
            if (messagesContainer) {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        }

        scrollToTop() {
            const messagesContainer = document.getElementById('cc-messages');
            if (messagesContainer) {
                messagesContainer.scrollTop = 0;
            }
        }

        scrollToLatestMessage() {
            const messagesContainer = document.getElementById('cc-messages');
            if (messagesContainer) {
                const messages = messagesContainer.querySelectorAll('.cc-message');
                if (messages.length > 0) {
                    const latestMessage = messages[messages.length - 1];
                    // Scroll to show the latest message at the top of the visible area
                    latestMessage.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        }

        // Save chat history to localStorage - simplified with backend session management
        saveChatHistory() {
            // Simplified session validation - backend manages session lifecycle
            
            const messagesContainer = document.getElementById('cc-messages');
            if (!messagesContainer) return;
            
            const messages = [];
            const messageElements = messagesContainer.querySelectorAll('.cc-message:not(.cc-typing-message)');
            
            messageElements.forEach(messageEl => {
                const isUser = messageEl.classList.contains('cc-user');
                const bubble = messageEl.querySelector('.cc-bubble');
                if (bubble) {
                    // Get text content without timestamp and buttons
                    const timestamp = bubble.querySelector('.cc-timestamp');
                    
                    // Clone bubble to extract clean text content
                    const bubbleClone = bubble.cloneNode(true);
                    const clonedTimestamp = bubbleClone.querySelector('.cc-timestamp');
                    const clonedButtons = bubbleClone.querySelector('.cc-buttons');
                    
                    // Remove timestamp and buttons from clone to get clean content
                    if (clonedTimestamp && clonedTimestamp.parentNode) {
                        clonedTimestamp.parentNode.removeChild(clonedTimestamp);
                    }
                    if (clonedButtons && clonedButtons.parentNode) {
                        clonedButtons.parentNode.removeChild(clonedButtons);
                    }
                    
                    // Store only plain text content
                    messages.push({
                        text: bubbleClone.textContent.trim(), // Store only plain text
                        sender: isUser ? 'user' : 'bot',
                        timestamp: timestamp ? timestamp.textContent : new Date().toLocaleTimeString('en-SG', { 
                            hour: '2-digit', 
                            minute: '2-digit',
                            hour12: true,
                            timeZone: 'Asia/Singapore'
                        })
                    });
                }
            });
            
            localStorage.setItem('cc_chat_history', JSON.stringify(messages));
            // Update session timestamp on activity
            this.updateSessionTimestamp();
        }

        // Load chat history from localStorage - simplified with backend session management
        loadChatHistory() {
            // Simplified session validation - backend manages session lifecycle
            
            const savedHistory = localStorage.getItem('cc_chat_history');
            if (!savedHistory) return;
            
            try {
                const messages = JSON.parse(savedHistory);
                const messagesContainer = document.getElementById('cc-messages');
                if (!messagesContainer) return;
                
                // Clear existing messages except welcome message
                const existingMessages = messagesContainer.querySelectorAll('.cc-message');
                existingMessages.forEach(msg => {
                    if (!msg.innerHTML.includes(this.clientConfig.welcomeMessage)) {
                        msg.remove();
                    }
                });
                
                // Restore messages with plain text content only
                for (const message of messages) {
                    if (message.sender && message.timestamp && message.text) {
                        this.addMessage(message.text, message.sender);
                    }
                }
                
                // Scroll to top after loading for better UX
                setTimeout(() => {
                    this.scrollToTop();
                }, 100);
                
            } catch (error) {
                console.error('Error loading chat history:', error);
                // Clear corrupted data
                localStorage.removeItem('cc_chat_history');
            }
        }
        



    }

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

    window.enlargeChart = enlargeChart;

    // Initialize widget when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.cleverCompanionWidget = new MultiTenantChatWidget();
        });
    } else {
        window.cleverCompanionWidget = new MultiTenantChatWidget();
    }
})();