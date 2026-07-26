# Disk I/O Pressure-Control Guidance

## Purpose

Use this guidance for sustained disk-reading or disk-writing work that could
make the host unresponsive. The concern is I/O stall pressure, not free disk
space.

The controller is a cooperative brake. It pauses new work before the storage
path becomes unsafe while allowing work already accepted by the storage system
to finish.

## Pressure Signal

Run the workload in its own cgroup v2 and monitor that cgroup's
`io.pressure`. Do not use system-wide pressure as the automatic control signal.

Every 250 milliseconds:

1. Read the `some total=` counter.
2. Keep a rolling two-second observation window.
3. Calculate:

   ```text
   pressure percent =
       100 × change in some total microseconds / elapsed microseconds
   ```

`some` measures time during which at least one non-idle task in the workload
cgroup was stalled on I/O. Use the cumulative counter rather than `avg10`,
which reacts too slowly for this controller.

Before normal admission begins, observe pressure for two seconds. Input may be
prefetched only into a strictly bounded memory buffer during this period; no
disk work may be admitted.

## Backoff Signals

Pause new disk work when either condition occurs:

- cgroup `some` pressure is at least 20%; or
- the storage API explicitly refuses new work, such as NostrDB returning
  `NoteProcessFailed`.

High pressure is not proof that the device has failed. It is sufficient reason
to stop adding work. Durable progress determines whether the system is merely
saturated or has become stuck.

The following remain diagnostics and are not additional automatic pause
thresholds:

- global `/proc/pressure/io`;
- cgroup `io.stat`;
- block-device completion and in-flight counters;
- application progress counters such as missing IDs.

These signals help explain an incident. They must not allow unrelated host
activity to override the workload's own pressure signal.

## Behavior While Paused

When backoff begins:

1. Stop reading or creating additional input.
2. Stop before the next storage-admission call, including retries of a rejected
   call.
3. Retain unsubmitted work in a bounded memory buffer.
4. Allow only work already accepted by the storage system to finish.
5. Continue observing durable progress.

Do not force a partial batch into storage. That adds work at the moment the
controller is trying to reduce it.

Do not suspend the whole process with `SIGSTOP`. That would also freeze the
writer or commit which must drain.

For an offline pipeline, an admission boundary must exist between bounded
read/write chunks. Pressure cannot safely stop one indivisible operation after
it has begun.

## Recovery

Resume normal admission only after:

- cgroup `some` pressure stays below 5% continuously for ten seconds; and
- work accepted by the storage system makes durable progress.

If no accepted work remains to demonstrate progress, admit exactly one bounded
probe after the cooldown. Resume only if that probe becomes durable. A rejected
or unusable probe begins another cooldown; it must not authorize another probe
immediately.

This hysteresis prevents rapid pause/resume oscillation.

## Fail-Closed Conditions

End the run safely when pressure remains paused for 60 seconds without durable
progress. Do not reopen or scan the large artifact while handling this failure.

Also fail closed when the pressure source cannot be read after three attempts
spaced ten milliseconds apart. If the cumulative pressure counter decreases,
treat it as a counter or cgroup reset: discard the current window and repeat
the initial observation instead of interpreting it as low pressure.

The pressure monitor stopping or panicking unexpectedly is also a terminal
failure.

## Interpretation

Use pressure and progress together:

- high pressure with durable completions means the storage path is saturated
  but alive;
- high pressure without durable progress means it may be stuck and must reach
  the fail-closed deadline.

The automatic controller deliberately uses only the workload cgroup's
`io.pressure some` value and concrete storage-admission failures to enter
backoff. Device and host counters are supporting evidence.

This policy was exercised under real contention: workload pressure reached
22.5%, admission paused, accepted work drained, and normal admission resumed
after approximately twelve seconds of low pressure.

## Provenance

This guidance records the investigation's conclusion. The reference implementation is
commit `aca6142` in `oracle-mvp-fresh-corpus-infra`.
