import pytest
from backend.formatting import percentage_label


@pytest.mark.parametrize("value,expected", [(1.0, ">99.9"), (.99998, ">99.9"), (.995, "99.5"), (.00001, "<0.1"), (0, "0.0")])
def test_display_does_not_round_to_certainty(value, expected):
    assert percentage_label(value) == expected
