# Reglas de Desarrollo y Arquitectura — Rossmix Flask (MVT Ágil)

Este documento define las directrices y reglas para el desarrollo del proyecto Rossmix. El proyecto adopta una metodología **Ágil**, priorizando la velocidad de desarrollo, adaptabilidad y la entrega continua de valor.

## 1. Metodología de Trabajo (Ágil)
- **Desarrollo Iterativo:** El código se construye en ciclos cortos, agregando funcionalidades utilizables rápidamente.
- **Flexibilidad:** Es válido reestructurar o refactorizar el código conforme surgen nuevos requerimientos. Se prefiere un código funcional e iterativo sobre la sobreingeniería inicial.

## 2. Arquitectura MVT y Manejo de Datos (Enfoque Simplificado)

Para mantener la velocidad de desarrollo sin perder seguridad, el proyecto adopta un enfoque **MVT (Model-View-Template) Relajado**:

* **Modelos (`app/models/`)**: 
  - Define únicamente las tablas, relaciones y columnas de la base de datos usando SQLAlchemy.
  - **No es obligatorio** crear encapsulamientos complejos (`@property`) ni constructores manuales (`__init__`). Los modelos pueden mantenerse simples.

* **Vistas / Blueprints (`app/views/`)**:
  - Actúan como los controladores principales de la aplicación.
  - **Se permite incluir la lógica de negocio y validaciones directamente en las funciones de las rutas** ("Fat Controllers") para agilizar la programación.
  - Ejemplo: Las validaciones de fechas, validación de empleados y cálculos de saldos pueden hacerse dentro de la misma función de la vista antes de guardar.
  - Las vistas deben registrarse dentro de Blueprints en `app/views/`.

## 3. Reglas de Negocio Centrales (Obligatorias)

Aunque la arquitectura del código sea flexible, las siguientes reglas del negocio de Rossmix se deben seguir respetando al momento de programar:

* **Políticas de Citas**:
  - Solo se pueden agendar citas en fechas y horas futuras (ej. mínimo 30 min de anticipación).
  - La duración de la cita depende estrictamente del servicio asociado.
  - Un cliente solo puede cancelar con un **mínimo de 2 horas de anticipación**.

* **Políticas de Pagos**:
  - El monto mínimo de abono es **$5,000.00**.
  - El `saldo_pendiente` debe recalcularse y guardarse cada vez que se registre un pago.
  - Si el `saldo_pendiente` llega a 0, el estado de la cita pasa automáticamente a `completada`.
  - Reembolsar un pago implica cancelar la cita y marcar `reembolsado` = True.

## 4. Estilo de Código y Transacciones Seguras

Para garantizar que programar rápido en las Vistas no corrompa la base de datos:

* **Control de Transacciones (CRUD Seguro)**: 
  Toda operación de escritura (Create, Update, Delete) debe usar obligatoriamente un bloque `try-except` con `db.session.rollback()`.
  
  ```python
  try:
      # Toda tu lógica ágil, validaciones y cálculos van aquí
      db.session.add(nueva_cita)
      db.session.commit()
  except Exception as e:
      db.session.rollback()
      # Manejo del error (flash message, logger, etc.)
  ```

* **Evitar Importaciones Circulares**: No importar `app` directamente. Usa `current_app` de Flask cuando necesites el contexto de la aplicación.
