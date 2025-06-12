import csv
import os
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# --- 1. CONFIGURACIÓN DE LA APLICACIÓN FLASK Y LA BASE DE DATOS ---

# Obtener la ruta del directorio actual para crear la base de datos allí
basedir = os.path.abspath(os.path.dirname(__file__))

# Crear una instancia de la aplicación Flask
app = Flask(__name__)
# Configurar la URI de la base de datos para usar MySQL igual que la app principal
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/medisoft'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la extensión SQLAlchemy
db = SQLAlchemy(app)

# --- 2. DEFINICIÓN DE LOS MODELOS DE LA BASE DE DATOS (Contenido de model.py) ---

class usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=True)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contrasena = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(15), nullable=True)
    direccion = db.Column(db.String(100), nullable=True)
    ciudad = db.Column(db.String(50), nullable=True)
    tipo_documento = db.Column(db.String(20), nullable=True)
    numero_documento = db.Column(db.String(20), nullable=True)
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.now)
    foto = db.Column(db.String(100), nullable=True)
    
class departamento(db.Model):
    __tablename__ = 'departamento'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    ciudades = db.relationship('ciudad', backref='departamento', lazy=True)

class ciudad(db.Model):
    __tablename__ = 'ciudad'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    departamento_id = db.Column(db.Integer, db.ForeignKey('departamento.id'), nullable=False)

class paciente(db.Model):
    __tablename__ = 'paciente'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    tipo_documento = db.Column(db.String(20), nullable=False)
    numero_documento = db.Column(db.String(20), unique=True, nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    sexo = db.Column(db.String(1), nullable=False)
    grupo_sanguineo = db.Column(db.String(3), nullable=True)
    tipo_regimen = db.Column(db.String(20), nullable=True)
    departamento_id = db.Column(db.Integer, db.ForeignKey('departamento.id'), nullable=False)
    ciudad_id = db.Column(db.Integer, db.ForeignKey('ciudad.id'), nullable=False)
    telefono = db.Column(db.String(15), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    direccion = db.Column(db.String(100), nullable=False)
    ciudad = db.relationship('ciudad', backref='pacientes', lazy=True)
    estado_civil = db.Column(db.String(20), nullable=False)
    ocupacion = db.Column(db.String(50), nullable=False)
    eps = db.Column(db.String(50), nullable=False)
    contactos_emergencia = db.Column(db.String(100), nullable=False)
    telefono_emergencia = db.Column(db.String(15), nullable=False)
    
class medico(db.Model):
    __tablename__ = 'medico'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    tipo_documento = db.Column(db.String(20), nullable=False)
    numero_documento = db.Column(db.String(20), unique=True, nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    genero = db.Column(db.String(10), nullable=False)
    telefono = db.Column(db.String(15), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    direccion = db.Column(db.String(100), nullable=False)
    departamento_id = db.Column(db.Integer, db.ForeignKey('departamento.id'), nullable=False)
    ciudad_id = db.Column(db.Integer, db.ForeignKey('ciudad.id'), nullable=False)
    universidad_id = db.Column(db.Integer, db.ForeignKey('universidad.id'), nullable=False)
    anios_experiencia = db.Column(db.Integer, nullable=False)
    especialidad = db.Column(db.String(50), nullable=False)
    numero_registro = db.Column(db.String(20), unique=True, nullable=False)
    estado = db.Column(db.String(20), default='Activo')
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    departamento = db.relationship('departamento', backref='medicos')
    ciudad = db.relationship('ciudad', backref='medicos')
    universidad = db.relationship('universidad', backref='medicos')

class cita(db.Model):
    __tablename__ = 'cita'
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey('medico.id'), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    duracion = db.Column(db.Integer, nullable=False)
    tipo_cita = db.Column(db.String(20), nullable=False)
    motivo = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(20), nullable=False)
    observaciones = db.Column(db.String(200), nullable=True)
    paciente = db.relationship('paciente', backref='citas')
    medico = db.relationship('medico', backref='citas')

class factura(db.Model):
    __tablename__ = 'factura'
    id = db.Column(db.Integer, primary_key=True)
    id_cita = db.Column(db.Integer, db.ForeignKey('cita.id'), nullable=False)
    servicio = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='pendiente')
    fecha_emision = db.Column(db.DateTime, nullable=False, default=datetime.now)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    metodo_pago = db.Column(db.String(20), nullable=False)
    tipo_factura = db.Column(db.String(20), nullable=False)
    observaciones = db.Column(db.Text)
    cita = db.relationship('cita', backref=db.backref('factura', uselist=False))

class configuracion(db.Model):
    __tablename__ = 'configuracion'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False, unique=True)
    nombre_empresa = db.Column(db.String(100), nullable=False)
    nit_empresa = db.Column(db.String(20), nullable=False)
    registro_sanitario = db.Column(db.String(50), nullable=False)
    slogan = db.Column(db.String(200), nullable=True)
    logo = db.Column(db.String(255), nullable=True)
    favicon = db.Column(db.String(255), nullable=True)
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    usuario = db.relationship('usuario', backref=db.backref('configuracion', uselist=False))

class universidad(db.Model):
    __tablename__ = 'universidad'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    siglas = db.Column(db.String(20))
    departamento = db.Column(db.String(50))
    ciudad = db.Column(db.String(50))
    tipo = db.Column(db.String(20))
    estado = db.Column(db.String(20), default='Activa')

class Cie10(db.Model):
    __tablename__ = 'cie10'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False, index=True)
    descripcion = db.Column(db.String(500), nullable=False)
    capitulo = db.Column(db.String(255), nullable=True)
    grupo = db.Column(db.String(255), nullable=True)
    activo = db.Column(db.Boolean, default=True)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

