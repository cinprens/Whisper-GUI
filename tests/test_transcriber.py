import sys
from unittest import mock

# transcriber module requires 'torch' and 'whisper'. Provide mocks so it can be
# imported without installing these packages.
sys.modules.setdefault('torch', mock.MagicMock())
sys.modules.setdefault('whisper', mock.MagicMock())
sys.modules.setdefault('psutil', mock.MagicMock())
sys.modules.setdefault('GPUtil', mock.MagicMock())
sys.modules.setdefault('fpdf', mock.MagicMock())

import builtins
import transcriber
import ui


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

    original_import = builtins.__import__

    def import_mock(name, globals=None, locals=None, fromlist=(), level=0):
        if name in ("psutil", "GPUtil"):
            raise ImportError()
        return original_import(name, globals, locals, fromlist, level)

    with mock.patch('subprocess.run', side_effect=fake_run), \
         mock.patch('builtins.__import__', side_effect=import_mock):
        transcriber.install_requirements(["psutil", "gputil"])

    assert installed == ["psutil", "gputil"]


def test_create_main_window_missing_warning():
    dummy = mock.MagicMock()

    def stringvar_side_effect(*args, **kwargs):
        m = mock.MagicMock()
        m.get.return_value = kwargs.get('value')
        return m

    dummy.StringVar.side_effect = stringvar_side_effect
    with mock.patch('ui.tk', dummy), \
         mock.patch('ui.ttk', dummy), \
         mock.patch('ui.filedialog', dummy), \
         mock.patch('ui.check_requirements', return_value=['psutil', 'fpdf']), \
         mock.patch('ui.messagebox.showwarning') as mock_warn:
        ui.create_main_window()
        mock_warn.assert_called_once()
        args, _ = mock_warn.call_args
        assert 'psutil' in args[1]
        assert 'fpdf' in args[1]


def test_get_installed_models(tmp_path, monkeypatch):
    monkeypatch.setattr(transcriber, 'MODEL_FOLDER', str(tmp_path))
    (tmp_path / 'base.pt').touch()
    (tmp_path / 'medium.bin').touch()
    (tmp_path / 'readme.txt').touch()

    models = transcriber.get_installed_models()
    assert sorted(models) == ['base', 'medium']


def test_download_model_uses_load_model(monkeypatch):
    mock_load = mock.MagicMock()
    monkeypatch.setattr(transcriber, 'whisper', mock.MagicMock(load_model=mock_load))
    monkeypatch.setattr(transcriber, 'messagebox', mock.MagicMock(askyesno=mock.MagicMock(return_value=False)))
    monkeypatch.setattr(transcriber, 'filedialog', mock.MagicMock())
    transcriber.download_model('base')
    mock_load.assert_called_once_with('base', device='cpu', download_root=transcriber.MODEL_FOLDER)

def test_get_installed_models_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(transcriber, 'MODEL_FOLDER', str(tmp_path))
    models = transcriber.get_installed_models()
    assert models == []


def test_run_transcription_warns_when_model_missing(monkeypatch, tmp_path):
    q = transcriber.queue.Queue()
    stop_event = transcriber.threading.Event()
    mock_cuda = mock.MagicMock()
    mock_cuda.is_available.return_value = True
    monkeypatch.setattr(transcriber.torch, 'cuda', mock_cuda)
    monkeypatch.setattr(transcriber, 'MODEL_FOLDER', str(tmp_path))
    monkeypatch.setattr(transcriber.os.path, 'isfile', lambda path: False)

    transcriber.run_transcription(q, stop_event, 'base', tmp_path / 'audio.mp3')
    message = q.get_nowait()
    assert message[0] == 'Warning'
    assert 'Model bulunamadı' in message[1]
