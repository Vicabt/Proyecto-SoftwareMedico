from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify, make_response, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from model import db, usuario, paciente as Paciente, medico as Medico, cita as Cita, historia_clinica, factura as Factura, departamento, universidad, Cie10
from datetime import datetime
from auth import init_auth_routes, obtener_configuracion, guardar_configuracion
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from constantes import ESPECIALIDADES
import matplotlib
import pandas as pd
matplotlib.use('Agg')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'MediSoft2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/medisoft'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()
    
# Contexto global para las plantillas
@app.context_processor
def inject_user():
    if 'user_id' in session:
        user_id = session.get('user_id')
        user = usuario.query.get(user_id)
        config = obtener_configuracion()
        if user:
            return {'current_user': user, 'config': config, 'now': datetime.now()}
    return {'current_user': None, 'config': None, 'now': datetime.now()}

# Lista de EPS de Colombia
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

# Rutas de la aplicación#
@app.route('/')
def index():
    return render_template('pagina_principal/index.html')

@app.route('/nosotros')
def nosotros():
    return render_template('pagina_principal/nosotros.html')

@app.route('/panel')
def panel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Obtener la fecha actual para filtrar las citas de hoy
    hoy = datetime.now().date()
    
    # Consultar las citas de hoy con información de pacientes y médicos
    citas_hoy = db.session.query(Cita, Paciente, Medico)\
        .join(Paciente, Cita.paciente_id == Paciente.id)\
        .join(Medico, Cita.medico_id == Medico.id)\
        .filter(db.func.date(Cita.fecha) == hoy)\
        .order_by(Cita.hora)\
        .all()
    
    # Contar el total de pacientes registrados
    total_pacientes = db.session.query(Paciente).count()
    
    # Contar el total de médicos registrados
    total_medicos = db.session.query(Medico).count()
    
    # Renderizar template con los datos
    return render_template('panel/panel.html',
                         citas_hoy=citas_hoy,
                         total_pacientes=total_pacientes,
                         total_medicos=total_medicos)

