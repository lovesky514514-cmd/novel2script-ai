# Novel2Script AI Final Submission Notes

Generated: 2026-06-07 13:44:48

## Branch suggestion

```text
docs/qiniu-submission
```

## Online demo

```text
https://n2s.cc.cd
```

## Main final changes included in this package

```text
backend/app/services/final_result_guard.py
backend/app/services/character_guard.py
docs/patches/
docs/submission/quality_guard_final_update.md
docs/demo_samples/
```

## Suggested commit

```text
fix: improve scene and dialogue quality guard
```

Description:

```text
Strengthen scene-level fact binding, prevent action leakage across locations, and preserve off-stage sources such as SMS, recordings, and letters.
```

## Do not upload runtime secrets

This package excludes `.git`, virtual environments, node_modules, dist builds, and real `.env` files.
