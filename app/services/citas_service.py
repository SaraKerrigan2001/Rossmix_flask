"""Lógica de negocio para la gestión de citas."""
import secrets
import random
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from app.extensions import db
from app.models import Cita, Servicio, Empleado, EmpleadoServicio, HorarioEmpleado

logger = logging.getLogger(__name__)


class CitaService:
    DEFAULT_ABONO = Decimal('5000.00')

    @staticmethod
    def validar_disponibilidad_cita(id_empleado, fecha_hora_inicio, fecha_hora_fin):
        """Verifica si un empleado tiene un conflicto de agenda."""
        if not id_empleado:
            return True

        conflicto = Cita.query.filter(
            Cita.id_empleado == id_empleado,
            Cita.fecha_hora_inicio < fecha_hora_fin,
            Cita.fecha_hora_fin > fecha_hora_inicio,
            Cita.estado.in_(['pendiente_pago', 'confirmada', 'en_atencion'])
        ).first()

        return conflicto is None

    @staticmethod
    def obtener_horarios_disponibles(fecha, id_servicio, id_empleado=None):
        """Retorna los slots disponibles para un servicio y empleado en una fecha dada."""
        if not fecha or not id_servicio:
            return []

        if id_empleado == 0:
            empleados_ids = db.session.query(EmpleadoServicio.id_empleado).filter_by(id_servicio=id_servicio).all()
            empleados_ids = [e[0] for e in empleados_ids]
            if not empleados_ids:
                return []
            id_empleado = random.choice(empleados_ids)

        servicio = db.session.get(Servicio, id_servicio)
        if not servicio:
            return []

        dia_semana = (fecha.weekday() + 1) % 7
        horario = HorarioEmpleado.query.filter_by(id_empleado=id_empleado, dia_semana=dia_semana).first()
        if not horario:
            return []

        horarios_list = []
        hora_actual = datetime.combine(fecha, horario.hora_inicio)
        hora_fin = datetime.combine(fecha, horario.hora_fin)
        duracion = timedelta(minutes=servicio.duracion_minutos)

        # Si la fecha es hoy, descartar slots que ya pasaron o están muy próximos
        ahora = datetime.now()
        if fecha == ahora.date():
            # Saltar slots que ya iniciaron o faltan menos de 30 min
            minimo = ahora + timedelta(minutes=30)
            while hora_actual < minimo:
                hora_actual += timedelta(minutes=30)

        while hora_actual + duracion <= hora_fin:
            if CitaService.validar_disponibilidad_cita(id_empleado, hora_actual, hora_actual + duracion):
                horarios_list.append({
                    'hora': hora_actual.strftime('%H:%M'),
                    'hora_fin': (hora_actual + duracion).strftime('%H:%M'),
                    'disponible': True,
                })
            hora_actual += timedelta(minutes=30)

        return horarios_list

    @staticmethod
    def generar_codigo_reserva():
        """Genera un código de reserva criptográficamente seguro (8 chars)."""
        return secrets.token_urlsafe(6)[:8].upper()

    @staticmethod
    def generar_token_gestion():
        """Genera un token URL-safe de 32 caracteres para el link de gestión."""
        return secrets.token_urlsafe(24)  # 24 bytes → 32 caracteres base64url

    @staticmethod
    def bloquear_agenda_cita(cita_id):
        """Bloquea la agenda de una cita (cambia a pendiente_pago)."""
        try:
            cita = db.session.get(Cita, cita_id)
            if not cita:
                logger.warning(f'Cita {cita_id} no encontrada para bloqueo')
                return False

            cita.estado = 'pendiente_pago'
            db.session.commit()
            logger.info(f'Cita {cita_id} bloqueada a pendiente_pago')
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error al bloquear cita {cita_id}: {str(e)}')
            raise

    @staticmethod
    def desbloquear_agenda_cita(cita_id):
        """Desbloquea la agenda de una cita (cambia a cancelada)."""
        try:
            cita = db.session.get(Cita, cita_id)
            if not cita:
                logger.warning(f'Cita {cita_id} no encontrada para desbloqueo')
                return False

            cita.estado = 'cancelada'
            db.session.commit()
            logger.info(f'Cita {cita_id} desbloqueada (cancelada)')
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error al desbloquear cita {cita_id}: {str(e)}')
            raise

    @staticmethod
    def crear_cita(id_cliente, id_servicio, id_empleado, fecha_hora_inicio, fecha_hora_fin):
        """
        Crea una nueva cita con validación de disponibilidad.
        Transacción explícita con rollback en caso de error.
        """
        try:
            servicio = db.session.get(Servicio, id_servicio)
            if not servicio:
                logger.error(f'Servicio {id_servicio} no encontrado')
                raise ValueError('Servicio no encontrado')

            # Validar disponibilidad
            if not CitaService.validar_disponibilidad_cita(id_empleado, fecha_hora_inicio, fecha_hora_fin):
                logger.warning(
                    f'Conflicto de agenda: empleado {id_empleado} '
                    f'en {fecha_hora_inicio} - {fecha_hora_fin}'
                )
                raise ValueError('Horario no disponible')

            codigo_reserva = CitaService.generar_codigo_reserva()
            token_gestion  = CitaService.generar_token_gestion()
            monto_total = Decimal(str(servicio.precio_total))
            saldo_pendiente = monto_total - CitaService.DEFAULT_ABONO

            cita = Cita(
                id_cliente=id_cliente,
                id_empleado=id_empleado,
                id_servicio=id_servicio,
                fecha_hora_inicio=fecha_hora_inicio,
                fecha_hora_fin=fecha_hora_fin,
                monto_total=monto_total,
                monto_abono=CitaService.DEFAULT_ABONO,
                saldo_pendiente=saldo_pendiente,
                estado='pendiente_pago',
                reembolsado=False,
                codigo_reserva=codigo_reserva,
                token_gestion=token_gestion,
                fecha_creacion=datetime.now(),
            )

            db.session.add(cita)
            db.session.commit()
            logger.info(
                f'Cita creada: {cita.id_cita} (cliente {id_cliente}, '
                f'empleado {id_empleado}, código {codigo_reserva})'
            )
            return cita
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error al crear cita: {str(e)}', exc_info=True)
            raise
