/**
 * Page Interactions JavaScript
 * Handles page-specific functionality like smooth scrolling, animations, and page interactions
 * Separate from widget functionality to keep embed code clean
 */

(function() {
    'use strict';

    // Page functionality
    window.startChat = function() {
        if (window.CleverCompanionWidget) {
            window.CleverCompanionWidget.open();
        }
    };

    window.quickAction = function(action) {
        if (window.CleverCompanionWidget) {
            window.CleverCompanionWidget.open();
            setTimeout(() => {
                window.CleverCompanionWidget.sendMessage(action);
            }, 500);
        }
    };

    window.scrollToDemo = function() {
        const demoSection = document.getElementById('demo-section');
        if (demoSection) {
            demoSection.scrollIntoView({ 
                behavior: 'smooth' 
            });
        }
    };

    // Smooth scroll to any element by ID
    window.scrollToElement = function(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
        }
    };

    // Add smooth scrolling and animations
    document.addEventListener('DOMContentLoaded', function() {
        // Animate elements on scroll
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
        const animatedElements = document.querySelectorAll('.card-hover, .animate-on-scroll, .fade-in');
        animatedElements.forEach(element => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            element.style.transition = 'all 0.6s ease';
            observer.observe(element);
        });

        // Add hover effects to buttons
        const buttons = document.querySelectorAll('button, .btn, .cta-button');
        buttons.forEach(button => {
            button.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px)';
            });
            
            button.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });

        // Add smooth scrolling to all anchor links
        const anchorLinks = document.querySelectorAll('a[href^="#"]');
        anchorLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Add parallax effect to hero sections
        const heroSections = document.querySelectorAll('.hero, .header, .banner');
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;
            
            heroSections.forEach(hero => {
                hero.style.transform = `translateY(${rate}px)`;
            });
        });

        // Add loading animation
        const loadingElements = document.querySelectorAll('.loading');
        setTimeout(() => {
            loadingElements.forEach(element => {
                element.classList.remove('loading');
                element.classList.add('loaded');
            });
        }, 100);

        // Add typing effect for text elements
        const typingElements = document.querySelectorAll('.typing-effect');
        typingElements.forEach(element => {
            const text = element.textContent;
            element.textContent = '';
            let i = 0;
            
            const typeWriter = () => {
                if (i < text.length) {
                    element.textContent += text.charAt(i);
                    i++;
                    setTimeout(typeWriter, 50);
                }
            };
            
            // Start typing when element comes into view
            const typingObserver = new IntersectionObserver(function(entries) {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        typeWriter();
                        typingObserver.unobserve(entry.target);
                    }
                });
            });
            
            typingObserver.observe(element);
        });

        // Page interactions loaded successfully
    });

    // Add CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        .animated {
            animation: fadeInUp 0.6s ease forwards;
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
        
        .loading {
            opacity: 0;
            transform: scale(0.9);
            transition: all 0.3s ease;
        }
        
        .loaded {
            opacity: 1;
            transform: scale(1);
        }
        
        .typing-effect {
            border-right: 2px solid #333;
            animation: blink 1s infinite;
        }
        
        @keyframes blink {
            0%, 50% { border-color: transparent; }
            51%, 100% { border-color: #333; }
        }
    `;
    document.head.appendChild(style);

})();