from pathlib import Path

import pycodestyle


def test_style_frontend():
    s = pycodestyle.StyleGuide()
    p = (Path(__file__).parents[1].resolve()) / "poptpy"
    res = s.check_files([f for f in p.iterdir() if f.suffix == ".py"])
    assert res.total_errors == 0


def test_style_backend():
    s = pycodestyle.StyleGuide()
    p = (Path(__file__).parents[1].resolve()) / "poptpy" / "poptpy_backend"
    res = s.check_files([f for f in p.iterdir() if f.suffix == ".py"])
    assert res.total_errors == 0


def test_style_costfunctions():
    s = pycodestyle.StyleGuide()
    p = ((Path(__file__).parents[1].resolve()) / "poptpy" / "poptpy_backend" /
         "cost_functions")
    res = s.check_files([f for f in p.iterdir() if f.suffix == ".py"])
    assert res.total_errors == 0


def test_style_tests():   # how meta
    s = pycodestyle.StyleGuide()
    p = Path(__file__).parent
    res = s.check_files([f for f in p.iterdir() if f.suffix == ".py"])
    assert res.total_errors == 0
