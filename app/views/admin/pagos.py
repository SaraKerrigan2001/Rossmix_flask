"""Gestión de pagos (admin)."""
from decimal import Decimal
from flask import render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db
from app.models import Usuario, Servicio, Cita, Pago
from app.utils.decorators import admin_required
from app.utils.helpers import add_notificacion
from app.views.admin import admin_bp


@admin_bp.route('/pagos')
@admin_required
def pagos():
    """Listar todos los pagos registrados"""
    lista_pagos = db.session.query(Pago, Cita, Usuario, Servicio)\
        .join(Cita, Pago.id_cita == Cita.id_cita)\
        .join(Usuario, Cita.id_cliente == Usuario.id)\
        .join(Servicio, Cita.id_servicio == Servicio.id_servicio)\
        .order_by(Pago.fecha_pago.desc()).all()

    return render_template('admin/pagos.html', pagos=lista_pagos)


@admin_bp.route('/pagos/registrar/<int:id_cita>', methods=['GET', 'POST'])
@admin_required
def pagos_registrar(id_cita):
    """Registrar pago para una cita"""
    cita = db.get_or_404(Cita, id_cita)
    cliente = db.session.get(Usuario, cita.id_cliente)
    servicio = db.session.get(Servicio, cita.id_servicio)

    # Verificar que no tenga ya un pago
    if cita.pago:
        flash('Esta cita ya tiene un pago registrado', 'error')
        return redirect(url_for('admin.pagos'))

    if request.method == 'POST':
        monto = request.form.get('monto', type=float)
        metodo = request.form.get('metodo_pago', 'efectivo')
        referencia = request.form.get('referencia', '').strip() or None
        notas = request.form.get('notas', '').strip() or None

        if not monto or monto <= 0:
            flash('El monto debe ser mayor a 0', 'error')
            return redirect(url_for('admin.pagos_registrar', id_cita=id_cita))

        # ── Tarea 2: Limitar monto al saldo pendiente real ─────────────────────
        saldo_real = float(cita.saldo_pendiente or cita.monto_total or 0)
        if monto > saldo_real + 0.01:   # tolerancia de 1 centavo por redondeo
            flash(f'El monto no puede superar el saldo pendiente de ${saldo_real:,.0f}', 'error')
            return redirect(url_for('admin.pagos_registrar', id_cita=id_cita))

        metodos_validos = ['efectivo', 'tarjeta', 'transferencia']
        if metodo not in metodos_validos:
            flash('Método de pago inválido', 'error')
            return redirect(url_for('admin.pagos_registrar', id_cita=id_cita))

        nuevo_pago = Pago(
            id_cita=id_cita,
            monto=Decimal(str(monto)),
            metodo_pago=metodo,
            estado_pago='completado',
            referencia=referencia,
            notas=notas
        )
        db.session.add(nuevo_pago)

        # Actualizar estado de cita y saldo — acumular abono (igual que el pago del cliente)
        cita.monto_abono = (cita.monto_abono or Decimal('0')) + Decimal(str(monto))
        cita.saldo_pendiente = (cita.monto_total or Decimal('0')) - cita.monto_abono
        if cita.saldo_pendiente <= 0:
            cita.estado = 'completada'
            cita.saldo_pendiente = Decimal('0')

        db.session.commit()
        # Notificar al cliente
        try:
            add_notificacion(
                cita.id_cliente,
                'Pago registrado',
                f'Se registró un pago de ${monto:,.0f} para tu cita. Saldo pendiente: ${cita.saldo_pendiente:,.0f}',
                target=url_for('citas.mis_citas')
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
                    target=url_for('admin.pagos')
                )
        except Exception:
            pass

        flash(f'Pago de ${monto:,.0f} registrado exitosamente', 'success')
        return redirect(url_for('admin.pagos'))

    # GET — formulario
    metodos = ['efectivo', 'tarjeta', 'transferencia']
    return render_template('admin/pagos_form.html',
                           cita=cita, cliente=cliente,
                           servicio=servicio, metodos=metodos)


@admin_bp.route('/pagos/eliminar/<int:id_pago>', methods=['POST'])
@admin_required
def pagos_eliminar(id_pago):
    """Eliminar un pago (reembolso)"""
    pago = db.get_or_404(Pago, id_pago)
    monto = float(pago.monto)
    id_cliente = pago.cita.id_cliente
    codigo = pago.cita.codigo_reserva or f'#{pago.cita.id_cita}'

    pago.cita.reembolsado = True
    pago.cita.estado = 'cancelada'
    db.session.delete(pago)
    db.session.commit()

    # Notificar al cliente del reembolso
    try:
        add_notificacion(
            id_cliente,
            'Reembolso procesado',
            f'Se procesó un reembolso de ${monto:,.0f} COP para tu cita {codigo}. '
            f'Tu cita ha sido cancelada.',
            target=url_for('citas.mis_citas')
        )
    except Exception:
        pass

    return jsonify({'success': True, 'message': f'Reembolso de ${monto:,.0f} procesado. Cita cancelada.'})


@admin_bp.route('/pagos/confirmar')
@admin_required
def pagos_confirmar():
    """Citas con pago pendiente de confirmación"""
    citas_pendientes = db.session.query(Cita, Usuario, Servicio)\
        .join(Usuario, Cita.id_cliente == Usuario.id)\
        .join(Servicio, Cita.id_servicio == Servicio.id_servicio)\
        .filter(
            Cita.estado.in_(['pendiente_pago', 'confirmada']),
            ~Cita.id_cita.in_(
                db.session.query(Pago.id_cita).filter(Pago.estado_pago == 'completado')
            )
        ).order_by(Cita.fecha_hora_inicio).all()

    return render_template('admin/pagos_confirmar.html', citas=citas_pendientes)
