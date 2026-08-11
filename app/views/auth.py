"""Vistas de autenticación (login, registro, logout)."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.forms.auth import LoginForm, RegisterForm
from app.models import Usuario
from app.models.auditoria import registrar_auditoria

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip()
        password = form.password.data

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.password, password):
            if not usuario.activo:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
                return redirect(url_for('auth.login'))

            session.permanent = True   # activa el timeout definido en PERMANENT_SESSION_LIFETIME
            session['usuario_id'] = usuario.id
            session['nombre'] = usuario.nombre
            session['tipo_usuario'] = usuario.tipo_usuario

            # Registrar login en auditoría
            registrar_auditoria(
                accion='login',
                id_usuario=usuario.id,
                id_actor=usuario.id,
                nombre=usuario.nombre,
                email=usuario.email,
                tipo_usuario=usuario.tipo_usuario,
                detalle=f'Inicio de sesión exitoso',
                ip_address=request.remote_addr,
            )
            db.session.commit()

            flash(f'¡Bienvenido/a {usuario.nombre}!', 'success')

            if usuario.tipo_usuario == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif usuario.tipo_usuario == 'especialista':
                return redirect(url_for('especialista.dashboard'))
            else:
                return redirect(url_for('cliente.dashboard_cliente'))
        else:
            flash('Email o contraseña incorrectos', 'error')

    return render_template('login.html', form=form)


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    form = RegisterForm()
    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        email = form.email.data.strip()
        telefono = form.telefono.data.strip()
        password = form.password.data

        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este email ya está registrado', 'error')
            return redirect(url_for('auth.registro'))

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

    return render_template('registro.html', form=form)


@auth_bp.route('/logout')
def logout():
    # Registrar logout antes de limpiar la sesión
    uid = session.get('usuario_id')
    uname = session.get('nombre', '')
    utype = session.get('tipo_usuario', '')
    if uid:
        try:
            registrar_auditoria(
                accion='logout',
                id_usuario=uid,
                id_actor=uid,
                nombre=uname,
                tipo_usuario=utype,
                detalle='Cierre de sesión',
                ip_address=request.remote_addr,
            )
            db.session.commit()
        except Exception:
            pass

    session.clear()
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('main.index'))
