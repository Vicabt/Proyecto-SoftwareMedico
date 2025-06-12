from flask import render_template, request, redirect, url_for, flash, session, make_response, jsonify
from model import db, usuario, medico as Medico, paciente as Paciente, cita, historia_clinica, factura as Factura, configuracion as Configuracion, ciudad as Ciudad, departamento as Departamento, universidad as Universidad
from datetime import datetime
import matplotlib.pyplot as plt
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from constantes import ESPECIALIDADES

# Colores personalizados para todos los reportes
primary_color = colors.HexColor('#2651a6')  # Azul principal
accent_color = colors.HexColor('#2C3E50')   # Azul oscuro para títulos
light_bg = colors.HexColor('#f8f9fa')      # Fondo claro para secciones
border_color = colors.HexColor('#dee2e6')   # Color sutil para bordes
success_color = colors.HexColor('#28a745')  # Verde para estados positivos
warning_color = colors.HexColor('#ffc107')  # Amarillo para advertencias
danger_color = colors.HexColor('#dc3545')   # Rojo para estados negativos

# Estilos base para todos los reportes
styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=18,
    spaceAfter=20,
    alignment=1,  # Centrado
    textColor=primary_color,
    fontName='Helvetica-Bold'
)

subtitle_style = ParagraphStyle(
    'Subtitle',
    parent=styles['Heading2'],
    fontSize=12,
    spaceAfter=10,
    spaceBefore=15,
    textColor=accent_color,
    backColor=light_bg,
    borderPadding=(6, 6, 6, 6),
    borderWidth=1,
    borderRadius=4,
    leading=16,
    fontName='Helvetica-Bold'
)

normal_style = ParagraphStyle(
    'CustomNormal',
    parent=styles['Normal'],
    fontSize=10,
    spaceAfter=5,
    leading=14,
    fontName='Helvetica'
)

content_style = ParagraphStyle(
    'Content',
    parent=styles['Normal'],
    fontSize=10,
    leading=14,
    spaceBefore=3,
    spaceAfter=8,
    fontName='Helvetica'
)

# Función auxiliar para crear encabezados de reporte
def create_report_header(doc, title, subtitle=None, logo_path=None):
    elements = []
    
    # Encabezado con logo y título
    header_data = []
    if logo_path:
        header_data.append([
            Image(logo_path, width=100, height=40),
            Paragraph(f"<font size='16' color='{primary_color}'><b>{title}</b></font>", 
                     ParagraphStyle('Header', parent=styles['Normal'], alignment=2))
        ])
    else:
        header_data.append([
            Paragraph(f"<font size='16'><b>MediSoft</b></font><br/>"
                      "<font size='9'>Sistema de Gestión Médica</font>", 
              ParagraphStyle('Header', parent=styles['Normal'], alignment=0)),
            Paragraph(f"<font size='16' color='{primary_color}'><b>{title}</b></font>", 
              ParagraphStyle('Header', parent=styles['Normal'], alignment=2))
        ])
    
    header = Table(header_data, colWidths=[doc.width/2.0, doc.width/2.0])
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(header)
    
    # Línea separadora
    elements.append(Spacer(1, 4))
    elements.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=6, spaceBefore=0))
    elements.append(Spacer(1, 6))
    
    # Subtítulo si existe
    if subtitle:
        elements.append(Paragraph(subtitle, subtitle_style))
        elements.append(Spacer(1, 10))
    
    return elements

# Función auxiliar para crear tablas con estilo moderno
def create_modern_table(data, col_widths, header_bg=primary_color, header_text_color=colors.whitesmoke, left_columns=None):
    # left_columns: lista de índices de columnas que deben alinearse a la izquierda
    if left_columns is None:
        left_columns = []
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR', (0, 0), (-1, 0), header_text_color),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, border_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWHEIGHT', (0, 0), (-1, -1), 22),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ])
    # Alinear a la izquierda las columnas indicadas
    for col in left_columns:
        table_style.add('ALIGN', (col, 0), (col, -1), 'LEFT')
    # Permitir saltos de línea en todas las celdas
    for row in range(1, len(data)):
        for col in range(len(data[0])):
            if isinstance(data[row][col], str):
                data[row][col] = Paragraph(data[row][col], ParagraphStyle('cell', fontSize=8, leading=10, alignment=0 if col in left_columns else 1))
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(table_style)
    return table

# Función auxiliar para crear pie de página
def create_footer(doc, additional_info=None):
    elements = []
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceAfter=6))
    elements.append(Spacer(1, 10))
    
    footer_data = []
    if additional_info:
        footer_data.append([
            Paragraph(additional_info, 
                     ParagraphStyle('FooterInfo', parent=styles['Normal'], fontSize=8, textColor=colors.grey)),
            Paragraph(f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - MediSoft",
                     ParagraphStyle('FooterDate', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=2))
        ])
    else:
        footer_data.append([
            Paragraph(f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - MediSoft",
                     ParagraphStyle('FooterDate', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=2))
        ])
    
    footer = Table(footer_data, colWidths=[doc.width/2.0, doc.width/2.0])
    footer.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    elements.append(footer)
    return elements

def obtener_configuracion():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return Configuracion.query.filter_by(usuario_id=user_id).first()

def guardar_configuracion(request):
    user_id = session.get('user_id')
    if not user_id:
        return None
    config = Configuracion.query.filter_by(usuario_id=user_id).first()
    if not config:
        config = Configuracion(usuario_id=user_id)

    config.nombre_empresa = request.form.get('nombre_empresa', config.nombre_empresa)
    config.nit_empresa = request.form.get('nit_empresa', config.nit_empresa)
    config.registro_sanitario = request.form.get('registro_sanitario', config.registro_sanitario)
    config.slogan = request.form.get('slogan', config.slogan)

    # Guardar logo si se subió
    if 'logo' in request.files and request.files['logo'].filename:
        logo = request.files['logo']
        if logo.filename:
            filename = f"logo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{logo.filename}"
            uploads_dir = os.path.join('static', 'uploads')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
            logo_path = os.path.join(uploads_dir, filename)
            logo.save(logo_path)
            config.logo = f'uploads/{filename}'

    # Guardar favicon si se subió
    if 'favicon' in request.files and request.files['favicon'].filename:
        favicon = request.files['favicon']
        if favicon.filename:
            filename = f"favicon_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{favicon.filename}"
            uploads_dir = os.path.join('static', 'uploads')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
            favicon_path = os.path.join(uploads_dir, filename)
            favicon.save(favicon_path)
            config.favicon = f'uploads/{filename}'

    db.session.add(config)
    db.session.commit()
    return config

