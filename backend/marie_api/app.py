"""Single-process, bounded sessions. Deploy with exactly one Uvicorn worker."""
import asyncio
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass, field
import os
import secrets
import time
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from marieSimulator import Marie, assemble, AssemblyError
from marieSimulator.assembler import Program
from marieSimulator.Marie import ExecutionError

TTL = int(os.getenv('SESSION_TTL_SECONDS', '1800'))
MAX_SESSIONS = int(os.getenv('MAX_SESSIONS', '100'))
MAX_STEPS = 100_000
MAX_OUTPUT = 1024
MAX_RUN_SECONDS = 60
MAX_CPU_SECONDS = 2
COOKIE = 'marie_owner'


@dataclass
class Session:
    owner: str
    source: str
    program: Program
    engine: Marie
    status: str = 'ready'
    revision: int = 0
    steps: int = 0
    speed: int = 20
    error: str | None = None
    touched: float = field(default_factory=time.monotonic)
    cpu_seconds: float = 0
    run_seconds: float = 0
    credit: float = 0
    scheduled_at: float | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def snapshot(self, sid):
        e = self.engine
        return dict(id=sid, status=self.status, revision=self.revision, steps=self.steps,
                    speed=self.speed, error=self.error, source=self.source,
                    registers={name: getattr(e, name) for name in ('AC','PC','MAR','MBR','IR','InReg','OutReg')},
                    memory=e.M.copy(), output=e.outputs.copy(), input=list(e.inputs),
                    current_address=e.PC, current_line=self.program.lines.get(e.PC),
                    last_address=e.last_address, listing=self.program.listing,
                    expires_in=TTL, limits=dict(instructions=MAX_STEPS, output=MAX_OUTPUT, run_seconds=MAX_RUN_SECONDS))

    def account_runtime(self):
        now = time.monotonic()
        elapsed = now - self.scheduled_at if self.scheduled_at is not None and self.status == 'running' else 0
        self.run_seconds += elapsed
        self.scheduled_at = now if self.status == 'running' else None
        return elapsed

    def advance(self, count):
        start = time.perf_counter()
        try:
            for _ in range(count):
                if self.steps >= MAX_STEPS:
                    raise ExecutionError('Instruction limit reached. Reset to run again.')
                if self.cpu_seconds + time.perf_counter() - start >= MAX_CPU_SECONDS or self.run_seconds >= MAX_RUN_SECONDS:
                    raise ExecutionError('Execution time limit reached. Reset to run again.')
                # Refuse the next Output before allowing the output buffer to grow.
                if self.engine.M[self.engine.PC] >> 12 == 6 and len(self.engine.outputs) >= MAX_OUTPUT:
                    raise ExecutionError('Output limit reached. Reset to run again.')
                if not self.engine.tick():
                    self.status = 'waiting_for_input'
                    break
                self.steps += 1
                if not self.engine.running:
                    self.status = 'halted'
                    break
                if time.perf_counter() - start >= .003:
                    break
        except ExecutionError as exc:
            self.status, self.error = 'failed', str(exc)
        except Exception:
            # Unexpected failures are intentionally not reflected to visitors.
            self.status, self.error = 'failed', 'Execution failed. Reset or reassemble the program.'
        finally:
            self.cpu_seconds += time.perf_counter() - start


class Sessions:
    def __init__(self):
        self.items: dict[str, Session] = {}
        self.lock = asyncio.Lock()

    def cleanup(self):
        now = time.monotonic()
        for sid, session in list(self.items.items()):
            if now - session.touched > TTL:
                del self.items[sid]

    async def scheduler(self):
        while True:
            await asyncio.sleep(.02)
            self.cleanup()
            cycle_start = time.perf_counter()
            # Rotate to give every visitor fair access under load.
            for sid, session in list(self.items.items()):
                if session.status != 'running':
                    continue
                async with session.lock:
                    elapsed = session.account_runtime()
                    session.credit = min(session.credit + min(elapsed, .1) * session.speed, 100)
                    count = int(session.credit)
                    if count:
                        before = session.steps
                        session.advance(count)
                        session.credit -= session.steps - before
                self.items.pop(sid, None)
                self.items[sid] = session
                if time.perf_counter() - cycle_start >= .015:
                    break


