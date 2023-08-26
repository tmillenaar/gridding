import gridkit


def test_initialized_objects():
    expected_attributes = [
        "GridIndex",
        "validate_index",
        "BaseGrid",
        "RectGrid",
        "HexGrid",
        "BoundedRectGrid",
        "BoundedHexGrid",
        "mean",
        "sum",
        "count",
    ]
    for attr in expected_attributes:
        assert hasattr(gridkit, attr), f"Missing attribute '{attr}' from gridkit module"