def init_auth_routes(app, db):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # Check for logout message in cookie
        logout_message = request.cookies.get('logout_message')
        if logout_message:
            flash(logout_message, 'success')
            # Create a response that will delete the cookie
            response = make_response(render_template('pagina_principal/login.html'))
            response.delete_cookie('logout_message')
            
            # Only return the response if we're not processing a POST request
            if request.method != 'POST':
                return response
        
        # Check for logout message in session
        logout_message = session.pop('logout_message', None)
        if logout_message:
            flash(logout_message, 'success')
        
        # Check for logout message in URL (keep this as a fallback)
        url_logout_message = request.args.get('logout_message')
        if url_logout_message:
            flash(url_logout_message, 'success')
            
        if request.method == 'POST':
            correo = request.form.get('email')
            password = request.form.get('password')
            
            print(f"Intentando login con correo: {correo}")
            
            # Validar que se proporcionaron los campos requeridos
            if not correo:
                flash('Error: Por favor ingrese su correo electrónico', 'warning')
                return redirect(url_for('login'))
            if not password:
                flash('Error: Por favor ingrese su contraseña', 'warning')
                return redirect(url_for('login'))
            
            user = usuario.query.filter_by(correo=correo).first()
            
            if not user:
                flash('Error: El correo electrónico no está registrado', 'error')
                return redirect(url_for('login'))
            
            if user.contrasena != password:
                flash('Error: La contraseña es incorrecta', 'error')
                return redirect(url_for('login'))
            
            # Login exitoso
            session['user_id'] = user.id
            session['user_name'] = user.nombre
            flash(f'¡Bienvenido {user.nombre}!', 'success')
            return redirect(url_for('panel'))
                
        return render_template('pagina_principal/login.html')

    @app.route('/register', methods=['POST'])
    def register():
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        correo = request.form.get('email')
        telefono = request.form.get('telefono')
        ciudad = request.form.get('ciudad')
        password = request.form.get('password')
        
        try:
            # Validar campos requeridos
            if not nombre:
                flash('Error: Por favor ingrese su nombre', 'warning')
                return redirect(url_for('login'))
            if not correo:
                flash('Error: Por favor ingrese su correo electrónico', 'warning')
                return redirect(url_for('login'))
            if not password:
                flash('Error: Por favor ingrese una contraseña', 'warning')
                return redirect(url_for('login'))

            print(f"Intentando registrar usuario con correo: {correo}")
            
            # Verificar si el usuario ya existe
            user_exists = usuario.query.filter_by(correo=correo).first()
            if user_exists:
                print(f"Usuario ya existe con correo: {correo}")
                flash('Error: Este correo electrónico ya está registrado', 'error')
                return redirect(url_for('login'))
            
            # Validar contraseña
            if len(password) < 6:
                flash('Error: La contraseña debe tener al menos 6 caracteres', 'warning')
                return redirect(url_for('login'))
            
            # Validar formato de correo electrónico
            if '@' not in correo or '.' not in correo:
                flash('Error: Por favor ingrese un correo electrónico válido', 'warning')
                return redirect(url_for('login'))
                
            # Validar formato de teléfono si se proporciona
            if telefono and not telefono.isdigit():
                flash('Error: El número de teléfono debe contener solo dígitos', 'warning')
                return redirect(url_for('login'))

            # Crear nuevo usuario con los campos disponibles
            new_user = usuario(
                nombre=nombre,
                apellido=apellido,
                correo=correo,
                contrasena=password,
                telefono=telefono,
                ciudad=ciudad
            )
            
            print("Intentando agregar usuario a la base de datos...")
            db.session.add(new_user)
            db.session.commit()
            print(f"Nuevo usuario registrado: {correo}")
            flash('¡Registro exitoso! Ahora puedes iniciar sesión', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            import traceback
            print(f"Error detallado al registrar usuario:")
            print(f"Tipo de error: {type(e).__name__}")
            print(f"Mensaje de error: {str(e)}")
            print("Traceback completo:")
            print(traceback.format_exc())
            
            if 'Duplicate entry' in str(e):
                flash('El correo electrónico ya está registrado', 'error')
            else:
                error_msg = f'Error: Hubo un problema al crear tu cuenta. {str(e)}'
                flash(error_msg, 'error')
                flash('Si el problema persiste, contacta al soporte técnico.', 'info')
            return redirect(url_for('login'))

    @app.route('/logout', methods=['GET', 'POST'])
    def logout():
        try:
            # For both GET and POST requests, perform logout directly
            user_name = session.get('user_name', 'Usuario')
            # Store the message in a cookie instead of session
            response = redirect(url_for('login'))
            
            # Clear the session
            session.clear()
            
            return response
        except Exception as e:
            print(f'Error en logout: {str(e)}')
            flash('Error al cerrar sesión', 'error')
            return redirect(url_for('login'))
            
    @app.route('/perfil/actualizar', methods=['POST'])
    def actualizar_perfil():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            user_id = session.get('user_id')
            user = usuario.query.get(user_id)
            
            if not user:
                flash('Error: Usuario no encontrado', 'error')
                return redirect(url_for('panel'))
            
            # Actualizar información personal
            nombre = request.form.get('nombre')
            apellido = request.form.get('apellido')
            telefono = request.form.get('telefono')
            ciudad = request.form.get('ciudad')
            direccion = request.form.get('direccion')
            tipo_documento = request.form.get('tipo_documento')
            numero_documento = request.form.get('numero_documento')
            
            # Actualizar campos que no estén vacíos
            if nombre and nombre.strip():
                user.nombre = nombre
                session['user_name'] = nombre  # Actualizar el nombre en la sesión
                
            if apellido and apellido.strip():
                user.apellido = apellido
                
            if telefono:
                # Validar formato de teléfono
                if not telefono.isdigit():
                    flash('Error: El número de teléfono debe contener solo dígitos', 'warning')
                else:
                    user.telefono = telefono
            
            if ciudad and ciudad.strip():
                user.ciudad = ciudad
                
            if direccion and direccion.strip():
                user.direccion = direccion
                
            if tipo_documento:
                user.tipo_documento = tipo_documento
                
            if numero_documento and numero_documento.strip():
                user.numero_documento = numero_documento
                
            db.session.commit()
            flash('Perfil actualizado correctamente', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el perfil: {str(e)}', 'error')
            
        return redirect(url_for('perfil'))
        
    @app.route('/perfil/cambiar-password', methods=['POST'])
    def cambiar_password():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            user_id = session.get('user_id')
            user = usuario.query.get(user_id)
            
            if not user:
                flash('Error: Usuario no encontrado', 'error')
                return redirect(url_for('panel'))
            
            password_actual = request.form.get('passwordActual')
            password_nuevo = request.form.get('password')
            password_confirm = request.form.get('passwordConfirm')
            
            # Validar que se proporcionaron los campos requeridos
            if not password_actual:
                flash('Error: Por favor ingrese su contraseña actual', 'warning')
                return redirect(url_for('perfil'))
                
            if not password_nuevo:
                flash('Error: Por favor ingrese la nueva contraseña', 'warning')
                return redirect(url_for('perfil'))
                
            if not password_confirm:
                flash('Error: Por favor confirme la nueva contraseña', 'warning')
                return redirect(url_for('perfil'))
            
            # Validar que la contraseña actual sea correcta
            if user.contrasena != password_actual:
                flash('Error: La contraseña actual es incorrecta', 'error')
                return redirect(url_for('perfil'))
            
            # Validar que las contraseñas coincidan
            if password_nuevo != password_confirm:
                flash('Error: Las contraseñas no coinciden', 'error')
                return redirect(url_for('perfil'))
            
            # Validar que la nueva contraseña tenga al menos 6 caracteres
            if len(password_nuevo) < 6:
                flash('Error: La contraseña debe tener al menos 6 caracteres', 'warning')
                return redirect(url_for('perfil'))
            
            # Actualizar la contraseña
            user.contrasena = password_nuevo
            db.session.commit()
            
            flash('Contraseña actualizada correctamente', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la contraseña: {str(e)}', 'error')
            
        return redirect(url_for('perfil'))
        
    @app.route('/perfil/cambiar-foto', methods=['POST'])
    def cambiar_foto_perfil():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            user_id = session.get('user_id')
            user = usuario.query.get(user_id)
            
            if not user:
                flash('Error: Usuario no encontrado', 'error')
                return redirect(url_for('panel'))
                
            # Verificar si se subió una foto
            if 'foto' not in request.files:
                flash('Error: No se seleccionó ninguna imagen', 'warning')
                return redirect(url_for('perfil'))
                
            archivo = request.files['foto']
            
            # Verificar si el archivo tiene un nombre
            if archivo.filename == '':
                flash('Error: No se seleccionó ninguna imagen', 'warning')
                return redirect(url_for('perfil'))
                
            # Verificar que sea una imagen
            if not archivo.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                flash('Error: El archivo debe ser una imagen (PNG, JPG, JPEG, GIF)', 'warning')
                return redirect(url_for('perfil'))
                
            # Guardar la imagen
            # Crear la carpeta de uploads si no existe
            uploads_dir = os.path.join(app.static_folder, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Generar un nombre único para la imagen
            from werkzeug.utils import secure_filename
            import uuid
            
            # Obtener la extensión del archivo
            filename, ext = os.path.splitext(secure_filename(archivo.filename))
            # Crear un nombre único con el ID del usuario
            nuevo_nombre = f'usuario_{user_id}_{uuid.uuid4().hex}{ext}'
            ruta_completa = os.path.join(uploads_dir, nuevo_nombre)
            
            # Guardar el archivo
            archivo.save(ruta_completa)
            
            # Actualizar la ruta en la base de datos
            ruta_relativa = f'uploads/{nuevo_nombre}'
            user.foto = ruta_relativa
            db.session.commit()
            
            flash('Foto de perfil actualizada correctamente', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la foto de perfil: {str(e)}', 'error')
            
        return redirect(url_for('perfil'))

    @app.route('/medico/agregar', methods=['POST'])
    def agregar_medico():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            nuevo_medico = Medico(
                nombre=request.form.get('nombresMedico'),
                apellido=request.form.get('apellidosMedico'),
                tipo_documento=request.form.get('tipoDocumento'),
                numero_documento=request.form.get('numeroDocumento'),
                fecha_nacimiento=datetime.strptime(request.form.get('fechaNacimiento'), '%Y-%m-%d'),
                genero=request.form.get('genero'),
                telefono=request.form.get('telefonoMedico'),
                correo=request.form.get('emailMedico'),
                direccion=request.form.get('direccionMedico'),
                departamento_id=request.form.get('departamento'),
                ciudad_id=request.form.get('ciudad'),
                universidad_id=request.form.get('universidad'),
                anios_experiencia=int(request.form.get('aniosExperiencia')),
                especialidad=request.form.get('especialidadMedico'),
                numero_registro=request.form.get('registroMedico'),
                estado='Activo'
            )
            
            db.session.add(nuevo_medico)
            db.session.commit()
            flash('Médico agregado exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar médico: {str(e)}', 'error')
        
        return redirect(url_for('medico'))

    @app.route('/medico/editar/<int:id>', methods=['POST'])
    def editar_medico(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            medico_actual = Medico.query.get_or_404(id)
            medico_actual.nombre = request.form.get('editNombresMedico')
            medico_actual.apellido = request.form.get('editApellidosMedico')
            medico_actual.tipo_documento = request.form.get('editTipoDocumento')
            medico_actual.numero_documento = request.form.get('editNumeroDocumento')
            medico_actual.fecha_nacimiento = datetime.strptime(request.form.get('editFechaNacimiento'), '%Y-%m-%d')
            medico_actual.genero = request.form.get('editGenero')
            medico_actual.telefono = request.form.get('editTelefonoMedico')
            medico_actual.correo = request.form.get('editEmailMedico')
            medico_actual.direccion = request.form.get('editDireccionMedico')
            medico_actual.departamento_id = request.form.get('editDepartamento')
            medico_actual.ciudad_id = request.form.get('editCiudad')
            medico_actual.universidad_id = request.form.get('editUniversidad')
            medico_actual.anios_experiencia = int(request.form.get('editAniosExperiencia'))
            medico_actual.especialidad = request.form.get('editEspecialidadMedico')
            medico_actual.numero_registro = request.form.get('editRegistroMedico')
            medico_actual.estado = request.form.get('editEstado')
            
            db.session.commit()
            flash('Médico actualizado exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar médico: {str(e)}', 'error')
        
        return redirect(url_for('medico'))

    @app.route('/medico/eliminar/<int:id>', methods=['POST'])
    def eliminar_medico(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            medico_actual = Medico.query.get_or_404(id)
            db.session.delete(medico_actual)
            db.session.commit()
            flash('Médico eliminado exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al eliminar médico: {str(e)}', 'error')
        
        return redirect(url_for('medico'))

    @app.route('/paciente/agregar', methods=['POST'])
    def agregar_paciente():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            nuevo_paciente = Paciente(
                nombre=request.form.get('nombrePaciente'),
                apellido=request.form.get('apellidosPaciente'),
                tipo_documento=request.form.get('tipoDocumento'),
                numero_documento=request.form.get('numeroDocumento'),
                fecha_nacimiento=request.form.get('fechaNacimiento'),
                sexo=request.form.get('sexo'),
                grupo_sanguineo=request.form.get('grupoSanguineo'),
                tipo_regimen=request.form.get('tipoRegimen'),
                departamento_id=request.form.get('departamento'),
                ciudad_id=request.form.get('ciudad'),
                telefono=request.form.get('telefonoPaciente'),
                correo=request.form.get('emailPaciente'),
                direccion=request.form.get('direccionPaciente'),
                estado_civil=request.form.get('estadoCivil'),
                ocupacion=request.form.get('ocupacion'),
                eps=request.form.get('eps'),
                contactos_emergencia=request.form.get('contactoEmergencia'),
                telefono_emergencia=request.form.get('telefonoEmergencia')
            )
            
            db.session.add(nuevo_paciente)
            db.session.commit()
            flash('Paciente agregado exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar paciente: {str(e)}', 'error')
        
        return redirect(url_for('pacientes'))

    @app.route('/paciente/editar/<int:id>', methods=['POST'])
    def editar_paciente(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            paciente_actual = Paciente.query.get_or_404(id)
            paciente_actual.nombre = request.form.get('editNombrePaciente')
            paciente_actual.apellido = request.form.get('editApellidosPaciente')
            paciente_actual.tipo_documento = request.form.get('editTipoDocumento')
            paciente_actual.numero_documento = request.form.get('editNumeroDocumento')
            paciente_actual.fecha_nacimiento = request.form.get('editFechaNacimiento')
            paciente_actual.sexo = request.form.get('editSexo')
            paciente_actual.grupo_sanguineo = request.form.get('editGrupoSanguineo')
            paciente_actual.tipo_regimen = request.form.get('editTipoRegimen')
            paciente_actual.departamento_id = request.form.get('editDepartamento')
            paciente_actual.ciudad_id = request.form.get('editCiudad')
            paciente_actual.telefono = request.form.get('editTelefonoPaciente')
            paciente_actual.correo = request.form.get('editEmailPaciente')
            paciente_actual.direccion = request.form.get('editDireccionPaciente')
            paciente_actual.estado_civil = request.form.get('editEstadoCivil')
            paciente_actual.ocupacion = request.form.get('editOcupacion')
            paciente_actual.eps = request.form.get('editEps')
            paciente_actual.contactos_emergencia = request.form.get('editContactoEmergencia')
            paciente_actual.telefono_emergencia = request.form.get('editTelefonoEmergencia')
            
            db.session.commit()
            flash('Paciente actualizado exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar paciente: {str(e)}', 'error')
        
        return redirect(url_for('pacientes'))

    @app.route('/paciente/eliminar/<int:id>', methods=['POST'])
    def eliminar_paciente(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            paciente_actual = Paciente.query.get_or_404(id)
            db.session.delete(paciente_actual)
            db.session.commit()
            flash('Paciente eliminado exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al eliminar paciente: {str(e)}', 'error')
        
        return redirect(url_for('pacientes'))

    @app.route('/cita/agregar', methods=['POST'])
    def agregar_cita():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            nueva_cita = cita(
                paciente_id=request.form.get('pacienteCita'),
                medico_id=request.form.get('medicoCita'),
                fecha=datetime.strptime(request.form.get('fechaCita'), '%Y-%m-%d'),
                hora=datetime.strptime(request.form.get('horaCita'), '%H:%M').time(),
                duracion=request.form.get('duracionCita'),
                tipo_cita=request.form.get('tipoCita'),
                motivo=request.form.get('motivoCita'),
                estado=request.form.get('estadoCita'),
                observaciones=request.form.get('observacionesCita')
            )
            
            db.session.add(nueva_cita)
            db.session.commit()
            flash('Cita agregada exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar cita: {str(e)}', 'error')
        
        return redirect(url_for('cita'))

    @app.route('/cita/editar/<int:id>', methods=['POST'])
    def editar_cita(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            cita_actual = cita.query.get_or_404(id)
            cita_actual.paciente_id = request.form.get('editPacienteCita')
            cita_actual.medico_id = request.form.get('editMedicoCita')
            cita_actual.fecha = datetime.strptime(request.form.get('editFechaCita'), '%Y-%m-%d')
            cita_actual.hora = datetime.strptime(request.form.get('editHoraCita'), '%H:%M').time()
            cita_actual.duracion = request.form.get('editDuracionCita')
            cita_actual.tipo_cita = request.form.get('editTipoCita')
            cita_actual.motivo = request.form.get('editMotivoCita')
            cita_actual.estado = request.form.get('editEstadoCita')
            cita_actual.observaciones = request.form.get('editObservacionesCita')
            
            db.session.commit()
            flash('Cita actualizada exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar cita: {str(e)}', 'error')
        
        return redirect(url_for('cita'))

    @app.route('/cita/eliminar/<int:id>', methods=['POST'])
    def eliminar_cita(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        cita_obj = cita.query.get_or_404(id)
        db.session.delete(cita_obj)
        db.session.commit()
        flash('Cita eliminada exitosamente', 'success')
        return redirect(url_for('cita'))
    
    # Rutas para las historias clínicas (renombradas para evitar conflictos)
    @app.route('/historia/agregar_old', methods=['POST'])
    def agregar_historia_old():
        # Esta ruta está obsoleta y redirige a la nueva implementación
        return redirect(url_for('agregar_historia'))

    @app.route('/historia/editar_old/<int:id>', methods=['POST'])
    def editar_historia_old(id):
        # Esta ruta está obsoleta y redirige a la nueva implementación
        return redirect(url_for('editar_historia', id=id))

    @app.route('/historia/eliminar_old/<int:id>', methods=['POST'])
    def eliminar_historia_old(id):
        # Esta ruta está obsoleta y redirige a la nueva implementación
        return redirect(url_for('eliminar_historia', id=id))

    # Función para exportar historia clínica individual a PDF
    @app.route('/historia/exportar-pdf/<int:id>')
    def exportar_historia_pdf(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Obtener la historia clínica específica con sus relaciones
        historia = historia_clinica.query.join(cita, historia_clinica.id_cita == cita.id)\
            .join(Paciente, cita.paciente_id == Paciente.id)\
            .join(Medico, cita.medico_id == Medico.id)\
            .filter(historia_clinica.id == id).first_or_404()
        
        # Crear un buffer para el PDF
        buffer = BytesIO()
        
        # Crear el documento PDF con tamaño de página A4 portrait
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        
        # Contenedor para los elementos del PDF
        elements = []
        
        # Encabezado del reporte
        elements.extend(create_report_header(doc, "Historia Clínica"))
        
        # Datos del paciente y consulta en formato de tabla con dos columnas
        info_table_data = [
            # Primera fila: títulos de sección
            [
                Paragraph("<font color='#2651a6'><b>DATOS DEL PACIENTE</b></font>", normal_style),
                Paragraph("<font color='#2651a6'><b>DATOS DE LA CONSULTA</b></font>", normal_style),
            ],
            # Segunda fila: contenido
            [
                # Columna 1: Datos del paciente
                Table(
                    [
                        [Paragraph("<b>Nombre:</b>", normal_style), 
                         Paragraph(f"{historia.cita.paciente.nombre} {historia.cita.paciente.apellido}", normal_style)],
                        [Paragraph("<b>Documento:</b>", normal_style), 
                         Paragraph(f"{historia.cita.paciente.tipo_documento} {historia.cita.paciente.numero_documento}", normal_style)],
                        [Paragraph("<b>Teléfono:</b>", normal_style), 
                         Paragraph(f"{historia.cita.paciente.telefono}", normal_style)],
                        [Paragraph("<b>Correo:</b>", normal_style), 
                         Paragraph(f"{historia.cita.paciente.correo}", normal_style)],
                        [Paragraph("<b>EPS:</b>", normal_style), 
                         Paragraph(f"{historia.cita.paciente.eps}", normal_style)]
                    ],
                    colWidths=[65, 165],
                    style=TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ])
                ),
                
                # Columna 2: Datos de la consulta
                Table(
                    [
                        [Paragraph("<b>Fecha:</b>", normal_style), 
                         Paragraph(f"{historia.fecha.strftime('%d/%m/%Y')}", normal_style)],
                        [Paragraph("<b>Médico:</b>", normal_style), 
                         Paragraph(f"Dr. {historia.cita.medico.nombre} {historia.cita.medico.apellido}", normal_style)],
                        [Paragraph("<b>Especialidad:</b>", normal_style), 
                         Paragraph(ESPECIALIDADES.get(historia.cita.medico.especialidad, historia.cita.medico.especialidad), normal_style)],
                        [Paragraph("<b>Número de Cita:</b>", normal_style), 
                         Paragraph(f"C{str(historia.id_cita).zfill(3)}", normal_style)],
                    ],
                    colWidths=[70, 160],
                    style=TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ])
                ),
            ]
        ]
        
        info_table = Table(info_table_data, colWidths=[250, 250])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (0, 0), light_bg),
            ('BACKGROUND', (1, 0), (1, 0), light_bg),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
            ('TOPPADDING', (0, 0), (1, 0), 4),
            ('BOTTOMPADDING', (0, 0), (1, 0), 4),
            ('LEFTPADDING', (0, 0), (1, 0), 4),
            ('RIGHTPADDING', (0, 0), (1, 0), 4),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 10))
        
        # Contenido clínico
        # Datos clínicos
        clinico_style = ParagraphStyle(
            'Clinico',
            parent=normal_style,
            borderPadding=(6, 6, 6, 6),
            backColor=colors.white,
            borderColor=border_color,
            borderWidth=1,
            borderRadius=4,
            spaceAfter=10
        )
        
        # Motivo de consulta con encabezado coloreado
        elements.append(Paragraph("MOTIVO DE CONSULTA", subtitle_style))
        elements.append(Paragraph(historia.motivo_consulta, content_style))
        
        # Antecedentes
        elements.append(Paragraph("ANTECEDENTES", subtitle_style))
        antecedentes = historia.antesedentes if historia.antesedentes else "No se registraron antecedentes"
        elements.append(Paragraph(antecedentes, content_style))
        
        # Diagnóstico y tratamiento en dos columnas
        diag_treat_data = [
            [
                # Columna 1: Diagnóstico
                Table(
                    [
                        [Paragraph("DIAGNÓSTICO", subtitle_style)],
                        [Paragraph(historia.diagnostico, content_style)]
                    ],
                    colWidths=[240],
                    style=TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('GRID', (0, 0), (-1, -1), 0, colors.white),
                    ])
                ),
                
                # Columna 2: Tratamiento
                Table(
                    [
                        [Paragraph("TRATAMIENTO", subtitle_style)],
                        [Paragraph(historia.tratamiento, content_style)]
                    ],
                    colWidths=[240],
                    style=TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('GRID', (0, 0), (-1, -1), 0, colors.white),
                    ])
                ),
            ]
        ]
        
        diag_treat = Table(diag_treat_data, colWidths=[250, 250])
        diag_treat.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        
        elements.append(diag_treat)
        
        # Pie de página
        elements.extend(create_footer(doc))
        
        # Generar PDF
        doc.build(elements)
        
        # Preparar la respuesta
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.mimetype = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=historia_clinica_{id}.pdf'
        
        return response
    
    # Función para exportar todas las historias clínicas a PDF
    @app.route('/historia/exportar-pdf')
    def exportar_historias_pdf():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        historias = historia_clinica.query.join(cita, historia_clinica.id_cita == cita.id)\
            .join(Paciente, cita.paciente_id == Paciente.id)\
            .join(Medico, cita.medico_id == Medico.id).all()
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        elements = []
        elements.extend(create_report_header(doc, "Reporte de Historias Clínicas", "Resumen de historias clínicas del sistema"))
        total_historias = len(historias)
        medicos_distribution = {}
        diagnosticos_distribution = {}
        for h in historias:
            medico_key = f"{h.cita.medico.nombre} {h.cita.medico.apellido}"
            medicos_distribution[medico_key] = medicos_distribution.get(medico_key, 0) + 1
            diagnosticos_distribution[h.diagnostico] = diagnosticos_distribution.get(h.diagnostico, 0) + 1
        plt.figure(figsize=(8, 4))
        plt.pie(medicos_distribution.values(), labels=medicos_distribution.keys(), 
                autopct='%1.1f%%', colors=plt.cm.Pastel1.colors)
        plt.title('Distribución por Médico', pad=20)
        plt.axis('equal')
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        img_buffer.seek(0)
        elements.append(Image(img_buffer, width=500, height=250))
        elements.append(Spacer(1, 20))
        stats_data = [
            ['Total Historias:', str(total_historias)],
            ['Médico más activo:', max(medicos_distribution.items(), key=lambda x: x[1])[0]],
            ['Diagnóstico más común:', max(diagnosticos_distribution.items(), key=lambda x: x[1])[0]]
        ]
        stats_table = create_modern_table(stats_data, [200, 200], header_bg=accent_color)
        elements.append(stats_table)
        elements.append(PageBreak())
        elements.extend(create_report_header(doc, "Listado de Historias Clínicas", "Detalle completo de historias clínicas registradas"))
        data = [['ID', 'Fecha', 'Paciente', 'Médico', 'Especialidad', 'Motivo', 'Diagnóstico', 'Tratamiento']]
        for h in historias:
            especialidad_nombre = ESPECIALIDADES.get(h.cita.medico.especialidad, h.cita.medico.especialidad)
            data.append([
                f'HC{str(h.id).zfill(3)}',
                h.fecha.strftime('%d/%m/%Y'),
                f'{h.cita.paciente.nombre} {h.cita.paciente.apellido}',
                f'Dr. {h.cita.medico.nombre} {h.cita.medico.apellido}',
                especialidad_nombre,
                h.motivo_consulta,
                h.diagnostico,
                h.tratamiento
            ])
        col_widths = [40, 60, 90, 90, 90, 120, 120, 120]
        left_columns = [2, 3, 4, 5, 6, 7]
        table = create_modern_table(data, col_widths, left_columns=left_columns)
        elements.append(table)
        elements.extend(create_footer(doc, "Este reporte contiene información confidencial de historias clínicas"))
        doc.build(elements)
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.mimetype = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=historias_clinicas_report.pdf'
        return response
    
    # Función para exportar citas a PDF
    @app.route('/cita/exportar-pdf')
    def exportar_citas_pdf():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        citas = cita.query.join(Paciente).join(Medico).all()
        
        # Crear un buffer para el PDF
        buffer = BytesIO()
        
        # Crear el documento PDF con tamaño de página más grande (A4 landscape)
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        # Contenedor para los elementos del PDF
        elements = []
        
        # Encabezado del reporte
        elements.extend(create_report_header(doc, "Reporte de Citas", "Resumen de citas del sistema"))
        
        # Estadísticas generales
        total_citas = len(citas)
        estados_distribution = {}
        tipos_distribution = {}
        medicos_distribution = {}
        
        for c in citas:
            estados_distribution[c.estado] = estados_distribution.get(c.estado, 0) + 1
            tipos_distribution[c.tipo_cita] = tipos_distribution.get(c.tipo_cita, 0) + 1
            medico_key = f"{c.medico.nombre} {c.medico.apellido}"
            medicos_distribution[medico_key] = medicos_distribution.get(medico_key, 0) + 1
        
        # Crear gráfico de estados
        plt.figure(figsize=(8, 4))
        plt.pie(estados_distribution.values(), labels=estados_distribution.keys(), 
                autopct='%1.1f%%', colors=plt.cm.Pastel1.colors)
        plt.title('Distribución por Estado', pad=20)
        plt.axis('equal')
        
        # Guardar gráfico en buffer
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        img_buffer.seek(0)
        
        # Agregar gráfico al PDF
        elements.append(Image(img_buffer, width=500, height=250))
        elements.append(Spacer(1, 20))
        
        # Estadísticas resumidas
        stats_data = [
            ['Total Citas:', str(total_citas)],
            ['Estado más común:', max(estados_distribution.items(), key=lambda x: x[1])[0]],
            ['Tipo más común:', max(tipos_distribution.items(), key=lambda x: x[1])[0]],
            ['Médico más solicitado:', max(medicos_distribution.items(), key=lambda x: x[1])[0]]
        ]
        
        stats_table = create_modern_table(stats_data, [200, 200], header_bg=accent_color)
        elements.append(stats_table)
        elements.append(Spacer(1, 20))
        
        # Agregar salto de página
        elements.append(PageBreak())
        
        # Encabezado para la tabla de citas
        elements.extend(create_report_header(doc, "Listado de Citas", "Detalle completo de citas registradas"))
        
        # Tabla de citas
        data = [['ID', 'Fecha', 'Hora', 'Paciente', 'Médico', 'Tipo', 'Estado', 'Motivo']]
        
        for c in citas:
            # Determinar color del estado
            estado_color = success_color if c.estado.lower() == 'completada' else \
                          warning_color if c.estado.lower() == 'pendiente' else \
                          danger_color if c.estado.lower() == 'cancelada' else \
                          colors.black
            
            especialidad_nombre = ESPECIALIDADES.get(c.medico.especialidad, c.medico.especialidad)
            data.append([
                f'C{str(c.id).zfill(3)}',
                c.fecha.strftime('%d/%m/%Y'),
                c.hora.strftime('%H:%M'),
                f'{c.paciente.nombre} {c.paciente.apellido}',
                f'Dr. {c.medico.nombre} {c.medico.apellido}',
                especialidad_nombre,
                Paragraph(c.estado.title(), 
                         ParagraphStyle('Estado', parent=styles['Normal'], 
                                      fontSize=9, textColor=estado_color)),
                c.motivo
            ])
        
        # Crear tabla con anchos específicos
        col_widths = [40, 70, 60, 100, 100, 80, 80, 120]
        left_columns = [3, 4, 5, 6, 8]
        table = create_modern_table(data, col_widths, left_columns=left_columns)
        elements.append(table)
        
        # Pie de página
        elements.extend(create_footer(doc, "Este reporte contiene información confidencial de citas"))
        
        # Generar PDF
        doc.build(elements)
        
        # Preparar la respuesta
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.mimetype = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=citas_report.pdf'
        
        return response
        
    @app.route('/factura/agregar', methods=['POST'])
    def agregar_factura():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            valor = request.form.get('valor')
            if not valor:
                flash('Error: El valor es requerido', 'error')
                return redirect(url_for('factura'))
                
            nueva_factura = Factura(
                id_cita=request.form.get('id_cita'),
                servicio=request.form.get('servicio'),
                valor=float(valor),
                estado=request.form.get('estadoFactura'),
                fecha_emision=datetime.now(),
                fecha_vencimiento=datetime.strptime(request.form.get('fechaVencimientoFactura'), '%Y-%m-%d') if request.form.get('fechaVencimientoFactura') else None,
                metodo_pago=request.form.get('metodoPagoFactura'),
                tipo_factura=request.form.get('tipoFactura'),
                observaciones=request.form.get('observacionesFactura')
            )
            
            db.session.add(nueva_factura)
            db.session.commit()
            flash('Factura agregada exitosamente', 'success')
        except ValueError:
            flash('Error: El valor debe ser un número válido', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar factura: {str(e)}', 'error')
        
        return redirect(url_for('factura'))

    @app.route('/factura/editar/<int:id>', methods=['POST'])
    def editar_factura(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            factura = Factura.query.get_or_404(id)
            
            # Validar que el valor no sea None
            valor = request.form.get('editValorFactura')
            if not valor:
                flash('Error: El valor es requerido', 'error')
                return redirect(url_for('factura'))
            
            factura.servicio = request.form.get('editServicioFactura')
            factura.valor = float(valor)
            factura.estado = request.form.get('editEstadoFactura')
            factura.fecha_vencimiento = datetime.strptime(request.form.get('editFechaVencimientoFactura'), '%Y-%m-%d') if request.form.get('editFechaVencimientoFactura') else None
            factura.metodo_pago = request.form.get('editMetodoPagoFactura')
            factura.observaciones = request.form.get('editObservacionesFactura')
            
            db.session.commit()
            flash('Factura actualizada exitosamente', 'success')
        except ValueError:
            flash('Error: El valor debe ser un número válido', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar factura: {str(e)}', 'error')
        
        return redirect(url_for('factura'))

    @app.route('/factura/eliminar/<int:id>', methods=['POST'])
    def eliminar_factura(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            factura = Factura.query.get_or_404(id)
            db.session.delete(factura)
            db.session.commit()
            flash('Factura eliminada exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al eliminar factura: {str(e)}', 'error')
        
        return redirect(url_for('factura'))

    @app.route('/factura/exportar-pdf')
    def exportar_facturas_pdf():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Obtener todas las facturas con información relacionada
        facturas = Factura.query.join(cita, Factura.id_cita == cita.id)\
            .join(Paciente, cita.paciente_id == Paciente.id)\
            .join(Medico, cita.medico_id == Medico.id).all()
        
        # Crear un buffer para el PDF
        buffer = BytesIO()
        
        # Crear el documento PDF con tamaño de página más grande (A4 landscape)
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        # Contenedor para los elementos del PDF
        elements = []
        
        # Encabezado del reporte
        elements.extend(create_report_header(doc, "Reporte de Facturas", "Resumen de facturas del sistema"))
        
        # Estadísticas generales
        total_facturas = len(facturas)
        total_valor = sum(f.valor for f in facturas)
        estados = {}
        metodos_pago = {}
        
        for f in facturas:
            estados[f.estado] = estados.get(f.estado, 0) + 1
            metodos_pago[f.metodo_pago] = metodos_pago.get(f.metodo_pago, 0) + 1
        
        # Crear gráfico de estados
        plt.figure(figsize=(8, 4))
        plt.pie(estados.values(), labels=estados.keys(), autopct='%1.1f%%', 
                colors=['#28a745', '#ffc107', '#dc3545', '#6c757d'])
        plt.title('Distribución por Estado', pad=20)
        plt.axis('equal')
        
        # Guardar gráfico en buffer
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        img_buffer.seek(0)
        
        # Agregar gráfico al PDF
        elements.append(Image(img_buffer, width=500, height=250))
        elements.append(Spacer(1, 20))
        
        # Estadísticas resumidas
        stats_data = [
            ['Total Facturas:', str(total_facturas)],
            ['Valor Total:', f"${total_valor:,.2f}"],
            ['Promedio por Factura:', f"${(total_valor/total_facturas):,.2f}" if total_facturas > 0 else "$0.00"],
            ['Estado más común:', max(estados.items(), key=lambda x: x[1])[0]],
            ['Método de pago más usado:', max(metodos_pago.items(), key=lambda x: x[1])[0]]
        ]
        
        stats_table = create_modern_table(stats_data, [200, 200], header_bg=accent_color)
        elements.append(stats_table)
        elements.append(Spacer(1, 20))
        
        # Agregar salto de página
        elements.append(PageBreak())
        
        # Encabezado para la tabla de facturas
        elements.extend(create_report_header(doc, "Listado de Facturas", "Detalle completo de facturas registradas"))
        
        # Tabla de facturas
        data = [['ID', 'Fecha', 'Paciente', 'Médico', 'Servicio', 'Valor', 'Estado']]
        for f in facturas:
            estado_color = success_color if f.estado.lower() == 'pagada' else \
                          warning_color if f.estado.lower() == 'pendiente' else \
                          danger_color if f.estado.lower() == 'anulada' else \
                          colors.black
            data.append([
                f'F{str(f.id).zfill(3)}',
                f.fecha_emision.strftime('%d/%m/%Y'),
                f'{f.cita.paciente.nombre} {f.cita.paciente.apellido}',
                f'Dr. {f.cita.medico.nombre} {f.cita.medico.apellido}',
                f.servicio,
                f"${f.valor:,.2f}",
                Paragraph(f.estado.title(), ParagraphStyle('Estado', parent=styles['Normal'], fontSize=9, textColor=estado_color))
            ])
        col_widths = [40, 60, 90, 90, 100, 70, 60]
        left_columns = [2, 3, 4]
        table = create_modern_table(data, col_widths, left_columns=left_columns)
        elements.append(table)
        elements.extend(create_footer(doc, "Este reporte contiene información confidencial"))
        doc.build(elements)
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.mimetype = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=facturas_report.pdf'
        return response

    @app.route('/factura/imprimir/<int:id>')
    def imprimir_factura(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Obtener la factura específica
        factura = Factura.query.get_or_404(id)
        
        # Crear PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        
        # Contenedor para los elementos del PDF
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Título
        title = Paragraph(
            f"<font color='#2651a6'><b>FACTURA MÉDICA</b></font><br/>"
            f"<font size='10'>N° F{str(factura.id).zfill(3)}</font>",
            ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=20,
                alignment=1
            )
        )
        elements.append(title)
        
        # Datos de la factura
        factura_data = [
            ['Fecha de Emisión:', factura.fecha_emision.strftime('%d/%m/%Y')],
            ['Fecha de Vencimiento:', factura.fecha_vencimiento.strftime('%d/%m/%Y')],
            ['Estado:', factura.estado.title()],
            ['Método de Pago:', factura.metodo_pago.title()],
            ['Tipo de Factura:', factura.tipo_factura.title()]
        ]
        
        factura_table = Table(factura_data, colWidths=[150, 350])
        factura_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        
        elements.append(factura_table)
        elements.append(Spacer(1, 20))
        
        # Información del Paciente
        paciente = Paragraph(
            "<font color='#2651a6'><b>INFORMACIÓN DEL PACIENTE</b></font><br/>"
            f"Nombre: {factura.cita.paciente.nombre} {factura.cita.paciente.apellido}<br/>"
            f"Documento: {factura.cita.paciente.tipo_documento} {factura.cita.paciente.numero_documento}<br/>"
            f"EPS: {factura.cita.paciente.eps}",
            ParagraphStyle(
                'Paciente',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=20
            )
        )
        elements.append(paciente)
        
        # Información del Servicio
        servicio = Paragraph(
            "<font color='#2651a6'><b>INFORMACIÓN DEL SERVICIO</b></font><br/>"
            f"Servicio: {factura.servicio}<br/>"
            f"Médico: Dr. {factura.cita.medico.nombre} {factura.cita.medico.apellido}<br/>"
            f"Especialidad: {ESPECIALIDADES.get(factura.cita.medico.especialidad, factura.cita.medico.especialidad)}",
            ParagraphStyle(
                'Servicio',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=20
            )
        )
        elements.append(servicio)
        
        # Detalles de Pago
        pago_data = [
            ['DESCRIPCIÓN', 'VALOR'],
            [factura.servicio, f"${factura.valor:,.2f}"]
        ]
        
        pago_table = Table(pago_data, colWidths=[400, 100])
        pago_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2651a6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ]))
        
        elements.append(pago_table)
        elements.append(Spacer(1, 20))
        
        # Total
        total_data = [
            ['', 'SUBTOTAL', f"${factura.valor:,.2f}"],
            ['', 'IVA (0%)', '$0.00'],
            ['', 'TOTAL', f"${factura.valor:,.2f}"]
        ]
        
        total_table = Table(total_data, colWidths=[300, 100, 100])
        total_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        
        elements.append(total_table)
        
        # Observaciones si existen
        if factura.observaciones:
            elements.append(Spacer(1, 20))
            elements.append(Paragraph(
                "<font color='#2651a6'><b>OBSERVACIONES:</b></font><br/>" + factura.observaciones,
                ParagraphStyle(
                    'Observaciones',
                    parent=styles['Normal'],
                    fontSize=10
                )
            ))
        
        # Pie de página
        elements.append(Spacer(1, 30))
        footer = Paragraph(
            "<font size='8' color='#666666'>"
            "Este documento es una factura generada electrónicamente por MediSoft.<br/>"
            "No requiere firma ni sello para su validez.<br/>"
            "© 2024 MediSoft - Todos los derechos reservados"
            "</font>",
            ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                alignment=1,
                textColor=colors.grey
            )
        )
        elements.append(footer)
        
        # Generar PDF
        doc.build(elements)
        
        # Preparar la respuesta
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.mimetype = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=factura_{id}.pdf'
        
        return response
    
    @app.route('/api/ciudades/<int:departamento_id>', methods=['GET'])
    def obtener_ciudades(departamento_id):
        if 'user_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        
        try:
            ciudades = Ciudad.query.filter_by(departamento_id=departamento_id).order_by(Ciudad.nombre).all()
            return jsonify([{
                'id': ciudad.id,
                'nombre': ciudad.nombre
            } for ciudad in ciudades])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    