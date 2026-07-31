from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from decimal import Decimal
import random
import string
import io
import openpyxl

import os
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'app', 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'app', 'static')
)
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui_cambiar_en_produccion'

# Configuración de PostgreSQL - Base de datos Rossmix
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg://postgres:1234@localhost:5432/Rossmix'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============================================================================
# MODELOS DE LA BASE DE DATOS CON RELACIONES
# ============================================================================


class Usuario(db.Model):
    """Usuarios del sistema (clientes y administradores)"""
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tipo_usuario = db.Column(db.String(20), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)

    # Relaciones
    citas = db.relationship('Cita', backref='cliente', lazy=True, foreign_keys='Cita.id_cliente')
    # Notificaciones del usuario
    notificaciones = db.relationship('Notificacion', backref='usuario', lazy=True)

    def __repr__(self):
        return f'<Usuario {self.nombre} - {self.tipo_usuario}>'


class Servicio(db.Model):
    """Servicios ofrecidos por el salón"""
    __tablename__ = 'servicios'

    id_servicio = db.Column(db.Integer, primary_key=True)
    nombre_servicio = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio_total = db.Column(db.Numeric(10, 2), nullable=False)
    duracion_minutos = db.Column(db.Integer, nullable=False)
    activo = db.Column(db.Boolean, default=True)

    # Relaciones
    citas = db.relationship('Cita', backref='servicio', lazy=True)
    empleados = db.relationship('Empleado', secondary='empleado_servicios', backref='servicios')

    def __repr__(self):
        return f'<Servicio {self.nombre_servicio}>'


class Empleado(db.Model):
    """Empleados del salón"""
    __tablename__ = 'empleados'

    id_empleado = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    especialidad = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    horarios = db.relationship('HorarioEmpleado', backref='empleado', lazy=True, cascade='all, delete-orphan')
    citas = db.relationship('Cita', backref='empleado', lazy=True)

    def __repr__(self):
        return f'<Empleado {self.nombre}>'


class EmpleadoServicio(db.Model):
    """Relación empleados-servicios (Tabla intermedia Many-to-Many)"""
    __tablename__ = 'empleado_servicios'

    id_empleado = db.Column(db.Integer, db.ForeignKey('empleados.id_empleado', ondelete='CASCADE'), primary_key=True)
    id_servicio = db.Column(db.Integer, db.ForeignKey('servicios.id_servicio', ondelete='CASCADE'), primary_key=True)


class HorarioEmpleado(db.Model):
    """Horarios de trabajo de los empleados"""
    __tablename__ = 'horarios_empleados'

    id_horario = db.Column(db.Integer, primary_key=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey('empleados.id_empleado', ondelete='CASCADE'), nullable=False)
    dia_semana = db.Column(db.Integer, nullable=False)  # 0=Domingo, 1=Lunes, ..., 6=Sábado
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)

    def __repr__(self):
        return f'<HorarioEmpleado {self.empleado.nombre if self.empleado else "N/A"} - Día {self.dia_semana}>'


class Cita(db.Model):
    """Citas agendadas"""
    __tablename__ = 'citas'

    id_cita = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    id_empleado = db.Column(db.Integer, db.ForeignKey('empleados.id_empleado', ondelete='SET NULL'))
    id_servicio = db.Column(db.Integer, db.ForeignKey('servicios.id_servicio', ondelete='RESTRICT'), nullable=False)
    fecha_hora_inicio = db.Column(db.DateTime, nullable=False)
    fecha_hora_fin = db.Column(db.DateTime, nullable=False)
    monto_total = db.Column(db.Numeric(10, 2))
    monto_abono = db.Column(db.Numeric(10, 2))
    saldo_pendiente = db.Column(db.Numeric(10, 2))
    estado = db.Column(
        db.Enum(
            'pendiente_pago',
            'confirmada',
            'en_atencion',
            'completada',
            'cancelada',
            'no_asistio',
            name='estado_cita_enum',
            native_enum=True,
            create_constraint=False,
        ),
        nullable=False,
        default='pendiente_pago',
    )
    reembolsado = db.Column(db.Boolean, default=False)
    codigo_reserva = db.Column(db.String(10), unique=True)
    notas = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación con pagos (una cita tiene máximo un pago)
    pago = db.relationship('Pago', backref='cita', uselist=False, lazy=True)

    def __repr__(self):
        return f'<Cita {self.id_cita} - {self.estado}>'


class Pago(db.Model):
    """Pagos registrados por cada cita"""
    __tablename__ = 'pagos'

    id_pago = db.Column(db.Integer, primary_key=True)
    id_cita = db.Column(db.Integer, db.ForeignKey('citas.id_cita', ondelete='CASCADE'),
                        nullable=False, unique=True)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pago = db.Column(
        db.Enum(
            'efectivo',
            'tarjeta',
            'transferencia',
            'nequi',
            'daviplata',
            name='metodo_pago_enum',
            native_enum=True,
            create_constraint=False,
        ),
        nullable=False,
        default='efectivo',
    )
    estado_pago = db.Column(db.String(20), nullable=False, default='completado')
    referencia = db.Column(db.String(100))
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)
    notas = db.Column(db.Text)

    def __repr__(self):
        return f'<Pago {self.id_pago} - Cita {self.id_cita} - ${self.monto}>'


class Notificacion(db.Model):
    """Notificaciones para usuarios"""
    __tablename__ = 'notificaciones'

    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    mensaje = db.Column(db.Text)
    target = db.Column(db.String(300))
    leido = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Notificacion {self.id} -> Usuario {self.id_usuario} - {self.titulo}>'


