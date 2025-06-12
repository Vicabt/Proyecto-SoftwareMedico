// Función para confirmar la eliminación
function confirmarEliminacion(event) {
    event.preventDefault();
    const form = event.target.closest('form');
    
    Swal.fire({
        title: '¿Estás seguro?',
        text: "Esta acción no se puede deshacer",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            form.submit();
        }
    });
}

// Inicializar cuando el documento esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Función para mostrar mensajes flash
    function mostrarMensajesFlash() {
        const flashMessages = document.getElementById('flash-messages');
        if (flashMessages) {
            const messages = JSON.parse(flashMessages.dataset.messages || '[]');
            messages.forEach(message => {
                const icon = message.category === 'success' ? 'success' : 
                           message.category === 'error' ? 'error' :
                           message.category === 'warning' ? 'warning' : 'info';
                
                Swal.fire({
                    title: message.category === 'success' ? '¡Éxito!' : 
                           message.category === 'error' ? '¡Error!' :
                           message.category === 'warning' ? '¡Advertencia!' : 'Información',
                    text: message.message,
                    icon: icon,
                    toast: true,
                    position: 'top-end',
                    showConfirmButton: false,
                    timer: 3000,
                    timerProgressBar: true
                });
            });
        }
    }

    // Manejar el formulario de búsqueda
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        const searchInput = searchForm.querySelector('input[name="busqueda"]');
        searchForm.addEventListener('submit', function(e) {
            searchInput.value = searchInput.value.trim();
        });
    }

    // Agregar event listeners para botones de eliminar
    document.querySelectorAll('form[action*="eliminar"]').forEach(form => {
        form.addEventListener('submit', confirmarEliminacion);
    });

    // Mostrar mensajes flash al cargar la página
    mostrarMensajesFlash();

    // Agregar estilos personalizados para SweetAlert2
    const style = document.createElement('style');
    style.textContent = `
        .swal2-popup-custom {
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .swal2-container-custom {
            z-index: 9999;
        }
        .swal2-title {
            font-size: 1.5em !important;
            font-weight: 600 !important;
            color: #2c3e50 !important;
            margin-bottom: 1em !important;
        }
        .swal2-html-container {
            font-size: 1.1em !important;
            color: #34495e !important;
            margin-bottom: 1.5em !important;
        }
    `;
    document.head.appendChild(style);
}); 