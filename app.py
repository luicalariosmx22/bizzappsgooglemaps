# app.py
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from dotenv import load_dotenv
import json
import googlemaps
import time
import os

load_dotenv()  # Load environment variables from a .env file

DEFAULT_DATA_FILE = 'clinicas_bariatricas.json'
SEARCH_HISTORY_FILE = 'historial_busquedas.json'

app = Flask(__name__)

@app.route('/')
def index():
    print("[INDEX] Cargando datos desde historial o default...")
    try:
        if os.path.exists(SEARCH_HISTORY_FILE):
            print("[INDEX] Historial encontrado.")
            if os.path.getsize(SEARCH_HISTORY_FILE) > 0:  # Check if file is not empty
                with open(SEARCH_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                print("[INDEX] Historial vacío. Cargando datos por defecto.")
                with open(DEFAULT_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
        else:
            print("[INDEX] Historial no encontrado. Cargando datos por defecto.")
            if os.path.exists(DEFAULT_DATA_FILE) and os.path.getsize(DEFAULT_DATA_FILE) > 0:
                with open(DEFAULT_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                print("[INDEX] ERROR: Archivo de datos por defecto vacío o no encontrado.")
                data = []  # Initialize with an empty list if default file is invalid
    except json.JSONDecodeError:
        print("[INDEX] ERROR: JSON inválido. Usando datos vacíos.")
        data = []  # Initialize with an empty list if JSON is invalid

    ciudades = sorted(set(item['ciudad'] for item in data if 'ciudad' in item))
    tipos = sorted(set(item['tipo'] for item in data if 'tipo' in item))

    print("[INDEX] Ciudades detectadas:", ciudades)
    print("[INDEX] Tipos detectados:", tipos)

    ciudad_filtro = request.args.get('ciudad')
    tipo_filtro = request.args.get('tipo')
    rating_min = request.args.get('rating', type=float)

    print(f"[INDEX] Filtros aplicados -> ciudad: {ciudad_filtro}, tipo: {tipo_filtro}, rating_min: {rating_min}")

    datos_filtrados = data
    if ciudad_filtro:
        datos_filtrados = [d for d in datos_filtrados if d.get('ciudad') == ciudad_filtro]
    if tipo_filtro:
        datos_filtrados = [d for d in datos_filtrados if d.get('tipo') == tipo_filtro]
    if rating_min is not None:
        datos_filtrados = [d for d in datos_filtrados if d.get('rating') and d['rating'] >= rating_min]

    print(f"[INDEX] Resultados después de filtrar: {len(datos_filtrados)}")

    return render_template('index.html', datos=datos_filtrados, ciudades=ciudades, tipos=tipos)

@app.route('/buscar', methods=['GET', 'POST'])
def buscar():
    if request.method == 'GET':
        print("[BUSCAR] Acceso por GET redirigiendo a index")
        return redirect(url_for('index'))

    termino = request.form.get('termino')
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    ubicacion = request.form.get('ubicacion')
    location = f"{lat},{lng}" if lat and lng else ubicacion

    print(f"[BUSCAR] término recibido: {termino}")
    print(f"[BUSCAR] ubicación recibida: {ubicacion}")
    print(f"[BUSCAR] coordenadas recibidas: lat={lat}, lng={lng}")
    print(f"[BUSCAR] location usado: {location}")

    if not termino or not location:
        print("[BUSCAR] ❌ Error: Formulario incompleto")
        return "❌ Error: Missing form data", 400

    api_key = os.getenv("GOOGLE_MAPS_API_BACKEND")
    if not api_key:
        print("[BUSCAR] ❌ Error: API Key no configurada en las variables de entorno")
        return "❌ Error: API Key not configured", 500

    gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_BACKEND"))
    resultados = []

    try:
        respuesta = gmaps.places(query=termino, location=location, radius=50000)
        resultados.extend(respuesta.get('results', []))
        print(f"[BUSCAR] Resultados iniciales: {len(respuesta.get('results', []))}")

        while 'next_page_token' in respuesta:
            time.sleep(2)
            respuesta = gmaps.places(query=termino, page_token=respuesta['next_page_token'])
            resultados.extend(respuesta.get('results', []))
            print(f"[BUSCAR] Página adicional con {len(respuesta.get('results', []))} resultados")

        datos_finales = []
        for lugar in resultados:
            try:
                detalles = gmaps.place(place_id=lugar['place_id'])
                descripcion = detalles['result'].get('editorial_summary', {}).get('overview', '–')  # Default to '–' if missing
                sitio_web = detalles['result'].get('website', '–')  # Default to '–' if missing
            except Exception as e:
                print(f"[BUSCAR] Error fetching details for place_id {lugar['place_id']}: {e}")
                descripcion = '–'
                sitio_web = '–'

            datos_finales.append({
                'nombre': lugar.get('name'),
                'direccion': lugar.get('formatted_address'),
                'rating': lugar.get('rating'),
                'num_reviews': lugar.get('user_ratings_total'),
                'sitio_web': sitio_web,  # Use fetched website
                'telefono': lugar.get('formatted_phone_number'),
                'estatus': lugar.get('business_status'),
                'tipo': termino,
                'ciudad': ubicacion,
                'descripcion': descripcion  # Use fetched description
            })

        print(f"[BUSCAR] Total guardados: {len(datos_finales)}")

        with open(SEARCH_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(datos_finales, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"[BUSCAR] ❌ EXCEPCIÓN: {e}")
        return f"❌ Error: {e}"

    return render_template('index.html', datos=datos_finales, ciudades=[], tipos=[])

@app.route('/borrar', methods=['POST'])
def borrar_historial():
    if os.path.exists(SEARCH_HISTORY_FILE):
        os.remove(SEARCH_HISTORY_FILE)
        print("[BORRAR] Historial eliminado.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
