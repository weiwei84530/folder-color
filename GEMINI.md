# GEMINI.md - AI Context & Operational Protocol

This repository is governed by the architecture, conventions, and engineering standards defined in [AGENT.md](./AGENT.md).

---

## 1. Primary Reference

For comprehensive technical context, module responsibilities, Win32 API contracts, and development workflows, refer directly to:
- **Architecture & System Guide**: [AGENT.md](./AGENT.md)
- **User Documentation (English)**: [README.md](./README.md)
- **User Documentation (Traditional Chinese)**: [README.zh-TW.md](./README.zh-TW.md)

---

## 2. Operational Invariants for AI Coding

When implementing new features, fixing issues, or refactoring in this repository:

1. **Language Standard**:
   All new code, comments, docstrings, function signatures, and CLI messages must be strictly written in **English**.
2. **Win32 Shell Standards**:
   - Always retain the dual notification broadcast (`SHCNE_UPDATEITEM` + `SHCNE_ASSOCCHANGED`) in `core.py` upon any folder state changes.
   - Maintain zero-privilege operation under `HKEY_CURRENT_USER`; do not require administrative elevation.
3. **Color Algorithm Integrity**:
   - Do not replace HLS luminance mapping with simple color overlays or opacity blending. Visual depth, high-contrast edge strips, and shadows must be preserved.
4. **Verification Requirement**:
   - Validate any Python changes using `python -m py_compile <file.py>` and verify CLI commands (`python cli.py list`, `python cli.py --help`) before committing.
