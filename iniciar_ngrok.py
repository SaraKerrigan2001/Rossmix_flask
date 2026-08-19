"""
Inicia el tunel ngrok para exponer Rossmix al internet.
Uso: python iniciar_ngrok.py
"""
from pyngrok import ngrok, conf
import time

TOKEN = "3I6yRR1R8jPXnaVtiTKCDeiicHY_5ghVrtLda93kDPFkg9rDf"

conf.get_default().auth_token = TOKEN

print("Iniciando tunel ngrok...")
tunnel = ngrok.connect(5000, "http")
url = tunnel.public_url

print()
print("=" * 55)
print(f"  URL PUBLICA: {url}")
print(f"  Comparte este link con cualquier persona.")
print(f"  Funciona desde celular, PC o cualquier lugar.")
print("=" * 55)
print()
print("Presiona Ctrl+C para cerrar el tunel.")

try:
    ngrok.get_ngrok_process().proc.wait()
except KeyboardInterrupt:
    ngrok.kill()
    print("Tunel cerrado.")
