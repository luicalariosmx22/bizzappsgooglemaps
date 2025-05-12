import googlemaps
import json
import time

# 👉 Reemplaza con tu propia API KEY de Google Places
API_KEY = 'AIzaSyDylhN9adFvJXFKZg0OgBJHqAblgJAgOzo'
gmaps = googlemaps.Client(key=API_KEY)

# 👉 Lista de ciudades base para recorrer Estados Unidos (puedes expandirla fácilmente)
ciudades = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
    "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
    "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC",
    "San Francisco, CA", "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Nashville, TN"
]

# 👉 Términos de búsqueda
terminos = ["gastric sleeve", "bariatric clinic"]

resultados = []

for ciudad in ciudades:
    for termino in terminos:
        print(f"🔍 Buscando '{termino}' en {ciudad}")
        try:
            lugares = gmaps.places(query=termino, location=ciudad, radius=50000)
            for lugar in lugares.get('results', []):
                resultados.append({
                    'nombre': lugar.get('name'),
                    'direccion': lugar.get('formatted_address'),
                    'rating': lugar.get('rating'),
                    'num_reviews': lugar.get('user_ratings_total'),
                    'sitio_web': lugar.get('website'),
                    'telefono': lugar.get('formatted_phone_number'),
                    'tipo': termino,
                    'ciudad': ciudad
                })
        except Exception as e:
            print(f"❌ Error en {ciudad} con término '{termino}': {e}")
        time.sleep(2)  # Espera para evitar límite de peticiones

# 💾 Guardar en archivo JSON
with open('clinicas_bariatricas.json', 'w', encoding='utf-8') as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

print(f"\n✅ Guardado completado: {len(resultados)} resultados en clinicas_bariatricas.json")
