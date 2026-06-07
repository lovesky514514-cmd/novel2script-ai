# Backend Quality Guard Final Update

Generated: 2026-06-07 13:44:48

## Summary

This final submission version synchronizes the online demo behavior with the GitHub codebase.

The backend quality guard was strengthened to improve product-level script generation quality:

- Prevent scene action leakage across different locations.
- Rebuild scene actions from scene-level facts instead of inheriting parent scene text.
- Preserve off-stage sources such as SMS, recordings, letters, notes, and screen text.
- Prevent recording content from being assigned to on-stage characters.
- Keep father-recording / SMS / note content as source text when appropriate.
- Clean debug-like notes from final output.

## Updated files

```text
backend/app/services/final_result_guard.py
backend/app/services/character_guard.py
```

## Demo result check

The final online generation for `雨夜的信` now shows:

- SMS content as `短信内容`.
- Recording content as `父亲录音`.
- The meeting room scene no longer includes old-building actions.
- The home key-search scene no longer includes warehouse or recording actions.
- The project manager line is assigned to `项目经理`.

## Online demo

```text
https://n2s.cc.cd
```
