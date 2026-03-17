# Secure Vault v2.0 (Jailbreak CTF Challenge)

Welcome to the **Secure Vault v2.0** CTF challenge. This aims to be an exact replication of the `tachyon.iittp.ac.in/ctf/jailbreak` challenge.

## Setup Instructions
1.  **Prerequisites**: Python 3.8+
2.  **Install Dependencies**:
    ```bash
    pip install Flask
    ```
3.  **Run the Server**:
    ```bash
    python app.py
    ```
4.  **Play**:
    Open a web browser and navigate to `http://localhost:5000`

## Challenge Details (Spoilers)

The flag is: `MYTHX{time_travel_success}`

The challenge presents a mock internal vault interface. 
It accepts payload injections and explicitly states: `Note: System strips forbidden keywords: print, printf, flag, txt, cat.`

### The Vulnerability & Solution
The backend uses a simple, non-recursive string replacement to sanitize input. For each forbidden keyword, it deletes it from the string exactly once.

This is a classic Web Application Firewall (WAF) bypass trick: If you nest the forbidden keywords inside each other, the single pass of deletion will re-assemble the target word!

So, the goal is to execute `cat flag.txt`.
Since `cat`, `flag`, and `txt` are blocked, you can construct:
*   `c[cat]at` -> `ccatat`
*   `fl[flag]ag` -> `flflagag`
*   `.t[txt]xt` -> `.ttxtxt`

**Winning Payload:**
```
ccatat flflagag.ttxtxt
```

Submitting this payload will successfully bypass the checks and output the vault's flag.
