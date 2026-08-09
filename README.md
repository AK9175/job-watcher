# Job Watcher

Watches Google Careers reqs for the closed → open transition and pushes a
notification via [ntfy.sh](https://ntfy.sh) when one opens. `state.json`
tracks last-known status per URL so notifications fire only on the
transition, not on every run.

## Local usage

```bash
./.venv/bin/python main.py [--dry-run] [--reset] [--verbose] [--test-notify]
```

- `--dry-run` — check and print, don't write `state.json` or notify.
- `--reset` — clear `state.json` (re-triggers the open transition).
- `--verbose` — log HTTP status, response size, and the matched snippet.
- `--test-notify` — send canned OPEN/CLOSED test notifications and exit,
  without touching `jobs.json` or `state.json`.

`NTFY_TOPIC` selects the notification backend: unset falls back to printing
to stdout; set it to post to `https://ntfy.sh/<topic>`.

## Deployment (GitHub Actions)

1. Create a **private** GitHub repo — `state.json` and the watched job URLs
   don't need to be public.
2. Install the ntfy app and subscribe to an unguessable topic (e.g.
   `arpit-goog-req-x7k2q9f4` — ntfy topics are readable by anyone who
   guesses the name, so avoid anything obvious).
3. In the repo: **Settings → Secrets and variables → Actions → New
   repository secret**, named exactly `NTFY_TOPIC`, value = your topic
   string.
4. Push, then **Actions tab → Job Watcher → Run workflow** to trigger it by
   hand and confirm the whole chain works before relying on the schedule.
5. The **CANARY - Content Safety** job should report `OPEN` on every run —
   it's a permanent health check. If it ever reports `closed`, check the
   page in a browser before assuming the req actually closed; it may mean
   the detector broke (Google changed their markup).
6. GitHub disables scheduled workflows after 60 days of repo inactivity.
   The workflow's keepalive step handles this automatically by committing a
   `.heartbeat` file whenever the last commit is more than ~5 days old — no
   action needed on your part. Heartbeat commits are kept separate from
   state-change commits so you can tell them apart at a glance.
