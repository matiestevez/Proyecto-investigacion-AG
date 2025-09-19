import random
from geopy.geocoders import Nominatim
from geopy.distance import geodesic     
import os
import time
import folium
import matplotlib.pyplot as plt

def clear():
    os.system("cls")

print("\n--- Configuración de Recursos ---")
RECURSOS_DISPONIBLES = {
    'alimentos': int(input("📦 Ingrese la cantidad de alimentos disponibles: ")),
    'agua': int(input("💧 Ingrese la cantidad de agua disponible: "))
}
clear()

def asignar_necesidad(tipo):
    print("\n---Ingrese cantidad de ", tipo, " necesaria---")
    cantidad=int(input())
    return cantidad

def obtener_coordenadas(ubicacion_nombre):
    geolocator = Nominatim(user_agent="mi_aplicacion_ag_v1")
    try:
        location = geolocator.geocode(ubicacion_nombre)
        if location:
            return (location.latitude, location.longitude)
        else:
            return None
    except Exception as e:
        print(f"Error al obtener coordenadas de {ubicacion_nombre}: {e}")
        return None

def crear_areas_reales(nombres_ubicaciones):
    areas = []
    for i, nombre in enumerate(nombres_ubicaciones):
        ubicacion_coords = obtener_coordenadas(nombre)
        print(f"📍 Ubicacion: {nombre} ")
        print(f"🧭 Coordenadas: {ubicacion_coords}")
        if ubicacion_coords:
            areas.append({
                'id': i + 1,
                'necesidad_alimentos': asignar_necesidad('alimentos'),
                'necesidad_agua': asignar_necesidad('agua'),
                'ubicacion': ubicacion_coords
            })
        else:
            print(f"No se pudieron obtener coordenadas para {nombre}. Se omite.")
    return areas

CENTRO_LOGISTICO_NOMBRE = "Zeballos 1341, Rosario, Santa Fe, Argentina" # Ubicación del centro de distribución.
CENTRO_LOGISTICO = obtener_coordenadas(CENTRO_LOGISTICO_NOMBRE)
if not CENTRO_LOGISTICO:
    print(f"No se pudieron obtener coordenadas para el centro logístico. Saliendo del programa.")
MAX_POBLACION = 50       # Tamaño de la población de soluciones.
NUM_GENERACIONES = 100   # Número de generaciones a simular.
PROB_MUTACION = 0.01     # Probabilidad de mutación.
PROB_Cruce = 0.75        #Probabiliad de crossover.

def crear_cromosoma_aleatorio(areas):
    clear()
    cromosoma = []
    recursos_restantes = RECURSOS_DISPONIBLES.copy()

    for area in areas:
        asignacion_alimentos = random.randint(0, recursos_restantes['alimentos'])
        recursos_restantes['alimentos'] -= asignacion_alimentos
        
        asignacion_agua = random.randint(0, recursos_restantes['agua'])
        recursos_restantes['agua'] -= asignacion_agua

        cromosoma.append({
            'area_id': area['id'],
            'alimentos': asignacion_alimentos,
            'agua': asignacion_agua
        })
    return cromosoma

def calcular_distancia(ubicacion1_coords, ubicacion2_coords):
    global recorrido
    distancia= geodesic(ubicacion1_coords, ubicacion2_coords).km
    recorrido=distancia
    return distancia
    
def funcion_aptitud(cromosoma,areas):
    global distancia_total
    aptitud = 0
    distancia_total = 0
    necesidad_satisfecha_total = 0
    recursos_distribuidos = {'alimentos': 0, 'agua': 0}
    
    for asignacion in cromosoma:
        area = next(a for a in areas if a['id'] == asignacion['area_id'])
        
        distancia_total += calcular_distancia(CENTRO_LOGISTICO, area['ubicacion'])
        
        satisfaccion_alimentos = min(1, asignacion['alimentos'] / area['necesidad_alimentos'])
        satisfaccion_agua = min(1, asignacion['agua'] / area['necesidad_agua'])
        
        necesidad_satisfecha_total += (satisfaccion_alimentos + satisfaccion_agua)
        
        recursos_distribuidos['alimentos'] += asignacion['alimentos']
        recursos_distribuidos['agua'] += asignacion['agua']
    
    desperdicio = max(0, recursos_distribuidos['alimentos'] - RECURSOS_DISPONIBLES['alimentos']) + \
                  max(0, recursos_distribuidos['agua'] - RECURSOS_DISPONIBLES['agua'])
   
    w1 = 100  # Peso para la satisfacción de necesidades
    w2 = 1    # Peso para la distancia 
    w3 = 500  # Peso para el desperdicio 

    aptitud = (w1 * necesidad_satisfecha_total) - (w2 * distancia_total) - (w3 * desperdicio)
    
    return aptitud

