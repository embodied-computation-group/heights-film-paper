"""Tests for analysis/plot_style.py helpers.

Run:  uv run pytest
"""
from analysis import plot_style


def test_film_time_label_gives_minutes_and_zero_padded_seconds():
    assert plot_style.film_time_label(636) == "10:36"
    assert plot_style.film_time_label(65) == "1:05"
    assert plot_style.film_time_label(0) == "0:00"
    assert plot_style.film_time_label(808.9) == "13:28"  # partial seconds are dropped, as on a video player


# ---------------------------------------------------------------- journal figure rules (Affective Science, 2026-10-11)

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402
from PIL import Image  # noqa: E402


def test_panel_letters_must_be_lowercase():
    fig, ax = plt.subplots()
    plot_style.panel_letter(ax, "a")
    with pytest.raises(ValueError):
        plot_style.panel_letter(ax, "A")
    plt.close(fig)


def test_save_print_refuses_a_figure_wider_than_174_mm(tmp_path):
    fig = plt.figure(figsize=(7.0, 4.0))  # 177.8 mm wide
    with pytest.raises(ValueError):
        plot_style.save_print(fig, tmp_path / "Fig9")


def test_save_print_refuses_a_figure_taller_than_234_mm(tmp_path):
    fig = plt.figure(figsize=(6.0, 9.5))  # 241.3 mm high
    with pytest.raises(ValueError):
        plot_style.save_print(fig, tmp_path / "Fig9")


def test_save_print_keeps_the_exact_size_at_600_dpi(tmp_path):
    fig = plt.figure(figsize=(6.5, 3.0))
    fig.add_subplot().plot([0, 1], [0, 1])
    plot_style.save_print(fig, tmp_path / "Fig9")
    assert (tmp_path / "Fig9.pdf").exists()
    with Image.open(tmp_path / "Fig9.png") as image:
        assert image.size == (3900, 1800)  # 6.5 x 3.0 inches at 600 dpi, no cropping


def test_style_keeps_all_text_between_8_and_12_points():
    plot_style.use()
    for key in ("font.size", "axes.labelsize", "axes.titlesize", "xtick.labelsize", "ytick.labelsize",
                "legend.fontsize"):
        size = plt.rcParams[key]
        assert isinstance(size, (int, float)) and 8 <= size <= 12, key
    assert 8 <= plot_style.LETTER_SIZE <= 12
