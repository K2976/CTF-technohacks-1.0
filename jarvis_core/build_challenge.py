#!/usr/bin/env python3
"""
Build script for "JARVIS Core" CTF Challenge
Category: Reverse Engineering | Difficulty: Medium

Architecture:
  - Constructor (__attribute__((constructor))) sets auth_level=0 and initializes key
  - boot_sequence() calls calibrate_heuristics() which MODIFIES the key
  - check_authorization() branches on auth_level:
    - auth_level == 1  → decrypt_credentials() → REAL flag  (dead code)
    - auth_level == 0  → "Authorization failed"              (always taken)
  - run_diagnostics() has another dead branch with debug_dump() → FALSE flag
  - debug_dump() uses simple XOR → easy to decode → DECOY

Anti-LLM layers:
  1. Two dead code functions - decoy is simpler/found first
  2. Constructor initializes state (LLMs often miss constructors)
  3. Key is mutated by calibrate_heuristics() at runtime
  4. Player must trace data flow across 3 functions for real flag
"""

import os
import sys
import subprocess
import struct

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "challenge_output")
C_SOURCE = os.path.join(BASE_DIR, "jarvis_core.c")

# ─────────────────────────────────────────────
# Flags
# ─────────────────────────────────────────────
REAL_FLAG = "MYTHIX{c0r3_unl0ck3d_7}"
FALSE_FLAG = "MYTHIX{j4rv1s_0nlin3}"
DECOY_XOR_KEY = 0x4A

# ─────────────────────────────────────────────
# Initial calibration key (set by constructor)
# ─────────────────────────────────────────────
INIT_KEY = [0x13, 0x37, 0x42, 0x58, 0x6B, 0x7A, 0x21, 0x0F,
            0x5C, 0x3E, 0x29, 0x44, 0x61, 0x78, 0x1D, 0x33]


def compute_calibrated_key(init_key):
    """Simulate calibrate_heuristics(): ROL(1) then XOR with (i+1)."""
    cal = list(init_key)
    for i in range(16):
        val = cal[i]
        rotated = ((val << 1) & 0xFF) | (val >> 7)
        cal[i] = rotated ^ (i + 1)
    return cal


def encode_false_flag(flag, xor_key):
    """Simple single-byte XOR encoding for the decoy."""
    return [ord(c) ^ xor_key for c in flag]


def encode_real_flag(flag, calibrated_key):
    """
    Encode real flag using the calibrated key.
    Decryption: result[i] = ((enc[i] ^ key[i%16]) - (i*3)) & 0xFF
    So encoding: enc[i] = (flag[i] + (i*3)) ^ key[i%16]
    """
    enc = []
    for i, ch in enumerate(flag):
        val = (ord(ch) + (i * 3)) & 0xFF
        k = calibrated_key[i % 16]
        enc.append(val ^ k)
    return enc


def verify_decryption(enc, calibrated_key, expected_flag):
    """Verify that our encoded data decrypts correctly."""
    result = []
    for i in range(len(enc)):
        k = calibrated_key[i % 16]
        ch = ((enc[i] ^ k) - (i * 3)) & 0xFF
        result.append(chr(ch))
    decoded = ''.join(result)
    assert decoded == expected_flag, f"Verification failed: got '{decoded}', expected '{expected_flag}'"
    return decoded


def format_c_array(data, name="data"):
    """Format a byte array as a C array initializer."""
    hex_strs = [f"0x{b:02X}" for b in data]
    # Wrap at 12 elements per line
    lines = []
    for i in range(0, len(hex_strs), 12):
        lines.append("        " + ", ".join(hex_strs[i:i+12]))
    return ",\n".join(lines)


