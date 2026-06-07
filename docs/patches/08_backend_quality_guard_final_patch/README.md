# 08 Backend Quality Guard Final Patch

Generated: 2026-06-07 13:44:48

## Purpose

Final backend quality guard patch used by the online Novel2Script AI demo.

## Files

```text
backend/app/services/final_result_guard.py
backend/app/services/character_guard.py
```

## What it fixes

- Scene action leakage across locations.
- Dialogue speaker mismatch for off-stage sources.
- SMS/recording/letter/note/screen text being assigned to on-stage characters.
- Recording lines being assigned to the protagonist instead of `父亲录音` / `录音声`.

## Apply manually

Copy the two files in this patch folder to the same paths in the project, then restart the backend.
