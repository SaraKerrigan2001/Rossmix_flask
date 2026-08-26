"""Funciones auxiliares compartidas."""
from flask import session, current_app
from threading import Thread
from flask_mail import Message
from app.extensions import db, mail
from app.models.notificacion import Notificacion
from app.models.usuario import Usuario

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print('Error al enviar correo asíncrono:', e)

def add_notificacion(id_usuario, titulo, mensaje=None, target=None):
    """Crear una notificación. NO hace commit propio — el llamador es responsable."""
    try:
        n = Notificacion(id_usuario=id_usuario, titulo=titulo, mensaje=mensaje, target=target)
        db.session.add(n)
        # No hacemos commit aquí para respetar la transacción del llamador.
        # Si el llamador no hace commit, la notificación no persiste — es intencional.

        # Enviar correo electrónico en background (no bloquea la transacción)
        usuario = db.session.get(Usuario, id_usuario)
        if usuario and usuario.email and '@' in usuario.email:
            msg = Message(
                subject=f"Rossmix - {titulo}",
                recipients=[usuario.email],
                body=f"Hola {usuario.nombre},\n\n{mensaje or titulo}\n\nRevisa tu portal para más detalles."
            )
            Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

    except Exception as e:
        print('Error al crear notificacion:', e)


def inject_notificaciones():
    """Context processor: inyecta notificaciones y contadores en todos los templates."""
    if 'usuario_id' in session:
        try:
            notifs = Notificacion.query.filter_by(
                id_usuario=session['usuario_id']).order_by(
                Notificacion.fecha.desc()).limit(6).all()
            unread = Notificacion.query.filter_by(
                id_usuario=session['usuario_id'], leido=False).count()

            # Contador de pagos por confirmar (solo para admins)
            pagos_por_confirmar = 0
            if session.get('tipo_usuario') == 'admin':
                try:
                    from app.models.cita import Cita
                    from app.models.pago import Pago
                    pagos_por_confirmar = db.session.query(
                        db.func.count(Cita.id_cita)
                    ).filter(
                        Cita.estado.in_(['confirmada', 'en_atencion']),
                        ~db.session.query(Pago.id_pago).filter(
                            Pago.id_cita == Cita.id_cita,
                            Pago.estado_pago == 'completado'
                        ).exists()
                    ).scalar() or 0
                except Exception:
                    pagos_por_confirmar = 0

            return dict(
                notificaciones=notifs,
                notificaciones_unread=unread,
                pagos_por_confirmar=pagos_por_confirmar,
            )
        except Exception:
            return dict(notificaciones=[], notificaciones_unread=0, pagos_por_confirmar=0)
    return dict(notificaciones=[], notificaciones_unread=0, pagos_por_confirmar=0)
