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

    const containerFuncionalidades = document.getElementById("card-container");

    if (containerFuncionalidades) {
        dataFuncionalidades.forEach((item, i) => {
            const col = document.createElement("div");
            col.className = "col-md-6 col-lg-4 mb-4";

            const bgClass = i % 2 === 0 ? 'bg-blue' : 'bg-white';
            const btnClass = i % 2 === 0 ? 'btn-outline-light' : 'btn-outline-primary';

            col.innerHTML = `
                <div class="flip-card animate-fade-in" style="animation-delay: ${i * 0.1}s">
                    <div class="flip-card-inner">
                        <div class="flip-card-front card-custom ${bgClass}">
                            <div class="card-body">
                                <i class="bi ${item.icon} icon-style"></i>
                                <h5 class="fw-bold">${item.title}</h5>
                                <p>${item.desc}</p>
                            </div>
                        </div>
                        <div class="flip-card-back card-custom ${bgClass}">
                             <div class="card-body">
                                <h5 class="fw-bold">${item.title} - Detalles</h5>
                                <p>${item.details}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            containerFuncionalidades.appendChild(col);
        });

        if (typeof IntersectionObserver === 'function') {
            const observerFuncionalidades = new IntersectionObserver(entries => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animated');
                        observerFuncionalidades.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1 });

            requestAnimationFrame(() => {
                document.querySelectorAll('#card-container .flip-card').forEach(el => {
                    if (el) {
                        observerFuncionalidades.observe(el);
                    }
                });
            });
        } else {
            document.querySelectorAll('#card-container .flip-card').forEach(el => {
                el.style.opacity = 1;
                el.style.transform = 'translateY(0)';
            });
        }
    }
});
