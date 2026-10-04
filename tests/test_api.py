from concurrent.futures import ThreadPoolExecutor
import time
import pytest
from fastapi.testclient import TestClient
from marie_api import app as module

HEADERS = {'x-marie-client':'web'}

@pytest.fixture
def client():
    with TestClient(module.create_app(), headers=HEADERS) as c:
        c.get('/api/bootstrap')
        yield c


def create(c, source='Load X\nOutput\nHalt\nX, DEC 42', **kw):
    r = c.post('/api/sessions', json={'source':source, **kw})
    assert r.status_code == 200, r.text
    return r.json()


def command(c, s, action, **kw):
    r = c.post(f"/api/sessions/{s['id']}/commands", json={'action':action,'revision':s['revision'], **kw})
    assert r.status_code == 200, r.text
    return r.json()


def test_step_halt_reset(client):
    s = create(client, 'Load X\nAdd X\nStore X\nOutput\nHalt\nX, DEC 7')
    assert s['status'] == 'ready' and len(s['memory']) == 4096
    for _ in range(5): s = command(client,s,'step')
    assert s['status'] == 'halted' and s['output'] == [14] and s['memory'][5] == 14
    s = command(client,s,'reset')
    assert s['memory'][5] == 7 and s['output'] == [] and s['steps'] == 0 and s['registers']['PC'] == 0


def test_run_input_pause_resume(client):
    s = create(client,'Input\nOutput\nHalt')
    s = command(client,s,'run')
    time.sleep(.09)
    s = client.get('/api/sessions/'+s['id']).json()
    assert s['status'] == 'waiting_for_input' and s['steps'] == 0
    s = command(client,s,'input',value=-8)
    assert s['status'] == 'paused' and s['steps'] == 1
    s = command(client,s,'run')
    time.sleep(.15)
    s = client.get('/api/sessions/'+s['id']).json()
    assert s['status'] == 'halted' and s['output'] == [65528]


def test_responsive_pause_and_concurrent_commands(client):
    s = create(client,'Loop, Jump Loop')
    s = command(client,s,'speed',speed=5000)
    s = command(client,s,'run')
    time.sleep(.04)
    start = time.monotonic(); s = command(client,s,'pause')
    assert time.monotonic() - start < .5
    steps = s['steps']; time.sleep(.08)
    assert client.get('/api/sessions/'+s['id']).json()['steps'] == steps
    payload={'action':'step','revision':s['revision']}
    with ThreadPoolExecutor(2) as pool:
        results=list(pool.map(lambda _: client.post('/api/sessions/'+s['id']+'/commands',json=payload).status_code,range(2)))
    assert sorted(results) == [200,409]


def test_session_isolation_and_owner_cookie(client):
    s = create(client)
    visitor = TestClient(client.app, headers=HEADERS)
    response=visitor.get('/api/bootstrap')
    assert 'HttpOnly' in response.headers['set-cookie'] and 'SameSite=strict' in response.headers['set-cookie']
    assert visitor.get('/api/sessions/'+s['id']).status_code == 404
    assert visitor.post('/api/sessions/'+s['id']+'/commands',json={'action':'reset','revision':0}).status_code == 404
    assert visitor.delete('/api/sessions/'+s['id']).status_code == 404
    assert visitor.post('/api/sessions',json={'source':'Halt','replace':s['id']}).status_code == 404
    own = create(visitor)
    assert own['id'] != s['id'] and len(own['id']) >= 32
    assert client.get('/api/sessions/'+s['id']).json()['steps'] == 0


def test_invalid_source_keeps_previous_session(client):
    s=create(client)
    r=client.post('/api/sessions',json={'source':'\nLoad Undefined','replace':s['id']})
    assert r.status_code == 422 and r.json()['kind'] == 'assembly' and r.json()['line'] == 2
    assert client.get('/api/sessions/'+s['id']).status_code == 200


def test_execution_error_and_reset(client):
    s=create(client,'HEX FFFF')
    s=command(client,s,'step')
    assert s['status'] == 'failed' and 'Opcode F' in s['error']
    assert 'Traceback' not in s['error']
    assert command(client,s,'reset')['status'] == 'ready'


