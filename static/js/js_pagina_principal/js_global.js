document.addEventListener('DOMContentLoaded', function () {
    const swiper = new Swiper('.client-swiper', {
        // Optional parameters
        loop: true,
        slidesPerView: 2, // Start with 2 slides on smallest screens
        spaceBetween: 30,
        autoplay: {
            delay: 2500,
            disableOnInteraction: false,
            pauseOnMouseEnter: true, // Pause when mouse is over
        },
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
        },
         breakpoints: {
            // when window width is >= 576px
            576: {
                slidesPerView: 3,
                spaceBetween: 30
            },
            // when window width is >= 768px
            768: {
                slidesPerView: 4,
                spaceBetween: 40
            },
            // when window width is >= 992px
            992: {
                slidesPerView: 5,
                spaceBetween: 50
            },
            // when window width is >= 1200px
            1200: {
                slidesPerView: 6,
                spaceBetween: 60
            }
        }
    });
});

document.addEventListener('DOMContentLoaded', function () {

    // --- IntersectionObserver para Contacto Info/Form ---
    if (typeof IntersectionObserver === 'function') {
        const contactObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                    contactObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 }); // Iniciar pronto

        requestAnimationFrame(() => {
            document.querySelectorAll('#contactInfoForm .animate-fade-in').forEach(el => {
                if (el) {
                    contactObserver.observe(el);
                }
            });
        });
    } else {
         // Fallback
         document.querySelectorAll('#contactInfoForm .animate-fade-in').forEach(el => {
            el.style.opacity = 1;
            el.style.transform = 'translateY(0)';
         });
    }

}); // Fin DOMContentLoaded
document.addEventListener('DOMContentLoaded', function () {
    // ... (Tu código JS existente para otras secciones como features.js) ...

    // --- IntersectionObserver para Timeline Items ---
    if (typeof IntersectionObserver === 'function') {
        const timelineItemObserver = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Aplicamos la animación al contenedor .timeline-item
                    entry.target.classList.add('animated');
                    timelineItemObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.15 }); // Activar cuando el 15% es visible

        requestAnimationFrame(() => {
            // Observamos el contenedor .timeline-item
            document.querySelectorAll('.timeline-item.animate-fade-in').forEach(el => {
                if (el) {
                    timelineItemObserver.observe(el);
                }
            });
        });
     } else {
         // Fallback si no hay IntersectionObserver
         document.querySelectorAll('.timeline-item.animate-fade-in').forEach(el => {
            el.style.opacity = 1;
            el.style.transform = 'translateY(0)';
         });
     }

    // ... (Resto de tu código JS como el del footer) ...

}); // Fin DOMContentLoaded
    // --- Footer Functionality ---

    // Set current year in copyright
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }

    // Back to Top button visibility
    const backToTopBtn = document.getElementById('backToTopBtn');
    const scrollThresholdFooter = 300; // Show button after scrolling 300px

    const handleBackToTopVisibility = () => {
        if (backToTopBtn) {
            if (window.scrollY > scrollThresholdFooter) {
                backToTopBtn.classList.add('visible');
            } else {
                backToTopBtn.classList.remove('visible');
            }
        }
    };

    // Smooth scroll to top when button clicked
    if (backToTopBtn) {
        backToTopBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Add scroll listener for the button visibility
    window.addEventListener('scroll', handleBackToTopVisibility);
    // Check visibility on initial load
    handleBackToTopVisibility();

    // --- End Footer Functionality ---
// Keep your existing JavaScript as it is
document.addEventListener('DOMContentLoaded', function() {
    const navbar = document.getElementById('mainNavbar');
    const scrollThreshold = 50;

    const handleScroll = () => {
        if (window.scrollY > scrollThreshold) {
            if (!navbar.classList.contains('navbar-scrolled')) {
                navbar.classList.add('navbar-scrolled');
            }
        } else {
            if (navbar.classList.contains('navbar-scrolled')) {
                navbar.classList.remove('navbar-scrolled');
            }
        }
    };

    handleScroll(); // Check initial state on load

    window.addEventListener('scroll', handleScroll);

    // Rest of your JS (toggler events, footer, etc.) remains the same
    const navbarCollapse = document.getElementById('navbarNav');
    if (navbarCollapse) {
        navbarCollapse.addEventListener('show.bs.collapse', function () {
           // Add any specific logic needed when mobile menu opens
        });
         navbarCollapse.addEventListener('hide.bs.collapse', function () {
           // Add any specific logic needed when mobile menu closes
        });
    }

    // --- Footer Functionality ---
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }

    const backToTopBtn = document.getElementById('backToTopBtn');
    const scrollThresholdFooter = 300;

    const handleBackToTopVisibility = () => {
        if (backToTopBtn) {
            if (window.scrollY > scrollThresholdFooter) {
                backToTopBtn.classList.add('visible');
            } else {
                backToTopBtn.classList.remove('visible');
            }
        }
    };

    if (backToTopBtn) {
        backToTopBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    window.addEventListener('scroll', handleBackToTopVisibility);
    handleBackToTopVisibility(); // Check initial state
    // --- End Footer Functionality ---
});

document.addEventListener('DOMContentLoaded', () => {
    const animatedItems = document.querySelectorAll('.animate-wave-scroll');

    if (!animatedItems.length) return;

    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.25
    };

    const observerCallback = (entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                element.classList.add('is-visible');
                observer.unobserve(element);
            }
        });
    };

    const intersectionObserver = new IntersectionObserver(observerCallback, observerOptions);

    animatedItems.forEach(item => {
        intersectionObserver.observe(item);
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('techCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const section = document.querySelector('.contact-info-form-section');
    if (!section) return;

    function resizeCanvas() {
        const rect = section.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
    }

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Partículas
    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.radius = Math.random() * 2 + 1;
            this.speed = Math.random() * 0.5 + 0.2;
            this.angle = Math.random() * 2 * Math.PI;
        }

        update() {
            this.x += Math.cos(this.angle) * this.speed;
            this.y += Math.sin(this.angle) * this.speed;

            if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.angle = Math.random() * 2 * Math.PI;
            }
        }

        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(1, 99, 185, 0.66)';
            ctx.fill();
        }
    }

    const particles = Array(100).fill().map(() => new Particle());

    // Cubos
    class Cube {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 20 + 10;
            this.rotation = Math.random() * Math.PI * 2;
            this.rotationSpeed = (Math.random() - 0.5) * 0.02;
            this.color = `rgba(79, 172, 254, ${Math.random() * 0.3 + 0.1})`;
        }

        update() {
            this.rotation += this.rotationSpeed;
        }

        draw() {
            ctx.save();
            ctx.translate(this.x, this.y);
            ctx.rotate(this.rotation);
            const halfSize = this.size / 2;

            ctx.beginPath();
            ctx.moveTo(-halfSize, -halfSize);
            ctx.lineTo(halfSize, -halfSize);
            ctx.lineTo(halfSize, halfSize);
            ctx.lineTo(-halfSize, halfSize);
            ctx.closePath();
            ctx.strokeStyle = this.color;
            ctx.lineWidth = 2;
            ctx.stroke();

            ctx.beginPath();
            ctx.moveTo(-halfSize, -halfSize);
            ctx.lineTo(halfSize, halfSize);
            ctx.moveTo(halfSize, -halfSize);
            ctx.lineTo(-halfSize, halfSize);
            ctx.stroke();

            ctx.restore();
        }
    }

    const cubes = Array(10).fill().map(() => new Cube());

    // Animación
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => { p.update(); p.draw(); });
        cubes.forEach(cube => { cube.update(); cube.draw(); });
        requestAnimationFrame(animate);
    }

    animate();
});

