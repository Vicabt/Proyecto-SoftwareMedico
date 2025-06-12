document.addEventListener('DOMContentLoaded', function() {
    // Manejar el formulario de búsqueda
    const searchForm = document.getElementById('searchForm');
    const searchInput = searchForm.querySelector('input[name="busqueda"]');
    const especialidadSelect = searchForm.querySelector('select[name="especialidad"]');

    // Limpiar espacios en blanco extras al buscar
    searchForm.addEventListener('submit', function(e) {
        searchInput.value = searchInput.value.trim();
    });

    // Actualizar la URL cuando cambie la especialidad
    especialidadSelect.addEventListener('change', function() {
        searchForm.submit();
    });

    // Función para cargar las ciudades según el departamento seleccionado
    function cargarCiudades(departamentoId, ciudadSelectId) {
        const ciudadSelect = document.getElementById(ciudadSelectId);
        ciudadSelect.innerHTML = '<option value="">Seleccionar ciudad</option>';
        
        if (departamentoId) {
            fetch(`/api/ciudades/${departamentoId}`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(ciudad => {
                        const option = document.createElement('option');
                        option.value = ciudad.id;
                        option.textContent = ciudad.nombre;
                        ciudadSelect.appendChild(option);
                    });
                })
                .catch(error => console.error('Error:', error));
        }
    }

    // Evento para el cambio de departamento en el formulario de agregar
    const departamentoSelect = document.getElementById('departamento');
    if (departamentoSelect) {
        departamentoSelect.addEventListener('change', function() {
            cargarCiudades(this.value, 'ciudad');
        });
    }

    // Eventos para los formularios de edición
    const editDepartamentos = document.querySelectorAll('[id^="editDepartamento"]');
    editDepartamentos.forEach(departamentoSelect => {
        departamentoSelect.addEventListener('change', function() {
            const id = this.id.replace('editDepartamento', '');
            cargarCiudades(this.value, `editCiudad${id}`);
        });
    });

    // Función para validar el formulario antes de enviar
    const formAgregarMedico = document.getElementById('formAgregarMedico');
    if (formAgregarMedico) {
        formAgregarMedico.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validar campos requeridos
            const campos = this.querySelectorAll('[required]');
            let valido = true;
            
            campos.forEach(campo => {
                if (!campo.value.trim()) {
                    valido = false;
                    campo.classList.add('is-invalid');
                } else {
                    campo.classList.remove('is-invalid');
                }
            });

            // Validar formato de correo
            const correo = document.getElementById('emailMedico');
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(correo.value)) {
                valido = false;
                correo.classList.add('is-invalid');
            }

            // Validar formato de teléfono
            const telefono = document.getElementById('telefonoMedico');
            const telefonoRegex = /^[0-9]{10}$/;
            if (!telefonoRegex.test(telefono.value.replace(/\D/g, ''))) {
                valido = false;
                telefono.classList.add('is-invalid');
            }

            // Validar años de experiencia
            const aniosExperiencia = document.getElementById('aniosExperiencia');
            if (aniosExperiencia.value < 0) {
                valido = false;
                aniosExperiencia.classList.add('is-invalid');
            }

            if (valido) {
                this.submit();
            }
        });
    }

    // Función para formatear el número de teléfono mientras se escribe
    const telefonoInput = document.getElementById('telefonoMedico');
    if (telefonoInput) {
        telefonoInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 10) value = value.slice(0, 10);
            e.target.value = value;
        });
    }
}); 