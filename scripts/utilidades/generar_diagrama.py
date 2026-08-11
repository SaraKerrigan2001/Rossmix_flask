"""
Genera un diagrama visual de la BD Rossmix en formato PNG usando matplotlib.
Guarda en: docs/Rossmix_BD_Diagrama.png
         + Rossmix-20260810T155230Z-1-001/Rossmix/Base de Datos/Rossmix.jpeg (reemplaza)
"""
import os, sys
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch
except ImportError:
    print("Instalando matplotlib...")
    os.system(f"{sys.executable} -m pip install matplotlib -q")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch

# ── Definición de tablas ──────────────────────────────────────────────────────
TABLAS = {
    'usuario': {
        'color': '#c41e3a', 'pos': (7.5, 9.5),
        'cols': [
            ('PK', 'id',             'serial'),
            ('',   'nombre',         'varchar(100)'),
            ('',   'email',          'varchar(150) UNIQUE'),
            ('',   'telefono',       'varchar(20)'),
            ('',   'password',       'varchar(200)'),
            ('',   'tipo_usuario',   'varchar(20) ✓admin/cliente/especialista'),
            ('',   'fecha_registro', 'timestamp'),
            ('',   'activo',         'boolean'),
            ('FK', 'id_empleado',    'integer → empleados'),
        ]
    },
    'servicios': {
        'color': '#059669', 'pos': (14, 9.5),
        'cols': [
            ('PK', 'id_servicio',      'serial'),
            ('',   'nombre_servicio',  'varchar(100)'),
            ('',   'descripcion',      'text'),
            ('',   'precio_total',     'numeric(10,2)'),
            ('',   'duracion_minutos', 'integer'),
            ('',   'activo',           'boolean'),
        ]
    },
    'empleados': {
        'color': '#7c3aed', 'pos': (7.5, 5.5),
        'cols': [
            ('PK', 'id_empleado',   'serial'),
            ('',   'nombre',        'varchar(100)'),
            ('',   'especialidad',  'varchar(100)'),
            ('',   'activo',        'boolean'),
            ('',   'fecha_registro','timestamp'),
        ]
    },
    'empleado_servicios': {
        'color': '#2563eb', 'pos': (11.5, 5.5),
        'cols': [
            ('FK', 'id_empleado', 'integer → empleados'),
            ('FK', 'id_servicio', 'integer → servicios'),
        ]
    },
    'horarios_empleados': {
        'color': '#0891b2', 'pos': (3.5, 5.5),
        'cols': [
            ('PK', 'id_horario',  'serial'),
            ('FK', 'id_empleado', 'integer → empleados'),
            ('',   'dia_semana',  'integer (0=Dom..6=Sáb)'),
            ('',   'hora_inicio', 'time'),
            ('',   'hora_fin',    'time'),
        ]
    },
    'citas': {
        'color': '#c41e3a', 'pos': (7.5, 1.5),
        'cols': [
            ('PK', 'id_cita',           'serial'),
            ('FK', 'id_cliente',        'integer → usuario'),
            ('FK', 'id_empleado',       'integer → empleados (NULL ok)'),
            ('FK', 'id_servicio',       'integer → servicios'),
            ('',   'fecha_hora_inicio', 'timestamp'),
            ('',   'fecha_hora_fin',    'timestamp'),
            ('',   'monto_total',       'numeric(10,2)'),
            ('',   'monto_abono',       'numeric(10,2) def 5000'),
            ('',   'saldo_pendiente',   'numeric(10,2)'),
            ('',   'estado',            'estado_cita_enum'),
            ('',   'reembolsado',       'boolean'),
            ('',   'codigo_reserva',    'varchar(20) UNIQUE'),
            ('',   'token_gestion',     'varchar(32) UNIQUE ✦'),
            ('',   'notas',             'text'),
            ('',   'fecha_creacion',    'timestamp'),
        ]
    },
    'pagos': {
        'color': '#d97706', 'pos': (2.5, 1.5),
        'cols': [
            ('PK', 'id_pago',     'serial'),
            ('FK', 'id_cita',     'integer → citas UNIQUE'),
            ('',   'monto',       'numeric(10,2)'),
            ('',   'metodo_pago', 'metodo_pago_enum'),
            ('',   'estado_pago', 'varchar(20)'),
            ('',   'referencia',  'varchar(100)'),
            ('',   'fecha_pago',  'timestamp'),
            ('',   'notas',       'text'),
        ]
    },
    'notificaciones': {
        'color': '#be185d', 'pos': (13, 1.5),
        'cols': [
            ('PK', 'id',         'serial'),
            ('FK', 'id_usuario', 'integer → usuario'),
            ('',   'titulo',     'varchar(200)'),
            ('',   'mensaje',    'text'),
            ('',   'target',     'varchar(300)'),
            ('',   'leido',      'boolean'),
            ('',   'fecha',      'timestamp'),
        ]
    },
    'auditoria_usuarios': {
        'color': '#475569', 'pos': (3, 9.5),
        'cols': [
            ('PK', 'id',             'serial'),
            ('',   'id_usuario',     'integer'),
            ('',   'nombre',         'varchar(100)'),
            ('',   'email',          'varchar(120)'),
            ('',   'telefono',       'varchar(20)'),
            ('',   'tipo_usuario',   'varchar(20)'),
            ('',   'fecha_registro', 'timestamp'),
            ('',   'accion',         'varchar(10) INSERT/BACKFILL'),
            ('',   'ip_address',     'varchar(45)'),
        ]
    },
}

