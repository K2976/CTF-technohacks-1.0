/*
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
typedef struct {
    int auth_level;
    int boot_stage;
    unsigned char heuristic_key[16];
} CoreState;

static CoreState jarvis = {0};

/* ============================================
 * Constructor: runs BEFORE main()
 * Initializes core state including heuristic key
 * ============================================ */
__attribute__((constructor))
static void __core_preinit(void) {
    jarvis.auth_level = 0;     /* Unauthorized - forces fail path */
    jarvis.boot_stage = 0;

    unsigned char init[] = {
        0x13, 0x37, 0x42, 0x58, 0x6B, 0x7A, 0x21, 0x0F, 0x5C, 0x3E, 0x29, 0x44,
        0x61, 0x78, 0x1D, 0x33
    };
    for (int i = 0; i < 16; i++) {
        jarvis.heuristic_key[i] = init[i];
    }
}

/* ============================================
 * Calibrate heuristic table
 * Modifies heuristic_key IN PLACE
 * This runs during boot - affects decrypt key
 * ============================================ */
static void calibrate_heuristics(void) {
    for (int i = 0; i < 16; i++) {
        unsigned char val = jarvis.heuristic_key[i];
        jarvis.heuristic_key[i] = ((val << 1) | (val >> 7)) ^ (i + 1);
    }
}

/* ============================================
 * DECOY: Debug diagnostic dump
 * Dead code - called from run_diagnostics()
 * when boot_stage == 99 (never true)
 *
 * Simple single-byte XOR - easy to reverse
 * Produces: FALSE FLAG
 * ============================================ */
static void debug_dump(void) {
    unsigned char data[] = {
        0x07, 0x13, 0x1E, 0x02, 0x12, 0x31, 0x20, 0x2B, 0x38, 0x3C, 0x23, 0x39,
        0x15, 0x25, 0x24, 0x26, 0x23, 0x24, 0x2F, 0x37
    };
    int len = sizeof(data);
    char buf[64];
    for (int i = 0; i < len; i++) {
        buf[i] = data[i] ^ 0x4A;
    }
    buf[len] = '\0';
    printf("JARVIS: Debug: %s\n", buf);
}

/* ============================================
 * REAL: Decrypt authorization credentials
 * Dead code - called from check_authorization()
 * when auth_level == 1 (never true)
 *
 * Uses heuristic_key AS MODIFIED by calibrate()
 * Player must trace: constructor → calibrate → decrypt
 * ============================================ */
static void decrypt_credentials(void) {
    unsigned char enc[] = {
        0x6A, 0x30, 0xDD, 0xE5, 0xB7, 0x78, 0x30, 0x53, 0x3B, 0x38, 0x24, 0x12,
        0x5D, 0x6D, 0x6F, 0xE6, 0xBC, 0x0A, 0x1D, 0x2C, 0xA0, 0x4E
    };
    int len = sizeof(enc);
    char buf[64];
    for (int i = 0; i < len; i++) {
        unsigned char k = jarvis.heuristic_key[i % 16];
        buf[i] = ((enc[i] ^ k) - (i * 3)) & 0xFF;
    }
    buf[len] = '\0';
    printf("JARVIS: Authorization data: %s\n", buf);
}

/* ============================================
 * Run system diagnostics
 * Contains a dead branch to debug_dump()
 * ============================================ */
static void run_diagnostics(void) {
    if (jarvis.boot_stage == 99) {
        debug_dump();
    }
}

/* ============================================
 * Boot sequence
 * ============================================ */
static void boot_sequence(void) {
    printf("Loading heuristics...\n");
    calibrate_heuristics();    /* KEY: modifies heuristic_key */
    jarvis.boot_stage = 2;
    run_diagnostics();
}

/* ============================================
 * Authorization check
 * ============================================ */
static void check_authorization(void) {
    if (jarvis.auth_level == 1) {
        decrypt_credentials();
        printf("JARVIS: Authorization confirmed.\n");
    } else {
        printf("JARVIS: Authorization failed.\n");
    }
}

/* ============================================
 * Main entry point
 * ============================================ */
int main(void) {
    printf("Booting Stark Industries AI Core...\n");
    boot_sequence();
    printf("JARVIS: All systems online.\n");
    check_authorization();
    return 0;
}
