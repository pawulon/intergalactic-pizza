"""
Generate All Artifacts from Pydantic Contract

This script is the SINGLE SOURCE OF TRUTH generator.
It takes Pydantic models and generates:
1. Avro schema (.avsc)
2. JSON Schema contract (.json)

Usage:
    python scripts/generate_schema.py
"""

import json
from pathlib import Path
from typing import get_args, get_origin


def python_to_avro_type(py_type):
    """
    Convert Python type to Avro type.

    Args:
        py_type: Python type annotation

    Returns:
        str or dict: Avro type representation
    """
    # Handle Optional types (Union[X, None])
    origin = get_origin(py_type)

    if origin is list or (
        hasattr(py_type, "__origin__") and py_type.__origin__ is list
    ):
        # List[X] -> array of X
        inner_type = get_args(py_type)[0]
        return {"type": "array", "items": python_to_avro_type(inner_type)}

    # Basic type mapping
    type_map = {
        str: "string",
        int: "int",
        float: "double",
        bool: "boolean",
        bytes: "bytes",
    }

    return type_map.get(py_type, "string")


def generate_avro_schema(contract_class, namespace="com.example"):
    """
    Generate Avro schema from Pydantic model.

    Args:
        contract_class: Pydantic BaseModel class
        namespace: Avro namespace

    Returns:
        dict: Avro schema
    """
    fields = []

    for field_name, field_info in contract_class.model_fields.items():
        avro_field = {
            "name": field_name,
            "doc": field_info.description or f"{field_name} field",
        }

        # Determine if field is required
        if field_info.is_required():
            # Required field
            avro_field["type"] = python_to_avro_type(field_info.annotation)
        else:
            # Optional field (nullable)
            base_type = python_to_avro_type(field_info.annotation)
            avro_field["type"] = ["null", base_type]
            avro_field["default"] = None

        fields.append(avro_field)

    schema = {
        "type": "record",
        "namespace": namespace,
        "name": contract_class.__name__.replace("Contract", ""),
        "doc": contract_class.__doc__.strip() if contract_class.__doc__ else "",
        "fields": fields,
    }

    return schema


def generate_json_schema(contract_class):
    """
    Generate JSON Schema from Pydantic model.

    Args:
        contract_class: Pydantic BaseModel class

    Returns:
        dict: JSON Schema
    """
    # Pydantic has built-in JSON schema generation
    return contract_class.model_json_schema()


def save_file(content, filepath):
    """Save content to file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(content, dict):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2)
    else:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    print(f"✅ Generated {filepath}")


def generate_all(contract_class, output_dir: Path, namespace="com.example"):
    """
    Generate all artifacts from a Pydantic contract.

    Args:
        contract_class: Pydantic BaseModel class
        output_dir: Output directory for schemas
        namespace: Avro namespace
    """
    schema_name = contract_class.__name__.replace("Contract", "").lower()
    base_path = output_dir / schema_name

    print(f"\n{'=' * 70}")
    print(f"Generating artifacts for {contract_class.__name__}")
    print(f"{'=' * 70}\n")

    # 1. Generate Avro schema
    avro_schema = generate_avro_schema(contract_class, namespace)
    avro_path = base_path / f"{schema_name}.avsc"
    save_file(avro_schema, avro_path)

    # 2. Generate JSON Schema
    json_schema = generate_json_schema(contract_class)
    json_path = base_path / f"{schema_name}-contract.json"
    save_file(json_schema, json_path)

    print(f"\n✨ All artifacts generated in {base_path}/\n")


# Main execution
if __name__ == "__main__":
    from intergalactic_pizza.contracts.pizza_order import PizzaOrder

    schemas_path = Path(__file__).parent.parent / "schemas"
    # Generate all artifacts for PizzaOrder
    generate_all(PizzaOrder, output_dir=schemas_path, namespace="com.intergalactic.pizza")
