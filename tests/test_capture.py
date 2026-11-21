import base64
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tequio.capture import CaptureBudget, CaptureUncertain


class CaptureTests(unittest.TestCase):
    def run_python(self, budget, code, timeout=3, index=1, callback=lambda proc: None):
        return budget.run_check([sys.executable, '-c', code], Path.cwd(), timeout, index, callback)

    def test_exact_and_excess(self):
        for count, state in ((10, 'complete'), (11, 'limit-exceeded')):
            with self.subTest(count=count):
                budget = CaptureBudget(10)
                result = self.run_python(budget, f'import os; os.write(1,b"x"*{count})')
                self.assertEqual(result['capture']['state'], state)
                self.assertEqual(base64.b64decode(result['capture']['stdout_base64']), b'x'*10)
                self.assertEqual(budget.retained_bytes, 10)
                self.assertEqual(budget.aborted, count == 11)

    def test_attempt_wide_many_checks(self):
        budget = CaptureBudget(10)
        for index in range(1, 12):
            result = self.run_python(budget, 'print("x",end="")', index=index)
        self.assertEqual(result['check'], 11)
        self.assertEqual(result['capture']['state'], 'limit-exceeded')
        self.assertEqual(budget.retained_bytes, 10)
        self.assertEqual(budget.observed_bytes, 11)
        with self.assertRaisesRegex(Exception, 'already aborted'):
            self.run_python(budget, '')

    def test_both_pipes_pressure_and_bound(self):
        budget = CaptureBudget(4000)
        result = self.run_python(budget, 'import os\nfor i in range(100):\n os.write(1,b"a"*4096); os.write(2,b"b"*4096)')
        self.assertEqual(result['capture']['state'], 'limit-exceeded')
        self.assertEqual(budget.retained_bytes, 4000)
        self.assertLessEqual(budget.observed_bytes, 4000+65536)
        self.assertIsInstance(budget.cleanup_discarded_bytes, int)

    def test_raw_invalid_utf8_and_boundary(self):
        budget = CaptureBudget(3)
        result = self.run_python(budget, 'import os; os.write(1,b"\\xff\\xe2\\x82\\xac")')
        self.assertEqual(base64.b64decode(result['capture']['stdout_base64']), b'\xff\xe2\x82')
        self.assertEqual(result['stdout'], '\ufffd\ufffd')
        self.assertFalse(result['capture']['complete'])

    def test_timeout_retains_prefix(self):
        budget = CaptureBudget(100)
        result = self.run_python(budget, 'import os,time; os.write(2,b"diagnostic"); time.sleep(5)', .1)
        self.assertEqual(result['stderr'], 'diagnostic')
        self.assertEqual(result['capture']['state'], 'timeout')
        self.assertTrue(budget.aborted)

    def test_launch_failure_does_not_abort(self):
        budget = CaptureBudget(10)
        result = budget.run_check(['/definitely/no/such/check'], Path.cwd(), 1, 1, lambda p: None)
        self.assertFalse(result['launched'])
        self.assertIsNone(result['exit_code'])
        self.assertEqual(result['capture']['state'], 'launch-failed')
        self.assertFalse(budget.aborted)
        self.assertTrue(self.run_python(budget, '', index=2)['capture']['complete'])

    def test_callback_failure_cleans_and_propagates(self):
        pids = []
        def callback(proc):
            pids.append(proc.pid)
            raise RuntimeError('durability failed')
        with self.assertRaisesRegex(RuntimeError, 'durability failed'):
            self.run_python(CaptureBudget(10), 'import time; time.sleep(5)', callback=callback)
        with self.assertRaises(ProcessLookupError):
            os.killpg(pids[0], 0)

    def test_read_failure_is_terminal(self):
        real_read = os.read
        failed = False
        def read(fd, count):
            nonlocal failed
            # Popen uses a separate large read for its launch error pipe.
            if count == 65536 and not failed:
                failed = True
                raise OSError('controlled read fault')
            self.assertLessEqual(count, 65536)
            return real_read(fd, count)
        with patch('tequio.capture.os.read', side_effect=read):
            result = self.run_python(CaptureBudget(10), 'print("x")')
        self.assertEqual(result['capture']['state'], 'capture-failed')

    def test_unknown_group_is_uncertain(self):
        real_killpg = os.killpg
        def killpg(pid, sig):
            if sig == 0:
                raise PermissionError('controlled unknown')
            return real_killpg(pid, sig)
        budget = CaptureBudget(10)
        with patch('tequio.capture.os.killpg', side_effect=killpg):
            with self.assertRaises(CaptureUncertain):
                self.run_python(budget, '')
        self.assertIsNone(budget.cleanup_discarded_bytes)

    def test_exited_zero_still_fails_excess(self):
        result = self.run_python(CaptureBudget(1), 'print("xx",end="")',
                                 callback=lambda proc: proc.wait(timeout=2))
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual(result['capture']['state'], 'limit-exceeded')
        self.assertFalse(result['capture']['complete'])

    def test_nonzero_is_complete_and_allows_later_check(self):
        budget = CaptureBudget(10)
        result = self.run_python(budget, 'raise SystemExit(7)')
        self.assertEqual(result['exit_code'], 7)
        self.assertTrue(result['capture']['complete'])
        self.assertFalse(budget.aborted)
        self.assertTrue(self.run_python(budget, '', index=2)['capture']['complete'])

    def test_keyboard_interrupt_cleans_reaps_and_propagates(self):
        handles = []
        budget = CaptureBudget(10)
        def interrupted(proc):
            handles.append(proc)
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.run_python(budget, 'import time; time.sleep(20)', callback=interrupted)
        self.assertIsNotNone(handles[0].returncode)
        with self.assertRaises(ProcessLookupError):
            os.killpg(handles[0].pid, 0)
        self.assertTrue(budget.aborted)

    def test_same_group_descendant_cleanup_or_honest_uncertainty(self):
        handles = []
        with tempfile.TemporaryDirectory() as directory:
            identity = Path(directory) / 'child'
            code = ('import os,signal,time\n'
                    'signal.signal(signal.SIGCHLD,signal.SIG_IGN)\n'
                    'pid=os.fork()\n'
                    'if pid == 0:\n'
                    ' time.sleep(20)\n'
                    'else:\n'
                    f' open({str(identity)!r},"w").write(str(pid))\n'
                    ' time.sleep(20)\n')
            def started(proc):
                handles.append(proc)
                deadline = time.monotonic()+2
                while not identity.exists() and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertTrue(identity.exists())
            budget = CaptureBudget(100)
            try:
                try:
                    result = self.run_python(budget, code, timeout=.05, callback=started)
                except CaptureUncertain:
                    self.assertIsNone(budget.cleanup_discarded_bytes)
                else:
                    self.assertEqual(result['capture']['state'], 'timeout')
                    with self.assertRaises(ProcessLookupError):
                        os.killpg(handles[0].pid, 0)
                self.assertIsNotNone(handles[0].returncode)
                descendant = int(identity.read_text())
                # An orphan zombie may await host reaping: cessation is distinct
                # from process-table/group disappearance, hence honest uncertainty.
                observation = subprocess.run(['ps', '-o', 'stat=', '-p', str(descendant)],
                                             capture_output=True, text=True, check=False)
                self.assertTrue(not observation.stdout.strip() or
                                observation.stdout.strip().startswith('Z'), observation.stdout)
            finally:
                for proc in handles:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait(timeout=2)

    def test_retained_allocations_and_reads_stay_bounded(self):
        class TrackingBuffer(bytearray):
            instances = []
            def __init__(self):
                super().__init__()
                self.instances.append(self)
            def extend(self, chunk):
                super().extend(chunk)
                self_peak = sum(len(item) for item in self.instances)
                if self_peak > 100:
                    raise AssertionError('retained buffers exceeded aggregate budget')
        reads = []
        real_read = os.read
        def read(fd, count):
            reads.append(count)
            self.assertLessEqual(count, 65536)
            return real_read(fd, count)
        with patch('tequio.capture.bytearray', TrackingBuffer, create=True), \
             patch('tequio.capture.os.read', side_effect=read):
            result = self.run_python(CaptureBudget(100),
                                     'import os; os.write(1,b"x"*1000000)')
        self.assertEqual(len(TrackingBuffer.instances), 2)
        self.assertEqual(sum(map(len, TrackingBuffer.instances)), 100)
        self.assertEqual(result['capture']['state'], 'limit-exceeded')
        self.assertTrue(reads)

    def test_invalid_limits(self):
        for limit in (True, 0, 16777217, '10'):
            with self.assertRaises(Exception):
                CaptureBudget(limit)

if __name__=='__main__':unittest.main()
