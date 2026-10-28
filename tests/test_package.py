import re
from importlib.metadata import distribution


def test_package_imports():
    import scientia

    assert scientia.__name__ == "scientia"


def test_runtime_dependencies_include_only_used_pdf_library():
    requirements = distribution("scientia").metadata.get_all("Requires-Dist") or []
    dependency_names = {
        re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", requirement).group().lower()
        for requirement in requirements
    }

    assert dependency_names == {"pypdf"}
