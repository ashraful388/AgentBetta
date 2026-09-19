import pytest

from agentbetta.tools.schema import ToolArgumentError, validate_arguments


def test_valid_arguments_pass_through():
    schema = {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
    assert validate_arguments(schema, {"path": "a.txt"}) == {"path": "a.txt"}


def test_missing_required_raises():
    schema = {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
    with pytest.raises(ToolArgumentError):
        validate_arguments(schema, {})


def test_wrong_type_raises():
    schema = {"type": "object", "properties": {"path": {"type": "string"}}}
    with pytest.raises(ToolArgumentError):
        validate_arguments(schema, {"path": 5})


def test_bool_is_not_integer():
    schema = {"type": "object", "properties": {"max_chars": {"type": "integer"}}}
    with pytest.raises(ToolArgumentError):
        validate_arguments(schema, {"max_chars": True})


def test_additional_properties_false_rejects_unknown():
    schema = {"type": "object", "properties": {"path": {"type": "string"}}, "additionalProperties": False}
    with pytest.raises(ToolArgumentError):
        validate_arguments(schema, {"path": "a", "evil": 1})


def test_non_object_arguments_raise():
    with pytest.raises(ToolArgumentError):
        validate_arguments({"type": "object"}, ["not", "a", "dict"])