fig, ax = plt.subplots(1, 1, figsize=(22, 16))
ax.set_xlim(0, 18); ax.set_ylim(-1, 13)
ax.axis('off')
ax.set_facecolor('#1a1a2e')
fig.patch.set_facecolor('#1a1a2e')

TITLE_H    = 0.45
ROW_H      = 0.30
BOX_W      = 4.8
PAD        = 0.15

for nombre, info in TABLAS.items():
    x, y   = info['pos']
    cols   = info['cols']
    color  = info['color']
    total_h = TITLE_H + len(cols) * ROW_H + PAD * 2

    # Sombra
    sombra = FancyBboxPatch((x - BOX_W/2 + 0.05, y - total_h - 0.05),
                             BOX_W, total_h, boxstyle='round,pad=0.05',
                             linewidth=0, facecolor='#000000', alpha=0.5, zorder=1)
    ax.add_patch(sombra)

    # Cuerpo
    cuerpo = FancyBboxPatch((x - BOX_W/2, y - total_h),
                             BOX_W, total_h, boxstyle='round,pad=0.05',
                             linewidth=1.5, edgecolor=color,
                             facecolor='#16213e', zorder=2)
    ax.add_patch(cuerpo)

    # Header
    header = FancyBboxPatch((x - BOX_W/2, y - TITLE_H),
                             BOX_W, TITLE_H, boxstyle='round,pad=0.05',
                             linewidth=0, facecolor=color, zorder=3)
    ax.add_patch(header)

    # Nombre tabla
    ax.text(x, y - TITLE_H/2, nombre, ha='center', va='center',
            fontsize=9, fontweight='bold', color='white', zorder=4)

    # Columnas
    for i, (tipo, col, dtype) in enumerate(cols):
        cy = y - TITLE_H - PAD - (i + 0.5) * ROW_H
        # Icono tipo
        if tipo == 'PK':
            icon, ic_color = 'PK', '#fbbf24'
        elif tipo == 'FK':
            icon, ic_color = 'FK', '#60a5fa'
        else:
            icon, ic_color = ' •', '#94a3b8'

        ax.text(x - BOX_W/2 + 0.15, cy, icon,
                ha='left', va='center', fontsize=7, color=ic_color, zorder=4)
        ax.text(x - BOX_W/2 + 0.45, cy, col,
                ha='left', va='center', fontsize=7.5, fontweight='bold',
                color='#e2e8f0', zorder=4)
        ax.text(x + BOX_W/2 - 0.1, cy, dtype,
                ha='right', va='center', fontsize=6.5,
                color='#64748b', zorder=4, style='italic')

# Título
ax.text(9, 12.5, 'ROSSMIX — Diagrama de Base de Datos',
        ha='center', va='center', fontsize=16, fontweight='bold',
        color='white', zorder=5)
ax.text(9, 12.1, '9 tablas · 2 tipos ENUM · 3 vistas · 1 trigger pg_notify',
        ha='center', va='center', fontsize=10, color='#94a3b8', zorder=5)

# Leyenda
leyenda_items = [
    mpatches.Patch(color='#c41e3a', label='usuario / citas'),
    mpatches.Patch(color='#059669', label='servicios'),
    mpatches.Patch(color='#7c3aed', label='empleados'),
    mpatches.Patch(color='#2563eb', label='relaciones'),
    mpatches.Patch(color='#d97706', label='pagos'),
    mpatches.Patch(color='#be185d', label='notificaciones'),
    mpatches.Patch(color='#475569', label='auditoría'),
]
ax.legend(handles=leyenda_items, loc='lower right',
          facecolor='#16213e', edgecolor='#475569',
          labelcolor='white', fontsize=8, ncol=4)

plt.tight_layout(pad=0.5)

# Guardar en docs/
os.makedirs('docs', exist_ok=True)
out_docs = 'docs/Rossmix_BD_Diagrama.png'
plt.savefig(out_docs, dpi=150, bbox_inches='tight',
            facecolor='#1a1a2e', edgecolor='none')
print(f'OK: {out_docs}')

# Reemplazar también la imagen del respaldo (guardar como PNG con extensión .jpeg)
out_backup = r'Rossmix-20260810T155230Z-1-001\Rossmix\Base de Datos\Rossmix.jpeg'
plt.savefig(out_backup, dpi=130, bbox_inches='tight',
            facecolor='#1a1a2e', edgecolor='none')
print(f'OK: {out_backup}')
plt.close()