# Crear las tablas
with app.app_context():
    db.create_all()
    # Crear usuario administrador por defecto si no existe
    admin = Usuario.query.filter_by(email='admin@rossmix.com').first()
    if not admin:
        admin = Usuario(
            nombre='Administrador',
            email='admin@rossmix.com',
            telefono='3000000000',
            password=generate_password_hash('admin123'),
            tipo_usuario='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print('Usuario administrador creado: admin@rossmix.com / admin123')

# ============================================================================
# DECORADOR PARA RUTAS DE ADMINISTRADOR
# ============================================================================


def admin_required(f):
    """Decorador para requerir acceso de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión', 'error')
            return redirect(url_for('login'))
        if session.get('tipo_usuario') != 'admin':
            flash('No tienes permisos para acceder a esta sección', 'error')
            return redirect(url_for('dashboard_cliente'))
        return f(*args, **kwargs)
    return decorated_function

# Rutas


@app.route('/')
def index():
    return render_template('index.html')

    # Helper: crear notificación


def add_notificacion(id_usuario, titulo, mensaje=None, target=None):
    try:
        n = Notificacion(id_usuario=id_usuario, titulo=titulo, mensaje=mensaje, target=target)
        db.session.add(n)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print('Error al crear notificacion:', e)

    # Inyectar notificaciones en templates


@app.context_processor
def inject_notificaciones():
    if 'usuario_id' in session:
        try:
            notifs = Notificacion.query.filter_by(
                id_usuario=session['usuario_id']).order_by(
                Notificacion.fecha.desc()).limit(6).all()
            unread = Notificacion.query.filter_by(id_usuario=session['usuario_id'], leido=False).count()
            return dict(notificaciones=notifs, notificaciones_unread=unread)
        except Exception:
            return dict(notificaciones=[], notificaciones_unread=0)
    return dict(notificaciones=[], notificaciones_unread=0)


@app.route('/notificaciones')
def notificaciones():
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('login'))
    # Paginación simple
    page = request.args.get('page', 1, type=int)
    per_page = 20
    q = Notificacion.query.filter_by(id_usuario=session['usuario_id']).order_by(Notificacion.fecha.desc())
    total = q.count()
    total_pages = (total + per_page - 1) // per_page
    notifs = q.offset((page - 1) * per_page).limit(per_page).all()
    return render_template('notificaciones.html', notificaciones=notifs, page=page, total_pages=total_pages)


@app.route('/test-image')
def test_image():
    return render_template('test_image.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.password, password):
            if not usuario.activo:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'error')
                return redirect(url_for('login'))

            session['usuario_id'] = usuario.id
            session['nombre'] = usuario.nombre
            session['tipo_usuario'] = usuario.tipo_usuario
            flash(f'¡Bienvenido/a {usuario.nombre}!', 'success')

            if usuario.tipo_usuario == 'admin':
                return redirect(url_for('dashboard_admin'))
            else:
                return redirect(url_for('dashboard_cliente'))
        else:
            flash('Email o contraseña incorrectos', 'error')

    return render_template('login.html')


@app.route('/registro', methods=['GET', 'POST'])
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
            return redirect(url_for('registro'))

        if password != confirmar_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('registro'))

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return redirect(url_for('registro'))

        # Verificar si el email ya existe
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este email ya está registrado', 'error')
            return redirect(url_for('registro'))

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
        return redirect(url_for('login'))

    return render_template('registro.html')


@app.route('/dashboard/admin')
@admin_required
def dashboard_admin():
    """Dashboard principal de administrador con estadísticas"""
    from sqlalchemy import func

    # Citas de hoy
    hoy = datetime.now().date()
    citas_hoy = Cita.query.filter(
        func.date(Cita.fecha_hora_inicio) == hoy,
        Cita.estado.in_(['pendiente_pago', 'confirmada', 'en_atencion'])
    ).count()

    # Total clientes
    total_clientes = Usuario.query.filter_by(tipo_usuario='cliente', activo=True).count()

    # Empleados activos
    empleados_activos = Empleado.query.filter_by(activo=True).count()

    # Ingresos del mes
    primer_dia_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ingresos_mes = db.session.query(func.sum(Cita.monto_total)).filter(
        Cita.fecha_creacion >= primer_dia_mes,
        Cita.estado.in_(['completada', 'confirmada'])
    ).scalar() or 0

    stats = {
        'citas_hoy': citas_hoy,
        'total_clientes': total_clientes,
        'empleados_activos': empleados_activos,
        'ingresos_mes': ingresos_mes,
        'pagos_pendientes': Cita.query.filter_by(estado='pendiente_pago').count()
    }

    return render_template('dashboard_admin.html', stats=stats)


@app.route('/dashboard/cliente')
def dashboard_cliente():
    if 'usuario_id' not in session or session.get('tipo_usuario') != 'cliente':
        flash('Debes iniciar sesión como cliente', 'error')
        return redirect(url_for('login'))

    id_cliente = session['usuario_id']

    # Citas pendientes/confirmadas (futuras)
    citas_pendientes = Cita.query.filter(
        Cita.id_cliente == id_cliente,
        Cita.fecha_hora_inicio >= datetime.now(),
        Cita.estado.in_(['pendiente_pago', 'confirmada'])
    ).count()

    # Citas completadas
    citas_completadas = Cita.query.filter(
        Cita.id_cliente == id_cliente,
        Cita.estado == 'completada'
    ).count()

    # Próxima cita
    proxima_cita = db.session.query(Cita, Servicio, Empleado).join(
        Servicio, Cita.id_servicio == Servicio.id_servicio
    ).outerjoin(
        Empleado, Cita.id_empleado == Empleado.id_empleado
    ).filter(
        Cita.id_cliente == id_cliente,
        Cita.fecha_hora_inicio >= datetime.now(),
        Cita.estado.in_(['pendiente_pago', 'confirmada'])
    ).order_by(Cita.fecha_hora_inicio).first()

    stats = {
        'citas_pendientes': citas_pendientes,
        'citas_completadas': citas_completadas
    }

    return render_template('dashboard_cliente.html', stats=stats, proxima_cita=proxima_cita)


@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('index'))


# Marcar una notificación como leída
@app.route('/notificaciones/marcar-leida/<int:notif_id>', methods=['POST'])
def notificacion_marcar_leida(notif_id):
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    n = Notificacion.query.get_or_404(notif_id)
    # permitir solo al propietario de la notificación o a admins
    if n.id_usuario != session['usuario_id'] and session.get('tipo_usuario') != 'admin':
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    n.leido = True
    db.session.commit()
    # devolver nuevo conteo de no leídos
    unread = Notificacion.query.filter_by(id_usuario=session['usuario_id'], leido=False).count()
    return jsonify({'success': True, 'unread': unread})


# Marcar todas las notificaciones del usuario como leídas
@app.route('/notificaciones/marcar-todas', methods=['POST'])
def notificaciones_marcar_todas():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    try:
        Notificacion.query.filter_by(id_usuario=session['usuario_id'], leido=False).update({'leido': True})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    return jsonify({'success': True, 'unread': 0})

# ============================================================================
# RUTAS DEL SISTEMA DE CITAS
# ============================================================================


@app.route('/citas/agendar/paso1')
def agendar_paso1():
    """Paso 1: Seleccionar servicio"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para agendar una cita', 'error')
        return redirect(url_for('login'))

    # Obtener todos los servicios activos
    servicios = Servicio.query.filter_by(activo=True).order_by(Servicio.nombre_servicio).all()

    return render_template('citas/paso1_servicio.html', servicios=servicios)


@app.route('/citas/agendar/paso2/<int:id_servicio>')
def agendar_paso2(id_servicio):
    """Paso 2: Seleccionar empleado o aleatorio"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para agendar una cita', 'error')
        return redirect(url_for('login'))

    # Obtener servicio seleccionado
    servicio = Servicio.query.get_or_404(id_servicio)

    # Obtener empleados que realizan este servicio
    empleados_ids = db.session.query(EmpleadoServicio.id_empleado).filter_by(id_servicio=id_servicio).all()
    empleados_ids = [e[0] for e in empleados_ids]

    empleados = Empleado.query.filter(
        Empleado.id_empleado.in_(empleados_ids),
        Empleado.activo
    ).all()

    return render_template('citas/paso2_empleado.html', servicio=servicio, empleados=empleados)


@app.route('/citas/agendar/paso3/<int:id_servicio>/<int:id_empleado>')
def agendar_paso3(id_servicio, id_empleado):
    """Paso 3: Seleccionar fecha y hora"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para agendar una cita', 'error')
        return redirect(url_for('login'))

    servicio = Servicio.query.get_or_404(id_servicio)
    empleado = Empleado.query.get_or_404(id_empleado) if id_empleado > 0 else None

    # Fechas para el template
    hoy = datetime.now().strftime('%Y-%m-%d')
    max_fecha = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')

    return render_template('citas/paso3_fecha_hora.html',
                           servicio=servicio,
                           empleado=empleado,
                           hoy=hoy,
                           max_fecha=max_fecha)


@app.route('/citas/horarios-disponibles')
def horarios_disponibles():
    """API: Obtener horarios disponibles para una fecha y empleado"""
    fecha_str = request.args.get('fecha')
    id_empleado = request.args.get('id_empleado', type=int)
    id_servicio = request.args.get('id_servicio', type=int)

    if not all([fecha_str, id_servicio]):
        return jsonify({'error': 'Faltan parámetros'}), 400

    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except BaseException:
        return jsonify({'error': 'Fecha inválida'}), 400

    # Si id_empleado es 0, seleccionar empleado aleatorio que haga el servicio
    if id_empleado == 0:
        empleados_ids = db.session.query(EmpleadoServicio.id_empleado).filter_by(id_servicio=id_servicio).all()
        empleados_ids = [e[0] for e in empleados_ids]
        if not empleados_ids:
            return jsonify({'horarios': []})
        id_empleado = random.choice(empleados_ids)

    # Obtener servicio para duración
    servicio = Servicio.query.get(id_servicio)
    if not servicio:
        return jsonify({'error': 'Servicio no encontrado'}), 404

    # Obtener día de la semana (0=Domingo, 1=Lunes, etc.)
    dia_semana = (fecha.weekday() + 1) % 7  # Convertir de Python (0=Lunes) a nuestra DB (0=Domingo)

    # Obtener horario del empleado para ese día
    horario = HorarioEmpleado.query.filter_by(
        id_empleado=id_empleado,
        dia_semana=dia_semana
    ).first()

    if not horario:
        return jsonify({'horarios': []})

    # Generar slots de tiempo disponibles
    horarios_disponibles = []
    hora_actual = datetime.combine(fecha, horario.hora_inicio)
    hora_fin = datetime.combine(fecha, horario.hora_fin)
    duracion = timedelta(minutes=servicio.duracion_minutos)

    while hora_actual + duracion <= hora_fin:
        # Verificar si ya hay una cita en este horario
        cita_existente = Cita.query.filter(
            Cita.id_empleado == id_empleado,
            Cita.fecha_hora_inicio < hora_actual + duracion,
            Cita.fecha_hora_fin > hora_actual,
            Cita.estado.in_(['pendiente_pago', 'confirmada', 'en_atencion'])
        ).first()

        if not cita_existente:
            horarios_disponibles.append({
                'hora': hora_actual.strftime('%H:%M'),
                'hora_fin': (hora_actual + duracion).strftime('%H:%M'),
                'disponible': True
            })

        hora_actual += timedelta(minutes=30)  # Intervalos de 30 minutos

    return jsonify({
        'horarios': horarios_disponibles,
        'id_empleado': id_empleado
    })


@app.route('/citas/agendar/paso4', methods=['POST'])
def agendar_paso4():
    """Paso 4: Confirmación y pago"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para agendar una cita', 'error')
        return redirect(url_for('login'))

    # Obtener datos del formulario
    id_servicio = request.form.get('id_servicio', type=int)
    id_empleado = request.form.get('id_empleado', type=int)
    fecha_str = request.form.get('fecha')
    hora_str = request.form.get('hora')

    if not all([id_servicio, fecha_str, hora_str]):
        flash('Datos incompletos', 'error')
        return redirect(url_for('agendar_paso1'))

    # Obtener información
    servicio = Servicio.query.get_or_404(id_servicio)
    empleado = Empleado.query.get_or_404(id_empleado) if id_empleado > 0 else None

    # Parsear fecha y hora
    try:
        fecha_hora_inicio = datetime.strptime(f"{fecha_str} {hora_str}", '%Y-%m-%d %H:%M')
        fecha_hora_fin = fecha_hora_inicio + timedelta(minutes=servicio.duracion_minutos)
    except BaseException:
        flash('Fecha u hora inválida', 'error')
        return redirect(url_for('agendar_paso1'))

    # Validar que la fecha sea futura
    if fecha_hora_inicio < datetime.now():
        flash('No puedes agendar citas en el pasado', 'error')
        return redirect(url_for('agendar_paso3', id_servicio=id_servicio, id_empleado=id_empleado or 0))

    return render_template('citas/paso4_confirmacion.html',
                           servicio=servicio,
                           empleado=empleado,
                           fecha_hora_inicio=fecha_hora_inicio,
                           fecha_hora_fin=fecha_hora_fin,
                           id_empleado=id_empleado or 0)


@app.route('/citas/confirmar', methods=['POST'])
def confirmar_cita():
    """Confirmar y crear la cita"""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    # Obtener datos
    id_servicio = request.form.get('id_servicio', type=int)
    id_empleado = request.form.get('id_empleado', type=int)
    fecha_hora_inicio_str = request.form.get('fecha_hora_inicio')
    fecha_hora_fin_str = request.form.get('fecha_hora_fin')

    try:
        fecha_hora_inicio = datetime.strptime(fecha_hora_inicio_str, '%Y-%m-%d %H:%M:%S')
        fecha_hora_fin = datetime.strptime(fecha_hora_fin_str, '%Y-%m-%d %H:%M:%S')
    except BaseException:
        flash('Error en las fechas', 'error')
        return redirect(url_for('agendar_paso1'))

    # Obtener servicio
    servicio = Servicio.query.get(id_servicio)
    if not servicio:
        flash('Servicio no encontrado', 'error')
        return redirect(url_for('agendar_paso1'))

    # Si empleado es 0, asignar aleatorio
    if id_empleado == 0:
        empleados_ids = db.session.query(EmpleadoServicio.id_empleado).filter_by(id_servicio=id_servicio).all()
        empleados_ids = [e[0] for e in empleados_ids]
        if empleados_ids:
            id_empleado = random.choice(empleados_ids)
        else:
            flash('No hay empleados disponibles para este servicio', 'error')
            return redirect(url_for('agendar_paso1'))

    # Generar código de reserva
    codigo_reserva = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # Crear cita
    nueva_cita = Cita(
        id_cliente=session['usuario_id'],
        id_empleado=id_empleado,
        id_servicio=id_servicio,
        fecha_hora_inicio=fecha_hora_inicio,
        fecha_hora_fin=fecha_hora_fin,
        monto_total=Decimal(str(servicio.precio_total)),
        monto_abono=Decimal('5000.00'),
        saldo_pendiente=Decimal(str(servicio.precio_total)) - Decimal('5000.00'),
        estado='pendiente_pago',
        reembolsado=False,
        codigo_reserva=codigo_reserva,
        fecha_creacion=datetime.now()
    )

    try:
        db.session.add(nueva_cita)
        db.session.commit()
        flash('¡Cita agendada exitosamente!', 'success')
        return redirect(url_for('cita_confirmada', codigo=codigo_reserva))
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear la cita: {str(e)}', 'error')
        return redirect(url_for('agendar_paso1'))


@app.route('/citas/confirmada/<codigo>')
def cita_confirmada(codigo):
    """Mostrar detalles de cita confirmada"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('login'))

    cita = Cita.query.filter_by(codigo_reserva=codigo, id_cliente=session['usuario_id']).first_or_404()
    servicio = Servicio.query.get(cita.id_servicio)
    empleado = Empleado.query.get(cita.id_empleado)

    return render_template('citas/confirmada.html', cita=cita, servicio=servicio, empleado=empleado)


@app.route('/citas/mis-citas')
def mis_citas():
    """Ver mis citas agendadas"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión', 'error')
        return redirect(url_for('login'))

    # Obtener citas futuras
    citas_futuras = db.session.query(Cita, Servicio, Empleado).join(
        Servicio, Cita.id_servicio == Servicio.id_servicio
    ).join(
        Empleado, Cita.id_empleado == Empleado.id_empleado
    ).filter(
        Cita.id_cliente == session['usuario_id'],
        Cita.fecha_hora_inicio >= datetime.now(),
        Cita.estado.in_(['pendiente_pago', 'confirmada'])
    ).order_by(Cita.fecha_hora_inicio).all()

    # Obtener citas pasadas
    citas_pasadas = db.session.query(Cita, Servicio, Empleado).join(
        Servicio, Cita.id_servicio == Servicio.id_servicio
    ).join(
        Empleado, Cita.id_empleado == Empleado.id_empleado
    ).filter(
        Cita.id_cliente == session['usuario_id'],
        Cita.fecha_hora_inicio < datetime.now()
    ).order_by(Cita.fecha_hora_inicio.desc()).limit(10).all()

    # Pasar función now para calcular tiempo restante en el template
    return render_template('citas/mis_citas.html',
                           citas_futuras=citas_futuras,
                           citas_pasadas=citas_pasadas,
                           now=datetime.now)


@app.route('/citas/cancelar/<int:id_cita>', methods=['POST'])
def cancelar_cita(id_cita):
    """Cancelar una cita"""
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    cita = Cita.query.filter_by(id_cita=id_cita, id_cliente=session['usuario_id']).first()

    if not cita:
        return jsonify({'error': 'Cita no encontrada'}), 404

    # Validar que falten al menos 2 horas
    tiempo_restante = cita.fecha_hora_inicio - datetime.now()
    if tiempo_restante < timedelta(hours=2):
        return jsonify({'error': 'Debes cancelar con mínimo 2 horas de anticipación'}), 400

    # Cancelar cita
    cita.estado = 'cancelada'
    db.session.commit()

    # Notificar al cliente
    try:
        add_notificacion(
            cita.id_cliente,
            'Cita cancelada',
            f'Tu cita programada para {cita.fecha_hora_inicio.strftime("%d/%m/%Y %H:%M")} ha sido cancelada.',
            target=url_for('mis_citas')
        )
    except Exception:
        pass

    # Notificar a administradores
    try:
        admins = Usuario.query.filter_by(tipo_usuario='admin').all()
        for a in admins:
            add_notificacion(
                a.id,
                'Cita cancelada',
                f'El cliente {
                    cita.cliente.nombre if cita.cliente else cita.id_cliente} canceló la cita #{
                    cita.id_cita} programada para {
                    cita.fecha_hora_inicio.strftime("%d/%m/%Y %H:%M")}',
                target=url_for('admin_citas') +
                f'?estado=cancelada&cliente_id={
                    cita.id_cliente}')
    except Exception:
        pass

    return jsonify({'success': True, 'message': 'Cita cancelada exitosamente'})

@app.route('/citas/pagar/<int:id_cita>', methods=['GET', 'POST'])
def cliente_pagos_registrar(id_cita):
    """Registrar pago para una cita por el cliente"""
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para realizar un pago', 'error')
        return redirect(url_for('login'))

    cita = Cita.query.get_or_404(id_cita)
    
    # Ensure the appointment belongs to the logged in user
    if cita.id_cliente != session['usuario_id']:
        flash('No tienes permiso para pagar esta cita', 'error')
        return redirect(url_for('mis_citas'))

    cliente = Usuario.query.get(cita.id_cliente)
    servicio = Servicio.query.get(cita.id_servicio)

    # Verificar que no tenga ya un pago o no esté cancelada
    if cita.pago:
        flash('Esta cita ya tiene un pago registrado', 'error')
        return redirect(url_for('mis_citas'))
    
    if cita.estado == 'cancelada':
        flash('No puedes pagar una cita cancelada', 'error')
        return redirect(url_for('mis_citas'))

    if request.method == 'POST':
        monto = request.form.get('monto', type=float)
        metodo = request.form.get('metodo_pago', 'efectivo')
        referencia = request.form.get('referencia', '').strip() or None
        notas = request.form.get('notas', '').strip() or None

        if not monto or monto <= 0:
            flash('El monto debe ser mayor a 0', 'error')
            return redirect(url_for('cliente_pagos_registrar', id_cita=id_cita))

        metodos_validos = ['efectivo', 'tarjeta', 'transferencia', 'nequi', 'daviplata']
        if metodo not in metodos_validos:
            flash('Método de pago inválido', 'error')
            return redirect(url_for('cliente_pagos_registrar', id_cita=id_cita))

        nuevo_pago = Pago(
            id_cita=id_cita,
            monto=Decimal(str(monto)),
            metodo_pago=metodo,
            estado_pago='completado',
            referencia=referencia,
            notas=notas
        )
        db.session.add(nuevo_pago)

        # Actualizar estado de cita y saldo
        cita.monto_abono = (cita.monto_abono or Decimal('0')) + Decimal(str(monto))
        cita.saldo_pendiente = (cita.monto_total or Decimal('0')) - cita.monto_abono
        if cita.saldo_pendiente <= 0:
            cita.estado = 'completada'
            cita.saldo_pendiente = Decimal('0')

        db.session.commit()
        
        # Notificar a administradores
        try:
            admins = Usuario.query.filter_by(tipo_usuario='admin').all()
            for a in admins:
                add_notificacion(
                    a.id,
                    'Pago registrado por cliente',
                    f'Pago de ${monto:,.0f} registrado por el cliente {cliente.nombre} para la cita #{cita.id_cita}',
                    target=url_for('admin_pagos')
                )
        except Exception:
            pass

        flash(f'Pago de ${monto:,.0f} registrado exitosamente', 'success')
        return redirect(url_for('mis_citas'))

    # GET — formulario
    metodos = ['efectivo', 'tarjeta', 'transferencia', 'nequi', 'daviplata']
    return render_template('citas/cliente_pagos_form.html',
                           cita=cita, cliente=cliente,
                           servicio=servicio, metodos=metodos)

# ============================================================================
# RUTAS PANEL ADMIN - GESTIÓN DE EMPLEADOS
# ============================================================================


@app.route('/admin/empleados')
@admin_required
def admin_empleados():
    """Listar todos los empleados"""
    empleados = Empleado.query.order_by(Empleado.nombre).all()
    return render_template('admin/empleados.html', empleados=empleados)


@app.route('/admin/empleados/crear', methods=['GET', 'POST'])
@admin_required
def admin_empleados_crear():
    """Crear nuevo empleado"""
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        especialidad = request.form.get('especialidad')
        servicios_ids = request.form.getlist('servicios')

        if not nombre:
            flash('El nombre es obligatorio', 'error')
            return redirect(url_for('admin_empleados_crear'))

        # Crear empleado
        nuevo_empleado = Empleado(
            nombre=nombre,
            especialidad=especialidad,
            activo=True
        )

        db.session.add(nuevo_empleado)
        db.session.flush()  # Para obtener el ID

        # Asignar servicios
        for id_servicio in servicios_ids:
            empleado_servicio = EmpleadoServicio(
                id_empleado=nuevo_empleado.id_empleado,
                id_servicio=int(id_servicio)
            )
            db.session.add(empleado_servicio)

        db.session.commit()
        flash(f'Empleado {nombre} creado exitosamente', 'success')
        return redirect(url_for('admin_empleados'))

    # GET: Mostrar formulario
    servicios = Servicio.query.filter_by(activo=True).all()
    return render_template('admin/empleados_form.html', empleado=None, servicios=servicios)


@app.route('/admin/empleados/editar/<int:id_empleado>', methods=['GET', 'POST'])
@admin_required
def admin_empleados_editar(id_empleado):
    """Editar empleado existente"""
    empleado = Empleado.query.get_or_404(id_empleado)

    if request.method == 'POST':
        empleado.nombre = request.form.get('nombre')
        empleado.especialidad = request.form.get('especialidad')
        empleado.activo = request.form.get('activo') == 'on'

        # Actualizar servicios
        servicios_ids = request.form.getlist('servicios')

        # Eliminar relaciones existentes
        EmpleadoServicio.query.filter_by(id_empleado=id_empleado).delete()

        # Agregar nuevas relaciones
        for id_servicio in servicios_ids:
            empleado_servicio = EmpleadoServicio(
                id_empleado=id_empleado,
                id_servicio=int(id_servicio)
            )
            db.session.add(empleado_servicio)

        db.session.commit()
        flash(f'Empleado {empleado.nombre} actualizado exitosamente', 'success')
        return redirect(url_for('admin_empleados'))

    # GET: Mostrar formulario
    servicios = Servicio.query.filter_by(activo=True).all()
    servicios_empleado = [es.id_servicio for es in EmpleadoServicio.query.filter_by(id_empleado=id_empleado).all()]

    return render_template('admin/empleados_form.html',
                           empleado=empleado,
                           servicios=servicios,
                           servicios_empleado=servicios_empleado)


@app.route('/admin/empleados/eliminar/<int:id_empleado>', methods=['POST'])
@admin_required
def admin_empleados_eliminar(id_empleado):
    """Eliminar empleado"""
    empleado = Empleado.query.get_or_404(id_empleado)

    # Verificar si tiene citas futuras
    citas_futuras = Cita.query.filter(
        Cita.id_empleado == id_empleado,
        Cita.fecha_hora_inicio >= datetime.now(),
        Cita.estado.in_(['pendiente_pago', 'confirmada'])
    ).count()

    if citas_futuras > 0:
        return jsonify({
            'success': False,
            'message': f'No se puede eliminar. El empleado tiene {citas_futuras} cita(s) pendiente(s)'
        }), 400

    nombre = empleado.nombre
    db.session.delete(empleado)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Empleado {nombre} eliminado exitosamente'
    })

# ============================================================================
# RUTAS PANEL ADMIN - GESTIÓN DE SERVICIOS
# ============================================================================


@app.route('/admin/servicios')
@admin_required
def admin_servicios():
    """Listar todos los servicios"""
    servicios = Servicio.query.order_by(Servicio.nombre_servicio).all()
    return render_template('admin/servicios.html', servicios=servicios)


@app.route('/admin/servicios/crear', methods=['GET', 'POST'])
@admin_required
def admin_servicios_crear():
    """Crear nuevo servicio"""
    if request.method == 'POST':
        nombre = request.form.get('nombre_servicio')
        descripcion = request.form.get('descripcion')
        precio = request.form.get('precio_total')
        duracion = request.form.get('duracion_minutos')

        if not all([nombre, precio, duracion]):
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('admin_servicios_crear'))

        # Crear servicio
        nuevo_servicio = Servicio(
            nombre_servicio=nombre,
            descripcion=descripcion,
            precio_total=Decimal(precio),
            duracion_minutos=int(duracion),
            activo=True
        )

        db.session.add(nuevo_servicio)
        db.session.commit()

        flash(f'Servicio {nombre} creado exitosamente', 'success')
        return redirect(url_for('admin_servicios'))

    return render_template('admin/servicios_form.html', servicio=None)


@app.route('/admin/servicios/editar/<int:id_servicio>', methods=['GET', 'POST'])
@admin_required
def admin_servicios_editar(id_servicio):
    """Editar servicio existente"""
    servicio = Servicio.query.get_or_404(id_servicio)

    if request.method == 'POST':
        servicio.nombre_servicio = request.form.get('nombre_servicio')
        servicio.descripcion = request.form.get('descripcion')
        servicio.precio_total = Decimal(request.form.get('precio_total'))
        servicio.duracion_minutos = int(request.form.get('duracion_minutos'))
        servicio.activo = request.form.get('activo') == 'on'

        db.session.commit()
        flash(f'Servicio {servicio.nombre_servicio} actualizado exitosamente', 'success')
        return redirect(url_for('admin_servicios'))

    return render_template('admin/servicios_form.html', servicio=servicio)


@app.route('/admin/servicios/eliminar/<int:id_servicio>', methods=['POST'])
@admin_required
def admin_servicios_eliminar(id_servicio):
    """Eliminar servicio"""
    servicio = Servicio.query.get_or_404(id_servicio)

    # Verificar si tiene citas futuras
    citas_futuras = Cita.query.filter(
        Cita.id_servicio == id_servicio,
        Cita.fecha_hora_inicio >= datetime.now(),
        Cita.estado.in_(['pendiente_pago', 'confirmada'])
    ).count()

    if citas_futuras > 0:
        return jsonify({
            'success': False,
            'message': f'No se puede eliminar. El servicio tiene {citas_futuras} cita(s) pendiente(s)'
        }), 400

    nombre = servicio.nombre_servicio
    db.session.delete(servicio)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Servicio {nombre} eliminado exitosamente'
    })

# ============================================================================
# RUTAS PANEL ADMIN - GESTIÓN DE CLIENTES
# ============================================================================


@app.route('/admin/clientes')
@admin_required
def admin_clientes():
    """Listar todos los clientes"""
    clientes = Usuario.query.filter_by(tipo_usuario='cliente').order_by(Usuario.nombre).all()
    # Añadir conteo de citas canceladas por cliente
    for c in clientes:
        try:
            c.citas_canceladas = Cita.query.filter_by(id_cliente=c.id, estado='cancelada').count()
        except Exception:
            c.citas_canceladas = 0
    return render_template('admin/clientes.html', clientes=clientes, filter_label='Todos')


@app.route('/admin/clientes/hoy')
@admin_required
def admin_clientes_hoy():
    """Listar clientes registrados hoy"""
    from sqlalchemy import func

    hoy = datetime.now().date()
    clientes = Usuario.query.filter(
        Usuario.tipo_usuario == 'cliente',
        func.date(Usuario.fecha_registro) == hoy
    ).order_by(Usuario.nombre).all()

    return render_template(
        'admin/clientes.html',
        clientes=clientes,
        view_title='Clientes registrados hoy',
        filter_label='Hoy'
    )


@app.route('/admin/clientes/editar/<int:id_cliente>', methods=['GET', 'POST'])
@admin_required
def admin_clientes_editar(id_cliente):
    """Editar cliente"""
    cliente = Usuario.query.get_or_404(id_cliente)

    if request.method == 'POST':
        cliente.nombre = request.form.get('nombre')
        cliente.email = request.form.get('email')
        cliente.telefono = request.form.get('telefono')
        cliente.activo = request.form.get('activo') == 'on'

        # Cambiar contraseña solo si se proporciona una nueva
        nueva_password = request.form.get('nueva_password')
        if nueva_password:
            cliente.password = generate_password_hash(nueva_password)

        db.session.commit()
        flash(f'Cliente {cliente.nombre} actualizado exitosamente', 'success')
        return redirect(url_for('admin_clientes'))

    return render_template('admin/clientes_form.html', cliente=cliente)


@app.route('/admin/clientes/eliminar/<int:id_cliente>', methods=['POST'])
@admin_required
def admin_clientes_eliminar(id_cliente):
    """Eliminar cliente"""
    cliente = Usuario.query.get_or_404(id_cliente)

    # Verificar si tiene citas futuras
    citas_futuras = Cita.query.filter(
        Cita.id_cliente == id_cliente,
        Cita.fecha_hora_inicio >= datetime.now(),
        Cita.estado.in_(['pendiente_pago', 'confirmada'])
    ).count()

    if citas_futuras > 0:
        return jsonify({
            'success': False,
            'message': f'No se puede eliminar. El cliente tiene {citas_futuras} cita(s) pendiente(s)'
        }), 400

    nombre = cliente.nombre
    db.session.delete(cliente)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Cliente {nombre} eliminado exitosamente'
    })

# ============================================================================
# RUTAS PANEL ADMIN - GESTIÓN DE HORARIOS
# ============================================================================


@app.route('/admin/horarios')
@admin_required
def admin_horarios():
    """Listar horarios de todos los empleados"""
    empleados = Empleado.query.filter_by(activo=True).all()
    dias_semana = {
        0: 'Domingo', 1: 'Lunes', 2: 'Martes', 3: 'Miércoles',
        4: 'Jueves', 5: 'Viernes', 6: 'Sábado'
    }
    return render_template('admin/horarios.html', empleados=empleados, dias_semana=dias_semana)


@app.route('/admin/horarios/crear/<int:id_empleado>', methods=['GET', 'POST'])
@admin_required
def admin_horarios_crear(id_empleado):
    """Crear horario para empleado"""
    empleado = Empleado.query.get_or_404(id_empleado)

    if request.method == 'POST':
        dia_semana = int(request.form.get('dia_semana'))
        hora_inicio_str = request.form.get('hora_inicio')
        hora_fin_str = request.form.get('hora_fin')

        # Validar que no exista ya un horario para ese día
        horario_existente = HorarioEmpleado.query.filter_by(
            id_empleado=id_empleado,
            dia_semana=dia_semana
        ).first()

        if horario_existente:
            flash('Ya existe un horario para este empleado en ese día', 'error')
            return redirect(url_for('admin_horarios_crear', id_empleado=id_empleado))

        # Convertir strings a time
        hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()

        if hora_inicio >= hora_fin:
            flash('La hora de inicio debe ser menor que la hora de fin', 'error')
            return redirect(url_for('admin_horarios_crear', id_empleado=id_empleado))

        # Crear horario
        nuevo_horario = HorarioEmpleado(
            id_empleado=id_empleado,
            dia_semana=dia_semana,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin
        )

        db.session.add(nuevo_horario)
        db.session.commit()

        flash(f'Horario creado exitosamente para {empleado.nombre}', 'success')
        return redirect(url_for('admin_horarios'))

    # GET
    dias_semana = {
        0: 'Domingo', 1: 'Lunes', 2: 'Martes', 3: 'Miércoles',
        4: 'Jueves', 5: 'Viernes', 6: 'Sábado'
    }
    return render_template('admin/horarios_form.html', empleado=empleado, horario=None, dias_semana=dias_semana)


@app.route('/admin/horarios/editar/<int:id_horario>', methods=['GET', 'POST'])
@admin_required
def admin_horarios_editar(id_horario):
    """Editar horario"""
    horario = HorarioEmpleado.query.get_or_404(id_horario)

    if request.method == 'POST':
        hora_inicio_str = request.form.get('hora_inicio')
        hora_fin_str = request.form.get('hora_fin')

        # Convertir strings a time
        hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()

        if hora_inicio >= hora_fin:
            flash('La hora de inicio debe ser menor que la hora de fin', 'error')
            return redirect(url_for('admin_horarios_editar', id_horario=id_horario))

        horario.hora_inicio = hora_inicio
        horario.hora_fin = hora_fin

        db.session.commit()
        flash('Horario actualizado exitosamente', 'success')
        return redirect(url_for('admin_horarios'))

    # GET
    dias_semana = {
        0: 'Domingo', 1: 'Lunes', 2: 'Martes', 3: 'Miércoles',
        4: 'Jueves', 5: 'Viernes', 6: 'Sábado'
    }
    return render_template(
        'admin/horarios_form.html',
        empleado=horario.empleado,
        horario=horario,
        dias_semana=dias_semana)


@app.route('/admin/horarios/eliminar/<int:id_horario>', methods=['POST'])
@admin_required
def admin_horarios_eliminar(id_horario):
    """Eliminar horario"""
    horario = HorarioEmpleado.query.get_or_404(id_horario)

    db.session.delete(horario)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Horario eliminado exitosamente'
    })

# ============================================================================
# RUTAS PANEL ADMIN - GESTIÓN DE CITAS
# ============================================================================


@app.route('/admin/citas')
@admin_required
def admin_citas():
    """Listar todas las citas"""
    # Filtros
    estado = request.args.get('estado', 'todas')
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')

    query = db.session.query(Cita, Usuario, Empleado, Servicio).join(
        Usuario, Cita.id_cliente == Usuario.id
    ).outerjoin(
        Empleado, Cita.id_empleado == Empleado.id_empleado
    ).join(
        Servicio, Cita.id_servicio == Servicio.id_servicio
    )

    # Aplicar filtros
    if estado != 'todas':
        query = query.filter(Cita.estado == estado)

    # Filtrar por cliente si se pasa cliente_id
    cliente_id = request.args.get('cliente_id')
    if cliente_id:
        try:
            cid = int(cliente_id)
            query = query.filter(Cita.id_cliente == cid)
        except ValueError:
            pass

    if fecha_desde:
        fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
        query = query.filter(Cita.fecha_hora_inicio >= fecha_desde_dt)

    if fecha_hasta:
        fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Cita.fecha_hora_inicio < fecha_hasta_dt)

    citas = query.order_by(Cita.fecha_hora_inicio.desc()).all()

    # Si se filtró por cliente, obtener objeto para mostrar en la cabecera
    cliente_filtrado = None
    cliente_id = request.args.get('cliente_id')
    if cliente_id:
        try:
            cliente_filtrado = Usuario.query.get(int(cliente_id))
        except Exception:
            cliente_filtrado = None

    return render_template('admin/citas.html', citas=citas, estado_filtro=estado, cliente_filtrado=cliente_filtrado)


@app.route('/admin/citas/cambiar-estado/<int:id_cita>', methods=['POST'])
@admin_required
def admin_citas_cambiar_estado(id_cita):
    """Cambiar estado de una cita"""
    cita = Cita.query.get_or_404(id_cita)
    nuevo_estado = request.form.get('estado')

    estados_validos = ['pendiente_pago', 'confirmada', 'en_atencion', 'completada', 'cancelada', 'no_asistio']

    if nuevo_estado not in estados_validos:
        return jsonify({'success': False, 'message': 'Estado inválido'}), 400

    cita.estado = nuevo_estado
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Estado de cita actualizado a {nuevo_estado}'
    })

# ============================================================================
# RUTAS PANEL ADMIN - GESTIÓN DE PAGOS
# ============================================================================


@app.route('/admin/pagos')
@admin_required
def admin_pagos():
    """Listar todos los pagos registrados"""
    pagos = db.session.query(Pago, Cita, Usuario, Servicio)\
        .join(Cita, Pago.id_cita == Cita.id_cita)\
        .join(Usuario, Cita.id_cliente == Usuario.id)\
        .join(Servicio, Cita.id_servicio == Servicio.id_servicio)\
        .order_by(Pago.fecha_pago.desc()).all()

    return render_template('admin/pagos.html', pagos=pagos)


@app.route('/admin/pagos/registrar/<int:id_cita>', methods=['GET', 'POST'])
@admin_required
def admin_pagos_registrar(id_cita):
    """Registrar pago para una cita"""
    cita = Cita.query.get_or_404(id_cita)
    cliente = Usuario.query.get(cita.id_cliente)
    servicio = Servicio.query.get(cita.id_servicio)

    # Verificar que no tenga ya un pago
    if cita.pago:
        flash('Esta cita ya tiene un pago registrado', 'error')
        return redirect(url_for('admin_pagos'))

    if request.method == 'POST':
        monto = request.form.get('monto', type=float)
        metodo = request.form.get('metodo_pago', 'efectivo')
        referencia = request.form.get('referencia', '').strip() or None
        notas = request.form.get('notas', '').strip() or None

        if not monto or monto <= 0:
            flash('El monto debe ser mayor a 0', 'error')
            return redirect(url_for('admin_pagos_registrar', id_cita=id_cita))

        metodos_validos = ['efectivo', 'tarjeta', 'transferencia', 'nequi', 'daviplata']
        if metodo not in metodos_validos:
            flash('Método de pago inválido', 'error')
            return redirect(url_for('admin_pagos_registrar', id_cita=id_cita))

        nuevo_pago = Pago(
            id_cita=id_cita,
            monto=Decimal(str(monto)),
            metodo_pago=metodo,
            estado_pago='completado',
            referencia=referencia,
            notas=notas
        )
        db.session.add(nuevo_pago)

        # Actualizar estado de cita y saldo
        cita.monto_abono = Decimal(str(monto))
        cita.saldo_pendiente = (cita.monto_total or Decimal('0')) - Decimal(str(monto))
        if cita.saldo_pendiente <= 0:
            cita.estado = 'completada'

        db.session.commit()
        # Notificar al cliente
        try:
            add_notificacion(
                cita.id_cliente,
                'Pago registrado',
                f'Se registró un pago de ${monto:,.0f} para tu cita. Saldo pendiente: ${cita.saldo_pendiente:,.0f}',
                target=url_for('mis_citas')
            )
        except Exception:
            pass

        # Notificar a administradores
        try:
            admins = Usuario.query.filter_by(tipo_usuario='admin').all()
            for a in admins:
                add_notificacion(
                    a.id,
                    'Pago registrado',
                    f'Pago de ${monto:,.0f} registrado para la cita #{cita.id_cita} del cliente {cliente.nombre}',
                    target=url_for('admin_pagos')
                )
        except Exception:
            pass

        flash(f'Pago de ${monto:,.0f} registrado exitosamente', 'success')
        return redirect(url_for('admin_pagos'))

    # GET — formulario
    metodos = ['efectivo', 'tarjeta', 'transferencia', 'nequi', 'daviplata']
    return render_template('admin/pagos_form.html',
                           cita=cita, cliente=cliente,
                           servicio=servicio, metodos=metodos)


@app.route('/admin/pagos/eliminar/<int:id_pago>', methods=['POST'])
@admin_required
def admin_pagos_eliminar(id_pago):
    """Eliminar un pago (reembolso)"""
    pago = Pago.query.get_or_404(id_pago)
    pago.cita.reembolsado = True
    pago.cita.estado = 'cancelada'
    db.session.delete(pago)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Pago eliminado y cita marcada como reembolsada'})
@app.route('/admin/exportar/<tipo>/<periodo>')
@admin_required
def admin_exportar_excel(tipo, periodo):
    if tipo not in ['citas', 'pagos', 'empleados', 'servicios', 'clientes', 'horarios']:
        flash('Tipo de exportación no válido.', 'error')
        return redirect(url_for('dashboard_admin'))

    hoy = datetime.now()
    if periodo == 'diario':
        fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=7)
    elif periodo == 'mes':
        fecha_inicio = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif periodo == 'ano':
        fecha_inicio = hoy.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        fecha_inicio = datetime(1900, 1, 1)

    wb = openpyxl.Workbook()
    ws = wb.active

    if tipo == 'citas':
        ws.title = "Citas"
        ws.append(["ID", "Código", "Cliente", "Servicio", "Monto", "Estado", "Fecha"])
        query = Cita.query.filter(Cita.fecha_creacion >= fecha_inicio).all()
        for c in query:
            cli = Usuario.query.get(c.id_cliente)
            srv = Servicio.query.get(c.id_servicio)
            ws.append([c.id_cita, c.codigo_reserva, cli.nombre if cli else '', srv.nombre_servicio if srv else '', float(c.monto_total), c.estado, c.fecha_creacion.strftime('%Y-%m-%d %H:%M')])
            
    elif tipo == 'pagos':
        ws.title = "Pagos"
        ws.append(["ID Pago", "Código Cita", "Monto", "Método", "Estado", "Fecha"])
        query = Pago.query.filter(Pago.fecha_pago >= fecha_inicio).all()
        for p in query:
            cita = Cita.query.get(p.id_cita)
            ws.append([p.id_pago, cita.codigo_reserva if cita else '', float(p.monto), p.metodo_pago, p.estado_pago, p.fecha_pago.strftime('%Y-%m-%d %H:%M')])
            
    elif tipo == 'empleados':
        ws.title = "Empleados"
        ws.append(["ID", "Nombre", "Email", "Especialidad", "Estado"])
        query = Usuario.query.filter_by(tipo_usuario='empleado').filter(Usuario.fecha_registro >= fecha_inicio).all()
        for e in query:
            ws.append([e.id, e.nombre, e.email, getattr(e, 'especialidad', ''), "Activo" if getattr(e, 'activo', True) else "Inactivo"])
            
    elif tipo == 'clientes':
        ws.title = "Clientes"
        ws.append(["ID", "Nombre", "Email", "Teléfono", "Fecha Registro"])
        query = Usuario.query.filter_by(tipo_usuario='cliente').filter(Usuario.fecha_registro >= fecha_inicio).all()
        for c in query:
            ws.append([c.id, c.nombre, c.email, c.telefono, c.fecha_registro.strftime('%Y-%m-%d %H:%M')])
            
    elif tipo == 'servicios':
        ws.title = "Servicios"
        ws.append(["ID", "Nombre", "Descripción", "Precio", "Duración"])
        query = Servicio.query.all() # No date filter for services
        for s in query:
            ws.append([s.id_servicio, s.nombre_servicio, s.descripcion, float(s.precio_total), s.duracion_minutos])
            
    elif tipo == 'horarios':
        ws.title = "Horarios"
        ws.append(["ID Horario", "Empleado", "Día", "Hora Inicio", "Hora Fin"])
        query = HorarioEmpleado.query.all()
        for h in query:
            emp = Empleado.query.get(h.id_empleado)
            ws.append([h.id_horario, emp.nombre if emp else '', h.dia_semana, h.hora_inicio.strftime('%H:%M'), h.hora_fin.strftime('%H:%M')])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f"export_{tipo}_{periodo}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ============================================================================
# RUTAS PANEL ADMIN - PAGOS POR CONFIRMAR
# ============================================================================

@app.route('/admin/pagos-por-confirmar')
@admin_required
def admin_pagos_confirmar():
    """Listar citas en estado pendiente_pago para que el admin confirme el abono"""
    citas = db.session.query(Cita, Usuario, Servicio, Empleado)\
        .join(Usuario, Cita.id_cliente == Usuario.id)\
        .join(Servicio, Cita.id_servicio == Servicio.id_servicio)\
        .outerjoin(Empleado, Cita.id_empleado == Empleado.id_empleado)\
        .filter(Cita.estado == 'pendiente_pago')\
        .order_by(Cita.fecha_hora_inicio.asc()).all()

    return render_template('admin/pagos_confirmar.html', citas=citas)


@app.route('/admin/pagos-por-confirmar/aceptar/<int:id_cita>', methods=['POST'])
@admin_required
def admin_aceptar_pago(id_cita):
    """Confirmar el pago de una cita: cambia estado a 'confirmada' y notifica a la clienta"""
    cita = Cita.query.get_or_404(id_cita)

    if cita.estado != 'pendiente_pago':
        return jsonify({'success': False, 'message': 'Esta cita ya fue procesada'}), 400

    cita.estado = 'confirmada'
    db.session.commit()

    # Notificar a la clienta
    try:
        add_notificacion(
            cita.id_cliente,
            '¡Cita Confirmada! 🎉',
            f'Tu pago fue verificado. Tu cita del {cita.fecha_hora_inicio.strftime("%d/%m/%Y a las %H:%M")} está confirmada. ¡Te esperamos!',
            target=url_for('mis_citas')
        )
    except Exception:
        pass

    return jsonify({'success': True, 'message': 'Pago aceptado y cita confirmada'})


if __name__ == '__main__':
    app.run(debug=True)