historia_cie10_association = db.Table('historia_cie10_association',
    db.Column('historia_clinica_id', db.Integer, db.ForeignKey('historia_clinica.id', ondelete='CASCADE'), primary_key=True),
    db.Column('cie10_id', db.Integer, db.ForeignKey('cie10.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tipo_diagnostico', db.String(20), nullable=True)
)

class historia_clinica(db.Model):
    __tablename__ = 'historia_clinica'
    id = db.Column(db.Integer, primary_key=True)
    id_cita = db.Column(db.Integer, db.ForeignKey('cita.id', ondelete='CASCADE'), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    motivo_consulta = db.Column(db.String(200), nullable=False)
    antesedentes = db.Column(db.String(200), nullable=True)
    tratamiento = db.Column(db.String(200), nullable=True)
    cita = db.relationship('cita', backref=db.backref('historia_clinica', uselist=False, cascade='all, delete'))
    diagnosticos = db.relationship('Cie10', secondary=historia_cie10_association, backref=db.backref('historias_clinicas', lazy='dynamic'), lazy='dynamic')

# --- 3. FUNCIÓN AUXILIAR PARA DETERMINAR EL CAPÍTULO CIE-10 ---
def get_capitulo_cie10(codigo):
    """Devuelve el nombre del capítulo CIE-10 basado en el código."""
    if not codigo:
        return "Capítulo no definido"
    
    letra = codigo[0].upper()
    num = -1
    try:
        if len(codigo) > 1 and codigo[1:3].isdigit():
            num = int(codigo[1:3])
    except ValueError:
        pass

    if letra in ['A', 'B']:
        return "I. Ciertas enfermedades infecciosas y parasitarias"
    elif letra == 'C' or (letra == 'D' and 0 <= num <= 48):
        return "II. Tumores [neoplasias]"
    elif letra == 'D' and 50 <= num <= 89:
        return "III. Enfermedades de la sangre y de los órganos hematopoyéticos, y ciertos trastornos que afectan el mecanismo de la inmunidad"
    elif letra == 'E':
        return "IV. Enfermedades endocrinas, nutricionales y metabólicas"
    elif letra == 'F':
        return "V. Trastornos mentales y del comportamiento"
    elif letra == 'G':
        return "VI. Enfermedades del sistema nervioso"
    elif letra == 'H' and 0 <= num <= 59:
        return "VII. Enfermedades del ojo y sus anexos"
    elif letra == 'H' and 60 <= num <= 95:
        return "VIII. Enfermedades del oído y de la apófisis mastoides"
    elif letra == 'I':
        return "IX. Enfermedades del sistema circulatorio"
    elif letra == 'J':
        return "X. Enfermedades del sistema respiratorio"
    elif letra == 'K':
        return "XI. Enfermedades del sistema digestivo"
    elif letra == 'L':
        return "XII. Enfermedades de la piel y del tejido subcutáneo"
    elif letra == 'M':
        return "XIII. Enfermedades del sistema osteomuscular y del tejido conjuntivo"
    elif letra == 'N':
        return "XIV. Enfermedades del sistema genitourinario"
    elif letra == 'O':
        return "XV. Embarazo, parto y puerperio"
    elif letra == 'P':
        return "XVI. Ciertas afecciones originadas en el período perinatal"
    elif letra == 'Q':
        return "XVII. Malformaciones congénitas, deformidades y anomalías cromosómicas"
    elif letra == 'R':
        return "XVIII. Síntomas, signos y hallazgos anormales clínicos y de laboratorio, no clasificados en otra parte"
    elif letra in ['S', 'T']:
        return "XIX. Traumatismos, envenenamientos y algunas otras consecuencias de causas externas"
    elif letra == 'U':
        return "XXII. Códigos para propósitos especiales"
    elif letra in ['V', 'W', 'X', 'Y']:
        return "XX. Causas externas de morbilidad y de mortalidad"
    elif letra == 'Z':
        return "XXI. Factores que influyen en el estado de salud y contacto con los servicios de salud"
    else:
        return "Capítulo no definido"

# --- 4. FUNCIÓN PRINCIPAL PARA CARGAR LOS DATOS ---
def cargar_datos_cie10(archivo_csv='CIE-10.csv'):
    """Lee el archivo CSV y carga los datos en la tabla Cie10."""
    with app.app_context():
        # Crear todas las tablas si no existen
        db.create_all()

        # Obtener los códigos que ya existen para evitar duplicados
        codigos_existentes = {c.codigo for c in Cie10.query.all()}
        print(f"Encontrados {len(codigos_existentes)} códigos existentes en la base de datos.")

        try:
            with open(archivo_csv, mode='r', encoding='utf-8') as f:
                lector_csv = csv.reader(f)
                
                # Omitir las primeras dos líneas (línea vacía y encabezado)
                next(lector_csv, None)  
                next(lector_csv, None)  

                nuevos_registros = 0
                for fila in lector_csv:
                    if len(fila) < 4:
                        continue

                    codigo_3_char, desc_3_char, codigo_4_char, desc_4_char = [item.strip() for item in fila]

                    # Procesamos solo las filas que tienen un código de 4 caracteres
                    if not codigo_4_char:
                        continue
                    
                    if codigo_4_char in codigos_existentes:
                        continue

                    capitulo = get_capitulo_cie10(codigo_4_char)
                    
                    # Limpiar las comillas dobles que a veces quedan al final
                    descripcion_limpia = desc_4_char.strip('"')

                    nuevo_codigo = Cie10(
                        codigo=codigo_4_char,
                        descripcion=descripcion_limpia,
                        capitulo=capitulo,
                        grupo=desc_3_char
                    )
                    db.session.add(nuevo_codigo)
                    codigos_existentes.add(codigo_4_char)
                    nuevos_registros += 1

                print(f"Se agregarán {nuevos_registros} nuevos registros.")
                if nuevos_registros > 0:
                    db.session.commit()
                    print("¡Datos del CIE-10 cargados exitosamente!")
                else:
                    print("No se encontraron nuevos registros para agregar.")

        except FileNotFoundError:
            print(f"Error: El archivo '{archivo_csv}' no fue encontrado. Asegúrate de que esté en el mismo directorio que este script.")
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")
            db.session.rollback()

# --- 5. EJECUCIÓN DEL SCRIPT ---
if __name__ == '__main__':
    print("Iniciando la integración de datos CIE-10...")
    cargar_datos_cie10()
    print("Proceso finalizado.") 