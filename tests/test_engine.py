import sys
import pytest
from marieSimulator import Marie, MarieReader, assemble, AssemblyError
from marieSimulator.Marie import ExecutionError, signed


def execute(source, inputs=(), cap=200):
    engine = Marie(assemble(source), nonblocking=True)
    engine.inputs.extend(inputs)
    for _ in range(cap):
        if not engine.running or not engine.tick():
            return engine
    pytest.fail('Program did not terminate within test bound')


def test_headless_import():
    import subprocess
    from pathlib import Path
    code = "import marieSimulator, sys; assert 'marieSimulator.MarieGUI' not in sys.modules; assert 'PySide6' not in sys.modules"
    subprocess.run([sys.executable, '-c', code], cwd=Path(__file__).resolve().parents[1] / 'src', check=True)


def test_encoding_and_forward_labels():
    p = assemble('/ comment\n\nLoad X\nAdd Y\nStore X\nHalt\nX, HEX FFFF\nY, DEC 1')
    assert p.M[:6] == [0x1004,0x3005,0x2004,0x7000,0xFFFF,1]
    assert p.lines == {0:3,1:4,2:5,3:6,4:7,5:8}


@pytest.mark.parametrize('name,opcode', [('JnS',0),('Load',1),('Store',2),('Add',3),('Subt',4),('Input',5),('Output',6),('Halt',7),('Skipcond',8),('Jump',9),('Clear',10),('AddI',11),('JumpI',12),('LoadI',13),('StoreI',14)])
def test_all_opcodes(name, opcode):
    operand = '' if name in ('Input','Output','Halt','Clear') else ' 000'
    assert assemble(name+operand).M[0] == opcode << 12


def test_add_store_output_clear_and_reset_copy(tmp_path):
    source = 'Load X\nAdd One\nStore X\nOutput\nClear\nHalt\nX, HEX FFFF\nOne, DEC 1'
    p = assemble(source)
    e = execute(source)
    assert e.AC == 0 and e.outputs == [0] and e.M[6] == 0
    assert p.M[6] == 65535
    f = tmp_path / 'test.mas'; f.write_text(source)
    reader = MarieReader(f)
    first = Marie(reader, nonblocking=True); first.run()
    fresh = Marie(reader, nonblocking=True)
    assert fresh.M[6] == 65535 and len(reader.M) == 4096
    assert fresh.PC == 0 and fresh.outputs == []


def test_overflow_and_subtraction():
    e = execute('Load Max\nAdd One\nOutput\nSubt One\nOutput\nHalt\nMax, HEX 7FFF\nOne, DEC 1')
    assert e.outputs == [0x8000,0x7FFF]
    assert signed(0xFFFF) == -1
    assert execute('Clear\nSubt One\nHalt\nOne, DEC 1').AC == 65535


@pytest.mark.parametrize('value,condition,skip', [(-1,'000',True),(0,'000',False),(1,'000',False),(-1,'400',False),(0,'400',True),(1,'400',False),(-1,'800',False),(0,'800',False),(1,'800',True)])
def test_skipcond(value, condition, skip):
    e = Marie(assemble(f'Load X\nSkipcond {condition}\nHalt\nHalt\nX, DEC {value}'), nonblocking=True)
    e.tick(); e.tick()
    assert e.PC == (3 if skip else 2)


def test_indirect_load_add_store_and_high_pointer_bits():
    e = execute('LoadI P\nAddI P\nStoreI P\nOutput\nHalt\nP, HEX F006\nX, DEC 21')
    assert e.outputs == [42] and e.M[6] == 42 and e.M[5] == 0xF006


def test_subroutine_jns_and_jumpi():
    e = execute('Load X\nJnS Double\nOutput\nHalt\nDouble, HEX 0\nStore Temp\nAdd Temp\nJumpI Double\nX, DEC 9\nTemp, DEC 0')
    # MARIE JnS changes AC to the subroutine entry (5), so save caller AC explicitly.
    assert e.M[4] == 2 and e.outputs == [10]


def test_input_yields_without_fetch_then_consumes_once():
    e = Marie(assemble('Input\nOutput\nHalt'), nonblocking=True)
    assert not e.tick() and e.waiting and e.PC == 0 and e.IR == 0
    e.inputs.append(-7)
    assert e.tick() and not e.waiting and e.PC == 1
    e.run()
    assert e.outputs == [65529] and e.InReg == 65529
    assert e.step() is None


def test_address_wrapping_and_origin():
    e = execute('ORG FFF\nClear\nORG 000\nHalt')
    assert e.last_address == 0 and e.PC == 1
    assert len(e.M) == 4096


def test_data_execution_is_error():
    with pytest.raises(ExecutionError):
        execute('HEX FFFF')


@pytest.mark.parametrize('source,line', [('Load Missing',1),('Wat 1',1),('Load',1),('Halt 1',1),('Skipcond C00',1),('Jump 1000',1),('DEC 32768',1),('HEX 10000',1),('A, DEC 1\nA, Halt',2),('ORG FFF\nHalt\nHalt',3),('ORG 0\nHalt\nORG 0\nHalt',4),('/ only comments',1),('A,',1),('ORG -1',1)])
def test_assembly_errors_have_lines(source, line):
    with pytest.raises(AssemblyError) as exc:
        assemble(source)
    assert exc.value.line == line


def test_source_byte_limit():
    with pytest.raises(AssemblyError):
        assemble('/' + 'é' * 33000)


def test_invalid_unicode_and_runtime_skipcond():
    with pytest.raises(AssemblyError):
        assemble('Halt\ud800')
    e = Marie(assemble('HEX 8C00'), nonblocking=True)
    with pytest.raises(ExecutionError, match='condition C00'):
        e.tick()


def test_jns_clobbers_accumulator_and_saves_return():
    e = Marie(assemble('Load X\nJnS Sub\nHalt\nSub, HEX 0\nJumpI Sub\nX, DEC 42'), nonblocking=True)
    e.tick(); e.tick()
    assert e.AC == 4 and e.PC == 4 and e.M[3] == 2
    e.tick()
    assert e.PC == 2
