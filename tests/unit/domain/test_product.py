import pytest
from domain.product import Product


class TestProduct:

    def test__product__given_valid_inputs__creates_successfully(self):
        # ARRANGE / ACT
        product = Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=89)

        # ASSERT
        assert product.name == "banana"
        assert product.price_usd == 0.5
        assert product.weight_kg == 0.12
        assert product.calories == 89

    @pytest.mark.parametrize("invalid_name", ["", None])
    def test__product__given_invalid_name__raises_value_error(self, invalid_name):
        # ARRANGE / ACT / ASSERT
        with pytest.raises(ValueError, match="name"):
            Product(name=invalid_name, price_usd=0.5, weight_kg=0.12, calories=89)

    @pytest.mark.parametrize("price", [0, -1, -0.01])
    def test__product__given_non_positive_price__raises_value_error(self, price):
        with pytest.raises(ValueError, match="price_usd"):
            Product(name="banana", price_usd=price, weight_kg=0.12, calories=89)

    @pytest.mark.parametrize("weight", [0, -1, -0.001])
    def test__product__given_non_positive_weight__raises_value_error(self, weight):
        with pytest.raises(ValueError, match="weight_kg"):
            Product(name="banana", price_usd=0.5, weight_kg=weight, calories=89)

    @pytest.mark.parametrize("calories", [0, -1, -100])
    def test__product__given_non_positive_calories__raises_value_error(self, calories):
        with pytest.raises(ValueError, match="calories"):
            Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=calories)