def generate_c_source(false_enc, real_enc, init_key):
    """Generate the C source code for the challenge binary."""

    false_arr = format_c_array(false_enc)
    real_arr = format_c_array(real_enc)
    init_arr = format_c_array(init_key)

    source = f'''/*
 * JARVIS Core - CTF Challenge Binary
 * Category: Reverse Engineering
 *
 * DO NOT DISTRIBUTE THIS SOURCE - challenge binary only
 */

#include <stdio.h>
#include <string.h>

/* ============================================
 * Global JARVIS core state
 * ============================================ */
typedef struct {{
    int auth_level;
    int boot_stage;
    unsigned char heuristic_key[16];
}} CoreState;

static CoreState jarvis = {{0}};

/* ============================================
 * Constructor: runs BEFORE main()
 * Initializes core state including heuristic key
 * ============================================ */
__attribute__((constructor))
static void __core_preinit(void) {{
    jarvis.auth_level = 0;     /* Unauthorized - forces fail path */
    jarvis.boot_stage = 0;

    unsigned char init[] = {{
{init_arr}
    }};
    for (int i = 0; i < 16; i++) {{
        jarvis.heuristic_key[i] = init[i];
    }}
}}

/* ============================================
 * Calibrate heuristic table
 * Modifies heuristic_key IN PLACE
 * This runs during boot - affects decrypt key
 * ============================================ */
static void calibrate_heuristics(void) {{
    for (int i = 0; i < 16; i++) {{
        unsigned char val = jarvis.heuristic_key[i];
        jarvis.heuristic_key[i] = ((val << 1) | (val >> 7)) ^ (i + 1);
    }}
}}

/* ============================================
 * DECOY: Debug diagnostic dump
 * Dead code - called from run_diagnostics()
 * when boot_stage == 99 (never true)
 *
 * Simple single-byte XOR - easy to reverse
 * Produces: FALSE FLAG
 * ============================================ */
static void debug_dump(void) {{
    unsigned char data[] = {{
{false_arr}
    }};
    int len = sizeof(data);
    char buf[64];
    for (int i = 0; i < len; i++) {{
        buf[i] = data[i] ^ 0x{DECOY_XOR_KEY:02X};
    }}
    buf[len] = '\\0';
    printf("JARVIS: Debug: %s\\n", buf);
}}

/* ============================================
 * REAL: Decrypt authorization credentials
 * Dead code - called from check_authorization()
 * when auth_level == 1 (never true)
 *
 * Uses heuristic_key AS MODIFIED by calibrate()
 * Player must trace: constructor → calibrate → decrypt
 * ============================================ */
static void decrypt_credentials(void) {{
    unsigned char enc[] = {{
{real_arr}
    }};
    int len = sizeof(enc);
    char buf[64];
    for (int i = 0; i < len; i++) {{
        unsigned char k = jarvis.heuristic_key[i % 16];
        buf[i] = ((enc[i] ^ k) - (i * 3)) & 0xFF;
    }}
    buf[len] = '\\0';
    printf("JARVIS: Authorization data: %s\\n", buf);
}}

/* ============================================
 * Run system diagnostics
 * Contains a dead branch to debug_dump()
 * ============================================ */
static void run_diagnostics(void) {{
    if (jarvis.boot_stage == 99) {{
        debug_dump();
    }}
}}

/* ============================================
 * Boot sequence
 * ============================================ */
static void boot_sequence(void) {{
    printf("Loading heuristics...\\n");
    calibrate_heuristics();    /* KEY: modifies heuristic_key */
    jarvis.boot_stage = 2;
    run_diagnostics();
}}

/* ============================================
 * Authorization check
 * ============================================ */
static void check_authorization(void) {{
    if (jarvis.auth_level == 1) {{
        decrypt_credentials();
        printf("JARVIS: Authorization confirmed.\\n");
    }} else {{
        printf("JARVIS: Authorization failed.\\n");
    }}
}}

/* ============================================
 * Main entry point
 * ============================================ */
int main(void) {{
    printf("Booting Stark Industries AI Core...\\n");
    boot_sequence();
    printf("JARVIS: All systems online.\\n");
    check_authorization();
    return 0;
}}
'''
    return source


