from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from model import db, usuario
from werkzeug.security import generate_password_hash

recuperar_bp = Blueprint('recuperar', __name__)

def generar_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='recuperar-contrasena')

def validar_token(token, max_age=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='recuperar-contrasena', max_age=max_age)
        return email
    except (SignatureExpired, BadSignature):
        return None

@recuperar_bp.route('/olvidar_contraseña', methods=['GET', 'POST'])
def olvidar_contraseña():
    if request.method == 'POST':
        email = request.form.get('email')
        user = usuario.query.filter_by(correo=email).first()
        if not user:
            flash('No existe una cuenta con ese correo.', 'warning')
            return redirect(url_for('recuperar.olvidar_contraseña'))
        token = generar_token(email)
        link = url_for('recuperar.restablecer_contraseña', token=token, _external=True)
        # Enviar correo
        mail = current_app.extensions['mail']
        msg = Message('Recupera tu contraseña', recipients=[email])
        msg.body = f'Hola, para restablecer tu contraseña haz clic en el siguiente enlace (válido por 1 hora): {link}'
        mail.send(msg)
        flash('Te hemos enviado un correo con instrucciones para restablecer tu contraseña.', 'success')
        return redirect(url_for('login'))
    return render_template('pagina_principal/olvidar_contraseña.html')

@recuperar_bp.route('/restablecer_contraseña/<token>', methods=['GET', 'POST'])
def restablecer_contraseña(token):
    email = validar_token(token)
    if not email:
        flash('El enlace es inválido o ha expirado.', 'danger')
        return redirect(url_for('recuperar.olvidar_contraseña'))
    if request.method == 'POST':
        password = request.form.get('password')
        password2 = request.form.get('password2')
        if not password or len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'warning')
            return redirect(request.url)
        if password != password2:
            flash('Las contraseñas no coinciden.', 'warning')
            return redirect(request.url)
        user = usuario.query.filter_by(correo=email).first()
        if user:
            user.contrasena = password
            db.session.commit()
            flash('¡Contraseña restablecida correctamente! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Usuario no encontrado.', 'danger')
            return redirect(url_for('recuperar.olvidar_contraseña'))
    return render_template('pagina_principal/restablecer_contraseña.html', token=token) 