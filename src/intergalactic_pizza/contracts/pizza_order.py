from pydantic import BaseModel, Field


class PizzaOrder(BaseModel):
    order_id: str = Field(
        ...,  # Required
        description="Unique order identifier",
        examples=["ORD-12345"],
        pattern="^ORD-[0-9]+$"
    )
