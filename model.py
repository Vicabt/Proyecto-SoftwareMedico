from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import os
from datetime import datetime

db = SQLAlchemy()

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
    sexo = db.Column(db.String(1), nullable=False)  # 'M', 'F', 'O'
    grupo_sanguineo = db.Column(db.String(3), nullable=True)  # 'A+', 'O-', etc.
    tipo_regimen = db.Column(db.String(20), nullable=True)  # 'Contributivo', etc.
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

    # Relaciones
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
    tipo = db.Column(db.String(20))  # Pública o Privada
    estado = db.Column(db.String(20), default='Activa')  # Activa o Inactiva

    def __repr__(self):
        return f'<universidad {self.nombre}>'
        
# En model.py
class Cie10(db.Model):
    __tablename__ = 'cie10'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(10), unique=True, nullable=False, index=True)
    descripcion = db.Column(db.String(500), nullable=False)
    capitulo = db.Column(db.String(100), nullable=True)
    grupo = db.Column(db.String(100), nullable=True)
    activo = db.Column(db.Boolean, default=True)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Cie10 {self.codigo} - {self.descripcion[:30]}>'

# Tabla de asociación para historia_clinica y Cie10
historia_cie10_association = db.Table('historia_cie10_association',
    db.Column('historia_clinica_id', db.Integer, db.ForeignKey('historia_clinica.id', ondelete='CASCADE'), primary_key=True),
    db.Column('cie10_id', db.Integer, db.ForeignKey('cie10.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tipo_diagnostico', db.String(20), nullable=True)  # 'Principal', 'Relacionado', etc.
)

class historia_clinica(db.Model):
    __tablename__ = 'historia_clinica'
    id = db.Column(db.Integer, primary_key=True)
    id_cita = db.Column(db.Integer, db.ForeignKey('cita.id', ondelete='CASCADE'), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    motivo_consulta = db.Column(db.String(200), nullable=False)
    antesedentes = db.Column(db.String(200), nullable=True)
    # Removemos el campo diagnostico ya que ahora usaremos la relación con Cie10
    tratamiento = db.Column(db.String(200), nullable=True)
    cita = db.relationship('cita', backref=db.backref('historia_clinica', uselist=False, cascade='all, delete'))
    
    # Nueva relación con Cie10
    diagnosticos = db.relationship('Cie10', 
                                 secondary=historia_cie10_association,
                                 backref=db.backref('historias_clinicas', lazy='dynamic'),
                                 lazy='dynamic')