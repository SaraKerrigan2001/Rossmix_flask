"""Vistas de autenticación (login, registro, logout)."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import Usuario

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.password, password):
            if not usuario.activo:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
                return redirect(url_for('auth.login'))

            session['usuario_id'] = usuario.id
            session['nombre'] = usuario.nombre
            session['tipo_usuario'] = usuario.tipo_usuario
            flash(f'¡Bienvenido/a {usuario.nombre}!', 'success')

            if usuario.tipo_usuario == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('cliente.dashboard_cliente'))
        else:
            flash('Email o contraseña incorrectos', 'error')

    return render_template('login.html')


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        password = request.form.get('password')
        confirmar_password = request.form.get('confirmar_password')

        # Validaciones
        if not all([nombre, email, telefono, password, confirmar_password]):
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('auth.registro'))

        if password != confirmar_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('auth.registro'))

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return redirect(url_for('auth.registro'))

        # Verificar si el email ya existe
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este email ya está registrado', 'error')
            return redirect(url_for('auth.registro'))

        # Crear nuevo usuario
        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            telefono=telefono,
            password=generate_password_hash(password),
            tipo_usuario='cliente'
        )

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('¡Registro exitoso! Ya puedes iniciar sesión', 'success')
        return redirect(url_for('auth.login'))

    return render_template('registro.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('main.index'))
