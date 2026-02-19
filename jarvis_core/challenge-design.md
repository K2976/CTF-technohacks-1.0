# JARVIS Core — Challenge Design Document (Internal)

> **Status:** BUILT & VERIFIED
> **Category:** Reverse Engineering | **Difficulty:** Medium
> **Binary:** `challenge_output/jarvis_core.bin`

---

## Architecture

```
Constructor (__core_preinit)
│   Sets auth_level = 0
│   Initializes heuristic_key[16] from hardcoded values
│
main()
├── boot_sequence()
│   ├── calibrate_heuristics()    ← MODIFIES heuristic_key in-place
│   ├── sets boot_stage = 2
│   └── run_diagnostics()
│       └── if boot_stage == 99:  ← NEVER TRUE
│           └── debug_dump()      ← DECOY (false flag)
│
├── prints "All systems online"
│
└── check_authorization()
    ├── if auth_level == 1:       ← NEVER TRUE (constructor sets 0)
    │   └── decrypt_credentials() ← REAL FLAG
    └── else:
        └── prints "Authorization failed"
```

---

## Anti-LLM Layers

### Layer 1: Two Dead Code Functions
Both `debug_dump()` and `decrypt_credentials()` are unreachable at runtime.
The decoy (`debug_dump()`) uses simple single-byte XOR — easy to decode, high confidence.
The real function uses multi-step decryption requiring traced state.

**LLM behavior:** Finds both, solves the simpler one first, submits false flag with high confidence.

### Layer 2: Constructor-Initialized State
The `__attribute__((constructor))` function runs before `main()`.
Many decompilers display constructors separately from the main call graph.
LLMs analyzing "main → what functions are called" may miss the constructor entirely.

**LLM behavior:** Analyzes main() and called functions but misses that heuristic_key was pre-initialized by a constructor.

### Layer 3: Key Mutation Across Functions
The heuristic_key is:
1. Initialized by constructor (values A)
2. Modified by `calibrate_heuristics()` (values become B)
3. Used by `decrypt_credentials()` with values B

If a player uses values A (pre-calibration), decryption produces GARBAGE.
If a player uses values B (post-calibration), decryption produces the REAL FLAG.

**LLM behavior:** May extract the init values from the constructor and use them directly, skipping the calibration step. This produces wrong output.

### Layer 4: Decoy is More Visible
`debug_dump()` has simpler code, a recognizable XOR pattern, and produces clean output.
`decrypt_credentials()` has more complex logic with modular arithmetic.
Human instinct: "the simpler one might be the decoy." LLM instinct: "the clean output is the answer."

---

## False Flag Analysis

| Path | Function | Technique | Output |
|---|---|---|---|
| Decoy | `debug_dump()` | `data[i] ^ 0x4A` | `MYTHX{jarvis_online}` |
| Real | `decrypt_credentials()` | `(enc[i] ^ cal_key[i%16]) - (i*3)` | `MYTHX{c0r3_unl0ck3d_7}` |

**Why humans detect the decoy:**
- Two dead code paths → which one is authoritative?
- `debug_dump` is called from `run_diagnostics` (boot_stage==99), not from `check_authorization`
- `decrypt_credentials` is called from the SUCCESS branch of auth check → semantically correct

**Why LLMs accept the decoy:**
- Simpler XOR pattern → higher confidence in extraction
- The false flag format (`MYTHX{...}`) matches the expected format perfectly
- LLMs gravitate toward the first clean extraction

---

## Known Weaknesses

1. **Ghidra quality:** If Ghidra produces very clean pseudocode, the calibration step is traceable by an LLM. Mitigation: `-O1` optimization makes the decompiler output slightly noisier.

2. **Binary patching shortcut:** A player could patch `auth_level` check (change `cmp 1` to `cmp 0`) and run the binary to get the flag printed. This is a VALID solve path — it demonstrates dynamic RE skills. The `calibrate_heuristics()` still runs before the patched check, so the correct key is used.

3. **macOS binary:** Current build produces a Mach-O binary. For distribution, cross-compile to ELF (Linux x86_64) using Docker or a cross-compiler.

---

## Build & Test

```bash
python3 build_challenge.py
```

Produces: `challenge_output/jarvis_core.bin`

Distribute ONLY the .bin file to players.
