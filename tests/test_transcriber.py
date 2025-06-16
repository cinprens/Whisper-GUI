import sys
from unittest import mock

# transcriber module requires 'torch' and 'whisper'. Provide mocks so it can be
# imported without installing these packages.
sys.modules.setdefault('torch', mock.MagicMock())
sys.modules.setdefault('whisper', mock.MagicMock())
sys.modules.setdefault('huggingface_hub', mock.MagicMock())

import builtins
import transcriber


def test_check_requirements_all_present():
    original_import = builtins.__import__

    def import_mock(name, globals=None, locals=None, fromlist=(), level=0):
        if name in ("psutil", "GPUtil", "fpdf"):
            return mock.MagicMock()
        return original_import(name, globals, locals, fromlist, level)

    with mock.patch('builtins.__import__', side_effect=import_mock):
        assert transcriber.check_requirements() == []


def test_check_requirements_missing_psutil():
    original_import = builtins.__import__

    def import_mock(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "psutil":
            raise ImportError()
        if name in ("GPUtil", "fpdf"):
            return mock.MagicMock()
        return original_import(name, globals, locals, fromlist, level)

    with mock.patch('builtins.__import__', side_effect=import_mock):
        assert transcriber.check_requirements() == ["psutil"]


def test_check_requirements_missing_all():
    original_import = builtins.__import__

    def import_mock(name, globals=None, locals=None, fromlist=(), level=0):
        if name in ("psutil", "GPUtil", "fpdf"):
            raise ImportError()
        return original_import(name, globals, locals, fromlist, level)

    with mock.patch('builtins.__import__', side_effect=import_mock):
        assert transcriber.check_requirements() == ["psutil", "gputil", "fpdf"]


def test_install_requirements_installs_only_missing():
    installed = []

    def fake_run(cmd, capture_output=True, text=True):
        installed.append(cmd[-1])
        return mock.MagicMock(returncode=0)

    with mock.patch('subprocess.run', side_effect=fake_run):
        transcriber.install_requirements(["psutil", "gputil"])

    assert installed == ["psutil", "gputil"]
