"""Optional Qt smoke test. QT_QPA_PLATFORM=offscreen pytest tests/test_desktop.py."""
import os
import pytest


def test_desktop_load_step_run_reset(tmp_path):
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    pytest.importorskip('PySide6')
    from marieSimulator import MarieGUI, MarieReader, app
    from PySide6.QtTest import QTest
    window = MarieGUI()
    source = tmp_path / 'desktop.mas'
    source.write_text('Load X\nAdd X\nStore X\nOutput\nHalt\nX, DEC 7')
    window.marieReader = MarieReader(source)
    window.marie = window._newMachine()
    window.updateProgramTableWidget()
    window.updateSymbolTableWidget()
    window.guiStep()
    assert window.marie.AC == 7
    window.guiRun()
    QTest.qWait(600)
    assert window.marie.outputs == [14] and not window.timer.isActive()
    assert window.marie.M[5] == 14
    window.guiReset()
    assert window.marie.M[5] == 7 and window.marie.PC == 0
    window.marie.input_provider = lambda: -7
    source.write_text('Input\nOutput\nHalt')
    window.marieReader = MarieReader(source)
    window.marie = window._newMachine()
    window.marie.input_provider = lambda: 0xFFF9
    window.updateProgramTableWidget()
    window.guiStep(); window.guiStep(); window.guiStep()
    assert window.marie.outputs == [0xFFF9]
    window.close()
