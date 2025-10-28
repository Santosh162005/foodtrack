// Enhanced Animations for Food Expiry Tracker

document.addEventListener('DOMContentLoaded', function() {
    
    // Simple animations only
    animateOnScroll();
    countUpNumbers();
    addRippleEffect();
});

// Create floating food particles
function createParticles() {
    const particleCount = 15;
    const particles = ['🍎', '🥕', '🥬', '🍞', '🥛', '🧀', '🍅', '🥑', '🍊', '🍓'];
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'food-particle';
        particle.textContent = particles[Math.floor(Math.random() * particles.length)];
        particle.style.cssText = `
            position: fixed;
            font-size: ${Math.random() * 20 + 20}px;
            opacity: ${Math.random() * 0.3 + 0.1};
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
            animation: floatParticle ${Math.random() * 10 + 10}s infinite ease-in-out;
            z-index: -1;
            pointer-events: none;
        `;
        document.body.appendChild(particle);
    }
    
    // Add CSS animation
    if (!document.getElementById('particleStyle')) {
        const style = document.createElement('style');
        style.id = 'particleStyle';
        style.textContent = `
            @keyframes floatParticle {
                0%, 100% {
                    transform: translate(0, 0) rotate(0deg);
                }
                25% {
                    transform: translate(20px, -30px) rotate(90deg);
                }
                50% {
                    transform: translate(-20px, -60px) rotate(180deg);
                }
                75% {
                    transform: translate(30px, -30px) rotate(270deg);
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Animate elements on scroll
function animateOnScroll() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.card, .table, .alert').forEach(el => {
        observer.observe(el);
    });
}

// Success confetti animation
function setupSuccessAnimations() {
    const alerts = document.querySelectorAll('.alert-success');
    alerts.forEach(alert => {
        createConfetti(alert);
    });
}

function createConfetti(element) {
    const colors = ['#FF6B6B', '#4ECDC4', '#95E1D3', '#FFD93D'];
    const confettiCount = 30;
    
    for (let i = 0; i < confettiCount; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        confetti.style.cssText = `
            position: absolute;
            width: 8px;
            height: 8px;
            background: ${colors[Math.floor(Math.random() * colors.length)]};
            left: ${Math.random() * 100}%;
            top: 0;
            opacity: 0;
            animation: confettiFall ${Math.random() * 2 + 1}s ease-out forwards;
        `;
        element.style.position = 'relative';
        element.appendChild(confetti);
        
        setTimeout(() => confetti.remove(), 2000);
    }
    
    if (!document.getElementById('confettiStyle')) {
        const style = document.createElement('style');
        style.id = 'confettiStyle';
        style.textContent = `
            @keyframes confettiFall {
                0% {
                    transform: translateY(0) rotateZ(0deg);
                    opacity: 1;
                }
                100% {
                    transform: translateY(100px) rotateZ(360deg);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Enhanced card hover effects
function enhanceCardHovers() {
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const angleX = (y - centerY) / 30;
            const angleY = (centerX - x) / 30;
            
            card.style.transform = `perspective(1000px) rotateX(${angleX}deg) rotateY(${angleY}deg) scale(1.02)`;
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';
        });
    });
}

// Typewriter effect for headers
function typeWriterEffect() {
    const headers = document.querySelectorAll('h1, h2, h3');
    headers.forEach((header, index) => {
        if (header.classList.contains('typed')) return;
        
        const text = header.textContent;
        header.textContent = '';
        header.classList.add('typed');
        
        let i = 0;
        const speed = 50;
        
        setTimeout(() => {
            const typeInterval = setInterval(() => {
                if (i < text.length) {
                    header.textContent += text.charAt(i);
                    i++;
                } else {
                    clearInterval(typeInterval);
                }
            }, speed);
        }, index * 200);
    });
}

// Count up animation for numbers
function countUpNumbers() {
    const numbers = document.querySelectorAll('.card.text-white h2');
    numbers.forEach(num => {
        const target = parseInt(num.textContent);
        if (isNaN(target)) return;
        
        let current = 0;
        const increment = target / 50;
        const duration = 1500;
        const stepTime = duration / 50;
        
        num.textContent = '0';
        
        const counter = setInterval(() => {
            current += increment;
            if (current >= target) {
                num.textContent = target;
                clearInterval(counter);
            } else {
                num.textContent = Math.floor(current);
            }
        }, stepTime);
    });
}

