# Reglas de Desarrollo y Arquitectura — Rossmix Flask (MVT)

Este documento define las directrices y reglas de negocio para el desarrollo del proyecto Rossmix en su estructura MVT (Model-View-Template).

## 1. Arquitectura MVT y Separación de Responsabilidades

* **Modelos (`app/models/`)**: 
  - Toda la interacción con la base de datos y la definición del esquema debe estar encapsulada aquí.
  - No instanciar `db = SQLAlchemy()` en los modelos; importar la instancia global desde `app.extensions`.
  - La lógica de validación interna de los datos y cálculos automáticos de campos (ej. `saldo_pendiente = precio_total - monto_abono`) debe residir preferentemente en métodos del modelo o propiedades (`@property`).

* **Vistas / Blueprints (`app/views/`)**:
  - Actúan como controladores delegados para gestionar las peticiones HTTP y devolver respuestas (JSON o Renderizado de Templates HTML).
  - Mantener las vistas "delgadas" (Skinny Controllers). La lógica de negocio compleja debe extraerse a helpers o servicios.
  - Todas las vistas nuevas deben ser registradas dentro de un Blueprint en `app/views/` e importadas/registradas en `app/__init__.py`.

* **Plantillas / Templates (`app/templates/`)**:
  - Utilizar herencia con Jinja2 extendiendo de `base.html`.
  - Usar la función global adaptada `url_for` para la navegación dinámica. Para nuevos desarrollos, preferir la sintaxis explícita `url_for('blueprint.endpoint')`.

## 2. Reglas de Negocio del Sistema de Citas y Pagos

* **Políticas de Citas**:
  - Una cita solo puede ser agendada en fechas y horas futuras.
  - La duración de la cita depende estrictamente del atributo `duracion_minutos` del `Servicio` asociado.
  - **Cancelación**: Un cliente solo puede cancelar su cita con un **mínimo de 2 horas de anticipación** respecto a la fecha y hora de inicio de la cita.

* **Políticas de Pagos**:
  - El monto del abono mínimo por defecto al agendar una cita es de **$5,000.00**.
  - El `saldo_pendiente` debe actualizarse automáticamente cada vez que se registre un pago.
  - Si el `saldo_pendiente` llega a 0, el estado de la cita se actualiza automáticamente a `completada`.
  - El reembolso de un pago cancela la cita y marca la columna `reembolsado` en la base de datos.

## 3. Estilo de Código y Prevención de Errores

* **Evitar Importaciones Circulares**:
  - No importar el objeto `app` directamente dentro de los submódulos. Utilizar `current_app` de Flask cuando sea necesario acceder a la configuración o contexto de la aplicación activa.
  - Las importaciones de modelos dentro de la inicialización de la app (`app/__init__.py`) deben ser tardías (dentro de los bloques de contexto `with app.app_context():`).

* **Control de Transacciones**:
  - Siempre envolver las operaciones de escritura en la base de datos con bloques `try-except` adecuados, aplicando `db.session.rollback()` en caso de errores para mantener la integridad transaccional de PostgreSQL.

## 4. Metodología de Implementación de Clases y Reglas de Negocio (9 Pasos)

Para cada entidad, modelo o servicio lógico que maneje reglas de negocio o manipulación de datos, se debe estructurar el código siguiendo estrictamente esta secuencia:

### Fase de Definición (En el Modelo o Clase de Servicio)
1. **Crear la Clase**: Definir la entidad con la estructura formal de Python / SQLAlchemy.
2. **Definir Variables**: Declarar los campos de la base de datos o variables estáticas de clase.
3. **Crear Constructor (`__init__`)**: Inicializar el objeto asignando valores predeterminados y opcionales.
4. **Crear Atributos**: Asignar los parámetros a las propiedades del objeto (`self.propiedad`).
5. **Crear Encapsulamiento**: Definir propiedades protegidas o decoradas con `@property` y `@property.setter` para recibir y validar datos de forma controlada.
6. **Crear Métodos de Negocio**: Codificar funciones internas encargadas de aplicar las reglas de negocio (ej. cálculos de saldo, validación de fechas), manejo de responsabilidades y operaciones seguras sobre la base de datos (`db.session`).

---

### Fase de Consumo (En las Vistas, Blueprints o Scripts principales)
7. **Crear la Instancia del Objeto**: Invocar al constructor enviando los argumentos iniciales correspondientes.
8. **Llamar a los Métodos**: Ejecutar la lógica de negocio pasando los argumentos con los datos capturados en el request.
9. **Retornos y Almacenamiento**: Recibir los resultados de las operaciones en variables de almacenamiento para su posterior presentación, redirección o retorno en formato JSON.

