/**
 * CleverCompanion Page-Specific JavaScript
 * Contains animations, smooth scrolling, and page interactions
 * Separate from widget functionality to keep embed code clean
 */

(function() {
    'use strict';

    // Page functionality
    window.CleverCompanionPage = {
        // Start chat function
        startChat: function() {
            if (window.CleverCompanionWidget) {
                window.CleverCompanionWidget.open();
            }
        },
        
        // Quick action function
        quickAction: function(action) {
            if (window.CleverCompanionWidget) {
                window.CleverCompanionWidget.open();
                setTimeout(() => {
                    window.CleverCompanionWidget.sendMessage(action);
                }, 500);
            }
        },
        
        // Smooth scroll to demo section
        scrollToDemo: function() {
            const demoSection = document.getElementById('demo-section');
            if (demoSection) {
                demoSection.scrollIntoView({ 
                    behavior: 'smooth' 
                });
            }
        },
        
        // Initialize page animations and interactions
        init: function() {
            this.setupScrollAnimations();
            this.setupSmoothScrolling();
            this.setupCardHoverEffects();
        },
        
        // Setup scroll-triggered animations
        setupScrollAnimations: function() {
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };
            
            const observer = new IntersectionObserver(function(entries) {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                        entry.target.classList.add('animated');
                    }
                });
            }, observerOptions);
            
            // Observe all cards and animated elements
            document.querySelectorAll('.card-hover, .animate-on-scroll').forEach(element => {
                element.style.opacity = '0';
                element.style.transform = 'translateY(20px)';
                element.style.transition = 'all 0.6s ease';
                observer.observe(element);
            });
        },
        
        // Setup smooth scrolling for anchor links
        setupSmoothScrolling: function() {
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function(e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                });
            });
        },
        
        // Setup card hover effects
        setupCardHoverEffects: function() {
            document.querySelectorAll('.card-hover').forEach(card => {
                card.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-5px) scale(1.02)';
                    this.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.15)';
                });
                
                card.addEventListener('mouseleave', function() {
                    this.style.transform = 'translateY(0) scale(1)';
                    this.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.1)';
                });
            });
        },
        
        // Add parallax scrolling effect
        setupParallaxScrolling: function() {
            window.addEventListener('scroll', function() {
                const scrolled = window.pageYOffset;
                const parallaxElements = document.querySelectorAll('.parallax');
                
                parallaxElements.forEach(element => {
                    const speed = element.dataset.speed || 0.5;
                    const yPos = -(scrolled * speed);
                    element.style.transform = `translateY(${yPos}px)`;
                });
            });
        },
        
        // Add typing animation effect
        typeWriter: function(element, text, speed = 100) {
            let i = 0;
            element.innerHTML = '';
            
            function type() {
                if (i < text.length) {
                    element.innerHTML += text.charAt(i);
                    i++;
                    setTimeout(type, speed);
                }
            }
            
            type();
        },
        
        // Add fade-in animation for elements
        fadeInElements: function(selector, delay = 100) {
            const elements = document.querySelectorAll(selector);
            elements.forEach((element, index) => {
                setTimeout(() => {
                    element.style.opacity = '1';
                    element.style.transform = 'translateY(0)';
                }, index * delay);
            });
        },
        
        // Add loading animation
        showLoading: function(element) {
            element.innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <p>Loading...</p>
                </div>
            `;
        },
        
        // Hide loading animation
        hideLoading: function(element, content) {
            element.innerHTML = content;
        }
    };
    
    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            window.CleverCompanionPage.init();
        });
    } else {
        window.CleverCompanionPage.init();
    }
    
    // Expose global functions for backward compatibility
    window.startChat = window.CleverCompanionPage.startChat;
    window.quickAction = window.CleverCompanionPage.quickAction;
    window.scrollToDemo = window.CleverCompanionPage.scrollToDemo;
    
})();

// Add CSS for loading spinner
const pageStyles = `
    .loading-spinner {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px;
    }
    
    .spinner {
        width: 40px;
        height: 40px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .card-hover {
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .animate-on-scroll {
        transition: all 0.6s ease;
    }
    
    .parallax {
        transition: transform 0.1s ease-out;
    }
`;

// Inject page-specific styles
if (!document.getElementById('cc-page-styles')) {
    const style = document.createElement('style');
    style.id = 'cc-page-styles';
    style.textContent = pageStyles;
    document.head.appendChild(style);
}