// Ripple effect on buttons
function addRippleEffect() {
    document.querySelectorAll('.btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const rect = button.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.className = 'ripple-effect';
            ripple.style.cssText = `
                position: absolute;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.6);
                width: 20px;
                height: 20px;
                left: ${x}px;
                top: ${y}px;
                transform: translate(-50%, -50%);
                animation: ripple 0.6s ease-out;
                pointer-events: none;
            `;
            
            button.style.position = 'relative';
            button.style.overflow = 'hidden';
            button.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
    
    if (!document.getElementById('rippleStyle')) {
        const style = document.createElement('style');
        style.id = 'rippleStyle';
        style.textContent = `
            @keyframes ripple {
                to {
                    width: 200px;
                    height: 200px;
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Loading screen
function showLoadingScreen(message = 'Loading...') {
    const loader = document.createElement('div');
    loader.id = 'loadingScreen';
    loader.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.95);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 99999;
    `;
    
    loader.innerHTML = `
        <div style="text-align: center;">
            <div class="spinner-border text-primary" role="status" style="width: 4rem; height: 4rem;">
                <span class="visually-hidden">Loading...</span>
            </div>
            <h3 class="mt-4" style="color: #667eea;">${message}</h3>
            <div style="font-size: 3rem; animation: bounce 1s infinite;">🍎</div>
        </div>
    `;
    
    document.body.appendChild(loader);
    return loader;
}

function hideLoadingScreen() {
    const loader = document.getElementById('loadingScreen');
    if (loader) {
        loader.style.opacity = '0';
        loader.style.transition = 'opacity 0.5s';
        setTimeout(() => loader.remove(), 500);
    }
}

// Toast notification
function showToast(message, type = 'info') {
    const colors = {
        'success': '#95E1D3',
        'error': '#FF6B6B',
        'warning': '#FFD93D',
        'info': '#4ECDC4'
    };
    
    const icons = {
        'success': '✓',
        'error': '✗',
        'warning': '⚠',
        'info': 'ℹ'
    };
    
    const toast = document.createElement('div');
    toast.className = 'custom-toast';
    toast.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        background: ${colors[type]};
        color: white;
        padding: 20px 30px;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideInUp 0.5s ease-out;
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 600;
    `;
    
    toast.innerHTML = `
        <span style="font-size: 1.5rem;">${icons[type]}</span>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutDown 0.5s ease-out';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
    
    if (!document.getElementById('toastStyle')) {
        const style = document.createElement('style');
        style.id = 'toastStyle';
        style.textContent = `
            @keyframes slideInUp {
                from {
                    transform: translateY(100px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
            @keyframes slideOutDown {
                to {
                    transform: translateY(100px);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Progress bar
function showProgressBar() {
    const progress = document.createElement('div');
    progress.id = 'progressBar';
    progress.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        height: 4px;
        background: linear-gradient(90deg, #FA8BFF 0%, #2BD2FF 52%, #2BFF88 90%);
        z-index: 99999;
        width: 0%;
        transition: width 0.3s ease;
    `;
    document.body.appendChild(progress);
    
    let width = 0;
    const interval = setInterval(() => {
        width += Math.random() * 15;
        if (width >= 90) {
            clearInterval(interval);
        }
        progress.style.width = Math.min(width, 90) + '%';
    }, 200);
    
    return { progress, interval };
}

function completeProgressBar(progressObj) {
    clearInterval(progressObj.interval);
    progressObj.progress.style.width = '100%';
    setTimeout(() => {
        progressObj.progress.style.opacity = '0';
        setTimeout(() => progressObj.progress.remove(), 300);
    }, 500);
}

// Export functions to global scope
window.showLoadingScreen = showLoadingScreen;
window.hideLoadingScreen = hideLoadingScreen;
window.showToast = showToast;
window.showProgressBar = showProgressBar;
window.completeProgressBar = completeProgressBar;
window.createConfetti = createConfetti;
