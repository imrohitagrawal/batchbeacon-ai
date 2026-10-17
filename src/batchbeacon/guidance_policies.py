"""Fixed presentation policies. Only a trusted backend may choose required fields."""

from enum import StrEnum
from types import MappingProxyType

from batchbeacon.contracts import Record


class GuidanceField(StrEnum):
    PRODUCT_IDENTITY = "PRODUCT_IDENTITY"
    LOT = "LOT"
    BEST_BEFORE = "BEST_BEFORE"
    USE_BY = "USE_BY"


class GuidancePolicyId(StrEnum):
    V1 = "GUIDANCE_V1"
    V2 = "GUIDANCE_V2"


class GuidanceText(Record):
    field: GuidanceField
    text: str


class GuidancePolicy(Record):
    id: GuidancePolicyId
    family: str = "required-panel-presentation-1"
    instructions: tuple[GuidanceText, ...]


_BASE = (
    GuidanceText(
        field=GuidanceField.PRODUCT_IDENTITY,
        text="Photograph the complete product name, brand, pack size and any product code.",
    ),
    GuidanceText(
        field=GuidanceField.LOT,
        text="Photograph the complete printed LOT or Batch code, including leading zeros.",
    ),
    GuidanceText(
        field=GuidanceField.BEST_BEFORE, text="Photograph the complete best-before date marking."
    ),
    GuidanceText(field=GuidanceField.USE_BY, text="Photograph the complete use-by date marking."),
)
_HINTS = {
    GuidanceField.LOT: " Show the complete code in one frame. Keep the pack flat and avoid glare.",
    GuidanceField.BEST_BEFORE: " Keep the pack flat and avoid glare.",
    GuidanceField.USE_BY: " Keep the pack flat and avoid glare.",
}
POLICIES = MappingProxyType(
    {
        GuidancePolicyId.V1: GuidancePolicy(id=GuidancePolicyId.V1, instructions=_BASE),
        GuidancePolicyId.V2: GuidancePolicy(
            id=GuidancePolicyId.V2,
            instructions=tuple(
                GuidanceText(field=item.field, text=item.text + _HINTS.get(item.field, ""))
                for item in _BASE
            ),
        ),
    }
)


def wording_for(
    policy_id: GuidancePolicyId, required: tuple[GuidanceField, ...], *, max_instruction_chars: int
) -> tuple[GuidanceText, ...]:
    """Render exactly the required fields; never create a request or alter a result.

    Caller supplies current server-derived needs and effective validated limits.
    No request, model, database, source or counter operation occurs here.
    """
    if type(max_instruction_chars) is not int or max_instruction_chars <= 0:
        raise ValueError("instruction length must be a positive integer")
    if not isinstance(policy_id, GuidancePolicyId):
        raise ValueError("policy must be an allowlisted typed identity")
    if len(required) != len(set(required)) or any(
        not isinstance(field, GuidanceField) for field in required
    ):
        raise ValueError("required fields must be unique typed fields")
    if GuidanceField.PRODUCT_IDENTITY in required and len(required) != 1:
        raise ValueError("identity recovery precedes lot/date recovery")
    text_by_field = {item.field: item for item in POLICIES[policy_id].instructions}
    instructions = tuple(text_by_field[field] for field in required)
    if any(len(item.text) > max_instruction_chars for item in instructions):
        raise ValueError("allowlisted wording exceeds the effective format limit")
    return instructions
