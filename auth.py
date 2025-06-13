from flask import render_template, request, redirect, url_for, flash, session, make_response, jsonify, send_file
from model import db, usuario, medico as Medico, paciente as Paciente, cita as Cita, historia_clinica, factura as Factura, configuracion as Configuracion, ciudad as Ciudad, departamento as Departamento, universidad as Universidad, servicio as Servicio, cie10
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from constantes import ESPECIALIDADES
import pandas as pd

# Lista de EPS de Colombia (copiada de app.py)
LISTA_EPS = [
    {'codigo': 'NUEVA EPS', 'nombre': 'Nueva EPS'},
    {'codigo': 'SURA EPS', 'nombre': 'EPS Sura'},
    {'codigo': 'SANITAS EPS', 'nombre': 'EPS Sanitas'},
    {'codigo': 'COMPENSAR EPS', 'nombre': 'Compensar EPS'},
    {'codigo': 'FAMISANAR EPS', 'nombre': 'Famisanar EPS'},
    {'codigo': 'SALUD TOTAL EPS', 'nombre': 'Salud Total EPS'},
    {'codigo': 'COOSALUD EPS', 'nombre': 'Coosalud EPS'},
    {'codigo': 'MUTUAL SER EPS', 'nombre': 'Mutual Ser EPS'},
    {'codigo': 'ALIANSALUD EPS', 'nombre': 'Aliansalud EPS'},
    {'codigo': 'COMFENALCO VALLE EPS', 'nombre': 'Comfenalco Valle EPS'},
    {'codigo': 'EMSSANAR EPS', 'nombre': 'Emssanar EPS'},
    {'codigo': 'ASMET SALUD EPS', 'nombre': 'Asmet Salud EPS'},
    {'codigo': 'MALLAMAS EPS', 'nombre': 'Mallamas EPS'},
    {'codigo': 'PIJAOS SALUD EPS', 'nombre': 'Pijaos Salud EPS'},
    {'codigo': 'CAPITAL SALUD EPS', 'nombre': 'Capital Salud EPS'},
    {'codigo': 'SAVIA SALUD EPS', 'nombre': 'Savia Salud EPS'},
    {'codigo': 'MEDIMAS EPS', 'nombre': 'Medimás EPS'}
]