@pytest.mark.parametrize('limit,value,source,expected', [('MAX_STEPS',8,'Loop, Jump Loop','Instruction limit'),('MAX_OUTPUT',2,'Loop, Output\nJump Loop','Output limit'),('MAX_RUN_SECONDS',.03,'Loop, Jump Loop','time limit'),('MAX_CPU_SECONDS',0,'Loop, Jump Loop','time limit')])
def test_limits(client,monkeypatch,limit,value,source,expected):
    monkeypatch.setattr(module,limit,value)
    s=create(client,source); s=command(client,s,'speed',speed=5000); s=command(client,s,'run')
    time.sleep(.15)
    s=client.get('/api/sessions/'+s['id']).json()
    assert s['status'] == 'failed' and expected in s['error']
    assert s['steps'] <= module.MAX_STEPS and len(s['output']) <= module.MAX_OUTPUT


def test_expiry_and_replacement(client):
    s=create(client)
    client.app.state.sessions.items[s['id']].touched -= module.TTL + 1
    assert client.get('/api/sessions/'+s['id']).status_code == 404
    assert s['id'] not in client.app.state.sessions.items
    s=create(client); new=create(client,'Halt',replace=s['id'])
    assert client.get('/api/sessions/'+s['id']).status_code == 404 and new['id'] != s['id']


def test_capacity(client,monkeypatch):
    for _ in range(4): create(client)
    assert client.post('/api/sessions',json={'source':'Halt'}).status_code == 429
    monkeypatch.setattr(module,'MAX_SESSIONS',4)
    with TestClient(client.app,headers=HEADERS) as other:
        other.get('/api/bootstrap')
        assert other.post('/api/sessions',json={'source':'Halt'}).status_code == 429


def test_input_and_command_validation(client):
    s=create(client,'Input\nHalt')
    url='/api/sessions/'+s['id']+'/commands'
    assert client.post(url,json={'action':'input','revision':0,'value':4}).status_code == 409
    for payload in ({'action':'input','revision':0,'value':65536},{'action':'speed','revision':0,'speed':5001},{'action':'shell','revision':0}):
        r=client.post(url,json=payload)
        assert r.status_code == 422 and 'traceback' not in r.text.lower()


def test_body_boundary_csrf_and_bootstrap(client):
    assert client.post('/api/sessions',content=b'x'*72000).status_code == 413
    assert client.post('/api/sessions',json={'source':'Halt'},headers={'x-marie-client':''}).status_code == 403
    assert client.post('/api/sessions',json={'source':'Halt'},headers={'origin':'https://evil.example'}).status_code == 403
    client.cookies.clear()
    assert client.post('/api/sessions',json={'source':'Halt'}).status_code == 401


def test_restart_loses_state():
    with TestClient(module.create_app(),headers=HEADERS) as first:
        first.get('/api/bootstrap'); s=create(first); cookies=dict(first.cookies)
    with TestClient(module.create_app(),headers=HEADERS) as second:
        second.cookies.update(cookies)
        assert second.get('/api/sessions/'+s['id']).status_code == 404


def test_reset_stops_running_and_restores_input_wait(client):
    s=create(client,'Input\nLoop, Add One\nStore One\nJump Loop\nOne, DEC 1')
    s=command(client,s,'step')
    assert s['status'] == 'waiting_for_input'
    s=command(client,s,'input',value=7)
    s=command(client,s,'speed',speed=5000)
    s=command(client,s,'run')
    time.sleep(.05)
    s=command(client,s,'reset')
    assert s['steps'] == 0 and s['memory'][4] == 1 and s['output'] == []
    time.sleep(.05)
    assert client.get('/api/sessions/'+s['id']).json()['steps'] == 0
    s=command(client,s,'step')
    assert s['status'] == 'waiting_for_input' and s['registers']['PC'] == 0


def test_no_internal_traceback_on_unexpected_engine_error(client, monkeypatch):
    s=create(client)
    engine=client.app.state.sessions.items[s['id']].engine
    def fail():
        raise RuntimeError('private secret test traceback')
    monkeypatch.setattr(engine,'tick',fail)
    s=command(client,s,'step')
    assert s['status'] == 'failed' and 'private secret' not in s['error']
