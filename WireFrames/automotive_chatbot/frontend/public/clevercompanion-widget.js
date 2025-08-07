/**
 * CleverCompanion Multi-tenant Chatbot Widget
 * Dynamically configures based on client settings from database
 * Version: 3.0 - Multi-tenant SaaS Ready
 */

(function() {
    'use strict';

    class CleverCompanionWidget {
        constructor() {
            this.config = window.CleverCompanionConfig || {};
            this.clientId = this.config.clientId;
            this.apiUrl = this.config.apiUrl || 'http://localhost:8000/api/widget';
            this.sessionId = this.generateSessionId();
            this.userId = this.generateUserId();
            this.isOpen = false;
            this.messages = [];
            this.isProcessing = false;
            this.lastActionTime = 0;
            this.debounceDelay = 1500; // 1.5 second debounce
            this.actionCooldown = 3000; // 3 second cooldown
            
            this.init();
        }

        async init() {
            try {
                // Load client configuration from backend
                await this.loadClientConfig();
                
                // Create widget elements
                this.createWidget();
                
                // Apply client-specific branding
                this.applyClientBranding();
                
                // Add event listeners
                this.addEventListeners();
                
                // Add welcome message
                this.addWelcomeMessage();
                
                console.log('CleverCompanion Widget initialized successfully');
            } catch (error) {
                console.error('Widget initialization failed:', error);
                this.createFallbackWidget();
            }
        }

        async loadClientConfig() {
            if (!this.clientId) {
                throw new Error('No client ID provided');
            }

            try {
                const response = await fetch(`${this.apiUrl}/config/${this.clientId}`);
                if (response.ok) {
                    const clientConfig = await response.json();
                    this.config = { ...this.config, ...clientConfig };
                    console.log('Client config loaded:', this.config);
                } else {
                    throw new Error(`Failed to load client config: ${response.status}`);
                }
            } catch (error) {
                console.error('Failed to load client configuration:', error);
                // Use default config if API fails
                this.config = {
                    ...this.config,
                    branding: {
                        company_name: 'CleverCompanion',
                        primary_color: '#4F46E5',
                        secondary_color: '#7C3AED'
                    },
                    features: {
                        coe_prices: true,
                        loan_calculator: true,
                        test_drive_booking: true,
                        maintenance_tips: true,
                        vehicle_search: true,
                        contact_support: true
                    }
                };
            }
        }

        createWidget() {
            // Load CSS first
            this.loadCSS();

            // Create main container
            this.container = document.createElement('div');
            this.container.id = 'cc-chatbot-container';
            this.container.className = 'cc-chatbot-container';

            // Create widget HTML with client branding
            const companyName = this.config.branding?.company_name || 'CleverCompanion';
            const logoUrl = this.config.branding?.logo_url;

            this.container.innerHTML = `
                <div class="cc-header">
                    <div class="cc-header-content">
                        ${logoUrl ? `
                            <div class="cc-logo">
                                <img src="${logoUrl}" alt="${companyName} Logo" onerror="this.style.display='none'">
                            </div>
                        ` : `
                            <div class="cc-logo">
                                <span>🚗</span>
                            </div>
                        `}
                        <div class="cc-header-text">
                            <h3>${companyName}</h3>
                            <p>Your automotive assistant</p>
                        </div>
                    </div>
                </div>
                <div id="cc-messages" class="cc-messages"></div>
                <div class="cc-input-area">
                    <button id="cc-menu-btn" class="cc-menu-btn" title="Quick Options">☰</button>
                    <div class="cc-input-container">
                        <textarea id="cc-input" placeholder="Ask about COE prices, vehicles, loans..." rows="1"></textarea>
                        <button id="cc-send-btn" class="cc-send-btn" title="Send Message">➤</button>
                    </div>
                </div>
                <div id="cc-menu-dropdown" class="cc-menu-dropdown">
                    <div class="cc-menu-item" data-action="COE Prices">💰 COE Prices</div>
                    <div class="cc-menu-item" data-action="Test Drive">🚗 Test Drive</div>
                    <div class="cc-menu-item" data-action="Maintenance">🔧 Maintenance</div>
                    <div class="cc-menu-item" data-action="Contact Us">📞 Contact</div>
                    <div class="cc-menu-item" data-action="Help">❓ Help</div>
                </div>
            `;

            // Create toggle button
            this.toggleBtn = document.createElement('button');
            this.toggleBtn.id = 'cc-toggle';
            this.toggleBtn.className = 'cc-toggle';
            this.toggleBtn.innerHTML = logoUrl ? 
                `<img src="${logoUrl}" alt="Chat" onerror="this.innerHTML='💬'">` : 
                '💬';
            this.toggleBtn.title = `Chat with ${companyName}`;

            // Create close button
            this.closeBtn = document.createElement('button');
            this.closeBtn.id = 'cc-close-btn';
            this.closeBtn.className = 'cc-close-btn';
            this.closeBtn.innerHTML = '✕';
            this.closeBtn.title = 'Close Chat';

            // Add to page
            document.body.appendChild(this.container);
            document.body.appendChild(this.toggleBtn);
            document.body.appendChild(this.closeBtn);
        }

        applyClientBranding() {
            if (!this.config.branding) return;

            const primaryColor = this.config.branding.primary_color || '#4F46E5';
            const secondaryColor = this.config.branding.secondary_color || '#7C3AED';

            // Apply colors to header
            const header = this.container.querySelector('.cc-header');
            if (header) {
                header.style.background = `linear-gradient(135deg, ${primaryColor} 0%, ${secondaryColor} 100%)`;
            }

            // Apply colors to buttons
            const sendBtn = this.container.querySelector('#cc-send-btn');
            if (sendBtn) {
                sendBtn.style.background = `linear-gradient(135deg, ${primaryColor} 0%, ${secondaryColor} 100%)`;
            }

            // Apply colors to toggle button
            if (this.toggleBtn) {
                this.toggleBtn.style.borderColor = primaryColor;
                this.toggleBtn.style.background = `linear-gradient(135deg, ${primaryColor} 0%, ${secondaryColor} 100%)`;
            }
        }

        addEventListeners() {
            // Toggle widget
            this.toggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggle();
            });

            // Close widget
            this.closeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.close();
            });

            // Send message
            const sendBtn = this.container.querySelector('#cc-send-btn');
            const input = this.container.querySelector('#cc-input');
            
            sendBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.sendMessage();
            });

            // Input handling with auto-resize
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            input.addEventListener('input', () => {
                this.autoResizeTextarea();
            });

            // Menu functionality
            const menuBtn = this.container.querySelector('#cc-menu-btn');
            const menuDropdown = this.container.querySelector('#cc-menu-dropdown');
            
            menuBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                menuDropdown.classList.toggle('cc-show');
            });

            // Menu item clicks
            const menuItems = this.container.querySelectorAll('.cc-menu-item');
            menuItems.forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    const action = item.getAttribute('data-action');
                    this.sendMessage(action);
                    menuDropdown.classList.remove('cc-show');
                });
            });

            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!menuBtn.contains(e.target) && !menuDropdown.contains(e.target)) {
                    menuDropdown.classList.remove('cc-show');
                }
            });
        }

        addWelcomeMessage() {
            const companyName = this.config.branding?.company_name || 'CleverCompanion';
            const welcomeMessage = this.config.welcome_message || 
                `👋 Hello! Welcome to ${companyName}. I'm your automotive assistant. How can I help you today?`;
            
            this.addMessage(welcomeMessage, 'bot');
        }

        async sendMessage(messageText = null) {
            // Prevent double-clicking and rapid submissions
            const now = Date.now();
            if (this.isProcessing || (now - this.lastActionTime) < this.debounceDelay) {
                console.log('Message blocked: Too soon after last action');
                return;
            }

            const input = this.container.querySelector('#cc-input');
            const message = messageText || input.value.trim();
            
            if (!message) return;

            // Set processing state
            this.isProcessing = true;
            this.lastActionTime = now;

            // Add user message
            this.addMessage(message, 'user');
            
            // Clear input and reset size
            if (!messageText) {
                input.value = '';
                this.resetTextareaSize();
            }

            // Show typing indicator
            this.showTyping();

            try {
                // Send to multi-tenant backend
                const response = await fetch(`${this.apiUrl}/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Client-Domain': window.location.hostname,
                        'X-Client-ID': this.clientId
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: this.sessionId,
                        user_id: this.userId,
                        client_id: this.clientId,
                        user_info: {
                            url: window.location.href,
                            user_agent: navigator.userAgent,
                            timestamp: new Date().toISOString()
                        }
                    })
                });

                this.hideTyping();

                if (response.ok) {
                    const data = await response.json();
                    this.addMessage(data.response, 'bot');
                } else {
                    throw new Error(`API Error: ${response.status}`);
                }
            } catch (error) {
                this.hideTyping();
                console.error('Chat error:', error);
                
                const companyName = this.config.branding?.company_name || 'us';
                const fallbackMessage = `I'm having trouble connecting right now. Please contact ${companyName} directly for assistance.`;
                this.addMessage(fallbackMessage, 'bot');
            } finally {
                // Reset processing state after cooldown
                setTimeout(() => {
                    this.isProcessing = false;
                }, this.actionCooldown);
            }
        }

        addMessage(text, sender) {
            const messagesContainer = this.container.querySelector('#cc-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `cc-message cc-${sender}`;
            
            const timestamp = new Date().toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            // Process text for HTML content (buttons, links, etc.)
            const processedText = this.processMessageContent(text);
            
            messageDiv.innerHTML = `
                <div class="cc-avatar cc-${sender}">
                    ${sender === 'bot' ? '🤖' : '👤'}
                </div>
                <div class="cc-bubble">
                    ${processedText}
                    <div class="cc-timestamp">${timestamp}</div>
                </div>
            `;

            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

            // Process any buttons in the message
            this.processMessageButtons(messageDiv);
        }

        processMessageContent(text) {
            // Convert markdown-style formatting to HTML
            return text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\n/g, '<br>')
                .replace(/`(.*?)`/g, '<code>$1</code>');
        }

        processMessageButtons(messageDiv) {
            // Find and activate any buttons in the message
            const buttons = messageDiv.querySelectorAll('button');
            buttons.forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    const onclick = button.getAttribute('onclick');
                    if (onclick) {
                        try {
                            // Safely execute the onclick function
                            eval(onclick);
                        } catch (error) {
                            console.error('Button click error:', error);
                        }
                    }
                });
            });

            // Process Google Maps iframes
            const iframes = messageDiv.querySelectorAll('iframe');
            iframes.forEach(iframe => {
                iframe.style.maxWidth = '100%';
                iframe.style.borderRadius = '8px';
            });
        }

        showTyping() {
            const messagesContainer = this.container.querySelector('#cc-messages');
            
            // Remove existing typing indicator
            const existingTyping = messagesContainer.querySelector('#cc-typing-indicator');
            if (existingTyping) {
                existingTyping.remove();
            }

            const typingDiv = document.createElement('div');
            typingDiv.id = 'cc-typing-indicator';
            typingDiv.className = 'cc-typing-indicator cc-show';
            typingDiv.innerHTML = `
                <div class="cc-avatar cc-bot">🤖</div>
                <div class="cc-typing">
                    <div class="cc-typing-dot"></div>
                    <div class="cc-typing-dot"></div>
                    <div class="cc-typing-dot"></div>
                </div>
            `;
            
            messagesContainer.appendChild(typingDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        hideTyping() {
            const typingIndicator = this.container.querySelector('#cc-typing-indicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
        }

        autoResizeTextarea() {
            const textarea = this.container.querySelector('#cc-input');
            if (textarea) {
                textarea.style.height = 'auto';
                textarea.style.height = Math.min(textarea.scrollHeight, 80) + 'px';
            }
        }

        resetTextareaSize() {
            const textarea = this.container.querySelector('#cc-input');
            if (textarea) {
                textarea.style.height = '40px'; // Reset to original size
            }
        }

        toggle() {
            if (this.isOpen) {
                this.close();
            } else {
                this.open();
            }
        }

        open() {
            this.container.classList.add('cc-open');
            this.closeBtn.classList.add('cc-visible');
            this.toggleBtn.style.display = 'none';
            this.isOpen = true;

            // Focus on input
            setTimeout(() => {
                const input = this.container.querySelector('#cc-input');
                if (input) input.focus();
            }, 300);
        }

        close() {
            this.container.classList.remove('cc-open');
            this.closeBtn.classList.remove('cc-visible');
            this.toggleBtn.style.display = 'flex';
            this.isOpen = false;

            // Hide menu if open
            const menu = this.container.querySelector('#cc-menu-dropdown');
            if (menu) {
                menu.classList.remove('cc-show');
            }
        }

        generateSessionId() {
            return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
        }

        generateUserId() {
            // Check if user ID exists in localStorage
            let userId = localStorage.getItem('cc_user_id');
            if (!userId) {
                userId = 'user_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
                localStorage.setItem('cc_user_id', userId);
            }
            return userId;
        }

        loadCSS() {
            // Check if CSS is already loaded
            if (document.querySelector('#cc-widget-styles')) return;

            const link = document.createElement('link');
            link.id = 'cc-widget-styles';
            link.rel = 'stylesheet';
            link.href = 'clevercompanion-widget.css';
            document.head.appendChild(link);
        }

        createFallbackWidget() {
            // Create a basic widget if initialization fails
            console.warn('Creating fallback widget due to initialization failure');
            
            this.container = document.createElement('div');
            this.container.innerHTML = `
                <div style="position: fixed; bottom: 20px; right: 20px; background: white; border: 2px solid #4F46E5; border-radius: 10px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 999999;">
                    <h3 style="margin: 0 0 10px 0; color: #4F46E5;">CleverCompanion</h3>
                    <p style="margin: 0; font-size: 14px; color: #666;">Chat widget is temporarily unavailable. Please contact us directly.</p>
                    <button onclick="this.parentElement.remove()" style="position: absolute; top: 5px; right: 10px; background: none; border: none; font-size: 18px; cursor: pointer;">×</button>
                </div>
            `;
            document.body.appendChild(this.container);
        }

        // Public API methods
        static open() {
            if (window.cleverCompanionWidgetInstance) {
                window.cleverCompanionWidgetInstance.open();
            }
        }

        static close() {
            if (window.cleverCompanionWidgetInstance) {
                window.cleverCompanionWidgetInstance.close();
            }
        }

        static sendMessage(message) {
            if (window.cleverCompanionWidgetInstance) {
                window.cleverCompanionWidgetInstance.sendMessage(message);
            }
        }
    }

    // Auto-initialize when DOM is ready
    function initializeWidget() {
        try {
            const widgetInstance = new CleverCompanionWidget();
            window.cleverCompanionWidgetInstance = widgetInstance;
            window.CleverCompanionWidget = {
                open: CleverCompanionWidget.open,
                close: CleverCompanionWidget.close,
                sendMessage: CleverCompanionWidget.sendMessage,
                instance: widgetInstance
            };
        } catch (error) {
            console.error('Widget initialization error:', error);
        }
    }

    // Initialize based on document state
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeWidget);
    } else {
        initializeWidget();
    }

})();