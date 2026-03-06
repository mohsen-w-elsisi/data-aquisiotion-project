from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional


class PriceType(Enum):
    DISCRETE = "discrete"
    RANGE = "range"


@dataclass(frozen=True)
class Listing:
    """
    Represents a single listing of a product on a vendor's website,
    for example, a user selling a laptop on eBay.
    """

    name: str
    url: str
    image: str

    price_type: PriceType
    price: Optional[float]
    price_range: Optional[tuple[float, float]]

    vendor: str
    subvendor: Optional[str]

    rating: Optional[float]
    review_count: Optional[int]

    def __post_init__(self):
        _PriceValidator(self.price_type, self.price, self.price_range).validate()
        if self.rating is not None:
            if self.rating > 5.0 or self.rating < 0.0:
                raise ValueError(
                    f"Invalid rating {self.rating}. Rating must be between 0 and 5"
                )

    def to_json(self) -> str:
        data = asdict(self)
        data["price_type"] = data["price_type"].value
        return data

    @classmethod
    def from_json(cls, data: dict) -> "Listing":
        data["price_type"] = PriceType(data["price_type"])
        if data["price_range"] is not None:
            data["price_range"] = tuple(data["price_range"])
        return cls(**data)


class _PriceValidator:
    def __init__(
        self,
        price_type: PriceType,
        price: Optional[float],
        price_range: Optional[tuple[float, float]],
    ) -> None:
        self.price_type = price_type
        self.price = price
        self.price_range = price_range

    def validate(self):
        match self.price_type:
            case PriceType.DISCRETE:
                self._validate_discrete_price()
            case PriceType.RANGE:
                self._validate_ranged_price()

    def _validate_discrete_price(self):
        if self.price is None:
            raise ValueError("Price cannot be None for discrete price type.")
        if self.price_range is not None:
            raise ValueError(
                f"Price range must be None for discrete price type. "
                f"Received {self.price_range}"
            )
        if self.price < 0.0:
            raise ValueError(
                f"Invalid price. Price cannot be negative. Received {self.price}"
            )

    def _validate_ranged_price(self):
        if self.price is not None:
            raise ValueError(
                f"Price must be None for range price type. Received {self.price}"
            )
        if self.price_range is None:
            raise ValueError("Price range cannot be None for range price type.")
        if self.price_range[0] < 0.0 or self.price_range[1] < 0.0:
            raise ValueError("Invalid price range. Price cannot be negative")
        if self.price_range[0] > self.price_range[1]:
            raise ValueError(
                "Invalid price range. Minimum price cannot be "
                "greater than maximum price"
            )
