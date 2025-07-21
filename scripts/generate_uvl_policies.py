import os
import yaml

def sanitize(name):
    return name.replace("-", "_").replace(".", "_").replace("/", "_").replace(" ", "_")

def clean_description(description: str) -> str:
    return description.replace("\n", " ").replace("'", "_")

def extract_policy_info(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        policy = yaml.safe_load(f)

    metadata = policy.get("metadata", {})
    annotations = metadata.get("annotations", {})
    name = metadata.get("name", "")
    title = annotations.get("policies.kyverno.io/title", name)
    category = annotations.get("policies.kyverno.io/category", "Uncategorized")

    return {
        "name": name,
        "title": title,
        "category": category,
        "description": annotations.get("policies.kyverno.io/description", ""),
    }

def extract_constraints_from_policy(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        policy = yaml.safe_load(f)

    constraints = []

    metadata = policy.get("metadata", {})
    annotations = metadata.get("annotations", {})
    name = sanitize(metadata.get("name", ""))
    #category = sanitize(annotations.get("policies.kyverno.io/category", "Uncategorized"))
    #title = sanitize(annotations.get("policies.kyverno.io/title", name))

    ## policy_feature = f"{category}_{title}"

    rules = policy.get("spec", {}).get("rules", [])
    for rule in rules:
        kinds = rule.get("match", {}).get("any", [{}])[0].get("resources", {}).get("kinds", [])
        kind_prefixes = [f"io_k8s_api_core_v1_{sanitize(kind)}_" for kind in kinds] ## Defined by the examples v1_Pod..
        pattern = rule.get("validate", {}).get("pattern", {})
        if "spec" in pattern:
            conditions = extract_conditions_from_spec(pattern["spec"], prefix="spec")
            for path, expected in conditions:
                for kind_prefix in kind_prefixes:
                    full_feature = sanitize(kind_prefix + path)
                    constraint = f"{name} → {full_feature} == {expected}"
                    constraints.append(constraint)

    return constraints

def extract_conditions_from_spec(obj, prefix="spec"):
    conditions = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = k.lstrip("=(").rstrip(")")
            new_prefix = f"{prefix}_{key}"
            if isinstance(v, dict):
                conditions.extend(extract_conditions_from_spec(v, new_prefix))
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                conditions.extend(extract_conditions_from_spec(v[0], new_prefix))
            else:
                # Convert "false" to false (boolean) for UVL
                if isinstance(v, str) and v.lower() == "false":
                    v = "false"
                elif isinstance(v, str) and v.lower() == "true":
                    v = "true"
                conditions.append((new_prefix, v))
    return conditions



def generate_uvl_from_policies(directory, output_path):
    category_map = {}

    for filename in os.listdir(directory):
        if not filename.endswith(".yaml") and not filename.endswith(".yml"):
            continue

        filepath = os.path.join(directory, filename)
        policy = extract_policy_info(filepath)

        cat = sanitize(policy["category"])
        title = sanitize(policy["title"])
        entry = {
            "name": title,
            "description": policy["description"]
        }

        category_map.setdefault(cat, []).append(entry)

    lines = ["namespace PoliciesKyverno", "features", "\tPolicies {abstract}", "\t\toptional"]

    for cat, entries in category_map.items():
        lines.append(f"\t\t\t{cat}")
        lines.append("\t\t\t\toptional")
        for e in entries:
            name = e["name"]
            doc = clean_description(e["description"])
            if doc:
                lines.append(f"\t\t\t\t\t{name} {{doc '{doc}'}}")
            else:
                lines.append(f"\t\t\t\t\t{name}")

    lines.append("constraints")
    for filename in os.listdir(directory):
        if not filename.endswith(".yaml") and not filename.endswith(".yml"):
            continue
        filepath = os.path.join(directory, filename)
        constraints = extract_constraints_from_policy(filepath)
        for c in constraints:
            lines.append(f"\t{c}")


    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ UVL generado: {output_path}")

# Ejemplo de uso
if __name__ == "__main__":
    generate_uvl_from_policies(
        directory="../resources/kyverno_policies_yamls",  # 📂 Carpeta con YAMLs de políticas
        output_path="../variability_model/policies_template/policy_structure.uvl"
    )