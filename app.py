from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify, make_response, send_file
from flask_sqlalchemy import SQLAlchemy
from model import db, usuario, paciente as Paciente, medico as Medico, cita as Cita, historia_clinica, factura as Factura, departamento, universidad, servicio as Servicio, cie10
from datetime import datetime, timedelta
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
from flask_mail import Mail
from recuperar import recuperar_bp
matplotlib.use('Agg')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'MediSoft2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/medisoft'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'carloscorreab52@gmail.com'
app.config['MAIL_PASSWORD'] = 'otar xykt cghs gicx'
app.config['MAIL_DEFAULT_SENDER'] = 'carloscorreab52@gmail.com'

db.init_app(app)
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
    
    # Obtener parámetros de búsqueda y paginación
    busqueda = request.args.get('busqueda', '')
    especialidad = request.args.get('especialidad', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Número de registros por página
    
    # Consulta base
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
    
    # Ordenar por ID y paginar resultados
    pagination = query.order_by(Medico.id.asc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    medicos = pagination.items
    
    # Agregar el nombre de la especialidad a cada médico
    for m in medicos:
        m.nombre_especialidad = ESPECIALIDADES.get(m.especialidad, 'Especialidad no encontrada')
    
    # Obtener lista de departamentos
    departamentos = departamento.query.order_by(departamento.nombre).all()
    
    # Obtener lista de universidades
    universidades = universidad.query.order_by(universidad.nombre).all()
    
    return render_template(
        'panel/medicos.html',
        medicos=medicos,
        especialidades=ESPECIALIDADES,
        pagination=pagination,
        busqueda=busqueda,
        especialidad_seleccionada=especialidad,
        departamentos=departamentos,
        universidades=universidades
    )

@app.route('/paciente')
def pacientes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Obtener parámetros de búsqueda y paginación
    busqueda = request.args.get('busqueda', '')
    grupo_sanguineo = request.args.get('grupo_sanguineo', '')
    sexo = request.args.get('sexo', '')
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
    
    if grupo_sanguineo:
        query = query.filter(Paciente.grupo_sanguineo == grupo_sanguineo)
        
    if sexo:
        query = query.filter(Paciente.sexo == sexo)
    
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
        grupo_sanguineo=grupo_sanguineo,
        sexo=sexo,
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
                Paciente.numero_documento.ilike(f'%{busqueda}%'),
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

    # Obtener todos los pacientes, médicos y servicios para los selectores
    pacientes = Paciente.query.all()
    medicos = Medico.query.all()
    servicios = Servicio.query.all()
    
    return render_template('panel/citas.html',
                         citas=citas,
                         pacientes=pacientes,
                         medicos=medicos,
                         servicios=servicios,
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
    fecha = request.args.get('fecha', '')
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
        
    if fecha:
        query = query.filter(db.func.date(historia_clinica.fecha) == datetime.strptime(fecha, '%Y-%m-%d').date())
    
    # Paginar resultados
    paginated_historias = query.order_by(historia_clinica.fecha.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Obtener lista de médicos para el formulario
    medicos = Medico.query.all()
    
    # Obtener lista de pacientes para el formulario
    pacientes = Paciente.query.all()
    
    # Obtener lista de citas para asociar con historias clínicas
    citas = Cita.query.all()
    
    # Obtener todos los diagnósticos CIE-10
    diagnosticos = cie10.query.order_by(cie10.codigo).all()
    
    return render_template('panel/historias.html', 
                           historias=paginated_historias,
                           medicos=medicos,
                           pacientes=pacientes,
                           citas=citas,
                           especialidades=ESPECIALIDADES,
                           busqueda=busqueda,
                           medico_id=medico_id,
                           fecha=fecha,
                           diagnosticos=diagnosticos)

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
    
    # Obtener todos los servicios para el selector
    servicios = Servicio.query.all()
    
    # Obtener el servicio si hay una cita seleccionada
    servicio = ''
    if id_cita:
        cita_seleccionada = Cita.query.get(id_cita)
        if cita_seleccionada and cita_seleccionada.medico:
            servicio = ESPECIALIDADES.get(cita_seleccionada.medico.especialidad, 'No especificada')
    
    return render_template('panel/facturas.html',
                         facturas=pagination,
                         citas=citas,
                         servicios=servicios,
                         id_cita=id_cita,
                         servicio=servicio,
                         busqueda=busqueda,
                         estado=estado,
                         fecha=fecha,
                         ESPECIALIDADES=ESPECIALIDADES,
                         datetime=datetime)


@app.route('/servicios')
def servicios():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Obtener parámetros de búsqueda y paginación
    busqueda = request.args.get('busqueda', '')
    tipo = request.args.get('tipo', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Número de registros por página
    
    # Obtener tipos únicos de servicios que existen en la base de datos
    tipos_disponibles = db.session.query(Servicio.tipo).distinct().filter(Servicio.tipo.isnot(None)).all()
    tipos_disponibles = [t[0] for t in tipos_disponibles if t[0]]  # Extraer los valores y filtrar nulos
    
    # Consulta base
    query = Servicio.query
    
    # Aplicar filtros si existen
    if busqueda:
        query = query.filter(
            db.or_(
                Servicio.codigo.ilike(f'%{busqueda}%'),
                Servicio.nombre.ilike(f'%{busqueda}%')
            )
        )
    
    if tipo:
        query = query.filter(Servicio.tipo == tipo)
    
    # Ordenar por ID y paginar resultados
    pagination = query.order_by(Servicio.id.asc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return render_template('panel/servicios.html',
                         servicios=pagination,
                         busqueda=busqueda,
                         tipo=tipo,
                         tipos_disponibles=tipos_disponibles)


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

@app.route('/buscar_diagnostico')
def buscar_diagnostico():
    q = request.args.get('q', '')
    resultados = cie10.query.filter(
        (cie10.codigo.like(f'%{q}%')) | (cie10.descripcion.like(f'%{q}%'))
    ).limit(10).all()
    return jsonify([{'codigo': d.codigo, 'descripcion': d.descripcion} for d in resultados])

@app.route('/olvidar_contraseña')
def olvidar_contraseña():
    return render_template('pagina_principal/olvidar_contraseña.html')

# ... configuración de Flask-Mail ...
mail = Mail(app)

app.register_blueprint(recuperar_bp)

init_auth_routes(app, db)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)