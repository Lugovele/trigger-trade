"""Small JSON Schema validator for the approved TriggerTrade wire schema subset."""

from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any, Mapping

from ._approved_wire_schema import WIRE_SCHEMA


class SchemaValidationError(ValueError):
    """Raised when a payload does not match the approved wire schema."""


def validate_wire_definition(definition: str, payload: Mapping[str, Any]) -> None:
    try:
        schema = WIRE_SCHEMA["$defs"][definition]
    except KeyError as exc:
        raise SchemaValidationError(f"unknown approved wire definition: {definition}") from exc
    _validate(schema, payload, path=definition)


def _validate(schema: Mapping[str, Any], value: Any, *, path: str) -> None:
    if "$ref" in schema:
        _validate(_resolve_ref(schema["$ref"]), value, path=path)
        if len(schema) == 1:
            return
        schema = {key: item for key, item in schema.items() if key != "$ref"}
    if "allOf" in schema:
        for index, child in enumerate(schema["allOf"]):
            _validate(child, value, path=f"{path}.allOf[{index}]")
    if "anyOf" in schema:
        errors: list[str] = []
        for child in schema["anyOf"]:
            try:
                _validate(child, value, path=path)
            except SchemaValidationError as exc:
                errors.append(str(exc))
            else:
                return
        raise SchemaValidationError(f"{path} does not match any allowed schema: {'; '.join(errors)}")
    if "oneOf" in schema:
        matches = 0
        errors: list[str] = []
        for child in schema["oneOf"]:
            try:
                _validate(child, value, path=path)
            except SchemaValidationError as exc:
                errors.append(str(exc))
            else:
                matches += 1
        if matches != 1:
            raise SchemaValidationError(f"{path} must match exactly one schema, matched {matches}: {'; '.join(errors)}")
    if "not" in schema:
        try:
            _validate(schema["not"], value, path=f"{path}.not")
        except SchemaValidationError:
            pass
        else:
            raise SchemaValidationError(f"{path} matches a forbidden schema")
    _validate_condition(schema, value, path=path)
    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(f"{path} must be {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaValidationError(f"{path} must be one of {tuple(schema['enum'])!r}, got {value!r}")
    if "type" in schema:
        _validate_type(schema["type"], value, path=path)

    schema_type = schema.get("type")
    if schema_type == "object" or (
        isinstance(value, Mapping)
        and {"properties", "required", "additionalProperties", "minProperties", "maxProperties"} & set(schema)
    ):
        _validate_object(schema, value, path=path)
    elif schema_type == "array":
        _validate_array(schema, value, path=path)
    elif schema_type == "string":
        _validate_string(schema, value, path=path)
    elif schema_type == "integer":
        _validate_integer(schema, value, path=path)


def _validate_condition(schema: Mapping[str, Any], value: Any, *, path: str) -> None:
    if_schema = schema.get("if")
    if if_schema is None:
        return
    try:
        _validate(if_schema, value, path=f"{path}.if")
    except SchemaValidationError:
        else_schema = schema.get("else")
        if else_schema is not None:
            _validate(else_schema, value, path=f"{path}.else")
        return
    then_schema = schema.get("then")
    if then_schema is not None:
        _validate(then_schema, value, path=f"{path}.then")


def _validate_object(schema: Mapping[str, Any], value: Any, *, path: str) -> None:
    if not isinstance(value, Mapping):
        raise SchemaValidationError(f"{path} must be an object")
    properties = schema.get("properties", {})
    required = set(schema.get("required", ()))
    missing = required - set(value)
    if missing:
        raise SchemaValidationError(f"{path} missing required fields: {', '.join(sorted(missing))}")
    if schema.get("additionalProperties") is False:
        unknown = set(value) - set(properties)
        if unknown:
            raise SchemaValidationError(f"{path} unknown fields: {', '.join(sorted(unknown))}")
    if "minProperties" in schema and len(value) < schema["minProperties"]:
        raise SchemaValidationError(f"{path} must have at least {schema['minProperties']} properties")
    if "maxProperties" in schema and len(value) > schema["maxProperties"]:
        raise SchemaValidationError(f"{path} must have at most {schema['maxProperties']} properties")
    for field, item in value.items():
        if not isinstance(field, str):
            raise SchemaValidationError(f"{path} object keys must be strings")
        if field in properties:
            _validate(properties[field], item, path=f"{path}.{field}")


def _validate_array(schema: Mapping[str, Any], value: Any, *, path: str) -> None:
    if not isinstance(value, list):
        raise SchemaValidationError(f"{path} must be an array")
    if "minItems" in schema and len(value) < schema["minItems"]:
        raise SchemaValidationError(f"{path} must have at least {schema['minItems']} items")
    if "maxItems" in schema and len(value) > schema["maxItems"]:
        raise SchemaValidationError(f"{path} must have at most {schema['maxItems']} items")
    if schema.get("uniqueItems") is True:
        seen: set[str] = set()
        for item in value:
            marker = json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            if marker in seen:
                raise SchemaValidationError(f"{path} must contain unique items")
            seen.add(marker)
    item_schema = schema.get("items")
    if item_schema is not None:
        for index, item in enumerate(value):
            _validate(item_schema, item, path=f"{path}[{index}]")


def _validate_string(schema: Mapping[str, Any], value: Any, *, path: str) -> None:
    if not isinstance(value, str):
        raise SchemaValidationError(f"{path} must be a string")
    if "minLength" in schema and len(value) < schema["minLength"]:
        raise SchemaValidationError(f"{path} must not be empty")
    if "maxLength" in schema and len(value) > schema["maxLength"]:
        raise SchemaValidationError(f"{path} must have at most {schema['maxLength']} characters")
    if "pattern" in schema and re.search(schema["pattern"], value) is None:
        raise SchemaValidationError(f"{path} does not match required pattern")
    if schema.get("format") == "date-time" and not _is_date_time(value):
        raise SchemaValidationError(f"{path} must be a valid date-time")


def _validate_integer(schema: Mapping[str, Any], value: Any, *, path: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SchemaValidationError(f"{path} must be an integer")
    if "minimum" in schema and value < schema["minimum"]:
        raise SchemaValidationError(f"{path} must be >= {schema['minimum']}")
    if "maximum" in schema and value > schema["maximum"]:
        raise SchemaValidationError(f"{path} must be <= {schema['maximum']}")
    if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
        raise SchemaValidationError(f"{path} must be > {schema['exclusiveMinimum']}")
    if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
        raise SchemaValidationError(f"{path} must be < {schema['exclusiveMaximum']}")


def _validate_type(expected_type: str, value: Any, *, path: str) -> None:
    if expected_type == "null":
        if value is not None:
            raise SchemaValidationError(f"{path} must be null")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            raise SchemaValidationError(f"{path} must be a boolean")
    elif expected_type == "string":
        if not isinstance(value, str):
            raise SchemaValidationError(f"{path} must be a string")
    elif expected_type == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise SchemaValidationError(f"{path} must be an integer")
    elif expected_type == "object":
        if not isinstance(value, Mapping):
            raise SchemaValidationError(f"{path} must be an object")
    elif expected_type == "array":
        if not isinstance(value, list):
            raise SchemaValidationError(f"{path} must be an array")
    else:
        raise SchemaValidationError(f"{path} uses unsupported schema type: {expected_type}")


def _is_date_time(value: str) -> bool:
    if not (value.endswith("Z") or re.search(r"[+-]\d{2}:\d{2}$", value)):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _resolve_ref(ref: str) -> Mapping[str, Any]:
    prefix = "#/$defs/"
    if not ref.startswith(prefix):
        raise SchemaValidationError(f"unsupported schema reference: {ref}")
    try:
        return WIRE_SCHEMA["$defs"][ref[len(prefix) :]]
    except KeyError as exc:
        raise SchemaValidationError(f"unknown schema reference: {ref}") from exc
