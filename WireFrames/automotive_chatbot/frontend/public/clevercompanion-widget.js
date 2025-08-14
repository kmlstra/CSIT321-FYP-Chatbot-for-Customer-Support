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
            this.apiUrl = this.config.apiUrl || (window.CLEVERCOMPANION_BACKEND_URL || window.BACKEND_URL || (window.DOMAIN || 'http://localhost') + ':8001') + '/api/widget';
            this.sessionId = this.generateSessionId();
            this.isOpen = false;
            this.messages = [];
            this.isProcessing = false;
            this.menuOpen = false;
            this.lastInteractionTime = new Date().toISOString();
            
            // Default configuration (will be overridden by client config)
            this.defaultConfig = {
                title: 'CleverCompanion',
                subtitle: 'Your automotive assistant',
                welcomeMessage: "Hello! I'm your automotive assistant. How can I help you today?",
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
                console.warn('Local storage access failed:', e);
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
            
            console.warn('No valid client ID detected, using default');
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
                console.warn('Failed to store client ID in local storage:', e);
            }
        }

        async init() {
            // Create widget immediately with default config to prevent delay
            this.clientConfig = this.defaultConfig;
            this.createWidget();
            
            // Add welcome message immediately with default config
            this.addWelcomeMessage();
            
            // Start cache preloading in background for faster responses
            this.preloadCache();
            
            // Load client configuration in background and update
            this.loadClientConfig().then(() => {
                this.updateWidgetWithConfig();
                this.applyBranding();
                // Update welcome message with client-specific config if different
                if (this.clientConfig.welcomeMessage !== this.defaultConfig.welcomeMessage) {
                    this.addWelcomeMessage();
                }
            }).catch((error) => {
                console.warn('Failed to load client config, using defaults:', error);
                // Still apply branding with defaults
                this.applyBranding();
            });
        }
        
        // Enhanced client-side caching system
        initClientCache() {
            // Initialize client-side cache with TTL support
            this.clientCache = {
                config: null,
                configExpiry: 0,
                features: null,
                featuresExpiry: 0,
                staticData: new Map(),
                connectionPool: new Map(),
                maxConnections: 5,
                connectionTimeout: 30000 // 30 seconds
            };
            
            // Cache TTL settings (in milliseconds)
            this.cacheTTL = {
                config: 60 * 60 * 1000, // 1 hour for configuration
                features: 30 * 60 * 1000, // 30 minutes for features
                staticData: 24 * 60 * 60 * 1000, // 24 hours for static data
                apiResponses: 5 * 60 * 1000 // 5 minutes for API responses
            };
            
            // Background refresh intervals
            this.refreshIntervals = new Map();
            
            // Start background refresh for critical data
            this.startBackgroundRefresh();
        }
        
        // Start background refresh for critical cached data
        startBackgroundRefresh() {
            // Refresh configuration every 30 minutes
            const configRefresh = setInterval(async () => {
                try {
                    await this.refreshCachedConfig();
                } catch (error) {
                    console.warn('Background config refresh failed:', error);
                }
            }, 30 * 60 * 1000);
            this.refreshIntervals.set('config', configRefresh);
            
            // Refresh features every 15 minutes
            const featuresRefresh = setInterval(async () => {
                try {
                    await this.refreshCachedFeatures();
                } catch (error) {
                    console.warn('Background features refresh failed:', error);
                }
            }, 15 * 60 * 1000);
            this.refreshIntervals.set('features', featuresRefresh);
            
            // Clean up expired cache entries every 5 minutes
            const cacheCleanup = setInterval(() => {
                this.cleanupExpiredCache();
            }, 5 * 60 * 1000);
            this.refreshIntervals.set('cleanup', cacheCleanup);
        }
        
        // Refresh cached configuration in background
        async refreshCachedConfig() {
            try {
                const fetchFn = await this.getPooledConnection(`${this.apiUrl}/config/${this.clientId}`);
                const response = await fetchFn(`${this.apiUrl}/config/${this.clientId}`);
                
                if (response.ok) {
                    const config = await response.json();
                    this.setCachedData('config', config, 'config');
                    console.log('Background config refresh completed');
                }
            } catch (error) {
                console.warn('Background config refresh failed:', error);
            }
        }
        
        // Refresh cached features in background
        async refreshCachedFeatures() {
            try {
                const fetchFn = await this.getPooledConnection(`${this.apiUrl}/features/${this.clientId}`);
                const response = await fetchFn(`${this.apiUrl}/features/${this.clientId}`);
                
                if (response.ok) {
                    const features = await response.json();
                    this.setCachedData('features', features, 'features');
                    console.log('Background features refresh completed');
                }
            } catch (error) {
                console.warn('Background features refresh failed:', error);
            }
        }
        
        // Clean up expired cache entries
        cleanupExpiredCache() {
            try {
                const keys = Object.keys(localStorage);
                const clientPrefix = `cc_cache_${this.clientId}_`;
                const expiryPrefix = `cc_cache_expiry_${this.clientId}_`;
                
                keys.forEach(key => {
                    if (key.startsWith(expiryPrefix)) {
                        const expiry = parseInt(localStorage.getItem(key));
                        if (Date.now() > expiry) {
                            const dataKey = key.replace('expiry_', '');
                            localStorage.removeItem(key);
                            localStorage.removeItem(dataKey);
                        }
                    }
                });
                
                console.log('Cache cleanup completed');
            } catch (error) {
                console.warn('Cache cleanup failed:', error);
            }
        }
        
        // Invalidate specific cache entries
        invalidateCache(keys = []) {
            try {
                if (keys.length === 0) {
                    // Invalidate all cache for this client
                    const allKeys = Object.keys(localStorage);
                    const clientPrefix = `cc_cache_${this.clientId}_`;
                    
                    allKeys.forEach(key => {
                        if (key.startsWith(clientPrefix)) {
                            localStorage.removeItem(key);
                        }
                    });
                    console.log('All cache invalidated for client:', this.clientId);
                } else {
                    // Invalidate specific keys
                    keys.forEach(key => this.removeCachedData(key));
                    console.log('Specific cache keys invalidated:', keys);
                }
            } catch (error) {
                console.warn('Cache invalidation failed:', error);
            }
        }
        
        // Stop background refresh intervals
        stopBackgroundRefresh() {
            this.refreshIntervals.forEach((interval, key) => {
                clearInterval(interval);
                console.log(`Stopped background refresh for: ${key}`);
            });
            this.refreshIntervals.clear();
        }
        
        // Get cached data with TTL validation
        getCachedData(key, type = 'staticData') {
            try {
                const cacheKey = `cc_cache_${this.clientId}_${key}`;
                const expiryKey = `cc_cache_expiry_${this.clientId}_${key}`;
                
                const cachedData = localStorage.getItem(cacheKey);
                const expiry = localStorage.getItem(expiryKey);
                
                if (cachedData && expiry) {
                    const expiryTime = parseInt(expiry);
                    if (Date.now() < expiryTime) {
                        return JSON.parse(cachedData);
                    } else {
                        // Cache expired, remove it
                        this.removeCachedData(key);
                    }
                }
            } catch (error) {
                console.warn('Error reading cached data:', error);
            }
            return null;
        }
        
        // Store data in cache with TTL
        setCachedData(key, data, type = 'staticData') {
            try {
                const cacheKey = `cc_cache_${this.clientId}_${key}`;
                const expiryKey = `cc_cache_expiry_${this.clientId}_${key}`;
                const ttl = this.cacheTTL[type] || this.cacheTTL.staticData;
                const expiry = Date.now() + ttl;
                
                localStorage.setItem(cacheKey, JSON.stringify(data));
                localStorage.setItem(expiryKey, expiry.toString());
            } catch (error) {
                console.warn('Error storing cached data:', error);
            }
        }
        
        // Remove cached data
        removeCachedData(key) {
            try {
                const cacheKey = `cc_cache_${this.clientId}_${key}`;
                const expiryKey = `cc_cache_expiry_${this.clientId}_${key}`;
                localStorage.removeItem(cacheKey);
                localStorage.removeItem(expiryKey);
            } catch (error) {
                console.warn('Error removing cached data:', error);
            }
        }
        
        // Connection pooling for API requests
        async getPooledConnection(url, options = {}) {
            const connectionKey = `${url}_${JSON.stringify(options.headers || {})}`;
            
            // Check if we have an available connection
            if (this.clientCache.connectionPool.has(connectionKey)) {
                const connection = this.clientCache.connectionPool.get(connectionKey);
                if (connection.lastUsed + this.clientCache.connectionTimeout > Date.now()) {
                    connection.lastUsed = Date.now();
                    return connection.fetch;
                } else {
                    // Connection expired, remove it
                    this.clientCache.connectionPool.delete(connectionKey);
                }
            }
            
            // Create new connection if pool not full
            if (this.clientCache.connectionPool.size < this.clientCache.maxConnections) {
                const connection = {
                    fetch: fetch.bind(window),
                    lastUsed: Date.now(),
                    created: Date.now()
                };
                this.clientCache.connectionPool.set(connectionKey, connection);
                return connection.fetch;
            }
            
            // Pool is full, use regular fetch
            return fetch.bind(window);
        }
        
        // Enhanced cache preloading with static data caching
        async preloadCache() {
            try {
                // Initialize client cache system
                this.initClientCache();
                
                // Preload static assets in parallel
                const preloadPromises = [
                    this.preloadServerCache(),
                    this.preloadStaticAssets(),
                    this.preloadFeatureData()
                ];
                
                await Promise.allSettled(preloadPromises);
                console.log('Enhanced cache preloading completed for client:', this.clientId);
            } catch (error) {
                console.warn('Cache preloading error:', error);
                // Don't throw error - widget should work even if cache preloading fails
            }
        }
        
        // Preload server-side cache
        async preloadServerCache() {
            try {
                const cacheApiUrl = this.apiUrl.replace('/api/widget', '/api/cache');
                const fetchFn = await this.getPooledConnection(`${cacheApiUrl}/warm/${this.clientId}`);
                
                const response = await fetchFn(`${cacheApiUrl}/warm/${this.clientId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Client-Domain': window.location.hostname
                    }
                });
                
                if (response.ok) {
                    const result = await response.json();
                    console.log('Server cache preloaded successfully');
                    return result;
                }
            } catch (error) {
                console.warn('Server cache preloading failed:', error);
            }
        }
        
        // Preload static assets (logos, images, etc.)
        async preloadStaticAssets() {
            try {
                const staticAssets = [
                    '/static/media/images/CleverCompanion-logo.png',
                    this.clientConfig?.branding?.logo_url
                ].filter(Boolean);
                
                const preloadPromises = staticAssets.map(async (assetUrl) => {
                    try {
                        // Check if already cached
                        const cached = this.getCachedData(`asset_${assetUrl}`, 'staticData');
                        if (cached) return cached;
                        
                        // Preload image
                        const img = new Image();
                        img.src = assetUrl;
                        
                        return new Promise((resolve) => {
                            img.onload = () => {
                                this.setCachedData(`asset_${assetUrl}`, { loaded: true, url: assetUrl }, 'staticData');
                                resolve({ loaded: true, url: assetUrl });
                            };
                            img.onerror = () => resolve({ loaded: false, url: assetUrl });
                        });
                    } catch (error) {
                        console.warn(`Failed to preload asset ${assetUrl}:`, error);
                    }
                });
                
                await Promise.allSettled(preloadPromises);
                console.log('Static assets preloaded');
            } catch (error) {
                console.warn('Static asset preloading failed:', error);
            }
        }
        
        // Preload feature data
        async preloadFeatureData() {
            try {
                // Check cached features first
                const cachedFeatures = this.getCachedData('features', 'features');
                if (cachedFeatures) {
                    this.clientCache.features = cachedFeatures;
                    return cachedFeatures;
                }
                
                // Load features from API
                const fetchFn = await this.getPooledConnection(`${this.apiUrl}/features/${this.clientId}`);
                const response = await fetchFn(`${this.apiUrl}/features/${this.clientId}`);
                
                if (response.ok) {
                    const features = await response.json();
                    this.setCachedData('features', features, 'features');
                    this.clientCache.features = features;
                    console.log('Feature data preloaded and cached');
                    return features;
                }
            } catch (error) {
                console.warn('Feature data preloading failed:', error);
            }
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
                        <img src="${logoUrl}" alt="${this.clientConfig.branding?.company_name || 'CleverCompanion'}" />
                    </span>
                    ${this.clientConfig.branding?.company_name || 'CleverCompanion'}
                `;
            }
            
            // Update logo in toggle button
            logoElements.forEach(img => {
                const logoUrl = this.clientConfig.branding?.logo_url || '/static/media/images/CleverCompanion-logo.png';
                img.src = logoUrl;
                img.alt = this.clientConfig.branding?.company_name || 'CleverCompanion';
            });
            
            // Update menu items
            if (menuDropdown) {
                menuDropdown.innerHTML = this.generateMenuItems();
            }
            
            // Re-inject CSS with updated branding
            const existingStyle = document.getElementById('cc-widget-styles');
            if (existingStyle) {
                existingStyle.textContent = this.getWidgetCSS();
            }
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
            // Check if session has expired
            if (this.isSessionExpired()) {
                this.clearExpiredSession();
            }
            
            let sessionId = localStorage.getItem('cc_session_id');
            if (!sessionId) {
                sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                localStorage.setItem('cc_session_id', sessionId);
                localStorage.setItem('cc_session_timestamp', Date.now().toString());
            }
            return sessionId;
        }

        updateSessionTimestamp() {
            // Update session timestamp on activity
            localStorage.setItem('cc_session_timestamp', Date.now().toString());
        }

        async loadClientConfig() {
            try {
                // Check cached configuration first
                const cachedConfig = this.getCachedData('config', 'config');
                if (cachedConfig) {
                    this.clientConfig = { ...this.defaultConfig, ...cachedConfig };
                    console.log('Using cached client configuration');
                    return this.clientConfig;
                }
                
                // Load from API with connection pooling
                const fetchFn = await this.getPooledConnection(`${this.apiUrl}/config/${this.clientId}`);
                const response = await fetchFn(`${this.apiUrl}/config/${this.clientId}`);
                
                if (response.ok) {
                    const clientConfig = await response.json();
                    // Cache the configuration
                    this.setCachedData('config', clientConfig, 'config');
                    // Merge with default config
                    this.clientConfig = { ...this.defaultConfig, ...clientConfig };
                    console.log('Client configuration loaded and cached');
                } else {
                    console.warn('Failed to load client config, using defaults');
                    this.clientConfig = this.defaultConfig;
                }
            } catch (error) {
                console.warn('Error loading client config:', error);
                this.clientConfig = this.defaultConfig;
            }
            return this.clientConfig;
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
            style.textContent = this.getWidgetCSS();
            document.head.appendChild(style);
        }

        generateWidgetHTML() {
            const config = this.clientConfig;
            const logoUrl = config.branding?.logo_url || '/static/media/images/CleverCompanion-logo.png';
            
            return `
                <!-- Toggle Button -->
                <button id="cc-toggle" aria-label="Open chat">
                    <img src="${logoUrl}" alt="${config.branding?.company_name || 'CleverCompanion'}" />
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
                                <img src="${logoUrl}" alt="${config.branding?.company_name || 'CleverCompanion'}" />
                            </span>
                            ${config.branding?.company_name || 'CleverCompanion'}
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
                // { icon: '🚗', text: 'Search Vehicle', action: 'Help me search for vehicles by budget, type and brand preferences', enabled: this.clientConfig.features?.vehicle_search },
                { icon: '📅', text: 'Appointment Booking', action: 'I want to book an appointment', enabled: this.clientConfig.features?.appointment_booking },
                // { icon: '🔧', text: 'Maintenance Tips', action: 'Provide vehicle maintenance guidance and service center recommendations', enabled: this.clientConfig.features?.maintenance_tips },
                { icon: '💳', text: 'Loan Calculator', action: 'Calculate car loan with current interest rates and financing options', enabled: this.clientConfig.features?.loan_calculator },
                { icon: '📞', text: 'Contact Us', action: 'I need to contact customer support', enabled: true }, // Mandatory feature - always available
                // { icon: '📝', text: 'Feedback', action: 'I want to provide feedback about the service and suggest improvements', enabled: true },
                { icon: '💬', text: 'Live Support', action: 'I need live support assistance', enabled: this.clientConfig.features?.live_support }
            ];

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
                /* Widget Container */
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

                /* Toggle button */
                #cc-toggle {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background: white;
                    border: 3px solid ${primaryColor};
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

                /* Close button */
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

                /* Header */
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
                    border: 2px solid ${primaryColor};
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
                    background: linear-gradient(135deg, ${primaryColor} 0%, #7C3AED 100%);
                    color: white;
                    border-color: ${primaryColor};
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
                    background: linear-gradient(135deg, ${primaryColor} 0%, #7C3AED 100%);
                    color: white;
                    border: 1px solid ${primaryColor};
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

                /* Menu button */
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


                /* Send button */
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

                .cc-menu-item:first-child {
                    border-radius: 8px 8px 0 0;
                }

                .cc-menu-item:last-child {
                    border-radius: 0 0 8px 8px;
                }

                .cc-menu-dropdown.cc-show {
                    display: block;
                }

                /* Typing indicator */
                .cc-typing {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    padding: 8px 0;
                }

                .cc-typing-dot {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #9ca3af;
                    animation: typingDot 1.4s infinite ease-in-out;
                }

                .cc-typing-dot:nth-child(1) {
                    animation-delay: 0s;
                }

                .cc-typing-dot:nth-child(2) {
                    animation-delay: 0.2s;
                }

                .cc-typing-dot:nth-child(3) {
                    animation-delay: 0.4s;
                }

                @keyframes typingDot {
                    0%, 60%, 100% {
                        transform: translateY(0);
                        opacity: 0.4;
                    }
                    30% {
                        transform: translateY(-10px);
                        opacity: 1;
                    }
                }

                /* Mobile responsiveness */
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
                
                // Load chat history when widget opens
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

        async sendMessage(text) {
            const input = document.getElementById('cc-input');
            const sendBtn = document.getElementById('cc-send-btn');
            
            if (!text.trim()) return;

            // Check if session has expired before sending
            if (this.isSessionExpired()) {
                this.clearExpiredSession();
                this.sessionId = this.generateSessionId();
            }

            // Add user message
            this.addMessage(text, 'user');
            
            // Clear input and disable send button
            if (input) input.value = '';
            if (sendBtn) sendBtn.disabled = true;
            
            // Update session timestamp on activity
            this.updateSessionTimestamp();

            try {
                // First, get immediate acknowledgment with connection pooling
                const fetchFn = await this.getPooledConnection(`${this.apiUrl}/chat/quick-ack`);
                const ackResponse = await fetchFn(`${this.apiUrl}/chat/quick-ack`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Client-Domain': window.location.hostname,
                    },
                    body: JSON.stringify({
                        client_id: this.clientId,
                        session_id: this.sessionId,
                        message: text,
                        timestamp: new Date().toISOString()
                    })
                });

                if (ackResponse.ok) {
                    // Show typing indicator after acknowledgment
                    this.showTypingIndicator();
                    
                    // Now get the streaming response with connection pooling
                    const streamFetchFn = await this.getPooledConnection(`${this.apiUrl}/chat/stream`);
                    const streamResponse = await streamFetchFn(`${this.apiUrl}/chat/stream`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Client-Domain': window.location.hostname,
                        },
                        body: JSON.stringify({
                            client_id: this.clientId,
                            session_id: this.sessionId,
                            message: text,
                            timestamp: new Date().toISOString()
                        })
                    });

                    if (streamResponse.ok) {
                        const reader = streamResponse.body.getReader();
                        const decoder = new TextDecoder();
                        let buffer = '';

                        while (true) {
                            const { done, value } = await reader.read();
                            if (done) break;

                            buffer += decoder.decode(value, { stream: true });
                            const lines = buffer.split('\n');
                            buffer = lines.pop(); // Keep incomplete line in buffer

                            for (const line of lines) {
                                if (line.trim() && line.startsWith('data: ')) {
                                    try {
                                        const data = JSON.parse(line.slice(6));
                                        
                                        if (data.type === 'typing') {
                                            // Keep typing indicator visible
                                            continue;
                                        } else if (data.type === 'response') {
                                            // Hide typing indicator and show response
                                            this.hideTypingIndicator();
                                            this.addMessage(data.content, 'bot');
                                        } else if (data.type === 'error') {
                                            this.hideTypingIndicator();
                                            this.addMessage('I\'m experiencing technical difficulties. Please try again in a moment.', 'bot');
                                        }
                                    } catch (parseError) {
                                        console.warn('Failed to parse streaming data:', parseError);
                                    }
                                }
                            }
                        }
                    } else {
                        // Fallback to regular chat if streaming fails
                        await this.sendMessageFallback(text);
                    }
                } else {
                    // Fallback to regular chat if quick-ack fails
                    await this.sendMessageFallback(text);
                }
            } catch (error) {
                console.error('Error in streaming chat:', error);
                // Fallback to regular chat
                await this.sendMessageFallback(text);
            } finally {
                this.hideTypingIndicator();
                if (sendBtn) sendBtn.disabled = false;
                // Save chat history after message exchange
                this.saveChatHistory();
            }
        }

        // Fallback method for regular chat when streaming fails
        async sendMessageFallback(text) {
            try {
                this.showTypingIndicator();
                
                const fallbackFetchFn = await this.getPooledConnection(`${this.apiUrl}/chat`);
                const response = await fallbackFetchFn(`${this.apiUrl}/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Client-Domain': window.location.hostname,
                    },
                    body: JSON.stringify({
                        client_id: this.clientId,
                        session_id: this.sessionId,
                        message: text,
                        timestamp: new Date().toISOString()
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    
                    // Handle the ChatResponse structure from backend
                    if (data.response) {
                        this.addMessage(data.response, 'bot');
                    } else if (data.responses && data.responses.length > 0) {
                        data.responses.forEach(responseText => {
                            this.addMessage(responseText, 'bot');
                        });
                    } else {
                        this.addMessage('I apologize, but I\'m having trouble understanding your request. Could you please try rephrasing?', 'bot');
                    }
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            } catch (error) {
                console.error('Error in fallback chat:', error);
                this.addMessage('I\'m experiencing technical difficulties. Please try again in a moment.', 'bot');
            }
        }

        addMessage(text, sender) {
            const messagesContainer = document.getElementById('cc-messages');
            if (!messagesContainer) return;

            const config = this.clientConfig;
            const logoUrl = config.branding?.logo_url || '/static/media/images/CleverCompanion-logo.png';
            const userAvatarUrl = '/static/media/images/boy.png';
            const avatar = sender === 'bot' ? `<img src="${logoUrl}" alt="Bot" />` : `<img src="${userAvatarUrl}" alt="User" style="width: 20px; height: 20px; border-radius: 50%; object-fit: cover;" />`;
            const timestamp = new Date().toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit',
                hour12: true 
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

            messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
            this.scrollToBottom();
        }

        formatMessage(text) {
            return text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/_(.*?)_/g, '<em>$1</em>')
                .replace(/\n/g, '<br>');
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
            this.scrollToBottom();
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
                // With column-reverse, newest messages are at the top, so scroll to top
                messagesContainer.scrollTop = 0;
            }
        }

        // Save chat history to localStorage with session validation
        saveChatHistory() {
            // Check if session has expired before saving
            if (this.isSessionExpired()) {
                this.clearExpiredSession();
                return;
            }
            
            const messagesContainer = document.getElementById('cc-messages');
            if (!messagesContainer) return;
            
            const messages = [];
            const messageElements = messagesContainer.querySelectorAll('.cc-message:not(.cc-typing-message)');
            
            messageElements.forEach(messageEl => {
                const isUser = messageEl.classList.contains('cc-user');
                const bubble = messageEl.querySelector('.cc-bubble');
                if (bubble) {
                    // Get text content without timestamp
                    const timestamp = bubble.querySelector('.cc-timestamp');
                    
                    // Clone bubble to extract clean text
                    const bubbleClone = bubble.cloneNode(true);
                    const clonedTimestamp = bubbleClone.querySelector('.cc-timestamp');
                    
                    if (clonedTimestamp && clonedTimestamp.parentNode) {
                        clonedTimestamp.parentNode.removeChild(clonedTimestamp);
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
            this.updateSessionTimestamp();
        }

        // Load chat history from localStorage with session validation
        loadChatHistory() {
            // Check if session has expired before loading
            if (this.isSessionExpired()) {
                this.clearExpiredSession();
                return;
            }
            
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
                
                // Restore messages
                messages.forEach(message => {
                    if (message.sender && message.text && message.timestamp) {
                        this.addMessage(message.text, message.sender);
                    }
                });
                
                // Scroll to bottom after loading
                setTimeout(() => {
                    this.scrollToBottom();
                }, 100);
                
            } catch (error) {
                console.error('Error loading chat history:', error);
                // Clear corrupted data
                localStorage.removeItem('cc_chat_history');
            }
        }


    }

    // Initialize widget when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            const widget = new MultiTenantChatWidget();
            // Auto-open the chatbot when page loads
            setTimeout(() => {
                widget.openWidget();
            }, 1000); // Small delay to ensure widget is fully rendered
        });
    } else {
        const widget = new MultiTenantChatWidget();
        // Auto-open the chatbot when page loads
        setTimeout(() => {
            widget.openWidget();
        }, 1000); // Small delay to ensure widget is fully rendered
    }
})();