"""Shared experiment admission uses real file locks and separate processes."""

import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import queue
import tempfile
import time
import unittest
from unittest.mock import patch


def scopes(account='one', transport='subscription'):
    return {role: hashlib.sha256((transport + '\0' + value).encode()).hexdigest()
            for role, value in [('account', account), ('transport', transport)]}


def failure(status=429, proxy=None, retry_after=None):
    metadata = {'http_status': status}
    if proxy is not None:
        metadata['proxy_status'] = proxy
    if retry_after is not None:
        metadata['retry_after'] = retry_after
    return {'exit_code': 1, 'model_result': {
        'provider': 'openai-codex', 'stop_reason': 'error',
        'error': 'failed', 'response_metadata': metadata}}


SUCCESS = {'exit_code': 0, 'model_result': {
    'provider': 'openai-codex', 'stop_reason': 'stop',
    'response_metadata': {'http_status': 200, 'terminal_event': 'response.completed'}}}


def acquire_and_hold(directory, selected, output, release):
    from sse_multivector.provider_backoff import SharedProviderBackoff
    gate = SharedProviderBackoff(Path(directory))
    admitted = gate.acquire(selected, concurrency=32, timeout_seconds=10, owner_pid=os.getpid())
    output.put((admitted, time.monotonic()))
    release.wait(10)


class SharedProviderBackoffTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name) / 'backoff'

    def gate(self):
        from sse_multivector.provider_backoff import SharedProviderBackoff
        return SharedProviderBackoff(self.directory)

    def claim(self, gate, selected=None, concurrency=32):
        return gate.try_acquire(selected or scopes(), concurrency=concurrency,
                                timeout_seconds=300, owner_pid=os.getpid())

    def test_separate_processes_share_cooldown_and_admit_one_recovery_request(self):
        gate = self.gate()
        first = self.claim(gate)
        rejected_at = time.monotonic()
        gate.report(first['ticket'], failure())
        context = multiprocessing.get_context('spawn')
        output = context.Queue()
        release = context.Event()
        workers = [context.Process(target=acquire_and_hold,
                   args=(str(self.directory), scopes(), output, release)) for _ in range(2)]
        for worker in workers:
            worker.start()
        try:
            admitted, started = output.get(timeout=5)
            self.assertGreaterEqual(started - rejected_at, 1.9)
            with self.assertRaises(queue.Empty):
                output.get(timeout=0.2)
            gate.report(admitted['ticket'], SUCCESS)
            second, _ = output.get(timeout=3)
            gate.report(second['ticket'], SUCCESS)
        finally:
            release.set()
            for worker in workers:
                worker.join(5)
                if worker.is_alive():
                    worker.terminate()
                    worker.join(5)
                self.assertEqual(worker.exitcode, 0)
            output.close()

    def test_old_failures_share_wait_and_old_success_cannot_clear_it(self):
        gate = self.gate()
        clock = [time.monotonic()]
        with patch('sse_multivector.provider_backoff.time.monotonic', side_effect=lambda: clock[0]):
            first, second, old_success = [self.claim(gate) for _ in range(3)]
            gate.report(first['ticket'], failure())
            gate.report(second['ticket'], failure())
            gate.report(old_success['ticket'], SUCCESS)
            self.assertEqual(self.claim(gate)['wait_seconds'], 2.0)
            clock[0] += 2
            recovery = self.claim(gate)
            self.assertIn('ticket', recovery)
            self.assertGreater(self.claim(gate)['wait_seconds'], 0)
            gate.report(recovery['ticket'], failure())
            self.assertEqual(self.claim(gate)['wait_seconds'], 4.0)

    def test_account_failure_preserves_other_accounts_but_goaway_covers_transport(self):
        gate = self.gate()
        first = self.claim(gate, scopes('one'))
        gate.report(first['ticket'], failure())
        self.assertIn('ticket', other := self.claim(gate, scopes('two')))
        gate.report(other['ticket'], failure(200, proxy={
            'state': 'unknown', 'error_phase': 'body', 'read_error_kind': 'http2_goaway',
            'read_error_code': 'enhance_your_calm', 'request_context': 'active'}))
        self.assertNotIn('ticket', self.claim(gate, scopes('one')))
        self.assertNotIn('ticket', self.claim(gate, scopes('two')))
        unrelated = self.claim(gate, scopes('one', 'another-provider'))
        self.assertIn('ticket', unrelated)
        gate.report(unrelated['ticket'], SUCCESS)

    def test_exponential_cap_long_retry_after_and_gradual_recovery(self):
        gate = self.gate()
        clock = [time.monotonic()]
        with patch('sse_multivector.provider_backoff.time.monotonic', side_effect=lambda: clock[0]):
            for expected in (2, 4, 8, 16, 32, 60, 60):
                admitted = self.claim(gate, concurrency=4)
                gate.report(admitted['ticket'], failure())
                self.assertEqual(self.claim(gate, concurrency=4)['wait_seconds'], expected)
                clock[0] += expected
            admitted = self.claim(gate, concurrency=4)
            gate.report(admitted['ticket'], failure(retry_after='90'))
            self.assertEqual(self.claim(gate, concurrency=4)['wait_seconds'], 90)
            clock[0] += 90
            for limit in (1, 2, 4):
                cohort = [self.claim(gate, concurrency=4) for _ in range(limit)]
                self.assertTrue(all('ticket' in member for member in cohort))
                self.assertNotIn('ticket', self.claim(gate, concurrency=4))
                for member in cohort:
                    gate.report(member['ticket'], SUCCESS)
            admitted = self.claim(gate, concurrency=4)
            gate.report(admitted['ticket'], failure())
            self.assertEqual(self.claim(gate)['wait_seconds'], 2)

    def test_dead_process_does_not_hold_the_recovery_slot(self):
        gate = self.gate()
        clock = [time.monotonic()]
        with patch('sse_multivector.provider_backoff.time.monotonic', side_effect=lambda: clock[0]):
            first = self.claim(gate)
            gate.report(first['ticket'], failure())
            clock[0] += 2
            process = multiprocessing.get_context('spawn').Process(target=time.sleep, args=(10,))
            process.start()
            try:
                admitted = gate.try_acquire(scopes(), concurrency=32, timeout_seconds=300,
                                            owner_pid=process.pid)
                self.assertIn('ticket', admitted)
                self.assertNotIn('ticket', self.claim(gate))
            finally:
                process.terminate()
                process.join(5)
            self.assertIn('ticket', self.claim(gate))

    def test_later_smaller_experiment_recovers_to_its_current_concurrency(self):
        gate = self.gate()
        clock = [time.monotonic()]
        with patch('sse_multivector.provider_backoff.time.monotonic', side_effect=lambda: clock[0]):
            previous = self.claim(gate, concurrency=32)
            gate.report(previous['ticket'], SUCCESS)
            current = self.claim(gate, concurrency=4)
            gate.report(current['ticket'], failure())
            clock[0] += 2
            for limit in (1, 2, 4):
                cohort = [self.claim(gate, concurrency=4) for _ in range(limit)]
                for member in cohort:
                    gate.report(member['ticket'], SUCCESS)
            current = self.claim(gate, concurrency=4)
            gate.report(current['ticket'], failure())
            self.assertEqual(self.claim(gate, concurrency=4)['wait_seconds'], 2)

    def test_local_abort_and_completed_stream_cancellation_do_not_cool_down(self):
        gate = self.gate()
        for metadata in ({'http_status': 429, 'abort_reason': {'name': 'TimeoutError'}},
                         {'http_status': 200, 'terminal_event': 'response.completed',
                          'proxy_status': {'state': 'complete', 'request_context': 'canceled',
                                           'read_error_kind': 'context_canceled'}}):
            admitted = self.claim(gate)
            gate.report(admitted['ticket'], {'exit_code': 1, 'model_result': {
                'stop_reason': 'error', 'response_metadata': metadata}})
            self.assertIn('ticket', next_admission := self.claim(gate))
            gate.report(next_admission['ticket'], SUCCESS)

    def test_corrupt_state_fails_closed_before_admission(self):
        gate = self.gate()
        admitted = self.claim(gate)
        gate.report(admitted['ticket'], SUCCESS)
        (self.directory / 'state.json').write_text('{broken')
        with self.assertRaises(ValueError):
            self.claim(gate)


if __name__ == '__main__':
    unittest.main()
