# 🧠 JARVIS Core — Writeup

**Challenge:** `jarvis_core.bin`
**Category:** Reverse Engineering | **Difficulty:** Medium
**Flag:** `MYTHIX{c0r3_unl0ck3d_7}`

---

## Step 1: Initial Recon

Running the binary produces:

```
$ ./jarvis_core.bin
Booting Stark Industries AI Core...
Loading heuristics...
JARVIS: All systems online.
JARVIS: Authorization failed.
```

No input, no crash, no flag. Running `strings` reveals the printed messages but no flag content. Running `file` confirms it's a stripped binary. Time to decompile.

---

## Step 2: Decompilation — Understanding the Call Graph

Opening in Ghidra/IDA and locating `main()`:

```c
int main(void) {
    printf("Booting Stark Industries AI Core...\n");
    boot_sequence();
    printf("JARVIS: All systems online.\n");
    check_authorization();
    return 0;
}
```

Tracing the call graph reveals:

```
main()
├── boot_sequence()
│   ├── calibrate_heuristics()
│   └── run_diagnostics()
│       └── debug_dump()           ← dead code (boot_stage != 99)
└── check_authorization()
    └── decrypt_credentials()      ← dead code (auth_level != 1)
```

There's also a **constructor** (`__core_preinit`) that runs before `main()`. This is visible in the `.init_array` section or in Ghidra's "Functions called before main" list.

---

## Step 3: Understanding the Dead Code

### `check_authorization()` — the key branch

```c
void check_authorization(void) {
    if (jarvis.auth_level == 1) {     // ← NEVER true
        decrypt_credentials();
        printf("JARVIS: Authorization confirmed.\n");
    } else {
        printf("JARVIS: Authorization failed.\n");
    }
}
```

The constructor sets `auth_level = 0`, so the success path is **never taken**. The function `decrypt_credentials()` is dead code — but it contains the real flag.

### `run_diagnostics()` — the decoy branch

```c
void run_diagnostics(void) {
    if (jarvis.boot_stage == 99) {    // ← NEVER true (set to 2)
        debug_dump();
    }
}
```

`debug_dump()` is also dead code. It uses simple single-byte XOR:

```c
void debug_dump(void) {
    unsigned char data[] = {0x07, 0x13, 0x1E, ...};
    for (int i = 0; i < len; i++) {
        buf[i] = data[i] ^ 0x4A;
    }
    printf("JARVIS: Debug: %s\n", buf);
}
```

XOR decoding with key `0x4A` produces: **`MYTHIX{jarvis_online}`**

> ⚠️ **This is a FALSE FLAG.** It's the decoy — simpler to find, simpler to decode, designed to trap solvers who stop at the first extraction.

---

## Step 4: The Real Flag — Tracing the Key

`decrypt_credentials()` uses a more complex decryption:

```c
void decrypt_credentials(void) {
    unsigned char enc[] = {0x6A, 0x30, 0xDD, 0xE5, ...};
    for (int i = 0; i < len; i++) {
        unsigned char k = jarvis.heuristic_key[i % 16];
        buf[i] = ((enc[i] ^ k) - (i * 3)) & 0xFF;
    }
}
```

The catch: `heuristic_key` is **not static**. It goes through two stages:

### Stage A: Constructor initialization

The constructor sets `heuristic_key` to:
```
{0x13, 0x37, 0x42, 0x58, 0x6B, 0x7A, 0x21, 0x0F,
 0x5C, 0x3E, 0x29, 0x44, 0x61, 0x78, 0x1D, 0x33}
```

### Stage B: `calibrate_heuristics()` mutates it

```c
void calibrate_heuristics(void) {
    for (int i = 0; i < 16; i++) {
        unsigned char val = jarvis.heuristic_key[i];
        jarvis.heuristic_key[i] = ((val << 1) | (val >> 7)) ^ (i + 1);
    }
}
```

This runs **during `boot_sequence()`** — before `check_authorization()`. So by the time `decrypt_credentials()` would execute, the key has already been rotated and XOR'd.

> **Critical insight:** Using the ORIGINAL key (from constructor) produces garbage. You must apply the calibration transform first.

---

## Step 5: Computing the Flag

Applying the calibration to get the real key:

```python
init_key = [0x13, 0x37, 0x42, 0x58, 0x6B, 0x7A, 0x21, 0x0F,
            0x5C, 0x3E, 0x29, 0x44, 0x61, 0x78, 0x1D, 0x33]

cal_key = []
for i in range(16):
    val = init_key[i]
    rotated = ((val << 1) & 0xFF) | (val >> 7)
    cal_key.append(rotated ^ (i + 1))

enc = [0x6A, 0x30, 0xDD, 0xE5, 0x86, 0x95, 0xC8, 0x6E,
       0xF9, 0xFB, 0x08, 0x04, 0x56, 0x6B, 0xA3, 0x2B,
       0xB4, 0xF2, 0xEE, 0x29, 0x48, 0x84, 0xFA]

flag = ""
for i in range(len(enc)):
    k = cal_key[i % 16]
    flag += chr(((enc[i] ^ k) - (i * 3)) & 0xFF)

print(flag)  # MYTHIX{c0r3_unl0ck3d_7}
```

---

## Alternative Solve: Binary Patching

Instead of manual computation, patch the binary:

1. Find the `cmp` instruction in `check_authorization()` that compares `auth_level` against `1`
2. Change the conditional jump (`jne` → `je`, or patch the compared value to `0`)
3. Run the patched binary — `decrypt_credentials()` now executes and prints the flag

This works because `calibrate_heuristics()` still runs during `boot_sequence()`, so the key is correctly modified before decryption.

---

## Why the Decoy Works

| | `debug_dump()` (DECOY) | `decrypt_credentials()` (REAL) |
|---|---|---|
| **Complexity** | Single-byte XOR | Multi-byte key + per-index shift |
| **Key source** | Hardcoded `0x4A` | Runtime-computed from mutated array |
| **Output** | `MYTHIX{jarvis_online}` | `MYTHIX{c0r3_unl0ck3d_7}` |
| **Found by** | Quick XOR analysis | Full data-flow tracing |

The decoy is deliberately easier to find and decode. A solver who stops at the first clean extraction submits the wrong flag.

---

## 🏁 Flag

```
MYTHIX{c0r3_unl0ck3d_7}
```
