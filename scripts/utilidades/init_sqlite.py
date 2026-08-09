import os
from datetime import datetime, timedelta, time
from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models import Usuario, Servicio, Empleado, EmpleadoServicio, HorarioEmpleado, Cita, Pago

# 1. Remove outdated test.db from root and instance folder
for path in ['test.db', 'instance/test.db']:
    db_path = os.path.join(os.path.dirname(__file__), path)
    if os.path.exists(db_path):
        print(f"Deleting old database: {db_path}...")
        os.remove(db_path)


app = create_app()

with app.app_context():
    # 2. Create tables
    print("Creating database schema...")
    db.create_all()

    # 3. Seed Services
    print("Seeding services...")
    servicios_data = [
        # Uñas
        ('Manicure Clásico', 'Limado, esmaltado y cuidado básico de uñas', 25000, 45),
        ('Manicure con Gel', 'Manicure con esmalte en gel de larga duración', 45000, 60),
        ('Pedicure Spa', 'Pedicure completo con exfoliación y masaje', 35000, 60),
        ('Uñas Acrílicas', 'Aplicación de uñas acrílicas con diseño', 80000, 120),
        ('Decoración de Uñas', 'Diseños artísticos en uñas', 15000, 30),
        # Cabello
        ('Corte Dama', 'Corte profesional con lavado y secado', 30000, 45),
        ('Corte Caballero', 'Corte masculino con acabados', 20000, 30),
        ('Tinte Completo', 'Coloración completa con retoque de raíces', 70000, 120),
        ('Mechas Balayage', 'Iluminación natural con técnica balayage', 120000, 180),
        ('Keratina y Alisado', 'Tratamiento de keratina para alisar y nutrir', 150000, 150),
        ('Brushing y Peinado', 'Secado profesional con plancha o rizos', 25000, 45),
        # Depilación
        ('Depilación Piernas', 'Depilación con cera piernas completas', 40000, 45),
        ('Depilación Axilas', 'Depilación con cera axilas', 15000, 15),
        ('Depilación Facial', 'Depilación de bozo y mejillas', 20000, 30),
        # Cejas y Pestañas
        ('Diseño de Cejas', 'Perfilado y diseño profesional', 18000, 30),
        ('Laminado de Cejas', 'Tratamiento para cejas definidas y voluminosas', 50000, 60),
        ('Extensiones de Pestañas', 'Aplicación de extensiones pelo a pelo', 90000, 90),
        ('Lifting de Pestañas', 'Rizado y definición de pestañas naturales', 55000, 60)
    ]
    
    for nombre, desc, precio, duracion in servicios_data:
        s = Servicio(nombre_servicio=nombre, descripcion=desc, precio_total=precio, duracion_minutos=duracion)
        db.session.add(s)
    db.session.commit()

    # 4. Seed Employees
    print("Seeding employees...")
    empleados_data = [
        ('María González', 'Especialista en Uñas'),
        ('Ana Rodríguez', 'Manicurista Profesional'),
        ('Laura Martínez', 'Nail Artist'),
        ('Sofía López', 'Estilista Senior'),
        ('Carolina Pérez', 'Colorista Experta'),
        ('Valentina Torres', 'Estilista y Maquilladora'),
        ('Daniela Ramírez', 'Depilación y Estética'),
        ('Camila Flores', 'Especialista en Cejas'),
        ('Isabella Castro', 'Extensionista de Pestañas'),
        ('Gabriela Morales', 'Estilista Integral')
    ]
    
    for nombre, esp in empleados_data:
        e = Empleado(nombre=nombre, especialidad=esp, activo=True)
        db.session.add(e)
    db.session.commit()

    # 5. Link Employee-Services
    print("Linking employees and services...")
    services = Servicio.query.all()
    employees = Empleado.query.all()

    # Uñas: María(1), Ana(2), Laura(3)
    for emp_idx in [0, 1, 2]:
        for s_idx in range(5):
            db.session.add(EmpleadoServicio(id_empleado=employees[emp_idx].id_empleado, id_servicio=services[s_idx].id_servicio))

    # Cabello: Sofía(4), Carolina(5), Valentina(6)
    for emp_idx in [3, 4, 5]:
        for s_idx in range(5, 11):
            db.session.add(EmpleadoServicio(id_empleado=employees[emp_idx].id_empleado, id_servicio=services[s_idx].id_servicio))

    # Depilación: Daniela(7)
    for s_idx in range(11, 14):
        db.session.add(EmpleadoServicio(id_empleado=employees[6].id_empleado, id_servicio=services[s_idx].id_servicio))

    # Cejas/Pestañas: Camila(8), Isabella(9)
    for s_idx in range(14, 16):
        db.session.add(EmpleadoServicio(id_empleado=employees[7].id_empleado, id_servicio=services[s_idx].id_servicio))
    for s_idx in range(16, 18):
        db.session.add(EmpleadoServicio(id_empleado=employees[8].id_empleado, id_servicio=services[s_idx].id_servicio))

    # Integral: Gabriela(10)
    for s_idx in range(18):
        db.session.add(EmpleadoServicio(id_empleado=employees[9].id_empleado, id_servicio=services[s_idx].id_servicio))

    db.session.commit()

    # 6. Seed Horarios
    print("Seeding schedules...")
    for emp in employees:
        for dia in range(1, 6):
            h = HorarioEmpleado(
                id_empleado=emp.id_empleado,
                dia_semana=dia,
                hora_inicio=time(8, 0),
                hora_fin=time(18, 0)
            )
            db.session.add(h)
        h_sab = HorarioEmpleado(
            id_empleado=emp.id_empleado,
            dia_semana=6,
            hora_inicio=time(9, 0),
            hora_fin=time(16, 0)
        )
        db.session.add(h_sab)
    db.session.commit()

    # 7. Seed Users
    print("Seeding users...")
    admin_user = Usuario.query.filter_by(email='admin@rossmix.com').first()
    if not admin_user:
        admin_user = Usuario(
            nombre='Administrador',
            email='admin@rossmix.com',
            telefono='3000000000',
            password=generate_password_hash('admin123'),
            tipo_usuario='admin'
        )
        db.session.add(admin_user)

    client_user = Usuario.query.filter_by(email='andrea.vargas@email.com').first()
    if not client_user:
        client_user = Usuario(
            nombre='Andrea Vargas',
            email='andrea.vargas@email.com',
            telefono='3100000001',
            password=generate_password_hash('cliente123'),
            tipo_usuario='cliente'
        )
        db.session.add(client_user)

    specialist_user = Usuario.query.filter_by(email='maria@rossmix.com').first()
    if not specialist_user:
        specialist_user = Usuario(
            nombre='María González',
            email='maria@rossmix.com',
            telefono='3001234567',
            password=generate_password_hash('admin123'),
            tipo_usuario='especialista',
            id_empleado=employees[0].id_empleado
        )
        db.session.add(specialist_user)
    
    db.session.commit()


    # 8. Mock appointments
    print("Seeding mock appointments...")
    hoy = datetime.now()
    
    fecha_completada = hoy - timedelta(days=3)
    c_comp = Cita(
        id_cliente=client_user.id,
        id_empleado=employees[0].id_empleado,
        id_servicio=services[0].id_servicio,
        fecha_hora_inicio=fecha_completada.replace(hour=10, minute=0, second=0),
        fecha_hora_fin=fecha_completada.replace(hour=10, minute=45, second=0),
        monto_total=25000,
        monto_abono=25000,
        saldo_pendiente=0,
        estado='completada',
        codigo_reserva='RES-COMPL1',
        fecha_creacion=fecha_completada
    )
    db.session.add(c_comp)
    db.session.flush()

    pago_comp = Pago(
        id_cita=c_comp.id_cita,
        monto=25000,
        metodo_pago='efectivo',
        estado_pago='completado',
        fecha_pago=fecha_completada
    )
    db.session.add(pago_comp)

    fecha_futura = hoy + timedelta(days=1)
    c_fut = Cita(
        id_cliente=client_user.id,
        id_empleado=employees[0].id_empleado,
        id_servicio=services[1].id_servicio,
        fecha_hora_inicio=fecha_futura.replace(hour=14, minute=0, second=0),
        fecha_hora_fin=fecha_futura.replace(hour=15, minute=0, second=0),
        monto_total=45000,
        monto_abono=5000,
        saldo_pendiente=40000,
        estado='confirmada',
        codigo_reserva='RES-FUTUR1',
        fecha_creacion=hoy
    )
    db.session.add(c_fut)
    db.session.flush()

    pago_fut = Pago(
        id_cita=c_fut.id_cita,
        monto=5000,
        metodo_pago='nequi',
        estado_pago='completado',
        fecha_pago=hoy
    )
    db.session.add(pago_fut)

    db.session.commit()
    print("Database SQLite initialization and seeding completed successfully!")
