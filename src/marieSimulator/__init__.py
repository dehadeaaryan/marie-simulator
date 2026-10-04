"""Headless imports never initialize Qt. Desktop exports remain compatible."""
from .Marie import Marie
from .MarieReader import MarieReader
from .assembler import assemble, AssemblyError

__all__ = ['Marie', 'MarieReader', 'assemble', 'AssemblyError', 'MarieGUI', 'app']


def __getattr__(name):
    if name in ('MarieGUI', 'app'):
        from .MarieGUI import MarieGUI, app
        globals().update(MarieGUI=MarieGUI, app=app)
        return globals()[name]
    raise AttributeError(name)