# Función auxiliar para obtener el nombre de EPS desde el código
def obtener_nombre_eps(codigo_eps):
    if not codigo_eps:
        return 'No especificada'
    for eps in LISTA_EPS:
        if eps['codigo'] == codigo_eps:
            return eps['nombre']
    return codigo_eps  # Si no se encuentra, devolver el código

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
    
    # Obtener configuración dinámica
    config = obtener_configuracion()
    empresa_nombre = config.nombre_empresa if config and config.nombre_empresa else "MediSoft"
    empresa_slogan = config.slogan if config and config.slogan else "Sistema de Gestión Médica"
    
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
            Paragraph(f"<font size='16'><b>{empresa_nombre}</b></font><br/>"
                      f"<font size='9'>{empresa_slogan}</font>", 
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
def create_footer(doc, additional_info=None, historia_fecha=None):
    elements = []
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceAfter=6))
    elements.append(Spacer(1, 10))
    
    # Obtener configuración dinámica
    config = obtener_configuracion()
    empresa_nombre = config.nombre_empresa if config and config.nombre_empresa else "MediSoft"
    
    footer_data = []
    if additional_info:
        footer_data.append([
            Paragraph(additional_info, 
                     ParagraphStyle('FooterInfo', parent=styles['Normal'], fontSize=8, textColor=colors.grey)),
            Paragraph(f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - {empresa_nombre}",
                     ParagraphStyle('FooterDate', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=2))
        ])
    elif historia_fecha:
        # Pie de página específico para historia clínica
        footer_data.append([
            Paragraph(f"Historia clínica creada el {historia_fecha.strftime('%d/%m/%Y')}<br/>"
                     "Documento generado con el software MediSoft", 
                     ParagraphStyle('FooterInfo', parent=styles['Normal'], fontSize=8, textColor=colors.grey)),
            Paragraph(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br/>"
                     f"Sistema: {empresa_nombre}",
                     ParagraphStyle('FooterDate', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=2))
        ])
    else:
        footer_data.append([
            Paragraph(f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - {empresa_nombre}",
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

    # Usar valores por defecto si los campos están vacíos o son None
    # Los campos obligatorios (NOT NULL) deben tener valores no vacíos
    config.nombre_empresa = request.form.get('nombre_empresa', '').strip() or config.nombre_empresa or 'MediSoft'
    config.nit_empresa = request.form.get('nit_empresa', '').strip() or config.nit_empresa or 'Sin NIT'
    config.registro_sanitario = request.form.get('registro_sanitario', '').strip() or config.registro_sanitario or 'Sin registro'
    config.slogan = request.form.get('slogan', '').strip() or config.slogan or 'Sistema de Gestión Médica'

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
                telefono=telefono
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
            servicio_id = request.form.get('servicioCita')
            nueva_cita = Cita(
                paciente_id=request.form.get('pacienteCita'),
                medico_id=request.form.get('medicoCita'),
                servicio_id=servicio_id if servicio_id else None,
                fecha=datetime.strptime(request.form.get('fechaCita'), '%Y-%m-%d'),
                hora=datetime.strptime(request.form.get('horaCita'), '%H:%M').time(),
                duracion=request.form.get('duracionCita'),
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
            cita_actual = Cita.query.get_or_404(id)
            servicio_id = request.form.get('editServicioCita')
            cita_actual.paciente_id = request.form.get('editPacienteCita')
            cita_actual.medico_id = request.form.get('editMedicoCita')
            cita_actual.servicio_id = servicio_id if servicio_id else None
            cita_actual.fecha = datetime.strptime(request.form.get('editFechaCita'), '%Y-%m-%d')
            cita_actual.hora = datetime.strptime(request.form.get('editHoraCita'), '%H:%M').time()
            cita_actual.duracion = request.form.get('editDuracionCita')
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
        
        try:
            cita_actual = Cita.query.get_or_404(id)
            db.session.delete(cita_actual)
            db.session.commit()
            flash('Cita eliminada exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al eliminar cita: {str(e)}', 'error')
        
        return redirect(url_for('cita'))
    
    # Rutas para las historias clínicas
    @app.route('/historia/agregar', methods=['POST'])
    def agregar_historia():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            # Obtener el ID de la cita desde el formulario
            id_cita = request.form.get('citaHistoria')
            
            # Verificar si ya existe una historia clínica para esta cita
            historia_existente = historia_clinica.query.filter_by(id_cita=id_cita).first()
            if historia_existente:
                flash('Ya existe una historia clínica para esta cita', 'warning')
                return redirect(url_for('historia'))
            
            # Crear nueva historia clínica
            nueva_historia = historia_clinica(
                id_cita=id_cita,
                fecha=datetime.now(),
                motivo_consulta=request.form.get('motivoConsulta'),
                antecedentes=request.form.get('antecedentesMedicos'),
                diagnostico_codigo=request.form.get('diagnostico_codigo'),
                tratamiento=request.form.get('tratamiento')
            )
            
            db.session.add(nueva_historia)
            db.session.commit()
            flash('Historia clínica agregada exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar historia clínica: {str(e)}', 'error')
        
        return redirect(url_for('historia'))
    
    @app.route('/historia/editar/<int:id>', methods=['POST'])
    def editar_historia(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            historia_actual = historia_clinica.query.get_or_404(id)
            
            # Actualizar los campos de la historia clínica
            historia_actual.motivo_consulta = request.form.get('motivoConsulta')
            historia_actual.antecedentes = request.form.get('antecedentesMedicos')
            historia_actual.diagnostico_codigo = request.form.get('diagnostico_codigo')
            historia_actual.tratamiento = request.form.get('tratamiento')
            historia_actual.fecha = datetime.now()  # Actualizar fecha de modificación
            
            db.session.commit()
            flash('Historia clínica actualizada exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar historia clínica: {str(e)}', 'error')
        
        return redirect(url_for('historia'))
    
    @app.route('/historia/eliminar/<int:id>', methods=['POST'])
    def eliminar_historia(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            historia_actual = historia_clinica.query.get_or_404(id)
            db.session.delete(historia_actual)
            db.session.commit()
            flash('Historia clínica eliminada exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al eliminar historia clínica: {str(e)}', 'error')
        
        return redirect(url_for('historia'))
    
    # Función para exportar historia clínica individual a PDF
    @app.route('/historia/exportar-pdf/<int:id>')
    def exportar_historia_pdf(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Obtener la historia clínica específica con sus relaciones
        historia = historia_clinica.query.join(Cita, historia_clinica.id_cita == Cita.id)\
            .join(Paciente, Cita.paciente_id == Paciente.id)\
            .join(Medico, Cita.medico_id == Medico.id)\
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
                         Paragraph(f"{obtener_nombre_eps(historia.cita.paciente.eps)}", normal_style)]
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
        antecedentes = historia.antecedentes if historia.antecedentes else "No se registraron antecedentes"
        elements.append(Paragraph(antecedentes, content_style))
        
        # Diagnóstico y tratamiento en dos columnas
        diag_treat_data = [
            [
                # Columna 1: Diagnóstico
                Table(
                    [
                        [Paragraph("DIAGNÓSTICO", subtitle_style)],
                        [Paragraph(historia.diagnostico.descripcion, content_style)]
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
        elements.extend(create_footer(doc, historia_fecha=historia.fecha))
        
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
        try:
            busqueda = request.args.get('busqueda', '')
            medico_id = request.args.get('medico_id', '')
            fecha = request.args.get('fecha', '')
            query = historia_clinica.query.join(Cita, historia_clinica.id_cita == Cita.id)\
                .join(Paciente, Cita.paciente_id == Paciente.id)\
                .join(Medico, Cita.medico_id == Medico.id)
            if busqueda:
                query = query.filter(
                    db.or_(
                        Paciente.nombre.ilike(f'%{busqueda}%'),
                        Paciente.apellido.ilike(f'%{busqueda}%'),
                        Paciente.numero_documento.ilike(f'%{busqueda}%'),
                        Medico.nombre.ilike(f'%{busqueda}%'),
                        Medico.apellido.ilike(f'%{busqueda}%')
                    )
                )
            if medico_id:
                query = query.filter(Medico.id == medico_id)
            if fecha:
                query = query.filter(db.func.date(historia_clinica.fecha) == fecha)
            historias = query.order_by(historia_clinica.fecha.desc()).all()
            
            # Crear un buffer para el PDF
            buffer = BytesIO()
            
            # Crear el documento PDF
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )
            
            # Contenedor para los elementos del PDF
            elements = []
            
            # Encabezado del reporte
            elements.extend(create_report_header(doc, "Reporte de Historias Clínicas", "Resumen de historias clínicas del sistema"))
            
            # Agregar información de filtros aplicados
            filtros_texto = []
            if busqueda:
                filtros_texto.append(f"Búsqueda: {busqueda}")
            if medico_id:
                medico = Medico.query.get(medico_id)
                if medico:
                    filtros_texto.append(f"Médico: Dr. {medico.nombre} {medico.apellido}")
            
            if filtros_texto:
                elements.append(Paragraph(
                    "<font color='#666666'>Filtros aplicados: " + " | ".join(filtros_texto) + "</font>",
                    ParagraphStyle(
                        'Filtros',
                        parent=getSampleStyleSheet()['Normal'],
                        fontSize=8,
                        spaceAfter=20
                    )
                ))
            
            # Estadísticas generales
            total_historias = len(historias)
            medicos_distribution = {}
            diagnosticos_distribution = {}
            
            for h in historias:
                medico_key = f"{h.cita.medico.nombre} {h.cita.medico.apellido}"
                medicos_distribution[medico_key] = medicos_distribution.get(medico_key, 0) + 1
                
                if h.diagnostico:
                    diagnostico_key = h.diagnostico.descripcion
                    diagnosticos_distribution[diagnostico_key] = diagnosticos_distribution.get(diagnostico_key, 0) + 1
            
            # Crear gráfico de médicos
            plt.figure(figsize=(8, 4))
            plt.pie(medicos_distribution.values(), labels=medicos_distribution.keys(), 
                    autopct='%1.1f%%', colors=plt.cm.Pastel1.colors)
            plt.title('Distribución por Médico', pad=20)
            plt.axis('equal')
            
            # Guardar gráfico en buffer
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
            plt.close()
            img_buffer.seek(0)
            
            # Agregar gráfico al PDF
            elements.append(Image(img_buffer, width=400, height=200))
            elements.append(Spacer(1, 20))
            
            # Estadísticas resumidas
            stats_data = [
                ['Total Historias:', str(total_historias)],
                ['Médico más activo:', max(medicos_distribution.items(), key=lambda x: x[1])[0]],
                ['Diagnóstico más común:', max(diagnosticos_distribution.items(), key=lambda x: x[1])[0] if diagnosticos_distribution else 'No hay diagnósticos']
            ]
            
            stats_table = create_modern_table(stats_data, [200, 200], header_bg=accent_color)
            elements.append(stats_table)
            elements.append(Spacer(1, 20))
            
            # Agregar salto de página
            elements.append(PageBreak())
            
            # Encabezado para la tabla de historias
            elements.extend(create_report_header(doc, "Listado de Historias Clínicas", "Detalle completo de historias clínicas registradas"))
            
            # Tabla de historias
            data = [['ID', 'Fecha', 'Paciente', 'Documento', 'Médico', 'Diagnóstico', 'Tratamiento']]
            
            for h in historias:
                data.append([
                    f'H{str(h.id).zfill(3)}',
                    h.fecha.strftime('%d/%m/%Y'),
                    f'{h.cita.paciente.nombre} {h.cita.paciente.apellido}',
                    h.cita.paciente.numero_documento,
                    f'Dr. {h.cita.medico.nombre} {h.cita.medico.apellido}',
                    h.diagnostico.descripcion if h.diagnostico else 'No especificado',
                    h.tratamiento
                ])
            
            # Crear tabla con anchos específicos
            col_widths = [40, 70, 100, 80, 100, 100, 100]
            left_columns = [2, 3, 4, 5, 6]  # Paciente, Documento, Médico, Diagnóstico, Tratamiento
            table = create_modern_table(data, col_widths, left_columns=left_columns)
            elements.append(table)
            
            # Pie de página
            elements.extend(create_footer(doc, "Este reporte contiene información confidencial de historias clínicas"))
            
            # Generar PDF
            doc.build(elements)
            
            # Preparar la respuesta
            buffer.seek(0)
            response = make_response(buffer.getvalue())
            response.mimetype = 'application/pdf'
            
            # Generar nombre de archivo basado en los filtros
            filename = 'historias_clinicas'
            if medico_id:
                medico = Medico.query.get(medico_id)
                if medico:
                    filename += f'_{medico.apellido}'
            if busqueda:
                filename += f'_{busqueda}'
            filename += '.pdf'
            
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            return response
            
        except Exception as e:
            flash(f'Error al exportar historias clínicas: {str(e)}', 'error')
            return redirect(url_for('historia'))

    @app.route('/historia/exportar-excel')
    def exportar_historias_excel():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        try:
            busqueda = request.args.get('busqueda', '')
            medico_id = request.args.get('medico_id', '')
            fecha = request.args.get('fecha', '')
            query = historia_clinica.query.join(Cita, historia_clinica.id_cita == Cita.id)\
                .join(Paciente, Cita.paciente_id == Paciente.id)\
                .join(Medico, Cita.medico_id == Medico.id)
            if busqueda:
                query = query.filter(
                    db.or_(
                        Paciente.nombre.ilike(f'%{busqueda}%'),
                        Paciente.apellido.ilike(f'%{busqueda}%'),
                        Paciente.numero_documento.ilike(f'%{busqueda}%'),
                        Medico.nombre.ilike(f'%{busqueda}%'),
                        Medico.apellido.ilike(f'%{busqueda}%')
                    )
                )
            if medico_id:
                query = query.filter(Medico.id == medico_id)
            if fecha:
                query = query.filter(db.func.date(historia_clinica.fecha) == fecha)
            historias = query.order_by(historia_clinica.fecha.desc()).all()
            
            # Crear un DataFrame con los datos
            data = []
            for h in historias:
                data.append({
                    'ID': f'H{str(h.id).zfill(3)}',
                    'Fecha': h.fecha.strftime('%d/%m/%Y'),
                    'Paciente': f'{h.cita.paciente.nombre} {h.cita.paciente.apellido}',
                    'Documento': h.cita.paciente.numero_documento,
                    'Médico': f'Dr. {h.cita.medico.nombre} {h.cita.medico.apellido}',
                    'Diagnóstico': h.diagnostico.descripcion if h.diagnostico else 'No especificado',
                    'Tratamiento': h.tratamiento,
                    'Antecedentes': h.antecedentes
                })
            
            df = pd.DataFrame(data)
            
            # Crear un buffer para el archivo Excel
            output = BytesIO()
            
            # Crear el archivo Excel con el DataFrame
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Historias Clínicas', index=False)
                
                # Obtener el objeto workbook y worksheet
                workbook = writer.book
                worksheet = writer.sheets['Historias Clínicas']
                
                # Definir formatos
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                # Aplicar formato al encabezado
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 15)  # Ancho de columna
                
                # Ajustar ancho de columnas específicas
                worksheet.set_column('B:B', 12)  # Fecha
                worksheet.set_column('C:C', 25)  # Paciente
                worksheet.set_column('D:D', 15)  # Documento
                worksheet.set_column('E:E', 25)  # Médico
                worksheet.set_column('F:F', 30)  # Diagnóstico
                worksheet.set_column('G:G', 30)  # Tratamiento
                worksheet.set_column('H:H', 30)  # Antecedentes
            
            # Preparar la respuesta
            output.seek(0)
            response = make_response(output.getvalue())
            response.mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
            # Generar nombre de archivo basado en los filtros
            filename = 'historias_clinicas'
            if medico_id:
                medico = Medico.query.get(medico_id)
                if medico:
                    filename += f'_{medico.apellido}'
            if busqueda:
                filename += f'_{busqueda}'
            filename += '.xlsx'
            
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            return response
            
        except Exception as e:
            flash(f'Error al exportar historias clínicas: {str(e)}', 'error')
            return redirect(url_for('historia'))

    @app.route('/cita/exportar-pdf')
    def exportar_citas_pdf():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Obtener los parámetros de filtrado
        busqueda = request.args.get('busqueda', '')
        estado = request.args.get('estado', '')
        fecha = request.args.get('fecha', '')
        
        # Consulta base para citas con JOIN a pacientes y médicos
        query = Cita.query.join(Paciente, Cita.paciente_id == Paciente.id)\
            .join(Medico, Cita.medico_id == Medico.id)
        
        # Aplicar filtros si existen
        if busqueda:
            query = query.filter(
                db.or_(
                    Paciente.nombre.ilike(f'%{busqueda}%'),
                    Paciente.apellido.ilike(f'%{busqueda}%'),
                    Paciente.numero_documento.ilike(f'%{busqueda}%'),
                    Medico.nombre.ilike(f'%{busqueda}%'),
                    Medico.apellido.ilike(f'%{busqueda}%'),
                    Cita.motivo.ilike(f'%{busqueda}%')
                )
            )
        
        if estado:
            query = query.filter(Cita.estado == estado)
        
        if fecha:
            query = query.filter(db.func.date(Cita.fecha) == fecha)
        
        # Obtener las citas filtradas
        citas = query.order_by(Cita.fecha.desc(), Cita.hora.desc()).all()
        
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
        medicos_distribution = {}
        
        for c in citas:
            estados_distribution[c.estado] = estados_distribution.get(c.estado, 0) + 1
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
        data = [['ID', 'Fecha', 'Hora', 'Paciente', 'Médico', 'Estado', 'Motivo']]
        
        for c in citas:
            # Determinar color del estado
            estado_color = success_color if c.estado.lower() == 'completada' else \
                          warning_color if c.estado.lower() == 'pendiente' else \
                          danger_color if c.estado.lower() == 'cancelada' else \
                          colors.black
            
            data.append([
                f'C{str(c.id).zfill(3)}',
                c.fecha.strftime('%d/%m/%Y'),
                c.hora.strftime('%H:%M'),
                f'{c.paciente.nombre} {c.paciente.apellido}',
                f'Dr. {c.medico.nombre} {c.medico.apellido}',
                Paragraph(c.estado.title(), 
                         ParagraphStyle('Estado', parent=styles['Normal'], 
                                      fontSize=9, textColor=estado_color)),
                c.motivo
            ])
        
        # Crear tabla con anchos específicos
        col_widths = [40, 70, 60, 100, 100, 80, 120]
        left_columns = [3, 4, 6]  # Paciente, Médico, Motivo
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
        
        # Generar nombre de archivo basado en los filtros
        filename = 'citas'
        if estado:
            filename += f'_{estado}'
        if fecha:
            filename += f'_{fecha}'
        if busqueda:
            filename += f'_{busqueda}'
        filename += '.pdf'
        
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    # Función para exportar médicos a PDF
    @app.route('/medico/exportar-pdf')
    def exportar_medicos_pdf():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            # Obtener parámetros de filtrado
            busqueda = request.args.get('busqueda', '')
            especialidad = request.args.get('especialidad', '')
            sexo = request.args.get('sexo', '')
            
            # Construir la consulta base
            query = Medico.query
            
            # Aplicar filtros si existen
            if busqueda:
                query = query.filter(
                    db.or_(
                        Medico.nombre.ilike(f'%{busqueda}%'),
                        Medico.apellido.ilike(f'%{busqueda}%'),
                        Medico.numero_documento.ilike(f'%{busqueda}%'),
                        Medico.correo.ilike(f'%{busqueda}%'),
                        Medico.telefono.ilike(f'%{busqueda}%')
                    )
                )
            
            if especialidad:
                query = query.filter(Medico.especialidad == especialidad)
                
            if sexo:
                query = query.filter(Medico.genero == sexo)
            
            # Obtener los médicos
            medicos = query.all()
            
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
            elements.extend(create_report_header(doc, "Reporte de Médicos", "Resumen de médicos del sistema"))
            
            # Agregar información de filtros aplicados
            filtros_texto = []
            if busqueda:
                filtros_texto.append(f"Búsqueda: {busqueda}")
            if especialidad:
                filtros_texto.append(f"Especialidad: {ESPECIALIDADES.get(especialidad, especialidad)}")
            if sexo:
                sexo_texto = 'Masculino' if sexo == 'M' else 'Femenino' if sexo == 'F' else 'Otro'
                filtros_texto.append(f"Género: {sexo_texto}")
            
            if filtros_texto:
                filtros_parrafo = Paragraph(
                    "Filtros aplicados: " + " | ".join(filtros_texto),
                    ParagraphStyle('Filtros', parent=styles['Normal'], fontSize=10, textColor=colors.grey)
                )
                elements.append(filtros_parrafo)
                elements.append(Spacer(1, 10))
            
            # Tabla de médicos
            data = [['ID', 'Nombre', 'Apellido', 'Especialidad', 'Documento', 'Teléfono', 'Correo', 'Estado']]
            
            for m in medicos:
                data.append([
                    f'M{str(m.id).zfill(3)}',
                    m.nombre,
                    m.apellido,
                    ESPECIALIDADES.get(m.especialidad, 'No especificada'),
                    f'{m.tipo_documento} {m.numero_documento}',
                    m.telefono,
                    m.correo,
                    m.estado
                ])
            
            # Crear tabla con anchos específicos
            col_widths = [40, 70, 70, 90, 70, 70, 150, 70]
            left_columns = [1, 2, 3, 4, 5, 6, 7]  # Todas menos el ID
            table = create_modern_table(data, col_widths, left_columns=left_columns)
            elements.append(table)
            
            # Pie de página
            elements.extend(create_footer(doc, "Este reporte contiene información confidencial de médicos"))
            
            # Generar PDF
            doc.build(elements)
            
            # Preparar la respuesta
            buffer.seek(0)
            response = make_response(buffer.getvalue())
            response.mimetype = 'application/pdf'
            
            # Generar nombre de archivo basado en los filtros
            filename = 'medicos'
            if especialidad:
                filename += f'_{especialidad}'
            if sexo:
                filename += f'_{sexo}'
            if busqueda:
                filename += f'_{busqueda}'
            filename += '.pdf'
            
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            return response
            
        except Exception as e:
            flash(f'Error al exportar médicos: {str(e)}', 'error')
            return redirect(url_for('medico'))

    @app.route('/paciente/exportar-pdf')
    def exportar_pacientes_pdf():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            # Obtener los parámetros de filtrado
            busqueda = request.args.get('busqueda', '')
            grupo_sanguineo = request.args.get('grupo_sanguineo', '')
            sexo = request.args.get('sexo', '')
            
            query = Paciente.query
            
            if busqueda:
                query = query.filter(
                    db.or_(
                        Paciente.nombre.ilike(f'%{busqueda}%'),
                        Paciente.apellido.ilike(f'%{busqueda}%'),
                        Paciente.numero_documento.ilike(f'%{busqueda}%'),
                        Paciente.correo.ilike(f'%{busqueda}%'),
                        Paciente.telefono.ilike(f'%{busqueda}%')
                    )
                )
            if grupo_sanguineo:
                query = query.filter(Paciente.grupo_sanguineo == grupo_sanguineo)
            if sexo:
                query = query.filter(Paciente.sexo == sexo)
            
            pacientes = query.order_by(Paciente.id.asc()).all()
            
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
            elements.extend(create_report_header(doc, "Reporte de Pacientes", "Resumen de pacientes del sistema"))
            
            # Agregar información de filtros aplicados
            filtros_texto = []
            if busqueda:
                filtros_texto.append(f"Búsqueda: {busqueda}")
            if grupo_sanguineo:
                filtros_texto.append(f"Grupo Sanguíneo: {grupo_sanguineo}")
            if sexo:
                filtros_texto.append(f"Sexo: {sexo}")
            
            if filtros_texto:
                filtros_paragraph = Paragraph(
                    "<font color='#2651a6'><b>Filtros aplicados:</b></font><br/>" + 
                    "<br/>".join(filtros_texto),
                    ParagraphStyle(
                        'Filtros',
                        parent=styles['Normal'],
                        fontSize=10,
                        spaceAfter=20
                    )
                )
                elements.append(filtros_paragraph)
            
            # Estadísticas generales
            total_pacientes = len(pacientes)
            eps_distribution = {}
            ciudades_distribution = {}
            
            for p in pacientes:
                eps_nombre = obtener_nombre_eps(p.eps)
                eps_distribution[eps_nombre] = eps_distribution.get(eps_nombre, 0) + 1
                if hasattr(p, 'ciudad_id'):
                    ciudad_obj = Ciudad.query.get(p.ciudad_id)
                    if ciudad_obj:
                        ciudad_nombre = ciudad_obj.nombre
                        ciudades_distribution[ciudad_nombre] = ciudades_distribution.get(ciudad_nombre, 0) + 1
            
            # Crear gráfico de EPS
            plt.figure(figsize=(8, 4))
            plt.pie(eps_distribution.values(), labels=eps_distribution.keys(), 
                    autopct='%1.1f%%', colors=plt.cm.Pastel1.colors)
            plt.title('Distribución por EPS', pad=20)
            plt.axis('equal')
            
            # Guardar gráfico en buffer
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
            plt.close()
            img_buffer.seek(0)
            
            # Agregar gráfico al PDF
            elements.append(Image(img_buffer, width=500, height=250))
            elements.append(Spacer(1, 20))
            
            # Tabla de pacientes con datos esenciales
            data = [['ID', 'Nombre Completo', 'Documento', 'Edad', 'Sexo', 'EPS', 'Teléfono']]
            
            for p in pacientes:
                # Calcular edad
                edad = ''
                if p.fecha_nacimiento:
                    hoy = datetime.now()
                    edad = hoy.year - p.fecha_nacimiento.year - ((hoy.month, hoy.day) < (p.fecha_nacimiento.month, p.fecha_nacimiento.day))
                
                data.append([
                    f'P{str(p.id).zfill(3)}',
                    f'{p.nombre} {p.apellido}',
                    f'{p.tipo_documento} {p.numero_documento}',
                    edad,
                    'Masculino' if p.sexo == 'M' else 'Femenino' if p.sexo == 'F' else 'Otro',
                    obtener_nombre_eps(p.eps),
                    p.telefono
                ])
            
            # Ajustar anchos de columna para mejor visualización
            col_widths = [50, 150, 120, 40, 60, 120, 80]
            left_columns = [1, 2, 5, 6]  # Columnas que se alinean a la izquierda
            
            table = create_modern_table(data, col_widths, left_columns=left_columns)
            elements.append(table)
            
            # Agregar estadísticas resumidas
            elements.append(Spacer(1, 20))
            stats_data = [
                ['Total Pacientes:', str(total_pacientes)],
                ['EPS más común:', max(eps_distribution.items(), key=lambda x: x[1])[0] if eps_distribution else 'N/A'],
                ['Ciudad más común:', max(ciudades_distribution.items(), key=lambda x: x[1])[0] if ciudades_distribution else 'N/A']
            ]
            
            stats_table = create_modern_table(stats_data, [200, 200], header_bg=accent_color)
            elements.append(stats_table)
            
            elements.extend(create_footer(doc, "Este reporte contiene información confidencial de pacientes"))
            doc.build(elements)
            buffer.seek(0)
            response = make_response(buffer.getvalue())
            response.mimetype = 'application/pdf'
            
            # Generar nombre de archivo basado en los filtros
            filename = 'pacientes'
            if grupo_sanguineo:
                filename += f'_{grupo_sanguineo}'
            if sexo:
                filename += f'_{sexo}'
            if busqueda:
                filename += f'_{busqueda}'
            filename += '.pdf'
            
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            return response
            
        except Exception as e:
            flash(f'Error al exportar pacientes: {str(e)}', 'error')
            return redirect(url_for('pacientes'))

    @app.route('/factura/agregar', methods=['POST'])
    def agregar_factura():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            valor = request.form.get('valor')
            if not valor:
                flash('Error: El valor es requerido', 'error')
                return redirect(url_for('factura'))
                
            # Obtener el servicio seleccionado
            servicio_id = request.form.get('servicio_id')
            servicio_nombre = ''
            if servicio_id:
                servicio_obj = Servicio.query.get(servicio_id)
                if servicio_obj:
                    servicio_nombre = servicio_obj.nombre
            
            nueva_factura = Factura(
                id_cita=request.form.get('id_cita'),
                servicio_id=servicio_id if servicio_id else None,
                servicio=servicio_nombre or 'Consulta General',
                valor=float(valor),
                estado=request.form.get('estadoFactura'),
                fecha_emision=datetime.now(),
                fecha_vencimiento=datetime.strptime(request.form.get('fechaVencimientoFactura'), '%Y-%m-%d') if request.form.get('fechaVencimientoFactura') else None,
                metodo_pago=request.form.get('metodoPagoFactura'),
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
            
            # Obtener el servicio seleccionado
            servicio_id = request.form.get('editServicioId')
            servicio_nombre = factura.servicio  # Mantener el nombre actual por defecto
            if servicio_id:
                servicio_obj = Servicio.query.get(servicio_id)
                if servicio_obj:
                    servicio_nombre = servicio_obj.nombre
            
            factura.servicio_id = servicio_id if servicio_id else None
            factura.servicio = servicio_nombre
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
        
        try:
            # Obtener los parámetros de filtrado
            busqueda = request.args.get('busqueda', '')
            estado = request.args.get('estado', '')
            fecha = request.args.get('fecha', '')
            
            # Consulta base para facturas con JOIN a citas, pacientes y médicos
            query = Factura.query.join(Cita, Factura.id_cita == Cita.id)\
                .join(Paciente, Cita.paciente_id == Paciente.id)\
                .join(Medico, Cita.medico_id == Medico.id)
            
            # Aplicar filtros si existen
            if busqueda:
                query = query.filter(
                    db.or_(
                        Paciente.nombre.ilike(f'%{busqueda}%'),
                        Paciente.apellido.ilike(f'%{busqueda}%'),
                        Paciente.numero_documento.ilike(f'%{busqueda}%'),
                        Medico.nombre.ilike(f'%{busqueda}%'),
                        Medico.apellido.ilike(f'%{busqueda}%'),
                        Factura.servicio.ilike(f'%{busqueda}%')
                    )
                )
            
            if estado:
                query = query.filter(Factura.estado == estado)
            
            if fecha:
                query = query.filter(db.func.date(Factura.fecha_emision) == fecha)
            
            # Obtener las facturas filtradas
            facturas = query.order_by(Factura.fecha_emision.desc()).all()
            
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
            
            # Agregar información de filtros aplicados
            filtros_texto = []
            if busqueda:
                filtros_texto.append(f"Búsqueda: {busqueda}")
            if estado:
                filtros_texto.append(f"Estado: {estado.title()}")
            if fecha:
                filtros_texto.append(f"Fecha: {fecha}")
            
            if filtros_texto:
                elements.append(Paragraph(
                    "<font color='#666666'>Filtros aplicados: " + " | ".join(filtros_texto) + "</font>",
                    ParagraphStyle(
                        'Filtros',
                        parent=getSampleStyleSheet()['Normal'],
                        fontSize=8,
                        spaceAfter=20
                    )
                ))
            
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
            plt.pie(estados.values(), labels=[e.title() for e in estados.keys()], autopct='%1.1f%%')
            plt.title('Distribución por Estado')
            
            # Guardar el gráfico en un buffer
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight')
            plt.close()
            
            # Agregar el gráfico al PDF
            img_buffer.seek(0)
            elements.append(Image(img_buffer, width=400, height=200))
            elements.append(Spacer(1, 20))
            
            # Crear tabla de facturas
            data = [['#', 'Paciente', 'Servicio', 'Valor', 'Estado', 'Fecha', 'Método Pago']]
            
            for f in facturas:
                data.append([
                    f'F{str(f.id).zfill(3)}',
                    f'{f.cita.paciente.nombre} {f.cita.paciente.apellido}',
                    f.servicio,
                    f'${f.valor:,.0f}',
                    f.estado.title(),
                    f.fecha_emision.strftime('%d/%m/%Y'),
                    f.metodo_pago.title()
                ])
            
            # Crear la tabla
            table = Table(data, colWidths=[50, 150, 150, 80, 80, 80, 100])
            
            # Estilo de la tabla
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2651a6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
                ('ALIGN', (3, 1), (3, -1), 'RIGHT'),  # Alinear valores a la derecha
            ]))
            
            elements.append(table)
            
            # Agregar resumen
            elements.append(Spacer(1, 20))
            elements.append(Paragraph(
                f"<b>Resumen:</b><br/>"
                f"Total Facturas: {total_facturas}<br/>"
                f"Valor Total: ${total_valor:,.0f} COP",
                ParagraphStyle(
                    'Resumen',
                    parent=getSampleStyleSheet()['Normal'],
                    fontSize=10,
                    spaceAfter=20
                )
            ))
            
            # Generar PDF
            doc.build(elements)
            
            # Preparar la respuesta
            buffer.seek(0)
            response = make_response(buffer.getvalue())
            response.mimetype = 'application/pdf'
            
            # Generar nombre de archivo basado en los filtros
            filename = 'facturas'
            if estado:
                filename += f'_{estado}'
            if fecha:
                filename += f'_{fecha}'
            if busqueda:
                filename += f'_{busqueda}'
            filename += '.pdf'
            
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            return response
            
        except Exception as e:
            flash(f'Error al exportar facturas: {str(e)}', 'error')
            return redirect(url_for('factura'))

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
            ['Método de Pago:', factura.metodo_pago.title()]
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
            f"EPS: {obtener_nombre_eps(factura.cita.paciente.eps)}",
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
            [factura.servicio, f"${factura.valor:,.0f} COP"]
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
            ['', 'SUBTOTAL', f"${factura.valor:,.0f} COP"],
            ['', 'TOTAL', f"${factura.valor:,.0f} COP"]
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
        
        # Obtener configuración dinámica
        config = obtener_configuracion()
        empresa_nombre = config.nombre_empresa if config and config.nombre_empresa else "MediSoft"
        
        footer = Paragraph(
            "<font size='8' color='#666666'>"
            f"Este documento es una factura generada electrónicamente por {empresa_nombre}.<br/>"
            "No requiere firma ni sello para su validez.<br/>"
            f"© 2024 {empresa_nombre} - Todos los derechos reservados"
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
    
    # CRUD de Servicios
    @app.route('/servicio/agregar', methods=['POST'])
    def agregar_servicio():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            # Verificar que el código no exista
            codigo_existente = db.session.query(Servicio).filter_by(codigo=request.form['codigo']).first()
            if codigo_existente:
                flash('Error: Ya existe un servicio con ese código', 'error')
                return redirect(url_for('servicios'))
            
            nuevo_servicio = Servicio(
                codigo=request.form['codigo'],
                nombre=request.form['nombre'],
                precio=float(request.form['precio']),
                tipo=request.form['tipo']
            )
            
            db.session.add(nuevo_servicio)
            db.session.commit()
            flash('Servicio agregado exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar servicio: {str(e)}', 'error')
        
        return redirect(url_for('servicios'))

    @app.route('/servicio/editar/<int:id>', methods=['POST'])
    def editar_servicio(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            servicio_obj = Servicio.query.get_or_404(id)
            
            # Verificar que el código no exista en otro servicio
            codigo_existente = db.session.query(Servicio).filter(
                Servicio.codigo == request.form['editCodigo'],
                Servicio.id != id
            ).first()
            
            if codigo_existente:
                flash('Error: Ya existe otro servicio con ese código', 'error')
                return redirect(url_for('servicios'))
            
            servicio_obj.codigo = request.form['editCodigo']
            servicio_obj.nombre = request.form['editNombre']
            servicio_obj.precio = float(request.form['editPrecio'])
            servicio_obj.tipo = request.form['editTipo']
            
            db.session.commit()
            flash('Servicio actualizado exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar servicio: {str(e)}', 'error')
        
        return redirect(url_for('servicios'))

    @app.route('/servicio/eliminar/<int:id>', methods=['POST'])
    def eliminar_servicio(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            servicio_obj = Servicio.query.get_or_404(id)
            
            # Verificar si el servicio está siendo usado en citas o facturas
            citas_asociadas = db.session.query(Cita).filter_by(servicio_id=id).count()
            facturas_asociadas = db.session.query(Factura).filter_by(servicio_id=id).count()
            
            if citas_asociadas > 0 or facturas_asociadas > 0:
                flash('No se puede eliminar el servicio porque está siendo usado en citas o facturas', 'error')
                return redirect(url_for('servicios'))
            
            db.session.delete(servicio_obj)
            db.session.commit()
            flash('Servicio eliminado exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al eliminar servicio: {str(e)}', 'error')
        
        return redirect(url_for('servicios'))

    @app.route('/api/servicios', methods=['GET'])
    def obtener_servicios():
        if 'user_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        
        try:
            servicios = db.session.query(Servicio).order_by(Servicio.nombre).all()
            return jsonify([{
                'id': s.id,
                'codigo': s.codigo,
                'nombre': s.nombre,
                'precio': s.precio,
                'tipo': s.tipo
            } for s in servicios])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Función para exportar cita individual a PDF
    @app.route('/cita/exportar-pdf/<int:id>')
    def exportar_cita_pdf(id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Obtener la cita específica con sus relaciones
        cita = Cita.query.join(Paciente, Cita.paciente_id == Paciente.id)\
            .join(Medico, Cita.medico_id == Medico.id)\
            .filter(Cita.id == id).first_or_404()
        
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
        elements.extend(create_report_header(doc, "Cita Médica"))
        
        # Datos del paciente y cita en formato de tabla con dos columnas
        info_table_data = [
            # Primera fila: títulos de sección
            [
                Paragraph("<font color='#2651a6'><b>INFORMACIÓN DEL PACIENTE</b></font>", normal_style),
                Paragraph("<font color='#2651a6'><b>INFORMACIÓN DE LA CITA</b></font>", normal_style),
            ],
            # Segunda fila: contenido
            [
                # Columna 1: Datos del paciente
                Table(
                    [
                        [Paragraph("<b>Nombre:</b>", normal_style), 
                         Paragraph(f"{cita.paciente.nombre} {cita.paciente.apellido}", normal_style)],
                        [Paragraph("<b>Documento:</b>", normal_style), 
                         Paragraph(f"{cita.paciente.tipo_documento} {cita.paciente.numero_documento}", normal_style)],
                        [Paragraph("<b>Teléfono:</b>", normal_style), 
                         Paragraph(f"{cita.paciente.telefono}", normal_style)],
                        [Paragraph("<b>Correo:</b>", normal_style), 
                         Paragraph(f"{cita.paciente.correo}", normal_style)],
                        [Paragraph("<b>EPS:</b>", normal_style), 
                         Paragraph(f"{obtener_nombre_eps(cita.paciente.eps)}", normal_style)]
                    ],
                    colWidths=[65, 165],
                    style=TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ])
                ),
                
                # Columna 2: Datos de la cita
                Table(
                    [
                        [Paragraph("<b>Número de Cita:</b>", normal_style), 
                         Paragraph(f"C{str(cita.id).zfill(3)}", normal_style)],
                        [Paragraph("<b>Fecha:</b>", normal_style), 
                         Paragraph(f"{cita.fecha.strftime('%d/%m/%Y')}", normal_style)],
                        [Paragraph("<b>Hora:</b>", normal_style), 
                         Paragraph(f"{cita.hora.strftime('%H:%M')}", normal_style)],
                        [Paragraph("<b>Duración:</b>", normal_style), 
                         Paragraph(f"{cita.duracion} minutos", normal_style)],
                        [Paragraph("<b>Estado:</b>", normal_style), 
                         Paragraph(f"{cita.estado.title()}", normal_style)]
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
        elements.append(Spacer(1, 15))
        
        # Información del médico
        elements.append(Paragraph("INFORMACIÓN DEL MÉDICO", subtitle_style))
        medico_info = f"Dr. {cita.medico.nombre} {cita.medico.apellido}<br/>" \
                     f"Especialidad: {ESPECIALIDADES.get(cita.medico.especialidad, cita.medico.especialidad)}<br/>" \
                     f"Registro: {cita.medico.numero_registro}<br/>" \
                     f"Teléfono: {cita.medico.telefono}<br/>" \
                     f"Correo: {cita.medico.correo}"
        elements.append(Paragraph(medico_info, content_style))
        elements.append(Spacer(1, 15))
        
        # Información del servicio si existe
        if cita.servicio:
            elements.append(Paragraph("SERVICIO PROGRAMADO", subtitle_style))
            servicio_info = f"Código: {cita.servicio.codigo}<br/>" \
                           f"Servicio: {cita.servicio.nombre}<br/>" \
                           f"Tipo: {cita.servicio.tipo.title()}<br/>" \
                           f"Valor: ${cita.servicio.precio:,.0f} COP"
            elements.append(Paragraph(servicio_info, content_style))
            elements.append(Spacer(1, 15))
        
        # Motivo y observaciones
        elements.append(Paragraph("MOTIVO DE LA CITA", subtitle_style))
        elements.append(Paragraph(cita.motivo, content_style))
        
        if cita.observaciones:
            elements.append(Paragraph("OBSERVACIONES", subtitle_style))
            elements.append(Paragraph(cita.observaciones, content_style))
        
        # Pie de página específico para citas
        elements.extend(create_footer(doc, historia_fecha=cita.fecha))
        
        # Generar PDF
        doc.build(elements)
        
        # Preparar la respuesta
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.mimetype = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=cita_{id}.pdf'
        
        return response

    @app.route('/factura/exportar-excel')
    def exportar_facturas_excel():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            # Obtener los parámetros de filtrado
            busqueda = request.args.get('busqueda', '')
            estado = request.args.get('estado', '')
            fecha = request.args.get('fecha', '')
            
            # Consulta base para facturas con JOIN a citas, pacientes y médicos
            query = Factura.query.join(Cita, Factura.id_cita == Cita.id)\
                .join(Paciente, Cita.paciente_id == Paciente.id)\
                .join(Medico, Cita.medico_id == Medico.id)
            
            # Aplicar filtros si existen
            if busqueda:
                query = query.filter(
                    db.or_(
                        Paciente.nombre.ilike(f'%{busqueda}%'),
                        Paciente.apellido.ilike(f'%{busqueda}%'),
                        Paciente.numero_documento.ilike(f'%{busqueda}%'),
                        Medico.nombre.ilike(f'%{busqueda}%'),
                        Medico.apellido.ilike(f'%{busqueda}%'),
                        Factura.servicio.ilike(f'%{busqueda}%')
                    )
                )
            
            if estado:
                query = query.filter(Factura.estado == estado)
            
            if fecha:
                query = query.filter(db.func.date(Factura.fecha_emision) == fecha)
            
            # Obtener las facturas filtradas
            facturas = query.order_by(Factura.fecha_emision.desc()).all()
            
            # Crear un DataFrame con los datos
            data = []
            for f in facturas:
                data.append({
                    'Número Factura': f'F{str(f.id).zfill(3)}',
                    'Paciente': f'{f.cita.paciente.nombre} {f.cita.paciente.apellido}',
                    'Documento': f'{f.cita.paciente.tipo_documento} {f.cita.paciente.numero_documento}',
                    'EPS': f.cita.paciente.eps,
                    'Médico': f'Dr. {f.cita.medico.nombre} {f.cita.medico.apellido}',
                    'Especialidad': ESPECIALIDADES.get(f.cita.medico.especialidad, f.cita.medico.especialidad),
                    'Servicio': f.servicio,
                    'Valor': f.valor,
                    'Estado': f.estado.title(),
                    'Fecha Emisión': f.fecha_emision.strftime('%d/%m/%Y'),
                    'Fecha Vencimiento': f.fecha_vencimiento.strftime('%d/%m/%Y'),
                    'Método Pago': f.metodo_pago.title(),
                    'Observaciones': f.observaciones or ''
                })
            
            df = pd.DataFrame(data)
            
            # Crear un buffer para el archivo Excel
            output = BytesIO()
            
            # Crear el archivo Excel con el DataFrame
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Facturas', index=False)
                
                # Obtener el objeto workbook y worksheet
                workbook = writer.book
                worksheet = writer.sheets['Facturas']
                
                # Definir formatos
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#2651a6',
                    'font_color': 'white',
                    'border': 1
                })
                
                # Formato para valores monetarios
                money_format = workbook.add_format({
                    'num_format': '$#,##0',
                    'border': 1
                })
                
                # Formato para fechas
                date_format = workbook.add_format({
                    'num_format': 'dd/mm/yyyy',
                    'border': 1
                })
                
                # Formato para celdas normales
                cell_format = workbook.add_format({
                    'border': 1
                })
                
                # Aplicar formato al encabezado
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 15)  # Ancho de columna
                
                # Aplicar formatos específicos a las columnas
                for row_num in range(len(df)):
                    # Formato para valores monetarios
                    worksheet.write(row_num + 1, 7, df['Valor'].iloc[row_num], money_format)
                    
                    # Formato para fechas
                    worksheet.write(row_num + 1, 9, df['Fecha Emisión'].iloc[row_num], date_format)
                    worksheet.write(row_num + 1, 10, df['Fecha Vencimiento'].iloc[row_num], date_format)
                    
                    # Formato para el resto de celdas
                    for col_num in range(len(df.columns)):
                        if col_num not in [7, 9, 10]:  # Excluir columnas con formato especial
                            worksheet.write(row_num + 1, col_num, df.iloc[row_num, col_num], cell_format)
            
            # Preparar la respuesta
            output.seek(0)
            response = make_response(output.getvalue())
            response.mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
            # Generar nombre de archivo basado en los filtros
            filename = 'facturas'
            if estado:
                filename += f'_{estado}'
            if fecha:
                filename += f'_{fecha}'
            if busqueda:
                filename += f'_{busqueda}'
            filename += '.xlsx'
            
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            return response
            
        except Exception as e:
            flash(f'Error al exportar facturas: {str(e)}', 'error')
            return redirect(url_for('factura'))

    @app.route('/cita/exportar-excel')
    def exportar_citas_excel():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            # Obtener los parámetros de filtrado
            busqueda = request.args.get('busqueda', '')
            estado = request.args.get('estado', '')
            fecha = request.args.get('fecha', '')
            
            # Consulta base para citas con JOIN a pacientes y médicos
            query = Cita.query.join(Paciente, Cita.paciente_id == Paciente.id)\
                .join(Medico, Cita.medico_id == Medico.id)
            
            # Aplicar filtros si existen
            if busqueda:
                query = query.filter(
                    db.or_(
                        Paciente.nombre.ilike(f'%{busqueda}%'),
                        Paciente.apellido.ilike(f'%{busqueda}%'),
                        Paciente.numero_documento.ilike(f'%{busqueda}%'),
                        Medico.nombre.ilike(f'%{busqueda}%'),
                        Medico.apellido.ilike(f'%{busqueda}%'),
                        Cita.motivo.ilike(f'%{busqueda}%')
                    )
                )
            
            if estado:
                query = query.filter(Cita.estado == estado)
            
            if fecha:
                query = query.filter(db.func.date(Cita.fecha) == fecha)
            
            # Obtener las citas filtradas
            citas = query.order_by(Cita.fecha.desc(), Cita.hora.desc()).all()
            
            # Crear un DataFrame con los datos
            data = []
            for c in citas:
                data.append({
                    'Número Cita': f'C{str(c.id).zfill(3)}',
                    'Paciente': f'{c.paciente.nombre} {c.paciente.apellido}',
                    'Documento': f'{c.paciente.tipo_documento} {c.paciente.numero_documento}',
                    'EPS': obtener_nombre_eps(c.paciente.eps),
                    'Médico': f'Dr. {c.medico.nombre} {c.medico.apellido}',
                    'Especialidad': ESPECIALIDADES.get(c.medico.especialidad, c.medico.especialidad),
                    'Fecha': c.fecha.strftime('%d/%m/%Y'),
                    'Hora': c.hora.strftime('%H:%M'),
                    'Duración': f'{c.duracion} min',
                    'Estado': c.estado.title(),
                    'Motivo': c.motivo,
                    'Observaciones': c.observaciones or ''
                })
            
            df = pd.DataFrame(data)
            
            # Crear un buffer para el archivo Excel
            output = BytesIO()
            
            # Crear el archivo Excel con el DataFrame
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Citas', index=False)
                
                # Obtener el objeto workbook y worksheet
                workbook = writer.book
                worksheet = writer.sheets['Citas']
                
                # Definir formatos
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#2651a6',
                    'font_color': 'white',
                    'border': 1
                })
                
                # Formato para fechas
                date_format = workbook.add_format({
                    'num_format': 'dd/mm/yyyy',
                    'border': 1
                })
                
                # Formato para celdas normales
                cell_format = workbook.add_format({
                    'border': 1
                })
                
                # Aplicar formato al encabezado
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 15)  # Ancho de columna
                
                # Aplicar formatos específicos a las columnas
                for row_num in range(len(df)):
                    # Formato para fechas
                    worksheet.write(row_num + 1, 6, df['Fecha'].iloc[row_num], date_format)
                    
                    # Formato para el resto de celdas
                    for col_num in range(len(df.columns)):
                        if col_num != 6:  # Excluir columna de fecha
                            worksheet.write(row_num + 1, col_num, df.iloc[row_num, col_num], cell_format)
            
            # Preparar la respuesta
            output.seek(0)
            response = make_response(output.getvalue())
            response.mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
            # Generar nombre de archivo basado en los filtros
            filename = 'citas'
            if estado:
                filename += f'_{estado}'
            if fecha:
                filename += f'_{fecha}'
            if busqueda:
                filename += f'_{busqueda}'
            filename += '.xlsx'
            
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            return response
            
        except Exception as e:
            flash(f'Error al exportar citas: {str(e)}', 'error')
            return redirect(url_for('cita'))

    @app.route('/paciente/exportar-excel')
    def exportar_pacientes_excel():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            # Obtener los parámetros de filtrado
            busqueda = request.args.get('busqueda', '')
            grupo_sanguineo = request.args.get('grupo_sanguineo', '')
            sexo = request.args.get('sexo', '')
            
            query = Paciente.query
            
            if busqueda:
                query = query.filter(
                    db.or_(
                        Paciente.nombre.ilike(f'%{busqueda}%'),
                        Paciente.apellido.ilike(f'%{busqueda}%'),
                        Paciente.numero_documento.ilike(f'%{busqueda}%'),
                        Paciente.correo.ilike(f'%{busqueda}%'),
                        Paciente.telefono.ilike(f'%{busqueda}%')
                    )
                )
            if grupo_sanguineo:
                query = query.filter(Paciente.grupo_sanguineo == grupo_sanguineo)
            if sexo:
                query = query.filter(Paciente.sexo == sexo)
            
            pacientes = query.order_by(Paciente.id.asc()).all()
            
            # Crear un DataFrame con los datos
            data = []
            for p in pacientes:
                data.append({
                    'ID': p.id,
                    'Nombre': p.nombre,
                    'Apellido': p.apellido,
                    'Tipo Documento': p.tipo_documento,
                    'Número Documento': p.numero_documento,
                    'Fecha Nacimiento': p.fecha_nacimiento.strftime('%d/%m/%Y'),
                    'Sexo': p.sexo,
                    'Grupo Sanguíneo': p.grupo_sanguineo,
                    'EPS': obtener_nombre_eps(p.eps),
                    'Teléfono': p.telefono,
                    'Correo': p.correo,
                    'Dirección': p.direccion,
                    'Ciudad': p.ciudad.nombre if hasattr(p.ciudad, 'nombre') else ''
                })
            
            df = pd.DataFrame(data)
            
            # Crear un buffer para el archivo Excel
            output = BytesIO()
            
            # Crear el archivo Excel con el DataFrame
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Pacientes', index=False)
                
                # Obtener el objeto workbook y worksheet
                workbook = writer.book
                worksheet = writer.sheets['Pacientes']
                
                # Definir formatos
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#2651a6',
                    'font_color': 'white',
                    'border': 1
                })
                
                # Formato para fechas
                date_format = workbook.add_format({
                    'num_format': 'dd/mm/yyyy',
                    'border': 1
                })
                
                # Formato para celdas normales
                cell_format = workbook.add_format({
                    'border': 1
                })
                
                # Aplicar formato al encabezado
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 15)  # Ancho de columna
                
                # Aplicar formatos específicos a las columnas
                for row_num in range(len(df)):
                    # Formato para fechas
                    worksheet.write(row_num + 1, 5, df['Fecha Nacimiento'].iloc[row_num], date_format)
                    
                    # Formato para el resto de celdas
                    for col_num in range(len(df.columns)):
                        if col_num != 5:  # Excluir columna de fecha
                            worksheet.write(row_num + 1, col_num, df.iloc[row_num, col_num], cell_format)
            
            # Preparar la respuesta
            output.seek(0)
            response = make_response(output.getvalue())
            response.mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
            # Generar nombre de archivo basado en los filtros
            filename = 'pacientes'
            if grupo_sanguineo:
                filename += f'_{grupo_sanguineo}'
            if sexo:
                filename += f'_{sexo}'
            if busqueda:
                filename += f'_{busqueda}'
            filename += '.xlsx'
            
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            return response
            
        except Exception as e:
            flash(f'Error al exportar pacientes: {str(e)}', 'error')
            return redirect(url_for('pacientes'))

    @app.route('/medico/exportar-excel')
    def exportar_medicos_excel():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            # Obtener parámetros de filtrado
            busqueda = request.args.get('busqueda', '')
            especialidad = request.args.get('especialidad', '')
            sexo = request.args.get('sexo', '')
            
            # Construir la consulta base
            query = Medico.query
            
            # Aplicar filtros si existen
            if busqueda:
                query = query.filter(
                    db.or_(
                        Medico.nombre.ilike(f'%{busqueda}%'),
                        Medico.apellido.ilike(f'%{busqueda}%'),
                        Medico.numero_documento.ilike(f'%{busqueda}%'),
                        Medico.correo.ilike(f'%{busqueda}%'),
                        Medico.telefono.ilike(f'%{busqueda}%')
                    )
                )
            
            if especialidad:
                query = query.filter(Medico.especialidad == especialidad)
                
            if sexo:
                query = query.filter(Medico.genero == sexo)
            
            # Obtener los médicos
            medicos = query.all()
            
            # Crear un DataFrame con los datos
            data = []
            for medico in medicos:
                data.append({
                    'ID': f'M{str(medico.id).zfill(3)}',
                    'Nombre': medico.nombre,
                    'Apellido': medico.apellido,
                    'Tipo Documento': medico.tipo_documento,
                    'Número Documento': medico.numero_documento,
                    'Fecha Nacimiento': medico.fecha_nacimiento.strftime('%d/%m/%Y') if medico.fecha_nacimiento else '',
                    'Género': 'Masculino' if medico.genero == 'M' else 'Femenino' if medico.genero == 'F' else 'Otro',
                    'Teléfono': medico.telefono,
                    'Correo': medico.correo,
                    'Dirección': medico.direccion,
                    'Especialidad': ESPECIALIDADES.get(medico.especialidad, 'No especificada'),
                    'Años Experiencia': medico.anios_experiencia,
                    'Número Registro': medico.numero_registro,
                    'Estado': medico.estado
                })
            
            df = pd.DataFrame(data)
            
            # Crear un buffer para el archivo Excel
            output = BytesIO()
            
            # Escribir el DataFrame al buffer
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Médicos', index=False)
                
                # Obtener el objeto workbook y worksheet
                workbook = writer.book
                worksheet = writer.sheets['Médicos']
                
                # Formato para el encabezado
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#2651a6',
                    'font_color': 'white',
                    'border': 1
                })
                
                # Formato para fechas
                date_format = workbook.add_format({
                    'num_format': 'dd/mm/yyyy',
                    'border': 1
                })
                
                # Formato para celdas normales
                cell_format = workbook.add_format({
                    'border': 1
                })
                
                # Aplicar formato al encabezado
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 15)  # Ancho de columna
                
                # Aplicar formatos específicos a las columnas
                for row_num in range(len(df)):
                    # Formato para fechas
                    worksheet.write(row_num + 1, 5, df['Fecha Nacimiento'].iloc[row_num], date_format)
                    
                    # Formato para el resto de celdas
                    for col_num in range(len(df.columns)):
                        if col_num != 5:  # Excluir columna de fecha
                            worksheet.write(row_num + 1, col_num, df.iloc[row_num, col_num], cell_format)
            
            # Preparar la respuesta
            output.seek(0)
            response = make_response(output.getvalue())
            response.mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
            # Generar nombre de archivo basado en los filtros
            filename = 'medicos'
            if especialidad:
                filename += f'_{especialidad}'
            if sexo:
                filename += f'_{sexo}'
            if busqueda:
                filename += f'_{busqueda}'
            filename += '.xlsx'
            
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            return response
            
        except Exception as e:
            flash(f'Error al exportar médicos: {str(e)}', 'error')
            return redirect(url_for('medico'))

 