def compile_binary(source_path, output_path, target="native"):
    """Compile and strip the binary."""
    cc = "gcc"
    flags = ["-O1", "-s", "-o", output_path, source_path]

    if target == "linux" and sys.platform == "darwin":
        # Try cross-compiler
        for cross_cc in ["x86_64-linux-gnu-gcc", "x86_64-elf-gcc"]:
            try:
                subprocess.run([cross_cc, "--version"], capture_output=True, check=True)
                cc = cross_cc
                break
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
        else:
            print("[!] No cross-compiler found. Building native (macOS) binary.")
            print("    For Linux ELF, install: brew install x86_64-elf-gcc")
            print("    Or use Docker: docker run --rm -v $(pwd):/work gcc gcc ...")

    cmd = [cc] + flags
    print(f"[*] Compiling: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[!] Compilation failed:\n{result.stderr}")
        return False

    # Strip symbols
    strip_cmd = ["strip", output_path]
    subprocess.run(strip_cmd, capture_output=True)

    size = os.path.getsize(output_path)
    print(f"[+] Binary built: {output_path} ({size} bytes)")
    return True


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("  Building 'JARVIS Core' CTF Challenge")
    print("=" * 60)
    print()

    # Step 1: Compute calibrated key
    print("[*] Computing calibrated key...")
    calibrated = compute_calibrated_key(INIT_KEY)
    print(f"    Init key:       {[f'0x{b:02X}' for b in INIT_KEY]}")
    print(f"    Calibrated key: {[f'0x{b:02X}' for b in calibrated]}")

    # Step 2: Encode false flag
    print(f"\n[*] Encoding false flag: {FALSE_FLAG}")
    false_enc = encode_false_flag(FALSE_FLAG, DECOY_XOR_KEY)
    print(f"    XOR key: 0x{DECOY_XOR_KEY:02X}")
    print(f"    Encoded: {[f'0x{b:02X}' for b in false_enc]}")

    # Verify false flag
    false_verify = ''.join(chr(b ^ DECOY_XOR_KEY) for b in false_enc)
    assert false_verify == FALSE_FLAG
    print(f"    Verify:  {false_verify} ✓")

    # Step 3: Encode real flag
    print(f"\n[*] Encoding real flag: {REAL_FLAG}")
    real_enc = encode_real_flag(REAL_FLAG, calibrated)
    print(f"    Encoded: {[f'0x{b:02X}' for b in real_enc]}")

    # Verify real flag
    decoded = verify_decryption(real_enc, calibrated, REAL_FLAG)
    print(f"    Verify:  {decoded} ✓")

    # Step 4: Generate C source
    print(f"\n[*] Generating C source: {C_SOURCE}")
    source = generate_c_source(false_enc, real_enc, INIT_KEY)
    with open(C_SOURCE, 'w') as f:
        f.write(source)
    print(f"[+] C source written ({len(source)} bytes)")

    # Step 5: Compile
    binary_path = os.path.join(OUTPUT_DIR, "jarvis_core.bin")
    print(f"\n[*] Compiling binary...")
    if compile_binary(C_SOURCE, binary_path):
        print(f"[+] Challenge binary: {binary_path}")
    else:
        print("[!] Compilation failed — see errors above")
        sys.exit(1)

    # Step 6: Quick verification — run the binary
    print(f"\n[*] Testing binary...")
    try:
        result = subprocess.run([binary_path], capture_output=True, text=True, timeout=5)
        print(f"    Output:")
        for line in result.stdout.strip().split('\n'):
            print(f"      {line}")
        if "Authorization failed" in result.stdout:
            print(f"    ✓ Binary correctly takes the fail path")
        else:
            print(f"    ✗ WARNING: Binary did not print expected output!")
    except Exception as e:
        print(f"    Could not run binary: {e}")

    # Step 7: Verify strings aren't visible
    print(f"\n[*] Checking strings output...")
    try:
        result = subprocess.run(["strings", binary_path], capture_output=True, text=True)
        if REAL_FLAG in result.stdout:
            print(f"    ✗ CRITICAL: Real flag visible in strings!")
        elif FALSE_FLAG in result.stdout:
            print(f"    ✗ WARNING: False flag visible in strings!")
        elif "MYTHIX" in result.stdout:
            print(f"    ✗ WARNING: Flag prefix visible in strings!")
        else:
            print(f"    ✓ No flag content visible in strings output")
    except Exception as e:
        print(f"    Could not run strings: {e}")

    print()
    print("=" * 60)
    print("[✓] Challenge built successfully!")
    print("=" * 60)
    print()
    print("Solve path summary:")
    print(f"  1. Decompile binary → find main → trace call graph")
    print(f"  2. Identify check_authorization() branches on auth_level")
    print(f"  3. auth_level is set to 0 by constructor → fail path always taken")
    print(f"  4. Find TWO dead code functions:")
    print(f"     DECOY: debug_dump() — simple XOR 0x{DECOY_XOR_KEY:02X}")
    print(f"       → decodes to: {FALSE_FLAG}")
    print(f"     REAL:  decrypt_credentials() — uses calibrated heuristic_key")
    print(f"       → requires tracing constructor + calibrate_heuristics()")
    print(f"       → decodes to: {REAL_FLAG}")
    print(f"  5. Key insight: heuristic_key is MODIFIED by calibrate()")
    print(f"     Using init values directly → WRONG output")
    print(f"     Using calibrated values → CORRECT flag")


if __name__ == '__main__':
    main()
