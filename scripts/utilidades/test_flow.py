import os
from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import Usuario, Servicio, Empleado, EmpleadoServicio, Cita, Pago

app = create_app()

with app.app_context():
    # Ensure fresh DB (optional)
    db.session.commit()
    # Create a client user if not exists
    client = Usuario.query.filter_by(email='client@example.com').first()
    if not client:
        client = Usuario(
            nombre='Cliente Prueba',
            email='client@example.com',
            telefono='3001234567',
            password='hashed_password',  # assume pre‑hashed for test
            tipo_usuario='cliente'
        )
        db.session.add(client)

    # Create a service if not exists
    service = Servicio.query.filter_by(nombre='Test Service').first()
    if not service:
        service = Servicio(
            nombre='Test Service',
            descripcion='Servicio de prueba',
            precio_total=50000,
            duracion_minutos=60
        )
        db.session.add(service)

    # Create an employee (especialista)
    emp = Empleado.query.filter_by(email='emp@example.com').first()
    if not emp:
        emp = Empleado(
            nombre='Especialista Prueba',
            email='emp@example.com',
            telefono='3009876543',
            password='hashed_password',
            activo=True
        )
        db.session.add(emp)
        db.session.flush()  # get emp.id_empleado
        # link employee to user (optional)
        usuario_emp = Usuario(
            nombre='Especialista Usuario',
            email='emp_user@example.com',
            telefono='3001112222',
            password='hashed_password',
            tipo_usuario='especialista',
            id_empleado=emp.id_empleado
        )
        db.session.add(usuario_emp)

    # Associate employee with service
    if not EmpleadoServicio.query.filter_by(id_empleado=emp.id_empleado, id_servicio=service.id_servicio).first():
        emp_serv = EmpleadoServicio(id_empleado=emp.id_empleado, id_servicio=service.id_servicio)
        db.session.add(emp_serv)

    db.session.commit()

    # Schedule a cita for the client, tomorrow at 10:00
    start = datetime.utcnow() + timedelta(days=1)
    start = start.replace(hour=10, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=service.duracion_minutos)
    cita = Cita(
        id_cliente=client.id,
        id_servicio=service.id_servicio,
        fecha_hora_inicio=start,
        fecha_hora_fin=end,
        monto_total=service.precio_total,
        monto_abono=0,
        saldo_pendiente=service.precio_total,
        estado='pendiente_pago'
    )
    db.session.add(cita)
    db.session.commit()

    # Simulate payment (client pays full amount)
    pago = Pago(
        id_cita=cita.id_cita,
        monto=cita.monto_total,
        metodo_pago='efectivo',
        estado_pago='completado'
    )
    db.session.add(pago)
    # Update cita status and pending balance
    cita.monto_abono = cita.monto_total
    cita.saldo_pendiente = 0
    cita.estado = 'completada'
    db.session.commit()

    print('Test flow completed: cita created and marked as pagada.')
