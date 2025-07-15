#### Script for generation and modelation the FMs of policies from kyverno...


### policies dict with the folders to "translate", we could access only to a objetive folders...
import yaml ## pyyaml
import re
from collections import deque


class SchemaProcessor:
    def __init__(self, definitions):
        """
        Inicializa la clase `SchemaProcessor` para procesar y extraer información de las definiciones de un esquema JSON.
        descripciones, patrones y restricciones.

        Este constructor configura la clase con las definiciones del esquema JSON y establece varias variables internas
        que se utilizan para manejar referencias, descripciones, patrones y restricciones.
        
        definitions (dict): Un diccionario que contiene las definiciones del esquema Yaml.

        
        """
        self.definitions = definitions # Un diccionario que organiza las descripciones en tres categorías:
        self.resolved_references = {}
        self.seen_references = set()
        self.seen_features = set() ## Añadir condicion a las refs vistas para no omitir refs ya vistas
        self.processed_features = set()
        self.constraints = []  # Lista para almacenar las dependencias como constraints
        #Prueba pila para las referencias ciclicas
        self.stact_refs = []
        # Se inicializa un diccionario para almacenar descripciones por grupo
        self.descriptions = {
            'values': [], 
            'restrictions': [],
            'dependencies': []

        }
        self.seen_descriptions = set()

        # Patrones para clasificar descripciones en categorías de valores, restricciones y dependencias
        self.patterns = {
            'values': re.compile(r'(valid|values are|supported|acceptable|can be)', re.IGNORECASE),
            'restrictions': re.compile(r'(allowed|conditions|should|must be|cannot be|if[\s\S]*?then|only|never|forbidden|disallowed)', re.IGNORECASE),
            'dependencies': re.compile(r'(depends on|requires|if[\s\S]*?only if|relies on|contingent upon|related to)', re.IGNORECASE)
        }
