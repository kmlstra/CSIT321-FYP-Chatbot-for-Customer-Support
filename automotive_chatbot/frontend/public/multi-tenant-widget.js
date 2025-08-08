/**
 * CleverCompanion Multi-tenant Widget
 * Dynamically configures based on client settings
 */

(function() {
    'use strict';

    class MultiTenantChatWidget {
        constructor() {
            this.config = window.CleverCompanionConfig || {};
            this.clientId = this.config.clientId;
            this.apiUrl = this.config.apiUrl || 'http://localhost:8000/api/widget';
            this.sessionId = this.generateSessionId();
            this.isOpen = false;
            this.messages = [];
            
            this.init();
        }

        async init() {
            // Fetch client configuration
            await this.loadClientConfig();
            
            // Create widget elements
            this.createWidget();
            
            // Apply client branding
            this.applyBranding();
            
            // Add welcome message
            this.addWelcomeMessage();
        }

        async loadClientConfig() {
            try {
                const response = await fetch(`${this.apiUrl}/config/${this.clientId}`);
                if (response.ok) {
                    const clientConfig = await response.json();
                    this.config = { ...this.config, ...clientConfig };
                }
            } catch (error) {
                console.error('Failed to load client config:', error);
            }
        }

        createWidget() {
            // Create container
            this.container = document.createElement('div');
            this.container.id = 'cc-chatbot-container';
            this.container.innerHTML = `
                <div class="cc-header">
                    <div class="cc-logo">
                        <img src="${this.config.branding?.logo_url || ''}" alt="Logo" onerror="this.style.display='none'">
                    </div>
                    <div>
                        <h3>${this.config.branding?.company_name || 'CleverCompanion'}</h3>
                        <p>Your automotive assistant</p>
                    </div>
                </div>
                <div id="cc-messages" class="cc-messages"></div>
                <div class="cc-input-area">
                    <div class="cc-input-container">
                        <textarea id="cc-input" placeholder="Type your message..." rows="1"></textarea>
                        <button id="cc-send-btn">➤</button>
                    </div>
                </div>
            `;

            // Create toggle button
            this.toggleBtn = document.createElement('button');
            this.toggleBtn.id = 'cc-toggle';
            this.toggleBtn.innerHTML = '💬';

            // Create close button
            this.closeBtn = document.createElement('button');
            this.closeBtn.id = 'cc-close-btn';
            this.closeBtn.innerHTML = '✕';

            // Add to page
            document.body.appendChild(this.container);
            document.body.appendChild(this.toggleBtn);
            document.body.appendChild(this.closeBtn);

            // Add event listeners
            this.addEventListeners();

            // Load CSS
            this.loadCSS();
        }

        applyBranding() {
            if (!this.config.branding) return;

            const header = this.container.querySelector('.cc-header');
            const primaryColor = this.config.branding.primary_color || '#4F46E5';
            
            // Apply primary color to header
            header.style.background = `linear-gradient(135deg, ${primaryColor} 0%, ${this.adjustColor(primaryColor, -20)} 100%)`;
            
            // Apply to buttons
            const sendBtn = this.container.querySelector('#cc-send-btn');
            sendBtn.style.background = primaryColor;
            
            const toggleBtn = this.toggleBtn;
            toggleBtn.style.borderColor = primaryColor;
        }

        adjustColor(color, amount) {
            // Simple color adjustment function
            const num = parseInt(color.replace("#", ""), 16);
            const amt = Math.round(2.55 * amount);
            const R = (num >> 16) + amt;
            const G = (num >> 8 & 0x00FF) + amt;
            const B = (num & 0x0000FF) + amt;
            return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
                (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
                (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1);
        }

        addEventListeners() {
            // Toggle widget
            this.toggleBtn.addEventListener('click', () => this.toggle());
            this.closeBtn.addEventListener('click', () => this.close());

            // Send message
            const sendBtn = this.container.querySelector('#cc-send-btn');
            const input = this.container.querySelector('#cc-input');
            
            sendBtn.addEventListener('click', () => this.sendMessage());
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        addWelcomeMessage() {
            const welcomeMessage = this.config.welcome_message || 
                `Hello! Welcome to ${this.config.branding?.company_name || 'our automotive service'}. How can I help you today?`;
            
            this.addMessage(welcomeMessage, 'bot');
        }

        async sendMessage() {
            const input = this.container.querySelector('#cc-input');
            const message = input.value.trim();
            
            if (!message) return;

            // Add user message
            this.addMessage(message, 'user');
            input.value = '';

            // Show typing indicator
            this.showTyping();

            try {
                // Send to backend
                const response = await fetch(`${this.apiUrl}/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Client-Domain': window.location.hostname
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: this.sessionId,
                        client_id: this.clientId,
                        user_info: {
                            url: window.location.href,
                            user_agent: navigator.userAgent
                        }
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    this.hideTyping();
                    this.addMessage(data.response, 'bot');
                } else {
                    throw new Error('Failed to get response');
                }
            } catch (error) {
                this.hideTyping();
                this.addMessage('Sorry, I\'m having trouble connecting. Please try again later.', 'bot');
                console.error('Chat error:', error);
            }
        }

        addMessage(text, sender) {
            const messagesContainer = this.container.querySelector('#cc-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `cc-message cc-${sender}`;
            
            const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            messageDiv.innerHTML = `
                <div class="cc-avatar cc-${sender}">
                    ${sender === 'bot' ? '🤖' : '👤'}
                </div>
                <div class="cc-bubble">
                    ${text.replace(/\n/g, '<br>')}
                    <div class="cc-timestamp">${timestamp}</div>
                </div>
            `;

            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        showTyping() {
            const messagesContainer = this.container.querySelector('#cc-messages');
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
        }

        close() {
            this.container.classList.remove('cc-open');
            this.closeBtn.classList.remove('cc-visible');
            this.toggleBtn.style.display = 'flex';
            this.isOpen = false;
        }

        generateSessionId() {
            return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
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
    }

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            new MultiTenantChatWidget();
        });
    } else {
        new MultiTenantChatWidget();
    }

    // Expose widget globally
    window.CleverCompanionWidget = MultiTenantChatWidget;
})();