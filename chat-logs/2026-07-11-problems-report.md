# Chat Log: 2026-07-11 — Problems & Solutions Report

## Session Overview
Built two alternative tech stacks for instrument-designer: Option B (Pure Web) and Option A (Tauri Desktop). Both committed locally, push blocked by git auth.

---

## Problems Encountered

### 1. TypeScript Type Errors — Missing `source_url` Property
- **Error**: `Property 'source_url' is missing in type` (42 instruments)
- **Cause**: `Instrument` interface required `source_url: string` but many instruments didn't have one
- **Fix**: Made `source_url` and `demakein_preset` optional (`source_url?: string`)
- **File**: `web/src/data/instruments.ts`

### 2. TypeScript Error — Async Return Type
- **Error**: `The return type of an async function or must be Promise<T>`
- **Cause**: `getDesignDownloadUrl` was marked `async` but just returned a string
- **Fix**: Removed `async` keyword, changed return type to `string`
- **File**: `web/src/utils/api.ts`

### 3. TypeScript Error — Unused Variable
- **Error**: `'preset' is declared but its value is never read`
- **Cause**: `handleGenerateFromLibrary` parameter named `preset` but unused
- **Fix**: Renamed to `_preset` (underscore prefix convention)
- **File**: `web/src/App.tsx`

### 4. JSCAD API — Wrong Method Names
- **Error**: `Property 'subtract' does not exist on type 'transforms'`
- **Cause**: `subtract()` is in `booleans` module, not `transforms`
- **Fix**: Changed to `const { subtract } = booleans;`
- **File**: `web/src/components/ParametricGenerator.tsx`

### 5. JSCAD STL Serialization — Package Doesn't Exist
- **Error**: `@jscad/stl-serialization` not found on npm
- **Cause**: JSCAD v2 removed built-in STL serialization from `@jscad/modeling`; the separate package doesn't exist
- **Fix**: Wrote custom `geometryToSTL()` function that manually builds binary STL from JSCAD geometry data (positions + triangles → DataView binary buffer)
- **File**: `web/src/components/ParametricGenerator.tsx`

### 6. Three.js STLExporter — Invalid Import from drei
- **Error**: `Module '"@react-three/drei"' has no exported member 'STLExporter'`
- **Cause**: `STLExporter` was removed from drei in recent versions
- **Fix**: Removed the import and the `exportSTL` helper function entirely (not needed — STL generation handled by JSCAD side)
- **File**: `web/src/components/STLViewer.tsx`

### 7. Three.js STLLoader — Static vs Dynamic Import
- **Error**: Initially tried dynamic `import("three/addons/loaders/STLLoader.js")` inside async function
- **Fix**: Changed to static import at top of file: `import { STLLoader } from "three/addons/loaders/STLLoader.js"`
- **File**: `web/src/components/STLViewer.tsx`

### 8. Rust Build — Missing MSVC Linker
- **Error**: `linker 'link.exe' not found; msvc targets depend on msvc linker`
- **Cause**: Rust toolchain installed but Visual Studio Build Tools not configured for cargo
- **Fix**: Installed `Microsoft.VisualStudio.2022.BuildTools` via winget; ran cargo with `vcvarsall.bat x64` environment
- **Command**: `cmd /c "call vcvarsall.bat x64 && set PATH=%USERPROFILE%\.cargo\bin;%PATH% && cargo check"`

### 9. Rust Build — `#[command]` vs `use tauri::command` Conflict
- **Error**: `the name '__cmd__demakein_design' is defined multiple times` (22 errors)
- **Cause**: Had both `use tauri::command;` import AND `#[command]` attribute, which expanded to the same macros twice
- **Fix**: Removed `use tauri::command;` import, changed all `#[command]` to `#[tauri::command]`
- **File**: `web/src-tauri/src/lib.rs`

### 10. Rust Build — Triple Compilation from Multiple crate-types
- **Error**: Same "defined multiple times" errors persisted even after fixing the import
- **Cause**: `crate-type = ["staticlib", "cdylib", "rlib"]` compiles the lib 3 times, and `#[tauri::command]` macros expand each time, causing 3 definitions of each macro
- **Fix**: Moved all command functions to a separate `commands.rs` module, kept only `mod commands; use commands::*;` in `lib.rs`
- **File**: `web/src-tauri/src/commands.rs`, `web/src-tauri/src/lib.rs`

### 11. Git Push — Authentication Timeout
- **Error**: `git push origin option-b-web-app` timed out after 60s
- **Cause**: No git credentials configured for HTTPS push to GitHub
- **Status**: Not resolved — requires manual authentication (GitHub CLI `gh auth login`, or SSH key setup)
- **Workaround**: Commits are local; manual push needed

### 12. npm.ps1 Blocked by PowerShell Execution Policy
- **Error**: PowerShell blocks `npm.ps1` script
- **Cause**: Default execution policy prevents running .ps1 scripts
- **Fix**: Always use `npm.cmd` instead of `npm.ps1`, or refresh PATH with `[System.Environment]::GetEnvironmentVariable("Path","Machine")`

### 13. Node.js/npm Not in PATH After Install
- **Error**: `npm` not recognized after `winget install OpenJS.NodeJS.LTS`
- **Cause**: New installs don't update current shell PATH
- **Fix**: Refresh PATH manually: `$env:PATH = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")`

---

## Build Status Summary

| Branch | Frontend Build | Backend Build | Status |
|--------|---------------|---------------|--------|
| `option-b-web-app` | ✅ TypeScript + Vite | N/A (browser only) | Committed locally |
| `option-a-tauri` | ✅ TypeScript + Vite | ✅ Rust cargo check | Committed locally |
| `main` | ✅ (original Python) | N/A | Original codebase |

## Key Files Modified
- `web/src/data/instruments.ts` — 42 instruments ported from Python
- `web/src/components/ParametricGenerator.tsx` — custom STL serializer
- `web/src-tauri/src/commands.rs` — all Rust backend commands
- `web/src-tauri/src/lib.rs` — Tauri app setup
- `web/src-tauri/Cargo.toml` — Tauri + plugin dependencies