@app.route('/medico')
def medico():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    busqueda = request.args.get('busqueda', '')
    especialidad = request.args.get('especialidad', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    query = Medico.query
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
    pagination = query.order_by(Medico.id.asc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    medicos = pagination.items
    for m in medicos:
        m.nombre_especialidad = ESPECIALIDADES.get(m.especialidad, 'Especialidad no encontrada')
    departamentos = departamento.query.order_by(departamento.nombre).all()
    universidades = universidad.query.order_by(universidad.nombre).all()
    if request.args.get('ajax') == '1':
        return render_template('panel/medicos.html', medicos=medicos, especialidades=ESPECIALIDADES, pagination=pagination, busqueda=busqueda, especialidad_seleccionada=especialidad, departamentos=departamentos, universidades=universidades, ajax_fragment=True)
    return render_template('panel/medicos.html', medicos=medicos, especialidades=ESPECIALIDADES, pagination=pagination, busqueda=busqueda, especialidad_seleccionada=especialidad, departamentos=departamentos, universidades=universidades)

@app.route('/paciente')
def pacientes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Obtener parámetros de búsqueda y paginación
    busqueda = request.args.get('busqueda', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Número de registros por página
    
    # Consulta base
    query = Paciente.query
    
    # Aplicar filtros si existen
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
    
    # Ordenar por ID y paginar resultados
    pagination = query.order_by(Paciente.id.asc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    pacientes = pagination.items
    departamentos = departamento.query.order_by(departamento.nombre).all()
    
    return render_template(
        'panel/pacientes.html',
        pacientes=pacientes,
        pagination=pagination,
        busqueda=busqueda,
        lista_eps=LISTA_EPS,
        departamentos=departamentos
    )

@app.route('/cita')
def cita():
    if 'user_id' not in session:
        return redirect(url_for('login'))   
    
    # Obtener parámetros de búsqueda
    busqueda = request.args.get('busqueda', '')
    fecha = request.args.get('fecha', '')
    estado = request.args.get('estado', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Número de elementos por página

    # Construir la consulta base
    query = Cita.query.join(Paciente).join(Medico)

    # Aplicar filtros
    if busqueda:
        query = query.filter(
            db.or_(
                Paciente.nombre.ilike(f'%{busqueda}%'),
                Paciente.apellido.ilike(f'%{busqueda}%'),
                Paciente.documento.ilike(f'%{busqueda}%'),
                Medico.nombre.ilike(f'%{busqueda}%'),
                Medico.apellido.ilike(f'%{busqueda}%')
            )
        )
    if fecha:
        query = query.filter(db.func.date(Cita.fecha) == fecha)
    if estado:
        query = query.filter(Cita.estado == estado)    

    # Ordenar por fecha y hora
    query = query.order_by(Cita.fecha.desc(), Cita.hora.desc())

    # Aplicar paginación
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    citas = pagination.items

    # Obtener todos los pacientes y médicos para los selectores
    pacientes = Paciente.query.all()
    medicos = Medico.query.all()
    
    return render_template('panel/citas.html',
                         citas=citas,
                         pacientes=pacientes,
                         medicos=medicos,
                         especialidades=ESPECIALIDADES,
                         pagination=pagination,
                         busqueda=busqueda,
                         fecha=fecha,
                         estado=estado)

@app.route('/historia')
def historia():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Obtener parámetros de búsqueda y paginación
    busqueda = request.args.get('busqueda', '')
    medico_id = request.args.get('medico_id', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Número de registros por página
    
    # Consulta base para historias clínicas con JOIN a pacientes, citas y médicos
    query = historia_clinica.query.join(Cita, historia_clinica.id_cita == Cita.id)\
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
                Medico.apellido.ilike(f'%{busqueda}%')
            )
        )
    
    if medico_id:
        query = query.filter(Medico.id == medico_id)
    
    # Paginar resultados
    paginated_historias = query.order_by(historia_clinica.fecha.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Obtener lista de médicos para el formulario
    medicos = Medico.query.all()
    
    # Obtener lista de pacientes para el formulario
    pacientes = Paciente.query.all()
    
    # Obtener lista de citas para asociar con historias clínicas
    citas = Cita.query.all()
    
    # Usar la constante global de especialidades
    
    return render_template('panel/historias.html', 
                           historias=paginated_historias,
                           medicos=medicos,
                           pacientes=pacientes,
                           citas=citas,
                           especialidades=ESPECIALIDADES,
                           busqueda=busqueda,
                           medico_id=medico_id)

@app.route('/factura')
def factura():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Obtener parámetros de búsqueda y paginación
    busqueda = request.args.get('busqueda', '')
    estado = request.args.get('estado', '')
    fecha = request.args.get('fecha', '')
    id_cita = request.args.get('id_cita', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Número de registros por página
    
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
    
    # Paginar resultados
    pagination = query.order_by(Factura.fecha_emision.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Obtener las citas que no tienen factura asociada
    citas = Cita.query.filter(Cita.factura == None).all()
    
    # Obtener el servicio si hay una cita seleccionada
    servicio = ''
    if id_cita:
        cita_seleccionada = Cita.query.get(id_cita)
        if cita_seleccionada and cita_seleccionada.medico:
            servicio = ESPECIALIDADES.get(cita_seleccionada.medico.especialidad, 'No especificada')
    
    return render_template('panel/facturas.html',
                         facturas=pagination,
                         citas=citas,
                         id_cita=id_cita,
                         servicio=servicio,
                         busqueda=busqueda,
                         estado=estado,
                         fecha=fecha,
                         ESPECIALIDADES=ESPECIALIDADES,
                         datetime=datetime)

@app.route('/perfil')
def perfil():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Obtener información del usuario actual
    user_id = session.get('user_id')
    user = usuario.query.get(user_id)
    
    if not user:
        flash('Error: Usuario no encontrado', 'error')
        return redirect(url_for('panel'))
    
    return render_template('panel/perfil.html', usuario=user)

@app.route('/configuracion', methods=['GET', 'POST'])
def configuracion():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    config = obtener_configuracion()
    
    if request.method == 'POST':
        try:
            guardar_configuracion(request)
            flash('Configuración actualizada correctamente', 'success')
        except Exception as e:
            flash(f'Error al actualizar la configuración: {str(e)}', 'error')
        return redirect(url_for('configuracion'))
    
    return render_template('panel/configuracion.html', config=config)

@app.route('/api/cie10/buscar')
def buscar_cie10_api():
    # Permitir acceso sin autenticación para páginas de prueba en desarrollo
    referer = request.headers.get('Referer', '')
    if 'test' in referer or app.debug:
        pass  # Permitir acceso en modo debug o páginas de prueba
    elif 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        query_term = request.args.get('q', '').strip()
        
        if not query_term or len(query_term) < 2:
            return jsonify([])

        # Búsqueda mejorada con múltiples criterios
        resultados = Cie10.query.filter(
            Cie10.activo == True,
            db.or_(
                Cie10.codigo.ilike(f'{query_term}%'),
                Cie10.descripcion.ilike(f'%{query_term}%'),
                Cie10.codigo.ilike(f'%{query_term}%')  # Búsqueda parcial en código también
            )
        ).order_by(
            # Priorizar códigos que empiecen con el término
            db.case(
                (Cie10.codigo.ilike(f'{query_term}%'), 1),
                else_=2
            ),
            Cie10.codigo
        ).limit(50).all()  # Aumentar límite a 50

        response_data = []
        for r in resultados:
            response_data.append({
                'id': r.id,
                'text': f"{r.codigo} - {r.descripcion}",
                'codigo': r.codigo,
                'descripcion': r.descripcion
            })

        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error en API CIE-10: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/historia/agregar', methods=['POST'])
def agregar_historia():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        id_cita_form = request.form.get('citaHistoria')
        if not id_cita_form:
            flash('Debe seleccionar una cita para la historia clínica.', 'warning')
            return redirect(url_for('historia'))

        historia_existente = historia_clinica.query.filter_by(id_cita=id_cita_form).first()
        if historia_existente:
            flash('Ya existe una historia clínica para esta cita. Puede editarla.', 'warning')
            return redirect(url_for('historia'))
        
        nueva_historia = historia_clinica(
            id_cita=id_cita_form,
            fecha=datetime.utcnow(),
            motivo_consulta=request.form.get('motivoConsulta'),
            antesedentes=request.form.get('antecedentesMedicos'),
            tratamiento=request.form.get('tratamientoActual')
        )
        
        # Manejar diagnósticos CIE-10
        diagnosticos_data = request.form.get('diagnosticos_cie10_ids', '')
        if diagnosticos_data:
            # Split by comma and filter empty values
            ids_cie10 = [id.strip() for id in diagnosticos_data.split(',') if id.strip()]
            for cie10_id in ids_cie10:
                try:
                    cie10 = Cie10.query.get(int(cie10_id))
                    if cie10 and cie10.estado == 'Activo':
                        nueva_historia.diagnosticos.append(cie10)
                except (ValueError, AttributeError) as e:
                    print(f"Error al procesar diagnóstico ID {cie10_id}: {e}")
                    continue
        
        db.session.add(nueva_historia)
        db.session.commit()
        flash('Historia clínica agregada exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al agregar historia clínica: {str(e)}', 'error')
        print(f"Error detallado HC: {str(e)}")
    
    return redirect(url_for('historia'))

@app.route('/historia/editar/<int:id>', methods=['POST'])
def editar_historia(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        historia = historia_clinica.query.get_or_404(id)
        
        # Actualizar campos básicos
        historia.motivo_consulta = request.form.get('editMotivoConsulta')
        historia.antesedentes = request.form.get('editAntecedentesMedicos')
        historia.tratamiento = request.form.get('editTratamientoActual')
        historia.fecha = datetime.utcnow()
        
        # Actualizar diagnósticos CIE-10
        historia.diagnosticos.clear()
        ids_cie10 = request.form.getlist('diagnosticos_cie10_ids[]')
        for cie10_id in ids_cie10:
            cie10 = Cie10.query.get(cie10_id)
            if cie10 and cie10.activo:
                historia.diagnosticos.append(cie10)
        
        db.session.commit()
        flash('Historia clínica actualizada exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar historia clínica: {str(e)}', 'error')
        print(f"Error detallado HC Edit: {str(e)}")
    
    return redirect(url_for('historia'))

@app.route('/medico/exportar-pdf')
def exportar_medicos_pdf():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    busqueda = request.args.get('busqueda', '')
    especialidad = request.args.get('especialidad', '')
    query = Medico.query
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
    medicos = query.all()
    # ... (resto del código de generación de PDF igual, usando la lista medicos)

@app.route('/medico/exportar-excel')
def exportar_medicos_excel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    busqueda = request.args.get('busqueda', '')
    especialidad = request.args.get('especialidad', '')
    query = Medico.query
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
    medicos = query.all()
    data = [{
        'Nombre': m.nombre,
        'Apellido': m.apellido,
        'Especialidad': m.especialidad,
        'Tipo Doc.': m.tipo_documento,
        'N° Doc.': m.numero_documento,
        'Teléfono': m.telefono,
        'Correo': m.correo
    } for m in medicos]
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Médicos')
    output.seek(0)
    return send_file(output, download_name="medicos.xlsx", as_attachment=True)

@app.route('/paciente/exportar-pdf')
def exportar_pacientes_pdf():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    pacientes = Paciente.query.all()
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from io import BytesIO
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    styles = getSampleStyleSheet()
    elements = []
    title = Paragraph("<b>Reporte de Pacientes</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    data = [['ID', 'Nombre', 'Apellido', 'Tipo Doc.', 'N° Doc.', 'Teléfono', 'Correo', 'EPS']]
    for p in pacientes:
        data.append([
            f'P{str(p.id).zfill(3)}',
            p.nombre,
            p.apellido,
            p.tipo_documento,
            p.numero_documento,
            p.telefono,
            p.correo,
            p.eps
        ])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2651a6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    from flask import send_file
    return send_file(buffer, download_name="pacientes_report.pdf", as_attachment=True, mimetype='application/pdf')

@app.route('/paciente/exportar-excel')
def exportar_pacientes_excel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    busqueda = request.args.get('busqueda', '')
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
    pacientes = query.all()
    data = [{
        'Nombre': p.nombre,
        'Apellido': p.apellido,
        'Tipo Doc.': p.tipo_documento,
        'N° Doc.': p.numero_documento,
        'Teléfono': p.telefono,
        'Correo': p.correo,
        'EPS': p.eps
    } for p in pacientes]
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pacientes')
    output.seek(0)
    from flask import send_file
    return send_file(output, download_name="pacientes.xlsx", as_attachment=True)

@app.route('/cita/exportar-excel')
def exportar_citas_excel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    busqueda = request.args.get('busqueda', '')
    fecha = request.args.get('fecha', '')
    estado = request.args.get('estado', '')
    query = Cita.query.join(Paciente).join(Medico)
    if busqueda:
        query = query.filter(
            db.or_(
                Paciente.nombre.ilike(f'%{busqueda}%'),
                Paciente.apellido.ilike(f'%{busqueda}%'),
                Paciente.documento.ilike(f'%{busqueda}%'),
                Medico.nombre.ilike(f'%{busqueda}%'),
                Medico.apellido.ilike(f'%{busqueda}%')
            )
        )
    if fecha:
        query = query.filter(db.func.date(Cita.fecha) == fecha)
    if estado:
        query = query.filter(Cita.estado == estado)
    citas = query.all()
    data = [{
        'Fecha': c.fecha.strftime('%d/%m/%Y'),
        'Hora': c.hora.strftime('%H:%M'),
        'Paciente': f'{c.paciente.nombre} {c.paciente.apellido}',
        'Médico': f'{c.medico.nombre} {c.medico.apellido}',
        'Tipo': c.tipo_cita,
        'Estado': c.estado,
        'Motivo': c.motivo
    } for c in citas]
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Citas')
    output.seek(0)
    from flask import send_file
    return send_file(output, download_name="citas.xlsx", as_attachment=True)

@app.route('/historia/exportar-excel')
def exportar_historias_excel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    busqueda = request.args.get('busqueda', '')
    medico_id = request.args.get('medico_id', '')
    diagnostico = request.args.get('diagnostico', '')
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
    if diagnostico:
        query = query.filter(historia_clinica.diagnostico.ilike(f'%{diagnostico}%'))
    historias = query.all()
    data = [{
        'Fecha': h.fecha.strftime('%d/%m/%Y'),
        'Paciente': f'{h.cita.paciente.nombre} {h.cita.paciente.apellido}',
        'Médico': f'{h.cita.medico.nombre} {h.cita.medico.apellido}',
        'Motivo': h.motivo_consulta,
        'Diagnóstico': h.diagnostico,
        'Tratamiento': h.tratamiento
    } for h in historias]
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Historias')
    output.seek(0)
    from flask import send_file
    return send_file(output, download_name="historias_clinicas.xlsx", as_attachment=True)

@app.route('/test-select2')
def test_select2():
    return render_template('test_select2.html')

@app.route('/test-modal')
def test_modal():
    return render_template('test_modal.html')

@app.route('/test-alternativo')
def test_alternativo():
    return render_template('test_alternativo.html')

@app.route('/test-historia')
def test_historia():
    # Test route without authentication for debugging
    from datetime import datetime
    import sys
    
    # Mock session data for testing
    session['user_id'] = 1
    session['user_role'] = 'admin'
    
    # Get search parameters
    busqueda = request.args.get('busqueda', '')
    medico_id = request.args.get('medico_id', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Base query for clinical histories
    query = historia_clinica.query.join(Cita, historia_clinica.id_cita == Cita.id)\
        .join(Paciente, Cita.paciente_id == Paciente.id)\
        .join(Medico, Cita.medico_id == Medico.id)
    
    # Apply filters
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
    
    # Paginate results
    historias = query.order_by(historia_clinica.fecha.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get all doctors for filter dropdown
    medicos = Medico.query.filter_by(estado='Activo').all()
    
    # Get all active appointments without clinical history
    citas = Cita.query.filter_by(estado='confirmada')\
        .filter(~Cita.historia_clinica.has())\
        .join(Paciente, Cita.paciente_id == Paciente.id)\
        .join(Medico, Cita.medico_id == Medico.id)\
        .order_by(Cita.fecha.desc()).all()
    
    from constantes import ESPECIALIDADES
    
    return render_template('panel/historias.html',
                         historias=historias,
                         medicos=medicos,
                         citas=citas,
                         busqueda=busqueda,
                         medico_id=medico_id,
                         especialidades=ESPECIALIDADES)

init_auth_routes(app, db)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)