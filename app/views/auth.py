"""Vistas de autenticación (login, registro, logout)."""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, cache
from app.forms.auth import LoginForm, RegisterForm
from app.models import Usuario
from app.models.auditoria import registrar_auditoria

auth_bp = Blueprint('auth', __name__)

# ── Protección básica contra fuerza bruta ─────────────────────────────────────
# Usa Flask-Caching (SimpleCache en desarrollo) para rastrear intentos por IP.
# En producción se recomienda usar Redis como backend del cache.

MAX_INTENTOS   = 10          # intentos fallidos antes de bloquear
VENTANA_SEG    = 15 * 60     # ventana de 15 minutos
BLOQUEO_SEG    = 30 * 60     # bloqueo de 30 minutos

def _clave_intentos(ip: str) -> str:
    return f'login_fail:{ip}'

def _clave_bloqueo(ip: str) -> str:
    return f'login_block:{ip}'

def _registrar_intento_fallido(ip: str) -> int:
    """Incrementa el contador de fallos. Retorna el total de intentos."""
    clave = _clave_intentos(ip)
    intentos = cache.get(clave) or 0
    intentos += 1
    cache.set(clave, intentos, timeout=VENTANA_SEG)
    if intentos >= MAX_INTENTOS:
        cache.set(_clave_bloqueo(ip), True, timeout=BLOQUEO_SEG)
    return intentos

def _ip_bloqueada(ip: str) -> bool:
    return bool(cache.get(_clave_bloqueo(ip)))

def _limpiar_intentos(ip: str):
    cache.delete(_clave_intentos(ip))
    cache.delete(_clave_bloqueo(ip))


def _redirect_por_rol(tipo_usuario):
    """Redirige al dashboard según el rol."""
    rutas = {
        'admin':        url_for('admin.dashboard'),
        'especialista': url_for('especialista.dashboard'),
    }
    return redirect(rutas.get(tipo_usuario, url_for('cliente.dashboard_cliente')))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    ip = request.remote_addr or '0.0.0.0'

    # Verificar bloqueo por fuerza bruta
    if _ip_bloqueada(ip):
        flash('Demasiados intentos fallidos. Por favor espera 30 minutos antes de intentar de nuevo.', 'error')
        return render_template('login.html', form=form)

    if form.validate_on_submit():
        email = form.email.data.strip()
        password = form.password.data
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.password, password):
            if not usuario.activo:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
                return redirect(url_for('auth.login'))

            # Login exitoso — limpiar contador de intentos
            _limpiar_intentos(ip)

            session.permanent = True
            session['usuario_id']   = usuario.id
            session['nombre']       = usuario.nombre
            session['tipo_usuario'] = usuario.tipo_usuario
            session['email']        = usuario.email
            session['foto_perfil']  = usuario.foto_perfil or ''

            registrar_auditoria(
                accion='login',
                id_usuario=usuario.id,
                id_actor=usuario.id,
                nombre=usuario.nombre,
                email=usuario.email,
                tipo_usuario=usuario.tipo_usuario,
                detalle='Inicio de sesión exitoso',
                ip_address=ip,
            )
            db.session.commit()

            flash(f'¡Bienvenido/a {usuario.nombre}!', 'success')
            return _redirect_por_rol(usuario.tipo_usuario)
        else:
            intentos = _registrar_intento_fallido(ip)
            restantes = max(0, MAX_INTENTOS - intentos)
            if restantes > 0:
                flash(f'Email o contraseña incorrectos. Intentos restantes: {restantes}.', 'error')
            else:
                flash('Cuenta bloqueada temporalmente por múltiples intentos fallidos. Espera 30 minutos.', 'error')

            # Registrar intento fallido en auditoría si el email existe
            if usuario:
                try:
                    registrar_auditoria(
                        accion='login_fallido',
                        id_usuario=usuario.id,
                        id_actor=None,
                        nombre=usuario.nombre,
                        email=email,
                        detalle=f'Intento fallido de login ({intentos}/{MAX_INTENTOS})',
                        ip_address=ip,
                    )
                    db.session.commit()
                except Exception:
                    pass

    return render_template('login.html', form=form)


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    ip = request.remote_addr or '0.0.0.0'

    # Rate limiting — misma protección que el login
    if _ip_bloqueada(ip):
        flash('Demasiados intentos. Por favor espera 30 minutos antes de intentar de nuevo.', 'error')
        return redirect(url_for('auth.registro'))

    form = RegisterForm()
    if form.validate_on_submit():
        nombre   = form.nombre.data.strip()
        email    = form.email.data.strip()
        telefono = form.telefono.data.strip()
        password = form.password.data

        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            _registrar_intento_fallido(ip)   # contar intentos con email duplicado
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