def create_app():
    sessions = Sessions()

    @asynccontextmanager
    async def lifespan(app):
        if int(os.getenv('WEB_CONCURRENCY', '1')) != 1:
            raise RuntimeError('In-memory MARIE sessions require one worker.')
        task = asyncio.create_task(sessions.scheduler())
        yield
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        sessions.items.clear()

    app = FastAPI(title='MARIE API', lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.sessions = sessions

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(status_code=422, content={'detail': 'Invalid request. Check source size, command, speed, or input value.'})

    @app.middleware('http')
    async def security(request: Request, call_next):
        if request.method in ('POST','DELETE'):
            if request.headers.get('x-marie-client') != 'web':
                return JSONResponse(status_code=403, content={'detail':'Missing application header.'})
            origin = request.headers.get('origin')
            host = request.headers.get('host')
            if origin:
                from urllib.parse import urlsplit
                if urlsplit(origin).netloc != host:
                    return JSONResponse(status_code=403, content={'detail':'Cross-origin requests are not allowed.'})
            # Read at most 70 KiB, even if content-length is absent or forged.
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 71680:
                    return JSONResponse(status_code=413, content={'detail':'Request exceeds 70 KiB.'})
            request._body = bytes(body)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    def owner(request):
        token = request.cookies.get(COOKIE, '')
        if not 32 <= len(token) <= 128:
            raise HTTPException(401, 'Visitor identity missing. Reload the page.')
        return token

    def lookup(sid, request):
        sessions.cleanup()
        session = sessions.items.get(sid)
        if session is None or not secrets.compare_digest(session.owner, owner(request)):
            raise HTTPException(404, 'Session expired or unavailable. Assemble your saved source to start again.')
        session.touched = time.monotonic()
        return session

    @app.get('/api/health')
    async def health():
        return {'status':'ok'}

    @app.get('/api/bootstrap')
    async def bootstrap(request: Request, response: Response):
        token = request.cookies.get(COOKIE, '')
        if not 32 <= len(token) <= 128:
            response.set_cookie(COOKIE, secrets.token_urlsafe(32), httponly=True, samesite='strict',
                                secure=os.getenv('COOKIE_SECURE', 'false').lower() == 'true', max_age=86400, path='/api')
        return {'ttl_seconds':TTL}

    @app.post('/api/sessions')
    async def create(body: AssembleRequest, request: Request):
        visitor = owner(request)
        try:
            program = assemble(body.source)
        except AssemblyError as exc:
            return JSONResponse(status_code=422, content={'kind':'assembly', 'line':exc.line, 'detail':exc.message})
        async with sessions.lock:
            sessions.cleanup()
            old = sessions.items.get(body.replace or '')
            if old and old.owner != visitor:
                raise HTTPException(404, 'Session unavailable.')
            count = sum(s.owner == visitor for s in sessions.items.values()) - bool(old)
            if count >= 4 or len(sessions.items) - bool(old) >= MAX_SESSIONS:
                raise HTTPException(429, 'Session capacity reached. Please try again later.')
            if old:
                async with old.lock:
                    sessions.items.pop(body.replace, None)
            sid = secrets.token_urlsafe(32)
            session = Session(visitor, body.source, program, Marie(program, nonblocking=True))
            sessions.items[sid] = session
            return session.snapshot(sid)

    @app.get('/api/sessions/{sid}')
    async def state(sid: str, request: Request):
        session = lookup(sid, request)
        async with session.lock:
            return session.snapshot(sid)

    @app.post('/api/sessions/{sid}/commands')
    async def command(sid: str, body: Command, request: Request):
        session = lookup(sid, request)
        async with session.lock:
            if body.revision != session.revision:
                raise HTTPException(409, 'Another command changed this session. Refresh state and try again.')
            action, status = body.action, session.status
            session.account_runtime()
            if action == 'reset':
                session.engine = Marie(session.program, nonblocking=True)
                session.status, session.error, session.steps = 'ready', None, 0
                session.cpu_seconds = session.run_seconds = session.credit = 0
                session.scheduled_at = None
            elif action == 'speed':
                session.speed = body.speed
                session.credit = 0
            elif action == 'pause':
                if status == 'running':
                    session.status = 'paused'
                    session.credit = 0
            elif action in ('step','run'):
                if status not in ('ready','paused'):
                    raise HTTPException(409, 'Reset a finished program, or supply requested input first.')
                session.status = 'running' if action == 'run' else 'paused'
                session.scheduled_at = time.monotonic() if action == 'run' else None
                session.credit = 0
                if action == 'step':
                    session.advance(1)
            elif action == 'input':
                if status != 'waiting_for_input':
                    raise HTTPException(409, 'The program is not waiting for input.')
                session.engine.inputs.append(body.value)
                session.status = 'paused'
                session.advance(1)
                # Input is consumed as one instruction; resume is explicit.
            session.revision += 1
            return session.snapshot(sid)

    @app.delete('/api/sessions/{sid}')
    async def delete(sid: str, request: Request):
        session = lookup(sid, request)
        async with session.lock:
            sessions.items.pop(sid, None)
        return {'status':'deleted'}

    return app


class AssembleRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source: str = Field(min_length=1, max_length=65536)
    replace: str | None = Field(default=None, max_length=64)


class Command(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['step','run','pause','reset','speed','input']
    revision: int = Field(ge=0)
    speed: int = Field(default=20, ge=1, le=5000)
    value: int = Field(default=0, ge=-32768, le=65535)


app = create_app()
