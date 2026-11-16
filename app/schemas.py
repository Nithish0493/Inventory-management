from pydantic import BaseModel, ConfigDict


class Response(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def mask_phone(phone: str | None):
    if not phone:
        return None

    digits = "".join(char for char in phone if char.isdigit())

    if len(digits) <= 4:
        return "*" * len(digits)

    return "*" * (len(digits) - 4) + digits[-4:]