import sys, pathlib
import pytest

top = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(top))

from circuitpython_build_tools.munge import munge

@pytest.mark.parametrize("test_path", top.glob("testcases/*.py"))
def test_munge(test_path):
    result_path = test_path.with_suffix(".out")
    result_path.unlink(missing_ok = True)

    result_content = munge(test_path, "1.2.3")
    result_path.write_text(result_content, encoding="utf-8")

    expected_path = test_path.with_suffix(".exp")
    expected_content = expected_path.read_text(encoding="utf-8")

    assert result_content == expected_content

    result_path.unlink()
