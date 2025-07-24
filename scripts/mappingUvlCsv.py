"""
Script adaptado para procesar un modelo UVL generado a partir de un CRD (como el de Kyverno),
y generar:
- Un CSV con los nombres jerárquicos de las features.
- Un CSV con combinaciones únicas de (version, kind) detectadas.

Versión simplificada: se omite el group (como 'io_k8s_' o 'kyverno_io_').
"""

import re
import csv

uvl_model_path = '../variability_model/kyverno_clusterpolicy_test2.uvl'

# Almacenes de datos
csv_data = []
kinds_versions_set = set()
elementos_sin_version_o_kind = []

# Leer el archivo UVL línea por línea
with open(uvl_model_path, encoding="utf-8") as uvl_model:
    for line in uvl_model:
        line = line.strip()

        # Determinar si es un feature de interés
        if not line.startswith(("String", "Boolean", "Integer")) and "_" not in line:
            if line.startswith("constraints"):
                break  # Terminar cuando se alcanzan las constraints
            continue

        # Quitar contenido adicional como cardinalidad o documentación
        line_feature = line.split("cardinality")[0].split("{")[0].strip()

        # Extraer el nombre del feature
        parts = line_feature.split()
        feature = parts[1] if len(parts) >= 2 else parts[0]

        # Extraer version y kind usando patrón vX_Kind
        match = re.search(r'_v[0-9][a-z0-9]*_([A-Z][A-Za-z0-9]*)', feature)
        if match:
            kind = match.group(1)
            version_match = re.search(r'_v[0-9][a-z0-9]*_', feature)
            if version_match:
                version = version_match.group(0).strip('_')
                kinds_versions_set.add((version, kind))
            else:
                print(f"⚠ No se pudo extraer version de: {feature}")
                elementos_sin_version_o_kind.append(feature)
        else:
            print(f"⚠ No se pudo extraer kind de: {feature}")
            elementos_sin_version_o_kind.append(feature)

        # Generar columnas para CSV de features
        split_feature = feature.split("_")
        midle_row = match.group(1) if match else ""
        turned_row = split_feature[-1] if split_feature else ""
        value_row = turned_row if "Specific value" in line else ("-" if "cardinality" in line else "")

        # Añadir al CSV
        csv_data.append([feature, midle_row, turned_row, value_row])

# Rutas de salida
output_file_csv = '../resources/mapping_csv/kyverno_mapping_properties_features.csv'
output_file_kinds_versions = '../resources/mapping_csv/kinds_versions_detected.csv'

# Guardar el CSV principal
with open(output_file_csv, mode="w", newline="") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["Feature", "Midle", "Turned", "Value"])
    writer.writerows(csv_data)

# Guardar CSV de versiones y kinds
with open(output_file_kinds_versions, mode="w", newline="") as apis_file:
    writer = csv.writer(apis_file)
    writer.writerow(["Version", "Kind"])
    for version, kind in sorted(kinds_versions_set):
        writer.writerow([version, kind])

print(f"✅ Archivo CSV generado: {output_file_csv}")
print(f"✅ Archivo CSV kinds_versions generado: {output_file_kinds_versions}")
print(f"🧩 Features sin version o kind extraídos: {elementos_sin_version_o_kind}")
