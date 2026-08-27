# Manual de Usuario - Rossmix

Bienvenido(a) al sistema de gestión y reservas de **Rossmix**. Este manual te guiará paso a paso sobre cómo utilizar las funcionalidades de la plataforma de manera eficiente y respetando las políticas del salón.

El sistema cuenta con tres tipos de perfiles, cada uno con acceso a herramientas específicas:
1. **Cliente**: Reserva de citas, control de pagos, seguimiento de historial y notificaciones.
2. **Especialista**: Gestión de agenda personal, visualización de citas asignadas y tiempos de servicio.
3. **Administrador**: Control total del sistema, empleados, clientes, caja (confirmación de pagos) y distribución de citas.

---

## 1. Perfil: Cliente

El portal de clientes está diseñado para que puedas agendar y gestionar tus servicios de belleza de forma fácil, segura y rápida.

### 1.1. Registro e Inicio de Sesión
- **Registro:** Si eres nuevo, haz clic en el botón "Registrarse" en la parte superior derecha. Debes proporcionar Nombre, Teléfono, Email y Contraseña. 
- **Inicio de Sesión:** Ingresa tu correo y contraseña en la sección de "Iniciar Sesión".

### 1.2. Agendar una Cita (Flujo Completo)
Agendar una cita consta de tres pasos principales:
1. **Paso 1 (Servicio):** Elige la categoría y el servicio que deseas realizarte. El sistema te mostrará automáticamente la duración estimada y el precio total.
2. **Paso 2 (Especialista y Fecha):** 
   - Selecciona al especialista de tu preferencia. Si no tienes preferencia, selecciona **"Cualquier Especialista"**.
   - Elige una fecha futura en el calendario. *Nota: El sistema solo permite agendar citas en fechas y horas posteriores al momento actual.*
   - Selecciona la hora disponible.
3. **Paso 3 (Pago / Abono):** 
   - Para asegurar tu espacio, **el sistema requiere un abono mínimo de $5,000.00 COP**. 
   - Sube una foto o captura de pantalla de tu comprobante de transferencia o pago.
   - Si tu abono no cubre la totalidad del servicio, el sistema calculará automáticamente tu **Saldo Pendiente**.
4. **Confirmación:** Una vez que subas el comprobante, la cita quedará en estado **"Pendiente"**. Un administrador revisará el comprobante y, al validarlo, la cita pasará a estar **"Confirmada"**.

### 1.3. Cancelaciones y Políticas
- **Política de Cancelación:** Si necesitas cancelar tu cita, debes hacerlo con un **mínimo de 2 horas de anticipación** respecto a la hora de inicio. Pasado este tiempo, el sistema bloqueará la opción de cancelar para proteger el tiempo del especialista.
- **Reembolsos:** Si se aprueba una cancelación con derecho a devolución, el administrador marcará tu pago como "Reembolsado" y tu cita quedará cancelada en el sistema.

### 1.4. Mis Citas y Notificaciones
- **Mis Citas:** Historial completo. Aquí verás tu saldo pendiente y el estado real de tu cita (Pendiente, Confirmada, Completada, Cancelada).
- **Notificaciones (Campanita):** Alertas en tiempo real. Te avisaremos cuando tu pago sea verificado, cuando falte poco para tu cita o si ocurre alguna modificación.

---

## 2. Perfil: Especialista

Como especialista, tu portal (Mi Portal) te ayuda a mantener el orden exacto de tu agenda de trabajo diaria.

### 2.1. Panel Principal (Mi Portal)
Al iniciar sesión, verás un tablero con tus citas programadas para el día de hoy, organizadas por horario. El tiempo de cada cita está estrictamente calculado en base a la duración del servicio que eligió el cliente.

### 2.2. Citas Disponibles (La Bolsa de Citas)
Si un cliente agendó una cita seleccionando "Cualquier Especialista", dicha cita aparecerá en esta sección. 
- Puedes revisar las citas flotantes y hacer clic en **"Tomar"** si tienes el espacio en tu agenda. Una vez tomada, la cita te pertenece y el cliente será notificado.

### 2.3. Mis Citas
Detalle completo de tu trabajo. Por cada cita podrás consultar:
- **Datos del Cliente:** Nombre y botón directo a WhatsApp (si el cliente dejó su número).
- **Servicio:** Qué servicio exacto se realizará y cuánto tiempo tomará.
- **Estado de Pago:** Puedes ver si la cita ya está confirmada por caja, para que procedas con el servicio con total seguridad.

*Atención: Los especialistas no procesan pagos ni cancelan citas directamente. Si hay un cambio de última hora, debes notificar al Administrador.*

---

## 3. Perfil: Administrador

El perfil administrador (Panel Admin) es el centro de mando. Tienes el control total sobre la operación del salón y eres responsable de garantizar que los pagos coincidan con las citas.

### 3.1. Gestión Financiera (Módulo de Pagos)
- **Pagos por Confirmar:** Tu tarea más frecuente. Cuando los clientes suben un comprobante, debes revisar la imagen y verificar que el dinero ingresó a la cuenta del salón.
- Al hacer clic en **"Confirmar"**, el sistema automáticamente:
  1. Acredita el dinero.
  2. Actualiza el *saldo pendiente* del cliente.
  3. Pasa la cita de "Pendiente" a "Confirmada".
- **Cierre de Cita:** Cuando el cliente paga su saldo restante en el salón, registras ese pago extra. Si el saldo pendiente llega a $0, la cita pasa automáticamente a estado **"Completada"**.

### 3.2. Agenda Diaria y Distribución
- **Agenda Diaria:** Un mapa visual de cómo están ocupados todos los especialistas hoy. Te permite identificar tiempos muertos.
- **Distribuir Citas:** Las citas marcadas como "Cualquier Especialista" que no hayan sido tomadas por nadie, pueden ser asignadas manualmente a un empleado específico desde esta pantalla.

### 3.3. Catálogos y Configuraciones
- **Servicios:** Crea, edita o elimina servicios. El atributo `duracion_minutos` es crucial, ya que de eso depende cómo se bloquean los horarios en el calendario.
- **Empleados y Horarios:** Define qué días y en qué rango de horas trabaja cada especialista. El sistema usará esto para mostrar la disponibilidad a los clientes.
- **Accesos:** Genera cuentas de correo y contraseñas para que tu personal pueda entrar al sistema.

---

## 4. Funciones Generales y de Soporte

- **Mi Perfil:** Haz clic en tu nombre en el menú superior para actualizar tu teléfono, cambiar tu contraseña o subir una foto de perfil personalizada.
- **Botones Flotantes:** En la esquina inferior derecha siempre habrá un acceso rápido a WhatsApp o Instagram del salón por si surge alguna duda.
- **Seguridad:** El sistema protege todas las contraseñas e información personal de los clientes bajo encriptación estándar. Siempre recuerda **Cerrar Sesión** en computadoras compartidas del salón.
