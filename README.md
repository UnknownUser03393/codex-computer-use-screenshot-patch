# Codex Computer Use Screenshot Patch

Experimental, exact-binary patch for Windows 10 x64 and `@oai/sky 0.7.18`.

The patch addresses two observed problems:
- Screenshot capture times out while a capture callback holds a Direct3D critical section and waits for an asynchronous operation.
- Window screenshots include an overlapping foreground application because the capture path uses a monitor region.

The first stage adapts the community MTA-worker workaround. The second stage changes this binary's capture path to `CreateForWindow`, uses HWND as the capture/cache key, and resets the crop origin.

This repository contains binary adaptation scripts, not OpenAI's original native helper source. It is not an official OpenAI fix.

## Exact supported binary

| File | SHA-256 |
| --- | --- |
| Original helper | `F8AD259CAA82BC2A62C26CB1A3428E558D26959DE7B4D5BCE0D708F5C40E81D9` |
| MTA-worker candidate | `7BCF0B19481A96F478760A345B389AE47C44D6E2A6F745B331B9043CD9F7E804` |
| Window-capture candidate | `23F26A8950FFBBF8B6873467761DC45F56DE0BA175A2CE702632FEA9B209FC7B` |

A matching Sky version alone is insufficient. Both builders guard their exact input hash. Do not run Python with `-O`, which disables their assertions.

## Build

Requires Python, `pefile`, and `capstone` on Windows x64.

1. Preserve the original helper. Place a copy beside the scripts named `codex-computer-use-0.7.18.original.exe`.
2. Obtain the upstream [community patcher](https://github.com/chen0416ccc-cpu/codex-windows-fast-patch-skill/blob/main/scripts/patch-computer-use-helper-win10.ps1), saved beside the builders as `community-patcher.ps1`. The builder uses its `0.7.17 helper 7F73CF56` profile as a template. Do not run that upstream installer for this custom binary.
3. Run:

```powershell
py -3 -m pip install -r requirements.txt
py -3 build_candidate.py
py -3 build_window_candidate.py
```

The scripts only write candidate files beside themselves; installation and process restarts are not automated. Preserve the signed original and any previous working candidate before a manual replacement. Binary modification invalidates the original Authenticode signature. Updates can replace the runtime and require fresh analysis.

## Window-capture changes

| RVA | Change |
| --- | --- |
| `0x3D9EC` | Redirect to the private stub. |
| `0x17C0D0` | Read original HWND, use it as cache/capture key, zero crop coordinates, return to `0x3D9F5`. |
| `0x3DE1E` | Interop method slot `0x20` to `0x18`: `CreateForMonitor` to `CreateForWindow`. |

## Validation and limits

On one Windows 10 22H2 build 19045.6466 machine, the final candidate returned the occluded CLion window through the normal Sky interface in two successive captures.

The upstream [unwind test](https://github.com/chen0416ccc-cpu/codex-windows-fast-patch-skill/blob/main/scripts/test-computer-use-helper-win10-unwind.py), locally adapted with the final candidate hash and profile `(0x17c000, 0x8490, 0x42544)`, passed 47 instruction boundaries and four mocked paths (thread creation success, creation failure, busy callback, worker). This validates the MTA wrapper's tested behavior, not all window-capture changes.

Menus, coordinate input, multiple monitors, DPI changes, resizing, minimized windows, and long-running stability have not been comprehensively validated. The current evidence supports the callback/Direct3D waiting explanation but does not independently trace every object in the full asynchronous dependency cycle.

## Attribution

MTA-wrapper bytes and the adaptation approach derive from the community project [codex-windows-fast-patch-skill](https://github.com/chen0416ccc-cpu/codex-windows-fast-patch-skill). Upstream files are referenced rather than redistributed here. No license is asserted over upstream material or OpenAI binaries. No executables, credentials, private logs, or screenshots are included in this repository.
