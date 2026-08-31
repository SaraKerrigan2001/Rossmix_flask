"""
Carga citas y pagos de prueba realistas en el PostgreSQL LOCAL de Rossmix.
Conexión: localhost:5432, usuario postgres, contraseña 1234, base Rossmix.
"""
import os
import sys
import random
from datetime import datetime, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)

# Forzar la conexión LOCAL (no Docker)
os.environ['DATABASE_URL'] = 'postgresql+psycopg://postgres:1234@localhost:5432/Rossmix'

from app import create_app
from app.extensions import db
from app.models import Usuario, Servicio, Empleado, EmpleadoServicio, Cita, Pago

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
    "Recomendado por otra cliente regular.",
]

def generar_codigo_reserva():
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "RES-" + "".join(random.choices(chars, k=6))

def generar_token_gestion():
    import secrets
    return secrets.token_hex(16)

app = create_app()
with app.app_context():
    # ── Limpiar citas y pagos anteriores ─────────────────────
    try:
        db.session.query(Pago).delete()
        db.session.query(Cita).delete()
        db.session.commit()
        print("Tablas citas y pagos limpias.")
    except Exception as e:
        db.session.rollback()
        print(f"Error al limpiar tablas: {e}")
        sys.exit(1)

    try:
        clientes = Usuario.query.filter_by(tipo_usuario='cliente', activo=True).all()
        servicios = Servicio.query.filter_by(activo=True).all()
        empleados = Empleado.query.filter_by(activo=True).all()

        if not clientes or not servicios or not empleados:
            print("Error: faltan datos de base (usuarios, servicios o empleados).")
            sys.exit(1)

        print(f"Datos disponibles: {len(clientes)} clientes, {len(servicios)} servicios, {len(empleados)} empleados")

        # Mapear servicios → empleados calificados
        servicio_empleados = {}
        for rel in EmpleadoServicio.query.all():
            servicio_empleados.setdefault(rel.id_servicio, []).append(rel.id_empleado)
        for s in servicios:
            if s.id_servicio not in servicio_empleados:
                servicio_empleados[s.id_servicio] = [e.id_empleado for e in empleados]

        ahora = datetime.now()
        ocupaciones = {emp.id_empleado: [] for emp in empleados}
        citas_creadas = 0
        pagos_creados = 0

        # ── 15 citas pasadas ────────────────────────────────
        for _ in range(15):
            cliente = random.choice(clientes)
            servicio = random.choice(servicios)
            id_empleado = random.choice(servicio_empleados[servicio.id_servicio])

            for _intento in range(50):
                dias_atras = random.randint(1, 10)
                hora = random.randint(8, 17)
                minuto = random.choice([0, 30])
                fecha_inicio = ahora.replace(hour=hora, minute=minuto, second=0, microsecond=0) - timedelta(days=dias_atras)
                fecha_fin = fecha_inicio + timedelta(minutes=servicio.duracion_minutos)
                if not any(not (fecha_fin <= oi or fecha_inicio >= of_) for oi, of_ in ocupaciones[id_empleado]):
                    ocupaciones[id_empleado].append((fecha_inicio, fecha_fin))
                    break
            else:
                continue

            prob = random.random()
            if prob < 0.8:
                estado = 'completada'
                monto_abono = servicio.precio_total
            elif prob < 0.9:
                estado = 'no_asistio'
                monto_abono = 5000
            else:
                estado = 'cancelada'
                monto_abono = 0

            saldo = servicio.precio_total - monto_abono

            cita = Cita(
                id_cliente=cliente.id,
                id_empleado=id_empleado,
                id_servicio=servicio.id_servicio,
                fecha_hora_inicio=fecha_inicio,
                fecha_hora_fin=fecha_fin,
                monto_total=servicio.precio_total,
                monto_abono=monto_abono,
                saldo_pendiente=saldo,
                estado=estado,
                reembolsado=(estado == 'cancelada'),
                codigo_reserva=generar_codigo_reserva(),
                token_gestion=generar_token_gestion(),
                notas=random.choice(NOTAS_EJEMPLOS) if random.random() > 0.3 else None,
                fecha_creacion=fecha_inicio - timedelta(days=random.randint(1, 3)),
            )
            db.session.add(cita)
            db.session.flush()
            citas_creadas += 1

            if monto_abono > 0:
                pago = Pago(
                    id_cita=cita.id_cita,
                    monto=monto_abono,
                    metodo_pago=random.choice(['efectivo', 'tarjeta', 'transferencia', 'nequi', 'daviplata']),
                    estado_pago='completado',
                    referencia=f"TXN-{random.randint(10000000, 99999999)}",
                    fecha_pago=cita.fecha_creacion + timedelta(hours=random.randint(1, 4)),
                    notas="Pago registrado",
                )
                db.session.add(pago)
                pagos_creados += 1

        # ── 10 citas futuras ────────────────────────────────
        for _ in range(10):
            cliente = random.choice(clientes)
            servicio = random.choice(servicios)
            id_empleado = random.choice(servicio_empleados[servicio.id_servicio])

            for _intento in range(50):
                dias_adelante = random.randint(1, 10)
                hora = random.randint(8, 17)
                minuto = random.choice([0, 30])
                fecha_inicio = ahora.replace(hour=hora, minute=minuto, second=0, microsecond=0) + timedelta(days=dias_adelante)
                fecha_fin = fecha_inicio + timedelta(minutes=servicio.duracion_minutos)
                if not any(not (fecha_fin <= oi or fecha_inicio >= of_) for oi, of_ in ocupaciones[id_empleado]):
                    ocupaciones[id_empleado].append((fecha_inicio, fecha_fin))
                    break
            else:
                continue

            prob = random.random()
            if prob < 0.3:
                estado = 'pendiente_pago'
                monto_abono = 0
            else:
                estado = 'confirmada'
                monto_abono = random.choice([5000, 10000, 15000, 20000])
                if monto_abono > servicio.precio_total:
                    monto_abono = servicio.precio_total

            saldo = servicio.precio_total - monto_abono

            cita = Cita(
                id_cliente=cliente.id,
                id_empleado=id_empleado,
                id_servicio=servicio.id_servicio,
                fecha_hora_inicio=fecha_inicio,
                fecha_hora_fin=fecha_fin,
                monto_total=servicio.precio_total,
                monto_abono=monto_abono,
                saldo_pendiente=saldo,
                estado=estado,
                codigo_reserva=generar_codigo_reserva(),
                token_gestion=generar_token_gestion(),
                notas=random.choice(NOTAS_EJEMPLOS) if random.random() > 0.3 else None,
                fecha_creacion=ahora - timedelta(hours=random.randint(1, 24)),
            )
            db.session.add(cita)
            db.session.flush()
            citas_creadas += 1

            if monto_abono > 0:
                pago = Pago(
                    id_cita=cita.id_cita,
                    monto=monto_abono,
                    metodo_pago=random.choice(['efectivo', 'tarjeta', 'transferencia', 'nequi', 'daviplata']),
                    estado_pago='completado',
                    referencia=f"TXN-{random.randint(10000000, 99999999)}",
                    fecha_pago=cita.fecha_creacion + timedelta(minutes=random.randint(5, 30)),
                    notas="Abono de reserva",
                )
                db.session.add(pago)
                pagos_creados += 1

        db.session.commit()

        print("=" * 60)
        print("DATOS CARGADOS EN POSTGRESQL LOCAL CON ÉXITO")
        print(f"  Citas insertadas:  {citas_creadas}")
        print(f"  Pagos insertados:  {pagos_creados}")
        print("=" * 60)

    except Exception as e:
        db.session.rollback()
        print(f"Error al cargar datos: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
