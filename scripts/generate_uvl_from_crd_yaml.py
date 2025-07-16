import yaml
import os

def sanitize(name):
    return name.replace("-", "_").replace(".", "_").replace("/", "_")

def clean_description(description: str) -> str:
    return description.replace('\n', '') \
                      .replace('`', '') \
                      .replace('´', '') \
                      .replace("'", "_") \
                      .replace('{', '') \
                      .replace('}', '') \
                      .replace('"', '') \
                      .replace("\\", "_") \
                      .replace(".", "") \
                      .replace("//", "_")

def render_feature(entry, indent=2):
    i = "\t" * indent
    lines = []

    typename = entry.get("type", "Boolean").capitalize()
    name = sanitize(entry["name"])
    doc = entry.get("description", "")
    default = entry.get("default")
    enum = entry.get("enum", [])
    children = entry.get("children", [])

    attributes = []
    if doc:
      attributes.append(f'doc "{clean_description(doc.strip())}"')
    if default is not None:
      val = str(default).lower() if isinstance(default, bool) else f'"{default}"'
      attributes.append(f'default {val}')
    attr_str = f" {{{', '.join(attributes)}}}" if attributes else ""

    lines.append(f"{i}{typename} {name}{attr_str}")

    if enum:
        lines.append(i + "\talternative")
        for val in enum:
            enum_val = sanitize(f"{name}_{val}")
            lines.append(f"{i}\t\tString {enum_val}")
    
    if children:
        mand = [c for c in children if c.get("required")]
        opt = [c for c in children if not c.get("required")]
        if mand:
            lines.append(i + "\tmandatory")
            for c in mand:
                lines.extend(render_feature(c, indent + 2))
        if opt:
            lines.append(i + "\toptional")
            for c in opt:
                lines.extend(render_feature(c, indent + 2))
    
    return lines

def extract_features(schema, parent_name="", required_fields=None):
    required_fields = required_fields or []
    props = schema.get("properties", {})
    features = []

    for key, value in props.items():
        feature = {
            "name": f"{parent_name}_{key}" if parent_name else key,
            "type": value.get("type", "Boolean"),
            "description": value.get("description", ""),
            "default": value.get("default"),
            "enum": value.get("enum", []),
            "required": key in required_fields,
            "children": []
        }

        if value.get("type") == "object" and "properties" in value:
            feature["children"] = extract_features(value, feature["name"], value.get("required", []))
        elif value.get("type") == "array" and "items" in value:
            item = value["items"]
            if item.get("type") == "object" and "properties" in item:
                feature["children"] = extract_features(item, feature["name"] + "_item", item.get("required", []))
        features.append(feature)

    return features

def generate_uvl_from_crd(yaml_path, output_path):
    with open(yaml_path, 'r', encoding='utf-8') as f:
        crd = yaml.safe_load(f)

    kind = crd.get("spec", {}).get("names", {}).get("kind", "UnknownKind")
    version = crd.get("spec", {}).get("versions", [{}])[0].get("name", "v1")
    group = crd.get("spec", {}).get("group", "unknown.group")
    openapi = crd.get("spec", {}).get("versions", [{}])[0].get("schema", {}).get("openAPIV3Schema", {})
    root_name = sanitize(f"{group}_{version}_{kind}")

    features = extract_features(openapi, root_name, openapi.get("required", []))

    # UVL root
    lines = [f"namespace {sanitize(group)}", "features", "\tClusterPolicies {abstract}", "\t\toptional"]
    lines.append(f"\t\t{root_name} {{doc \"{openapi.get('description', '').strip()}\"}}")
    lines.append("\t\t\toptional")

    for feature in features:
        lines.extend(render_feature(feature, indent=4))

    # Write to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ UVL generado: {output_path}")


# 🔧 Uso
if __name__ == "__main__":
    generate_uvl_from_crd(
        yaml_path="../resources/kyverno_crds_definitions/kyverno.io_clusterpolicies.yaml",
        output_path="../variability_model/kyverno_clusterpolicy_test1.uvl"
    )