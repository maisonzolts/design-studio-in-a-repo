# Health data template

This directory contains schema examples only. It intentionally contains no personal measurements, meals, workouts, photos, device exports, transcripts, or history.

For real use:

1. Copy `profile.example.md` and the directory structure to a private repository.
2. Point the health-coach skill and API at that private path.
3. Add catalog entries only with an allowed source. Set `sex` to `female` or `male`; target math uses Mifflin-St Jeor and does not assume a sex.
4. Run `python scripts/health_validate.py --health-dir <PRIVATE_HEALTH_DIR>` before quoting or logging any nutrition number.
5. Never commit the private health tree to this public repository.
