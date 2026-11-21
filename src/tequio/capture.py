"""Attempt-wide bounded raw-byte capture for owned POSIX check processes."""
import base64
import os
import selectors
import signal
import subprocess
import time

from .core import Error


class CaptureUncertain(Error):
    """Cleanup or observation could not establish a safe publishable outcome."""


class CaptureBudget:
    def __init__(self, max_bytes):
        if type(max_bytes) is not int or not 1 <= max_bytes <= 16777216:
            raise Error('Invalid capture byte limit')
        self.max_bytes = max_bytes
        self.retained_bytes = 0
        self.observed_bytes = 0
        self.cleanup_discarded_bytes = 0
        self.aborted = False
        self.abort_state = None

    def run_check(self, argv, cwd, timeout, index, on_start):
        if self.aborted:
            raise Error('Capture attempt already aborted')
        buffers = {'stdout': bytearray(), 'stderr': bytearray()}
        observed = {'stdout': 0, 'stderr': 0}
        result = {'check': index, 'launched': False, 'argv': argv,
                  'exit_code': None, 'stdout': '', 'stderr': ''}
        state = 'complete'
        proc = None
        selector = selectors.DefaultSelector()

        def finish():
            for key in buffers:
                result[key] = buffers[key].decode('utf-8', errors='replace')
            result['capture'] = {
                'state': state, 'complete': state == 'complete',
                'stdout_observed_bytes': observed['stdout'],
                'stderr_observed_bytes': observed['stderr'],
                'stdout_retained_bytes': len(buffers['stdout']),
                'stderr_retained_bytes': len(buffers['stderr']),
                'stdout_base64': base64.b64encode(buffers['stdout']).decode('ascii'),
                'stderr_base64': base64.b64encode(buffers['stderr']).decode('ascii')}
            return result

        def kill():
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        def drain_cleanup():
            """No retained growth; exact discard count only after both pipe EOFs."""
            deadline = time.monotonic() + 2
            discarded = 0
            failed = False
            try:
                kill()
            except OSError as exc:
                self.cleanup_discarded_bytes = None
                raise CaptureUncertain('Capture group termination unresolved') from exc
            while time.monotonic() < deadline:
                for key, _ in selector.select(min(.05, max(0, deadline-time.monotonic()))):
                    try:
                        chunk = os.read(key.fd, 65536)
                    except BlockingIOError:
                        continue
                    except OSError:
                        failed = True
                        selector.unregister(key.fileobj)
                        continue
                    if chunk:
                        discarded += len(chunk)
                    else:
                        selector.unregister(key.fileobj)
                proc.poll()  # reap the direct child before testing group absence
                try:
                    os.killpg(proc.pid, 0)
                    group_absent = False
                except ProcessLookupError:
                    group_absent = True
                except PermissionError:
                    group_absent = False
                if not selector.get_map() and proc.returncode is not None and group_absent:
                    if failed:
                        break
                    self.cleanup_discarded_bytes += discarded
                    return
            self.cleanup_discarded_bytes = None
            raise CaptureUncertain('Capture cleanup unresolved; inspect actual process handles')

        try:
            try:
                proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, start_new_session=True)
            except OSError as exc:
                state = 'launch-failed'
                result['error'] = str(exc)
                return finish()
            result['launched'] = True
            # Registration precedes the callback so callback failures can drain safely.
            for stream, label in ((proc.stdout, 'stdout'), (proc.stderr, 'stderr')):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, label)
            on_start(proc)
            deadline = time.monotonic() + timeout
            while selector.get_map() or proc.poll() is None:
                if time.monotonic() >= deadline:
                    state = 'timeout'
                    result['error'] = 'timeout; process group terminated'
                    break
                for key, _ in selector.select(min(.05, max(0, deadline-time.monotonic()))):
                    try:
                        chunk = os.read(key.fd, 65536)
                    except BlockingIOError:
                        continue
                    except OSError as exc:
                        state = 'capture-failed'
                        result['error'] = str(exc)
                        break
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    observed[key.data] += len(chunk)
                    self.observed_bytes += len(chunk)
                    fitting = min(len(chunk), self.max_bytes-self.retained_bytes)
                    buffers[key.data].extend(chunk[:fitting])
                    self.retained_bytes += fitting
                    if fitting < len(chunk):
                        state = 'limit-exceeded'
                        result['error'] = 'capture byte limit exceeded; process group terminated'
                        break
                if state != 'complete':
                    break
            if state != 'complete':
                self.aborted, self.abort_state = True, state
            # Even a normally exiting parent may leave same-group descendants.
            drain_cleanup()
            result['exit_code'] = proc.returncode
            return finish()
        except CaptureUncertain:
            self.aborted = True
            self.abort_state = self.abort_state or 'capture-failed'
            raise
        except BaseException:
            if proc is not None:
                self.aborted = True
                self.abort_state = self.abort_state or 'capture-failed'
                drain_cleanup()
            raise
        finally:
            selector.close()
            if proc is not None:
                for stream in (proc.stdout, proc.stderr):
                    if stream is not None:
                        stream.close()
