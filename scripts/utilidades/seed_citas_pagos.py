"""Carga citas y pagos de prueba realistas en la base de datos de Rossmix."""
import os
import sys
import random
from datetime import datetime, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)

from app import create_app
from app.extensions import db
from app.models import Usuario, Servicio, Empleado, EmpleadoServicio, Cita, Pago

# Lista de comentarios reales para las notas de citas
NOTAS_EJEMPLOS = [
    "Cliente prefiere esmalte semipermanente brillante.",
    "Uñas acrílicas con diseño de mariposa en el dedo anular.",
    "Exfoliación suave por piel sensible.",
    "Corte estilo Bob con degrafilado.",
    "Cabello tinturado previamente, aplicar hidratación extra.",
    "Requiere diseño de cejas muy natural.",
    "Diseño de pestañas efecto rímel.",
    "Cliente llega 10 minutos tarde (notificó).",
    "Prefiere que la atienda en la cabina del fondo.",
    "Recomendado por otra cliente regular."
]

def generar_codigo_reserva():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "RES-" + "".join(random.choices(chars, k=6))

def generar_token_gestion():
    import secrets
    return secrets.token_hex(16)

app = create_app()
with app.app_context():
    try:
        print("Eliminando citas y pagos anteriores para iniciar limpio...")
        # Eliminación en cascada manual
        db.session.query(Pago).delete()
        db.session.query(Cita).delete()
        db.session.commit()
        print("Tablas citas y pagos limpias.")
    except Exception as e:
        db.session.rollback()
        print(f"Error al limpiar tablas: {e}")
        sys.exit(1)

    try:
        # Obtener clientes, servicios y empleados activos
        clientes = Usuario.query.filter_by(tipo_usuario='cliente', activo=True).all()
        servicios = Servicio.query.filter_by(activo=True).all()
        empleados = Empleado.query.filter_by(activo=True).all()

        if not clientes or not servicios or not empleados:
            print("Error: Asegúrate de correr los seeds de usuarios y catálogo primero.")
            sys.exit(1)

        # Mapear qué empleados pueden hacer qué servicios
        # estructura: {id_servicio: [id_empleado1, id_empleado2]}
        servicio_empleados = {}
        for relacion in EmpleadoServicio.query.all():
            if relacion.id_servicio not in servicio_empleados:
                servicio_empleados[relacion.id_servicio] = []
            servicio_empleados[relacion.id_servicio].append(relacion.id_empleado)

        # Rellenar con cualquier empleado si no hay relaciones específicas para evitar fallos
        for s in servicios:
            if s.id_servicio not in servicio_empleados:
                servicio_empleados[s.id_servicio] = [emp.id_empleado for emp in empleados]

        # Fechas de referencia
        ahora = datetime.now()
        
        # Generar 25 citas (15 en el pasado, 10 en el futuro)
        citas_creadas = 0
        pagos_creados = 0

        # Para evitar solapamientos de un mismo empleado a la misma hora
        # Guardaremos los bloques de tiempo ocupados: {id_empleado: [(inicio, fin)]}
        ocupaciones = {emp.id_empleado: [] for emp in empleados}

        # Generar citas pasadas (completadas, canceladas, no asistió)
        for i in range(15):
            cliente = random.choice(clientes)
            servicio = random.choice(servicios)
            
            # Seleccionar un empleado calificado para este servicio
            empleados_disponibles = servicio_empleados.get(servicio.id_servicio, [emp.id_empleado for emp in empleados])
            id_empleado = random.choice(empleados_disponibles)
            
            # Buscar una hora en el pasado (hace 1 a 10 días)
            # Intentar hasta encontrar un horario libre para el empleado
            for _ in range(50):
                dias_atras = random.randint(1, 10)
                hora = random.randint(8, 17)
                minuto = random.choice([0, 30])
                
                fecha_inicio = ahora.replace(hour=hora, minute=minuto, second=0, microsecond=0) - timedelta(days=dias_atras)
                fecha_fin = fecha_inicio + timedelta(minutes=servicio.duracion_minutos)
                
                # Verificar solapamiento
                solapado = False
                for (ocupado_ini, ocupado_fin) in ocupaciones[id_empleado]:
                    if not (fecha_fin <= ocupado_ini or fecha_inicio >= ocupado_fin):
                        solapado = True
                        break
                
                if not solapado:
                    # Reservar bloque
                    ocupaciones[id_empleado].append((fecha_inicio, fecha_fin))
                    break
            else:
                # Si no se encuentra slot libre tras 50 intentos, pasar a la siguiente cita
                continue

            # Estado de citas pasadas
            # 80% completada, 10% no_asistio, 10% cancelada
            prob = random.random()
            if prob < 0.8:
                estado = 'completada'
                monto_abono = servicio.precio_total
            elif prob < 0.9:
                estado = 'no_asistio'
                monto_abono = 5000  # Perdió el abono
            else:
                estado = 'cancelada'
                monto_abono = 0  # Reembolsado o cancelado sin pago

            saldo_pendiente = servicio.precio_total - monto_abono
            
            # Crear cita
            cita = Cita(
                id_cliente=cliente.id,
                id_empleado=id_empleado,
                id_servicio=servicio.id_servicio,
                fecha_hora_inicio=fecha_inicio,
                fecha_hora_fin=fecha_fin,
                monto_total=servicio.precio_total,
                monto_abono=monto_abono,
                saldo_pendiente=saldo_pendiente,
                estado=estado,
                reembolsado=(estado == 'cancelada'),
                codigo_reserva=generar_codigo_reserva(),
                token_gestion=generar_token_gestion(),
                notas=random.choice(NOTAS_EJEMPLOS) if random.random() > 0.3 else None,
                fecha_creacion=fecha_inicio - timedelta(days=random.randint(1, 3))
            )
            db.session.add(cita)
            db.session.flush() # obtener id_cita
            citas_creadas += 1

            # Registrar pago si hubo abono/pago
            if monto_abono > 0:
                pago = Pago(
                    id_cita=cita.id_cita,
                    monto=monto_abono,
                    metodo_pago=random.choice(['efectivo', 'tarjeta', 'transferencia', 'nequi', 'daviplata']),
                    estado_pago='completado',
                    referencia=f"TXN-{random.randint(10000000, 99999999)}",
                    fecha_pago=cita.fecha_creacion + timedelta(hours=random.randint(1, 4)),
                    notas="Pago registrado por seed de datos"
                )
                db.session.add(pago)
                pagos_creados += 1

        # Generar citas futuras (pendiente_pago, confirmada)
        for i in range(10):
            cliente = random.choice(clientes)
            servicio = random.choice(servicios)
            
            empleados_disponibles = servicio_empleados.get(servicio.id_servicio, [emp.id_empleado for emp in empleados])
            id_empleado = random.choice(empleados_disponibles)
            
            # Buscar una hora en el futuro (dentro de los próximos 1 a 10 días)
            for _ in range(50):
                dias_adelante = random.randint(1, 10)
                hora = random.randint(8, 17)
                minuto = random.choice([0, 30])
                
                fecha_inicio = ahora.replace(hour=hora, minute=minuto, second=0, microsecond=0) + timedelta(days=dias_adelante)
                fecha_fin = fecha_inicio + timedelta(minutes=servicio.duracion_minutos)
                
                # Verificar solapamiento
                solapado = False
                for (ocupado_ini, ocupado_fin) in ocupaciones[id_empleado]:
                    if not (fecha_fin <= ocupado_ini or fecha_inicio >= ocupado_fin):
                        solapado = True
                        break
                
                if not solapado:
                    ocupaciones[id_empleado].append((fecha_inicio, fecha_fin))
                    break
            else:
                continue

            # Estado de citas futuras
            # 30% pendiente_pago, 70% confirmada
            prob = random.random()
            if prob < 0.3:
                estado = 'pendiente_pago'
                monto_abono = 0
            else:
                estado = 'confirmada'
                # Abono puede ser el mínimo o un porcentaje
                monto_abono = random.choice([5000, 10000, 15000, 20000])
                if monto_abono > servicio.precio_total:
                    monto_abono = servicio.precio_total

            saldo_pendiente = servicio.precio_total - monto_abono
            
            # Crear cita
            cita = Cita(
                id_cliente=cliente.id,
                id_empleado=id_empleado,
                id_servicio=servicio.id_servicio,
                fecha_hora_inicio=fecha_inicio,
                fecha_hora_fin=fecha_fin,
                monto_total=servicio.precio_total,
                monto_abono=monto_abono,
                saldo_pendiente=saldo_pendiente,
                estado=estado,
                codigo_reserva=generar_codigo_reserva(),
                token_gestion=generar_token_gestion(),
                notas=random.choice(NOTAS_EJEMPLOS) if random.random() > 0.3 else None,
                fecha_creacion=ahora - timedelta(hours=random.randint(1, 24))
            )
            db.session.add(cita)
            db.session.flush()
            citas_creadas += 1

            # Registrar pago si hubo abono
            if monto_abono > 0:
                pago = Pago(
                    id_cita=cita.id_cita,
                    monto=monto_abono,
                    metodo_pago=random.choice(['efectivo', 'tarjeta', 'transferencia', 'nequi', 'daviplata']),
                    estado_pago='completado',
                    referencia=f"TXN-{random.randint(10000000, 99999999)}",
                    fecha_pago=cita.fecha_creacion + timedelta(minutes=random.randint(5, 30)),
                    notas="Abono de reserva"
                )
                db.session.add(pago)
                pagos_creados += 1

        db.session.commit()
        print('=' * 60)
        print('SEMILLERO DE CITAS Y PAGOS COMPLETADO CON ÉXITO')
        print(f"Citas insertadas: {citas_creadas}")
        print(f"Pagos insertados: {pagos_creados}")
        print('=' * 60)

    except Exception as e:
        db.session.rollback()
        print(f"Ocurrió un error al cargar los datos: {e}")
        sys.exit(1)
