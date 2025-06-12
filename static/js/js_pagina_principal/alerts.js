class CustomAlert {
    static activeAlerts = new Map(); // Cambiado a Map para almacenar el timestamp
    static validTypes = ['success', 'error', 'warning', 'info'];

    static getIconForType(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    static show(message, type = 'success') {
        // Solo mostrar alertas con tipos válidos
        if (!this.validTypes.includes(type)) {
            return;
        }

        const now = Date.now();
        const lastShown = this.activeAlerts.get(message);

        // Evitar alertas duplicadas en un intervalo de 5 segundos
        if (lastShown && (now - lastShown) < 5000) {
            return;
        }

        this.activeAlerts.set(message, now);

        const alertsContainer = document.getElementById('custom-alerts-container');
        if (!alertsContainer) {
            console.error('No se encontró el contenedor de alertas');
            return;
        }

        const alertElement = document.createElement('div');
        alertElement.className = `custom-alert ${type}`;
        
        const icon = this.getIconForType(type);
        
        alertElement.innerHTML = `
            <i class="bi bi-${icon} alert-icon"></i>
            <div class="alert-content">${message}</div>
            <button class="close-btn" title="Cerrar">
                <i class="bi bi-x"></i>
            </button>
        `;

        // Limitar el número de alertas visibles
        if (alertsContainer.children.length >= 3) {
            this.closeAlert(alertsContainer.children[0]);
        }

        alertsContainer.appendChild(alertElement);

        // Configurar el botón de cierre
        const closeBtn = alertElement.querySelector('.close-btn');
        closeBtn.addEventListener('click', () => this.closeAlert(alertElement));

        // Auto-cerrar después de 5 segundos
        setTimeout(() => {
            if (alertElement.parentNode) {
                this.closeAlert(alertElement);
            }
        }, 5000);
    }

    static closeAlert(alertElement) {
        const message = alertElement.querySelector('.alert-content').textContent;
        // No eliminamos el mensaje del Map inmediatamente para prevenir duplicados
        setTimeout(() => {
            this.activeAlerts.delete(message);
        }, 5000);

        alertElement.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => {
            if (alertElement.parentNode) {
                alertElement.parentNode.removeChild(alertElement);
            }
        }, 300);
    }
}

// Inicializar alertas cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    try {
        const messages = JSON.parse(document.getElementById('flash-messages').textContent || '[]');
        console.log('Mensajes flash:', messages);
        messages.forEach(msg => {
            CustomAlert.show(msg[1], msg[0]);
        });
    } catch (error) {
        console.error('Error al procesar mensajes:', error);
    }
});
