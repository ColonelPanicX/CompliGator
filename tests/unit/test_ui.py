"""Unit tests for compligator.ui."""

import pytest

from compligator.ui import WIDTH, visual_len


@pytest.mark.unit
def test_visual_len_ascii():
    assert visual_len("hello") == 5


@pytest.mark.unit
def test_visual_len_box_drawing():
    # Box-drawing characters (U+2500–U+257F) count as 1 column
    assert visual_len("─") == 1
    assert visual_len("═") == 1


@pytest.mark.unit
def test_visual_len_emoji():
    # Emoji outside box-drawing range count as 2 columns
    assert visual_len("✓") == 2


@pytest.mark.unit
def test_visual_len_zero_width():
    # Variation selectors are zero-width
    assert visual_len("\uFE0F") == 0


@pytest.mark.unit
def test_width_constant():
    assert WIDTH == 70
