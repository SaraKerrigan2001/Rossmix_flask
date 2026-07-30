from app import app, db, Servicio, Cita, Pago
with app.app_context():
    print("Servicios:")
    for s in Servicio.query.all():
        if s.precio_total == 18001:
            print(f"ID: {s.id_servicio}, Precio: {s.precio_total}")
            s.precio_total = 18000
    
    print("Citas:")
    for c in Cita.query.all():
        if c.monto_total == 18001:
            print(f"Cita ID: {c.id_cita}, Monto Total: {c.monto_total}")
            c.monto_total = 18000
        if c.saldo_pendiente == 18001:
            print(f"Cita ID: {c.id_cita}, Saldo Pendiente: {c.saldo_pendiente}")
            c.saldo_pendiente = 18000

    print("Pagos:")
    for p in Pago.query.all():
        if p.monto == 18001:
            print(f"Pago ID: {p.id_pago}, Monto: {p.monto}")
            p.monto = 18000
    db.session.commit()
    print("Updates committed!")
