document.addEventListener('DOMContentLoaded', function() {
    // Función para cargar ciudades
    function cargarCiudades(departamentoId, selectCiudad) {
        fetch(`/api/ciudades/${departamentoId}`)
            .then(response => response.json())
            .then(data => {
                // Limpiar opciones actuales
                selectCiudad.innerHTML = '<option value="" selected disabled>Seleccionar</option>';
                
                // Agregar nuevas opciones
                data.forEach(ciudad => {
                    const option = document.createElement('option');
                    option.value = ciudad.id;
                    option.textContent = ciudad.nombre;
                    selectCiudad.appendChild(option);
                });
            })
            .catch(error => console.error('Error:', error));
    }

    // Manejar cambios en el select de departamento para nuevo paciente
    const departamentoSelect = document.getElementById('departamento');
    const ciudadSelect = document.getElementById('ciudad');
    
    if (departamentoSelect && ciudadSelect) {
        departamentoSelect.addEventListener('change', function() {
            if (this.value) {
                cargarCiudades(this.value, ciudadSelect);
            } else {
                ciudadSelect.innerHTML = '<option value="" selected disabled>Seleccionar</option>';
            }
        });
    }

    // Manejar cambios en los selects de departamento para edición de pacientes
    document.querySelectorAll('[id^="editDepartamento"]').forEach(select => {
        const pacienteId = select.id.replace('editDepartamento', '');
        const ciudadSelect = document.getElementById(`editCiudad${pacienteId}`);
        
        if (ciudadSelect) {
            select.addEventListener('change', function() {
                if (this.value) {
                    cargarCiudades(this.value, ciudadSelect);
                } else {
                    ciudadSelect.innerHTML = '<option value="" selected disabled>Seleccionar</option>';
                }
            });
        }
    });
}); 