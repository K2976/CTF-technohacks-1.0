# 🧠 JARVIS Core

**Category:** Reverse Engineering
**Difficulty:** Medium
**Points:** 300
**Author:** MythX Team

---

## 📖 Story

> *"JARVIS was never meant to be clever.*
> *He was meant to be consistent."*

After the Battle of Endgame, Stark Industries recovered a fragment of the original JARVIS core. The AI initializes correctly, reports all systems online… yet refuses to reveal its authorization data.

Security analysts believe the flag is present inside the core logic itself.

- No network activity detected
- No user input required
- No encryption libraries detected

And yet — no flag.

---

## 📦 Files Provided

| File | Description |
|---|---|
| `jarvis_core.bin` | The recovered JARVIS core binary |

---

## 🧪 Program Behavior

When executed, the binary outputs:

```
Booting Stark Industries AI Core...
Loading heuristics...
JARVIS: All systems online.
JARVIS: Authorization failed.
```

The program exits normally. There is:

- ❌ No input prompt
- ❌ No crash
- ❌ No visible flag
- ❌ No obvious strings

---

## 🧠 Objective

Reverse engineer the binary and recover the hidden authorization data.

---

## ⚠️ Notes

- The binary is **not** packed
- The binary is **not** encrypted
- The binary is **not** anti-VM or anti-debug
- No brute-force is required
- Dynamic analysis is optional
- This is a **logic-reading** challenge, not a guessing challenge

---

## 💬 Author's Note

> *Sometimes the hardest part of reversing*
> *is accepting that the answer was already there.*

---

## 🏁 Submission

Submit the full flag including the prefix:

```
MYTHX{...}
```
