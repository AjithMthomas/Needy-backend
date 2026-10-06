"""Moderation engine tests — must match the Flutter screen's behaviour."""

from apps.core.moderation import normalize, screen


def test_clean_text_passes():
    assert screen("Bike wash", "Need help washing my bike").clean


def test_hard_word_blocks():
    verdict = screen("Weekend plan", "let's do some weed")
    assert not verdict.clean
    assert "safety rules" in verdict.reason


def test_leetspeak_evasion_caught():
    assert not screen("S3xy party", "").clean
    assert not screen("nude5", "").clean


def test_spacing_evasion_caught():
    assert not screen("w e e d time", "").clean


def test_soft_word_blocks_with_rephrase_reason():
    verdict = screen("Massage offer", "full body available")
    assert not verdict.clean
    assert "rephrase" in verdict.reason


def test_normalize_folds_symbols():
    assert normalize("S3XY  nudes!!") == "sexy nudes"