document.addEventListener('DOMContentLoaded', function () {

    const dataFuncionalidades = [
        { 
            icon: "bi-person-badge", 
            title: "Gestión de Médicos", 
            desc: "Organizo toda la información de tu equipo médico", 
            details: "Mantengo actualizados los datos de tus médicos, sus especialidades, horarios y disponibilidad. Así podrás asignar citas de manera más eficiente y mantener todo organizado." 
        },
        { 
            icon: "bi-people", 
            title: "Gestión de Pacientes", 
            desc: "Cuido la información de tus pacientes", 
            details: "Guardo y protejo todos los datos de tus pacientes de manera segura. Desde información personal hasta historial médico, todo está organizado y accesible cuando lo necesites." 
        },
        { 
            icon: "bi-calendar-check", 
            title: "Agenda y Citas", 
            desc: "Te ayudo a organizar las citas", 
            details: "Programo, confirmo y gestiono las citas de manera eficiente. Envío recordatorios automáticos a tus pacientes y mantengo tu agenda siempre actualizada." 
        },
        { 
            icon: "bi-file-medical", 
            title: "Historia Clínica", 
            desc: "Digitalizo las historias clínicas", 
            details: "Mantengo un registro completo y organizado de todas las consultas, diagnósticos y tratamientos. Accede a la información de tus pacientes de manera rápida y segura." 
        },
        { 
            icon: "bi-cash-stack", 
            title: "Facturación", 
            desc: "Simplifico la gestión financiera", 
            details: "Te ayudo con la facturación, el seguimiento de pagos y los reportes financieros. Todo integrado con la gestión de pacientes y servicios médicos." 
        },
        { 
            icon: "bi-hand-thumbs-up", 
            title: "¿Listo para comenzar?", 
            desc: "Transformemos juntos tu consultorio", 
            details: "Estoy aquí para hacer tu trabajo más fácil. Agenda una demostración y descubre cómo puedo ayudarte a gestionar tu consultorio de manera más eficiente." 
        }
    ];



});

document.addEventListener('DOMContentLoaded', function() {
    const testimoniosSwiper = new Swiper('.testimonios-swiper', {
        slidesPerView: 1,
        spaceBetween: 30,
        loop: true,
        autoplay: {
            delay: 5000,
            disableOnInteraction: false,
        },
        pagination: {
            el: '.testimonios-pagination',
            clickable: true,
            dynamicBullets: true,
        },
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
        breakpoints: {
            640: {
                slidesPerView: 2,
                spaceBetween: 20,
            },
            1024: {
                slidesPerView: 3,
                spaceBetween: 30,
            },
        },
        effect: 'slide',
        speed: 800,
        grabCursor: true,
    });

    // Animación de entrada para los testimonios
    const testimonioCards = document.querySelectorAll('.testimonio-card');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1
    });

    testimonioCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(card);
    });

    // Animación del contador
    const stats = document.querySelectorAll('.review-stat-number');
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = entry.target;
                const countTo = parseFloat(target.getAttribute('data-count'));
                const duration = 2000; // 2 segundos
                const step = countTo / (duration / 16); // 60fps
                let currentCount = 0;

                const updateCount = () => {
                    currentCount += step;
                    if (currentCount < countTo) {
                        target.textContent = Math.round(currentCount * 10) / 10;
                        requestAnimationFrame(updateCount);
                    } else {
                        target.textContent = countTo;
                    }
                };

                updateCount();
                statsObserver.unobserve(target);
            }
        });
    }, {
        threshold: 0.5
    });

    stats.forEach(stat => {
        statsObserver.observe(stat);
    });
}); 