def seleccion(poblacion_aptitudes):
    torneo = random.sample(poblacion_aptitudes, 5) # Elegimos 5 individuos al azar
    torneo.sort(key=lambda x: x[1], reverse=True)  # Los ordenamos por aptitud
    padre1 = torneo[0][0]
    padre2 = torneo[1][0]
    return padre1, padre2

def cruce(padre1, padre2):
    if random.random() < PROB_Cruce:
        punto_corte = random.randint(1, len(padre1) - 1)
        hijo1 = padre1[:punto_corte] + padre2[punto_corte:]
        hijo2 = padre2[:punto_corte] + padre1[punto_corte:]
        return hijo1, hijo2
    else: return padre1, padre2

def mutacion(cromosoma):
    if  random.random()< PROB_MUTACION:
        area_a_mutar = random.choice(cromosoma)
        recurso_a_mutar = random.choice(['alimentos', 'agua'])
        # Cambiamos el valor de forma aleatoria 
        cambio = random.uniform(-0.2, 0.2)
        area_a_mutar[recurso_a_mutar] *= (1 + cambio)
        area_a_mutar[recurso_a_mutar] = max(0, int(area_a_mutar[recurso_a_mutar]))
    return cromosoma

def ejecutar_ag():

    nombres_ubicaciones = []
    while True:
        print("\n--- 📍 INGRESO DE UBICACIONES (presione enter para finalizar) ---")
        ubicacion_input = input(f"Ubicación #{len(nombres_ubicaciones) + 1}: ")
        if not ubicacion_input.strip(): # Verifica si la línea está vacía
            break
        nombres_ubicaciones.append(ubicacion_input.strip())
    if nombres_ubicaciones:
        print("\n✅ Ubicaciones ingresadas:")
        for nombre in nombres_ubicaciones:
            print(f"   - {nombre}")
    if not nombres_ubicaciones:
        print("No se ingresaron ubicaciones. Saliendo del programa.")
        return
    time.sleep(2)
    clear()
    areas_afectadas = crear_areas_reales(nombres_ubicaciones)

    if not areas_afectadas:
        print("No se pudieron obtener coordenadas para las ubicaciones ingresadas. Saliendo del programa.")
        return
    aptitudes_por_generacion = []
    ban = False
    while ban == False:
        poblacion = [crear_cromosoma_aleatorio(areas_afectadas) for _ in range(MAX_POBLACION)]
        
        mejor_solucion = None
        mejor_aptitud = -float('inf')
        
        for generacion in range(NUM_GENERACIONES):

            poblacion_aptitudes = [(cromosoma, funcion_aptitud(cromosoma, areas_afectadas )) for cromosoma in poblacion]
            poblacion_aptitudes.sort(key=lambda x: x[1], reverse=True)
            
           
            if poblacion_aptitudes[0][1] > mejor_aptitud:
                mejor_aptitud = poblacion_aptitudes[0][1]
                mejor_solucion = poblacion_aptitudes[0][0]
                print(f"Generación {generacion}: Nueva mejor aptitud = {mejor_aptitud:.2f}")
            
            mejor_aptitud_generacion = poblacion_aptitudes[0][1]
            aptitudes_por_generacion.append(mejor_aptitud_generacion)
            
            nueva_poblacion = []
            # Elitismo
            nueva_poblacion.append(poblacion_aptitudes[0][0])
            
            while len(nueva_poblacion) < MAX_POBLACION:
                #Selección de padres
                padre1, padre2 = seleccion(poblacion_aptitudes)
                
                #Cruce
                hijo1, hijo2 = cruce(padre1, padre2)
                
                #Mutación
                hijo1 = mutacion(hijo1)
                hijo2 = mutacion(hijo2)
                
                nueva_poblacion.append(hijo1)
                if len(nueva_poblacion) < MAX_POBLACION:
                    nueva_poblacion.append(hijo2)
            
            poblacion = nueva_poblacion

        print("\n--- Asignación de Recursos por Área ---")
        print(f"🏆 Mejor aptitud encontrada: {mejor_aptitud:.2f}")
        print(f"🚚 Distancia recorrida: {distancia_total:.2f} km")
        print("{:<10} {:<15} {:<15} {:<15} {:<15}".format(
            "Área ID", "Alimentos Asig.", "Alimentacion Nec.", "Agua Asig.", "Agua Nec."
        ))
        print("-" * 75)
        agua = 0
        alimento = 0
        for asignacion in mejor_solucion:
            area_info = next(a for a in areas_afectadas if a['id'] == asignacion['area_id'])
            
            emoji_alimentos = "📦" if asignacion['alimentos'] >= area_info['necesidad_alimentos'] else "⚠️"
            emoji_agua = "💧" if asignacion['agua'] >= area_info['necesidad_agua'] else "⚠️"

            print("{:<10} {:<15} {:<15} {:<15} {:<15}".format(
                f"Área {asignacion['area_id']}",
                f"{asignacion['alimentos']} {emoji_alimentos}",
                area_info['necesidad_alimentos'],
                f"{asignacion['agua']} {emoji_agua}",
                area_info['necesidad_agua']
            ))
            agua += asignacion['agua']
            alimento += asignacion['alimentos']
        print(f"\nTotal entregado: {alimento} alimentos, {agua} agua")
        if alimento<=RECURSOS_DISPONIBLES['alimentos'] and agua<=RECURSOS_DISPONIBLES['agua']:
            ban=True
        else:
            print("\n⚠️ La solución excede los recursos disponibles. Reintentando...\n")
            time.sleep(5)
    
    print("\n--- 📈 Gráfico de evolución de aptitud generado ---")
    
    plt.figure(figsize=(10, 6))
    plt.plot(aptitudes_por_generacion, color='blue', linewidth=2)
    plt.title('Evolución de la Aptitud a lo Largo de las Generaciones')
    plt.xlabel('Generación')
    plt.ylabel('Aptitud')
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
    
    print("\n--- 🗺️ Generando mapa de la mejor solución... ---")
    #Crea el mapa base
    m = folium.Map(location=[CENTRO_LOGISTICO[0], CENTRO_LOGISTICO[1]], zoom_start=12)

    #Agrega el centro logístico
    folium.Marker(
        location=[CENTRO_LOGISTICO[0], CENTRO_LOGISTICO[1]],
        popup="<b>Centro Logístico</b>",
        icon=folium.Icon(color='blue', icon='truck', prefix='fa')
    ).add_to(m)

    
    for asignacion in mejor_solucion:
        area_info = next(a for a in areas_afectadas if a['id'] == asignacion['area_id'])
        area_coords = area_info['ubicacion']

        # Texto 
        popup_text = f"<b>Área ID: {asignacion['area_id']}</b><br>Alimentos: {asignacion['alimentos']}<br>Agua: {asignacion['agua']}"

        # Agregar el marcador del área
        folium.Marker(
            location=[area_coords[0], area_coords[1]],
            popup=popup_text,
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)

    # Dibuja ruta 
    ruta = [CENTRO_LOGISTICO]
    for asignacion in mejor_solucion:
        area_info = next(a for a in areas_afectadas if a['id'] == asignacion['area_id'])
        ruta.append(area_info['ubicacion'])
    folium.PolyLine(
        locations=ruta,
        color='green',
        weight=2,
        opacity=0.8
    ).add_to(m)

    
    ruta_del_script = os.path.dirname(os.path.abspath(__file__))
    map_filename = os.path.join(ruta_del_script, "distribucion_recursos_mapa.html")
    
    m.save(map_filename)
    print(f"✅ Mapa generado exitosamente: {map_filename}")
    print("Puedes abrir este archivo en tu navegador web.")

if __name__ == "__main__":
    ejecutar_ag()