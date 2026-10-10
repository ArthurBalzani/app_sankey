import re

from src.color_utils import convert_color_to_hex, convert_color_to_rgba

_HEX6 = re.compile(r"^#[0-9a-fA-F]{6}$")


def test_convert_plotly_rgb_string_with_opacity():
    assert convert_color_to_rgba("rgb(253, 231, 37)", 0.42) == "rgba(253, 231, 37, 0.42)"
    assert convert_color_to_rgba("rgb(68, 1, 84)", 0.5) == "rgba(68, 1, 84, 0.5)"
    assert convert_color_to_rgba("RGB(68, 1, 84)", 0.5) == "rgba(68, 1, 84, 0.5)"
    assert convert_color_to_rgba("rgb(68,1,84)", 0.5) == "rgba(68, 1, 84, 0.5)"


def test_convert_hex_and_rgba_replace_alpha():
    assert convert_color_to_rgba("#ff0000", 0.5) == "rgba(255, 0, 0, 0.5)"
    assert convert_color_to_rgba("rgba(10, 20, 30, 0.99)", 0.1) == "rgba(10, 20, 30, 0.1)"


def test_convert_color_to_hex_from_plotly_rgb():
    assert convert_color_to_hex("rgb(68, 1, 84)") == "#440154"
    assert convert_color_to_hex("RGB(68,1,84)") == "#440154"
    assert _HEX6.match(convert_color_to_hex("#440154"))
    assert convert_color_to_hex("#f00") == "#ff0000"
