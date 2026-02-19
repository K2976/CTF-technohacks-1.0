# 🧠 Challenge: jarvis_core.bin

**Category:** Reverse Engineering
**Difficulty:** Medium
**Author:** MythX Team

---

## 📖 Story

> "JARVIS was never meant to be clever.
> He was meant to be consistent."

After the Battle of Endgame, Stark Industries recovered a fragment of the original JARVIS core.
The AI initializes correctly, reports all systems online… yet refuses to reveal its authorization data.

Security analysts believe the flag is present inside the core logic itself.

- No network activity
- No user input required
- No encryption libraries detected

And yet—no flag.

---

## 📦 Files Provided

- `jarvis_core.bin`

## 🧪 Program Behavior

```
Booting Stark Industries AI Core...
Loading heuristics...
JARVIS: All systems online.
JARVIS: Authorization failed.
```

- ❌ No input prompt
- ❌ No crash
- ❌ No visible flag via `strings`

---

## 🧠 Objective

Reverse engineer the binary and recover the authorization data.

**Flag format:** `MYTHIX{...}`

---

## ⚠️ Notes

- The binary is not packed or encrypted
- The binary is not anti-VM or anti-debug
- No brute-force is required
- Dynamic analysis is optional
- This is a logic-reading challenge, not a guessing challenge

> **Author's Note:**
> Sometimes the hardest part of reversing
> is accepting that the answer was already there.

---

## 🏁 Submission

Submit the full flag including the prefix: `MYTHIX{...}`
