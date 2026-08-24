"""Carga el catalogo de servicios y sus especialistas en PostgreSQL."""
import os
import sys
from datetime import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)

from app import create_app
from app.extensions import db
from app.models import Servicio, Empleado, EmpleadoServicio, HorarioEmpleado

SERVICIOS = [
    ('Manicure Clásico', 'Limado, esmaltado y cuidado básico de uñas', 25000, 45),
    ('Manicure con Gel', 'Manicure con esmalte en gel de larga duración', 45000, 60),
    ('Pedicure Spa', 'Pedicure completo con exfoliación y masaje', 35000, 60),
    ('Uñas Acrílicas', 'Aplicación de uñas acrílicas con diseño', 80000, 120),
    ('Decoración de Uñas', 'Diseños artísticos en uñas', 15000, 30),
    ('Corte Dama', 'Corte profesional con lavado y secado', 30000, 45),
    ('Corte Caballero', 'Corte masculino con acabados', 20000, 30),
    ('Tinte Completo', 'Coloración completa con retoque de raíces', 70000, 120),
    ('Mechas Balayage', 'Iluminación natural con técnica balayage', 120000, 180),
    ('Keratina y Alisado', 'Tratamiento de keratina para alisar y nutrir', 150000, 150),
    ('Brushing y Peinado', 'Secado profesional con plancha o rizos', 25000, 45),
    ('Depilación Piernas', 'Depilación con cera piernas completas', 40000, 45),
    ('Depilación Axilas', 'Depilación con cera axilas', 15000, 15),
    ('Depilación Facial', 'Depilación de bozo y mejillas', 20000, 30),
    ('Diseño de Cejas', 'Perfilado y diseño profesional', 18000, 30),
    ('Laminado de Cejas', 'Tratamiento para cejas definidas y voluminosas', 50000, 60),
    ('Extensiones de Pestañas', 'Aplicación de extensiones pelo a pelo', 90000, 90),
    ('Lifting de Pestañas', 'Rizado y definición de pestañas naturales', 55000, 60),
]

GRUPOS = {
    'Ana Rodríguez': range(0, 5),
    'Laura Martínez': range(0, 5),
    'Sofía López': range(5, 11),
    'Carolina Pérez': range(5, 11),
    'Valentina Torres': range(5, 11),
    'Daniela Ramírez': range(11, 14),
    'Camila Flores': range(14, 16),
    'Isabella Castro': range(16, 18),
    'Gabriela Morales': range(0, 18),
}

app = create_app()
with app.app_context():
    servicios = []
    for nombre, descripcion, precio, duracion in SERVICIOS:
        servicio = Servicio.query.filter_by(nombre_servicio=nombre).first()
        if not servicio:
            servicio = Servicio(nombre_servicio=nombre, descripcion=descripcion,
                                precio_total=precio, duracion_minutos=duracion, activo=True)
            db.session.add(servicio)
            db.session.flush()
        servicios.append(servicio)

    for nombre_empleado, indices in GRUPOS.items():
        empleado = Empleado.query.filter_by(nombre=nombre_empleado).first()
        if not empleado:
            continue
        for indice in indices:
            relacion = EmpleadoServicio.query.filter_by(
                id_empleado=empleado.id_empleado,
                id_servicio=servicios[indice].id_servicio,
            ).first()
            if not relacion:
                db.session.add(EmpleadoServicio(
                    id_empleado=empleado.id_empleado,
                    id_servicio=servicios[indice].id_servicio,
                ))

    for empleado in Empleado.query.filter_by(activo=True).all():
        for dia_semana, hora_inicio, hora_fin in [
            (dia, time(8, 0), time(18, 0)) for dia in range(1, 6)
        ] + [(6, time(9, 0), time(16, 0))]:
            horario = HorarioEmpleado.query.filter_by(
                id_empleado=empleado.id_empleado,
                dia_semana=dia_semana,
            ).first()
            if not horario:
                db.session.add(HorarioEmpleado(
                    id_empleado=empleado.id_empleado,
                    dia_semana=dia_semana,
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin,
                ))

    db.session.commit()
    print(f'Catálogo listo: {Servicio.query.filter_by(activo=True).count()} servicios activos')
    print(f'Relaciones servicio-empleado: {EmpleadoServicio.query.count()}')
    print(f'Horarios configurados: {HorarioEmpleado.query.count()}')
