from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from math import radians, cos, sin, sqrt, atan2
import heapq

app = FastAPI()

# Configuración de las plantillas
templates = Jinja2Templates(directory="templates")

# Configuración para archivos estáticos (si es necesario)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Diccionario de coordenadas
coordenadas = {
    'EDO.MEX': (19.2938258568844, -99.65366252023884),
    'QRO': (20.593537489366717, -100.39004057702225),
    'CDMX': (19.432854452264177, -99.13330004822943),
    'SLP': (22.151725492903953, -100.97657666103268),
    'MTY': (25.673156272083876, -100.2974200019319),
    'PUE': (19.063532268065185, -98.30729139446866),
    'GDL': (20.67714565083998, -103.34696388920293),
    'MICH': (19.702614895389996, -101.19228631929688),
    'SON': (29.075273188617818, -110.95962477655333)
}

# Función de distancia entre dos coordenadas
def calcular_distancia(coord1, coord2):
    R = 6371  # Radio de la Tierra en km
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Grafo de ciudades conectadas y distancias
grafo = {
    'EDO.MEX': {'QRO': calcular_distancia(coordenadas['EDO.MEX'], coordenadas['QRO']),
                'CDMX': calcular_distancia(coordenadas['EDO.MEX'], coordenadas['CDMX'])},
    'QRO': {'EDO.MEX': calcular_distancia(coordenadas['QRO'], coordenadas['EDO.MEX']),
            'CDMX': calcular_distancia(coordenadas['QRO'], coordenadas['CDMX']),
            'SLP': calcular_distancia(coordenadas['QRO'], coordenadas['SLP'])},
    'CDMX': {'EDO.MEX': calcular_distancia(coordenadas['CDMX'], coordenadas['EDO.MEX']),
             'QRO': calcular_distancia(coordenadas['CDMX'], coordenadas['QRO']),
             'SLP': calcular_distancia(coordenadas['CDMX'], coordenadas['SLP']),
             'PUE': calcular_distancia(coordenadas['CDMX'], coordenadas['PUE'])},
    'SLP': {'QRO': calcular_distancia(coordenadas['SLP'], coordenadas['QRO']),
            'CDMX': calcular_distancia(coordenadas['SLP'], coordenadas['CDMX']),
            'MTY': calcular_distancia(coordenadas['SLP'], coordenadas['MTY'])},
    'MTY': {'SLP': calcular_distancia(coordenadas['MTY'], coordenadas['SLP']),
            'GDL': calcular_distancia(coordenadas['MTY'], coordenadas['GDL'])},
    'PUE': {'CDMX': calcular_distancia(coordenadas['PUE'], coordenadas['CDMX']),
            'GDL': calcular_distancia(coordenadas['PUE'], coordenadas['GDL'])},
    'GDL': {'MTY': calcular_distancia(coordenadas['GDL'], coordenadas['MTY']),
            'PUE': calcular_distancia(coordenadas['GDL'], coordenadas['PUE'])},
    'MICH': {'SON': calcular_distancia(coordenadas['MICH'], coordenadas['SON'])},
    'SON': {'MICH': calcular_distancia(coordenadas['SON'], coordenadas['MICH'])}
}

# Algoritmo de Dijkstra para encontrar el camino más corto
def dijkstra(grafo, inicio, destino):
    distancias = {ciudad: float('inf') for ciudad in grafo}
    distancias[inicio] = 0
    camino = {ciudad: [] for ciudad in grafo}
    pq = [(0, inicio)]  # Prioridad de la cola, distancia inicial es 0

    while pq:
        distancia, ciudad_actual = heapq.heappop(pq)

        if distancia > distancias[ciudad_actual]:
            continue

        for vecino, peso in grafo[ciudad_actual].items():
            nueva_distancia = distancias[ciudad_actual] + peso
            if nueva_distancia < distancias[vecino]:
                distancias[vecino] = nueva_distancia
                camino[vecino] = camino[ciudad_actual] + [ciudad_actual]
                heapq.heappush(pq, (nueva_distancia, vecino))

    ruta_final = camino[destino] + [destino]
    return ruta_final, distancias[destino]

@app.get("/", response_class=HTMLResponse)
def mostrar_formulario(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "ciudades": list(coordenadas.keys())
    })

@app.post("/caracteristicas", response_class=HTMLResponse)
def calcular_caracteristicas(request: Request, destino: str = Form(...), paquetes: int = Form(...)):
    almacen = 'CDMX'  # Ciudad de inicio
    peso_maximo = 40  # Peso máximo del automóvil

    # Verificar si el peso de los paquetes excede el límite
    if paquetes > peso_maximo:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "ciudades": list(coordenadas.keys()),
            "error": "El peso máximo del automóvil es de 40 unidades."
        })

    # Calcular la ruta más corta usando Dijkstra
    ruta, distancia_total = dijkstra(grafo, almacen, destino)

    # Calcular el tiempo y el combustible
    velocidad_promedio = 80  # km/h
    tiempo_total = distancia_total / velocidad_promedio
    combustible_total = distancia_total * 0.2  # Suponemos 0.2 litros/km

    # Mostrar el resultado
    return templates.TemplateResponse("index.html", {
        "request": request,
        "ciudades": list(coordenadas.keys()),
        "resultado": {
            "ruta": ruta,
            "distancia": round(distancia_total, 2),
            "tiempo": round(tiempo_total, 2),
            "combustible": round(combustible_total, 2),
            "destino": destino,
            "paquetes": paquetes
        }
    })
