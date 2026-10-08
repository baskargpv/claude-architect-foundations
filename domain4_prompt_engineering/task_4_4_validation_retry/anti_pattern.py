"""Task 4.4 — one runnable function per Exam Trap on the lesson.

Lesson: https://claudecertificationguide.com/learn/4-prompt-engineering/4-4-validation-retry-loops

Trap 1  assuming retries always work (retrying information that isn't in the source)
Trap 2  retrying without the specific validation error
Trap 3  relying on schema validation alone, with no semantic checks
Trap 4  treating Pydantic as redundant once tool_use enforces a schema
"""

from __future__ import annotations

from common.client import get_client
from domain4_prompt_engineering.task_4_4_validation_retry.good_example import SCHEMA, extract, mock_model, validate


def trap1_retry_absent_information(client, doc_id: str = "C", retries: int = 3) -> dict:
    results = [extract(client, doc_id, "\n\nThe department is missing - find it.")["department"] for _ in range(retries)]
    return {"retries": retries, "department_found": any(results)}  # it was never in the document


def trap2_retry_without_error(client, doc_id: str = "A", retries: int = 2) -> dict:
    errors = [validate(extract(client, doc_id, "\n\nPlease try again more carefully."))[1] for _ in range(retries)]
    return {"same_error_every_time": len(set(errors)) == 1 and errors[0] is not None, "error": errors[0]}


def schema_only_check(raw: dict) -> bool:
    """What a JSON schema can say: the right keys with the right types. Nothing about arithmetic."""
    return set(SCHEMA["required"]) <= raw.keys() and isinstance(raw["line_items"], list)


def trap3_schema_only(client) -> dict:
    raw = extract(client, "A")
    return {"schema_valid": schema_only_check(raw), "semantic_error": validate(raw)[1]}


def trap4_pydantic_redundant(client) -> dict:
    raw = extract(client, "B")  # dates the wrong way round - type-correct, logically wrong
    return {"passes_schema": schema_only_check(raw), "pydantic_says": validate(raw)[1]}


def main():
    print(f"trap 1 retry absent info : {trap1_retry_absent_information(get_client(mock_model))}")
    print(f"trap 2 retry, no error   : {trap2_retry_without_error(get_client(mock_model))}")
    print(f"trap 3 schema only       : {trap3_schema_only(get_client(mock_model))}")
    print(f"trap 4 skip Pydantic     : {trap4_pydantic_redundant(get_client(mock_model))}")


if __name__ == "__main__":
    main()
