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
    cita = Cita.query.get_or_404(id_cita)
    cliente = Usuario.query.get(cita.id_cliente)
    servicio = Servicio.query.get(cita.id_servicio)

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

        metodos_validos = ['efectivo', 'tarjeta', 'transferencia', 'nequi', 'daviplata']
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
    metodos = ['efectivo', 'tarjeta', 'transferencia', 'nequi', 'daviplata']
    return render_template('admin/pagos_form.html',
                           cita=cita, cliente=cliente,
                           servicio=servicio, metodos=metodos)


@admin_bp.route('/pagos/eliminar/<int:id_pago>', methods=['POST'])
@admin_required
def pagos_eliminar(id_pago):
    """Eliminar un pago (reembolso)"""
    pago = Pago.query.get_or_404(id_pago)
    pago.cita.reembolsado = True
    pago.cita.estado = 'cancelada'
    db.session.delete(pago)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Pago eliminado y cita marcada como reembolsada'})
