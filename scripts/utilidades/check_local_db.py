"""Verifica el estado de las tablas en PostgreSQL local."""
import psycopg

conn = psycopg.connect(host='localhost', port=5432, dbname='Rossmix',
                       user='postgres', password='1234')
cur = conn.cursor()

tables = ['usuario','servicios','empleados','empleado_servicios',
          'horarios_empleados','citas','pagos']

print("=" * 40)
print("ESTADO DE LA BD LOCAL — Rossmix")
print("=" * 40)
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"  {t:25s}: {cur.fetchone()[0]} filas")

conn.close()
