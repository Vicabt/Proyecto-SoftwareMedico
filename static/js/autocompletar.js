    // Función para autocompletar el motivo de consulta cuando se selecciona una cita
    function completarMotivo() {
        var selectCita = document.getElementById('citaHistoria');
        var inputMotivo = document.getElementById('motivoConsulta');
        
        if (selectCita.selectedIndex > 0) {
            var selectedOption = selectCita.options[selectCita.selectedIndex];
            var motivo = selectedOption.getAttribute('data-motivo');
            inputMotivo.value = motivo;
        } else {
            inputMotivo.value = '';
        }
    }

    function seleccionarDiagnostico(codigo, descripcion) {
        // Aquí puedes implementar la lógica para seleccionar el diagnóstico
        // Por ejemplo, llenar un campo oculto o actualizar un campo de texto
        document.getElementById('diagnostico_codigo').value = codigo;
        document.getElementById('diagnostico').value = descripcion;
        
        // Opcional: cerrar el modal o limpiar la búsqueda
        document.querySelector('input[name="busqueda_diagnostico"]').value = '';
    }

    document.addEventListener('DOMContentLoaded', function() {
        // Inicializar autocompletado para el formulario de nueva historia
        inicializarAutocompletado('diagnostico', 'diagnostico_codigo', 'diagnostico-sugerencias');

        // Inicializar autocompletado para cada formulario de editar
        document.querySelectorAll('[id^="editDiagnostico"]').forEach(input => {
            const historiaId = input.id.replace('editDiagnostico', '');
            inicializarAutocompletado(
                `editDiagnostico${historiaId}`,
                `editDiagnosticoCodigo${historiaId}`,
                `edit-diagnostico-sugerencias${historiaId}`
            );
        });
    });

    function inicializarAutocompletado(inputId, codigoId, sugerenciasId) {
        const diagnosticoInput = document.getElementById(inputId);
        const diagnosticoCodigo = document.getElementById(codigoId);
        const sugerenciasDiv = document.getElementById(sugerenciasId);
        let timeoutId;

        if (!diagnosticoInput || !diagnosticoCodigo || !sugerenciasDiv) return;

        diagnosticoInput.addEventListener('input', function() {
            clearTimeout(timeoutId);
            const busqueda = this.value.trim();
            
            if (busqueda.length < 2) {
                sugerenciasDiv.style.display = 'none';
                return;
            }

            // Mostrar indicador de carga
            sugerenciasDiv.innerHTML = '<div class="list-group-item text-center"><small>Cargando...</small></div>';
            sugerenciasDiv.style.display = 'block';

            timeoutId = setTimeout(() => {
                fetch(`/buscar_diagnostico?q=${encodeURIComponent(busqueda)}`)
                    .then(response => response.json())
                    .then(data => {
                        sugerenciasDiv.innerHTML = '';
                        if (data.length > 0) {
                            data.forEach(diag => {
                                const item = document.createElement('a');
                                item.href = '#';
                                item.className = 'list-group-item list-group-item-action';
                                item.innerHTML = `<strong>${diag.codigo}</strong> - ${diag.descripcion}`;
                                item.addEventListener('click', function(e) {
                                    e.preventDefault();
                                    diagnosticoInput.value = diag.descripcion;
                                    diagnosticoCodigo.value = diag.codigo;
                                    sugerenciasDiv.style.display = 'none';
                                });
                                sugerenciasDiv.appendChild(item);
                            });
                        } else {
                            sugerenciasDiv.innerHTML = '<div class="list-group-item text-center"><small>No se encontraron resultados</small></div>';
                        }
                    })
                    .catch(error => {
                        sugerenciasDiv.innerHTML = '<div class="list-group-item text-center text-danger"><small>Error al buscar diagnósticos</small></div>';
                    });
            }, 300);
        });

        // Cerrar sugerencias al hacer clic fuera
        document.addEventListener('click', function(e) {
            if (!diagnosticoInput.contains(e.target) && !sugerenciasDiv.contains(e.target)) {
                sugerenciasDiv.style.display = 'none';
            }
        });
    }