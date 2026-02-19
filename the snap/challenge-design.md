# CTF Challenge Design Document — "Endgame Protocol"

> **Status:** DRAFT — Awaiting co-designer feedback  
> **Challenges:** 12 total (4 Easy · 6 Medium · 2 Hard + 1 Optional Meta)  
> **Domains:** OSINT · Steganography · Audio/Signal · Misc  
> **Theme:** Avengers: Endgame (metaphorical only)

---

## Design Philosophy & Narrative Arc

The CTF tells a story: SHIELD's systems were corrupted during "The Snap." Players are recruited as field analysts to recover fragmented intelligence. Each challenge is a corrupted artifact from a different division of SHIELD. The narrative escalates from simple recovery ops (Easy) to full intelligence reconstruction (Hard).

This arc ensures thematic cohesion without requiring any Marvel knowledge — the skin is operational military/intelligence language dressed in Endgame metaphors.

---

## 🟢 EASY CHALLENGES (4) — ~10 min each

---

### E1: "The Blip" — OSINT

**Concept:** A leaked employee profile page (HTML file served locally or as static page) from "Stark Industries HR Portal." The profile has been partially sanitized — name removed, but residual metadata remains. The profile photo has been stripped of EXIF, but the HTML source contains a commented-out debug log with a partial API endpoint. Players must find the endpoint, realize it points to a staging server URL pattern, and extract the flag from a response header simulation embedded in a secondary file (JSON).

**Skill tested:** Source inspection, metadata reasoning, understanding API endpoint structures, cross-referencing artifacts.

**Layer structure:**
1. Inspect HTML source → find commented debug log with partial endpoint
2. Reconstruct full endpoint from context clues in page content (employee ID pattern visible in profile URL)
3. Open matching JSON file (simulating the API response) → flag is in a non-obvious header field (`X-Debug-Token`)

**False flag:** The HTML contains a `data-token` attribute on a div that looks like a base64-encoded flag. It decodes to a plausible but incorrect flag format: `flag{blip_recovery_complete}`. The real flag has a different prefix/structure.

**Anti-LLM analysis:**
- **LLM approach:** Parse HTML, find base64 in `data-token`, decode it, declare victory.
- **Why LLM fails:** It will stop at the high-confidence false flag. The real path requires reconstructing the endpoint and cross-referencing a second file — an action that requires understanding the *relationship* between files, not just parsing one.
- **Why humans succeed:** A skilled player will notice the debug log references a file path, and their instinct is to explore further. The false flag format is *slightly off* from the challenge description's specified format, which a careful human notices.

> [!WARNING]
> **Weakness:** If the false flag format is too obviously wrong, it doesn't waste enough time. If too similar, it frustrates unfairly. The false flag format must differ by exactly one structural element (e.g., prefix `flag{}` vs `FLAG{}` or a different wrapper). Calibrate carefully.

---

### E2: "Quantum Residue" — Steganography

**Concept:** A PNG image of a "quantum field scan" (abstract generative art — swirly colors). The image contains LSB steganography in the red channel only. However, running `zsteg` naively extracts data from *all* channels and produces a misleading output. Players must isolate the red channel, extract LSB data, which gives them a hex string. The hex string is a password for a `steghide`-protected secondary file (a JPEG embedded via `binwalk` inside the PNG — it's a polyglot).

**Skill tested:** Targeted stego extraction (channel isolation), polyglot file recognition, tool chaining (`zsteg` → `binwalk` → `steghide`).

**Layer structure:**
1. Run `zsteg` → noisy output with a plausible but wrong string in combined channels
2. Isolate red channel extraction → get hex password
3. Run `binwalk` → discover embedded JPEG
4. Use `steghide` with the password on the JPEG → real flag

**False flag:** The `zsteg` all-channel output contains `flag{quantum_noise_detected}` — a clean, confident, plausible extraction. LLMs (and lazy players) stop here.

**Anti-LLM analysis:**
- **LLM approach:** Run `zsteg image.png`, parse output, find the clean string, submit.
- **Why LLM fails:** The clean false flag is *designed* to look like the answer. An LLM has no reason to dig deeper — the confidence is high. Even if it runs `binwalk`, it wouldn't chain the hex output from the red channel to the `steghide` password without human-level hypothesis testing.
- **Why humans succeed:** Experienced stego players know single-channel extraction often yields different results. They also know to always `binwalk` any file. The *combination* of these instincts is the real challenge.

> [!IMPORTANT]
> The polyglot must be properly constructed or `binwalk` might not identify the JPEG. Test with multiple `binwalk` versions. Also ensure `zsteg` produces the false flag consistently across versions.

---

### E3: "Distress Signal" — Audio / Morse

**Concept:** An audio file (~30 sec) of a "distress transmission from the Quantum Realm." Contains Morse code at a non-standard speed (18 WPM), embedded at 14 kHz (above casual listening range but within spectrogram visibility), masked by ambient sci-fi noise. The Morse decodes to a URL slug, not the flag itself. Visiting the slug (appended to the CTF platform URL) reveals a page with a final substitution cipher (ROT variant but the shift value is encoded in the Morse timing gaps).

**Skill tested:** Spectrogram analysis (Sonic Visualizer / Audacity), Morse decoding at non-standard parameters, signal extraction from noise, chained decoding.

**Layer structure:**
1. Open in Audacity → visual waveform shows nothing useful (noise)
2. Switch to spectrogram view → identify pattern at 14 kHz
3. Isolate frequency band → decode Morse (non-standard WPM requires manual timing or tool adjustment)
4. Morse gives URL slug → navigate to it
5. Page contains ciphertext + hint that shift value is derived from Morse inter-word gap timing (measured in ms, mod 26)

**False flag:** In the low-frequency range (~500 Hz), there's a different Morse-like pattern that decodes to `TONYSTARKSENDGAME`. This is a thematic red herring that looks like a flag answer. It's planted to catch anyone who doesn't look at the spectrogram carefully — the timing is slightly irregular because it's actually amplitude-modulated noise, not real Morse.

**Anti-LLM analysis:**
- **LLM approach:** If it has tool access, it might extract audio, attempt automated Morse decoding. The low-frequency decoy would be found first and looks convincingly flag-like.
- **Why LLM fails:** Automated Morse decoders will struggle with the non-standard WPM at 14 kHz. The LLM would likely find the low-frequency decoy first and report it. Even if it finds the real Morse, it can't derive the ROT shift from timing gaps without physically measuring them — that requires tool-specific analysis.
- **Why humans succeed:** Spectrogram analysis is a trained visual skill. Experienced audio CTF players check multiple frequency ranges. Measuring inter-word gaps manually is tedious but straightforward with Audacity's selection tool.

> [!CAUTION]
> **Potential unintended path:** If the URL slug is guessable or brute-forceable (short, dictionary words), players skip the audio entirely. The slug must be a non-dictionary, non-guessable string (e.g., `q7x9_r3lm_45c`). Also, the substitution cipher page must not be indexable/discoverable without the slug.

---

### E4: "Nexus Point" — Misc

**Concept:** Players receive a ZIP file labeled "Recovered Nexus Event Logs." It contains 5 CSV files of "sensor readings" — timestamps, values, coordinates. Four files are internally consistent; one file has subtle data anomalies (impossible timestamps — dates before Unix epoch mixed with valid ones, coordinate pairs that don't match any real location but when plotted form ASCII characters, and values that follow a pattern except for specific rows).

Players must identify the anomalous file, extract the anomalous rows, and interpret the coordinates-as-ASCII-art to get a keyword. That keyword, combined with the anomalous row indices (used as a numeric shift), produces the flag.

**Skill tested:** Data analysis, anomaly detection, pattern recognition in structured data, creative interpretation of coordinate systems.

**Layer structure:**
1. Examine 5 CSV files → identify which one has anomalies (requires comparing timestamp ranges, value distributions)
2. Extract anomalous rows → notice coordinate pairs are unusual
3. Plot coordinates → see ASCII art spelling a word
4. Combine word + row indices as shift → decode flag

**False flag:** File #3 (not the real anomalous file) has a column header that, when the first letters are combined, spells `FLAG_NEXUS_EVENT`. This is metadata decoration, not a flag. The real anomalous file is #2.

**Anti-LLM analysis:**
- **LLM approach:** Read CSVs, look for obvious patterns, try to decode column headers. Likely finds the header-based false flag in File #3.
- **Why LLM fails:** Detecting the *subtle* anomalies in File #2 (impossible timestamps, coordinate plotting) requires statistical reasoning and spatial visualization that LLMs handle poorly, especially when four other files provide noise. An LLM analyzing CSV data will gravitate toward surface-level patterns.
- **Why humans succeed:** A human analyst opening the data in a spreadsheet or pandas will notice dates before 1970 and might try plotting coordinates on a whim. The "aha moment" of seeing ASCII art in a scatter plot is distinctly human.

> [!NOTE]
> The CSV files should be large enough (~500-1000 rows each) that manual inspection is impractical, forcing tool use. But the anomalous rows should be sparse (~15-20 rows in a 1000-row file) to test detection skills.

---

## 🟡 MEDIUM CHALLENGES (6) — ~30 min each

---

### M1: "Time Heist Briefing" — OSINT

**Concept:** A "leaked internal briefing document" (PDF) that has been through multiple format conversions. The document discusses a fictional operation with redacted sections. However, the PDF was generated from a DOCX that was itself generated from a Google Doc export. Each conversion left metadata ghosts:
- The PDF metadata still has the DOCX author
- The DOCX revision history (embedded in the PDF's XMP data) contains a URL
- The URL leads to a deliberately planted fake blog post (hosted on the CTF infra) with an embedded image
- The image's EXIF GPS coordinates, when reversed (lat↔long), produce numbers that are a phone number in international format — but the flag is the number encoded in a specific scheme (not the number itself)

**Skill tested:** Multi-tool metadata forensics (`exiftool`, `pdfinfo`, `strings`), OSINT methodology (following trails), verification (the GPS reversal is a non-obvious step that requires questioning the data).

**Layer structure:**
1. `exiftool` on PDF → find author name + XMP revision data with embedded URL
2. Visit URL → find blog post with image
3. `exiftool` on blog image → GPS coordinates
4. Notice coordinates don't map to any real place → try reversing lat/long
5. Reversed coordinates form a phone number → encode using challenge-specified scheme

**False flag:** The PDF's `Subject` field contains `Operation: CHRONO-7749-FLAG`. This looks like an operational code that could be the flag. Additionally, the blog post text contains a "mission code" in the body that's another decoy.

**Anti-LLM analysis:**
- **LLM approach:** Extract all metadata, find the Subject field flag-like string, submit it. Might also find the blog URL but would take the GPS coordinates at face value.
- **Why LLM fails:** The lat/long reversal is a *semantic* leap — there's no technical indicator that you should swap them. It requires the human insight of "these coordinates point to the middle of the ocean, that's suspicious." LLMs don't have the geographic intuition to flag impossible coordinates.
- **Why humans succeed:** An OSINT practitioner will paste coordinates into a map and go "wait, this is in the Pacific Ocean, that's wrong." The reversal is a known OSINT technique for catching deliberate data falsification.

> [!WARNING]
> **Weakness:** If the reversed coordinates map to a famous/recognizable location, astute players might skip the phone number step and Google the location directly. The reversed coordinates should map to an unremarkable suburban address with no online presence.

---

### M2: "Reality Stone Fragment" — Steganography

**Concept:** An image file labeled "reality_stone_scan.bmp." The BMP format is unusual for CTFs (most use PNG), and this is deliberate. The BMP has a modified header — the DIB header size field has been altered to a non-standard value, causing some image viewers to render it incorrectly (slight color shift). Players must:

1. Notice the BMP header anomaly (using `xxd` or hex editor)
2. Correct the header → image renders properly, revealing a QR code in the bottom-right corner
3. The QR code links to a pastebin-style page with a PGP-encrypted message
4. The PGP passphrase is hidden in the BMP's color palette table (the last 8 palette entries spell out a passphrase in ASCII when you read their RGB values)

**Skill tested:** Binary file format analysis, hex editing, QR extraction, PGP decryption, color palette forensics.

**Layer structure:**
1. Open BMP → notice rendering artifact or use `identify` to flag format error
2. Hex inspect → find corrupted DIB header → fix it
3. Re-render → QR code appears
4. QR → encrypted message
5. Revisit BMP palette → extract passphrase → decrypt

**False flag:** The incorrectly-rendered image (before header fix) contains a visible but distorted watermark that reads `REALITY_KEY_2847`. This is visible in the broken rendering but disappears when the header is fixed — it's an artifact of the misalignment, not actual embedded data.

**Anti-LLM analysis:**
- **LLM approach:** An LLM would likely try standard stego tools on the BMP directly. The broken header would cause `zsteg` and similar tools to either error out or produce garbage. The LLM might try `strings` and find `REALITY_KEY_2847` in the rendering buffer.
- **Why LLM fails:** Understanding that a BMP header is *deliberately broken* requires binary format knowledge that goes beyond "run stego tool." The LLM can't visually see the rendering difference. The PGP step after the QR adds another layer that requires knowing the passphrase, which is hidden in the palette — a deeply non-obvious location.
- **Why humans succeed:** CTF players with forensics experience check file headers first (`file`, `xxd | head`). They know BMP structures. Visual inspection of the corrected image reveals the QR code.

> [!IMPORTANT]
> Must ensure the broken BMP renders *at all* in common viewers (it should render just wrongly, not crash). Test on Chrome, Preview.app, GIMP, and `feh`. If it doesn't render, players can't see the false watermark.

---

### M3: "Vormir's Price" — Audio / Signal

**Concept:** An audio file containing what sounds like a scrambled radio transmission. It's actually two overlapping signals:
- **Signal A** (foreground): DTMF tones at standard frequencies — decodes to a phone number that's a red herring
- **Signal B** (background): A slow-scan television (SSTV) signal (Martin M1 mode), heavily attenuated

Players must:
1. Identify and separate the two signals
2. Recognize Signal B as SSTV (non-trivial; requires knowing what SSTV sounds like or spectral analysis)
3. Decode the SSTV image using `qsstv` or similar
4. The SSTV image contains text with the flag, but the image is intentionally transmitted with errors — some scan lines are corrupted, requiring players to reconstruct from partial data

**Skill tested:** Signal identification, SSTV decoding, audio filtering, partial data reconstruction.

**Layer structure:**
1. Listen / spectrogram → identify DTMF tones (obvious) and background signal (less obvious)
2. Decode DTMF → phone number (red herring)
3. Filter out DTMF, isolate background → recognize as SSTV
4. Decode SSTV → partial image with corrupted lines
5. Reconstruct/interpret partially corrupted text

**False flag:** The DTMF phone number (Signal A). It decodes cleanly and looks like a complete answer. An additional false path: the SSTV image contains *two* text strings — one that's clearly visible but is a decoy instruction ("SUBMIT CODE: VORMIR-ALPHA-9"), and the actual flag in the corrupted region that requires reconstruction.

**Anti-LLM analysis:**
- **LLM approach:** Identify DTMF tones (well-documented), decode them, submit the number. Even if it identifies SSTV, automated SSTV decoding of a degraded signal produces garbled images that require human visual interpretation.
- **Why LLM fails:** SSTV decoding from a noisy, overlapping source is tool-intensive and the corrupted output requires *visual* interpretation of partial text — exactly what LLMs can't do with audio data.
- **Why humans succeed:** Radio/signals CTF players recognize SSTV by its characteristic sound. `qsstv` decoding with manual calibration can recover the image. Reading partially corrupted text is a natural human skill.

> [!CAUTION]
> **Potential unintended path:** If the SSTV signal can be cleanly decoded by an automated tool without filtering, the phone number decoy loses its value. The SSTV must be degraded enough to require manual intervention but not so much that it's unsolvable. Test with `qsstv`, `MMSSTV`, and `robot36`.

---

### M4: "The Decimation Files" — Steganography

**Concept:** A zip file containing 10 images labeled `survivor_01.png` through `survivor_10.png`. Per "The Snap," exactly half contain hidden data and the other half are clean decoys. But it's not obvious which half is which.

Each of the 5 real images uses a *different* steganographic technique:
1. LSB in green channel only
2. Appended data after IEND chunk
3. Modified PNG chunk (custom `tEXt` chunk with non-standard keyword)
4. Pixel value differencing (PVD) — requires specialized tool
5. Alpha channel encoding where alpha values spell out ASCII

Players must identify which 5 images contain data, extract from each using the correct technique, and combine the 5 fragments to form the flag. The fragments are out of order — the correct order is determined by a sequence number embedded within each fragment.

**Skill tested:** Broad stego knowledge (multiple techniques), tool diversity, systematic approach, data reassembly.

**Layer structure:**
1. Triage 10 images to identify which 5 have hidden data
2. Determine the stego technique for each
3. Extract each → get 5 fragments with sequence numbers
4. Reassemble in correct order → flag

**False flag:** The 5 clean images aren't truly clean — each has a different subtle artifact (e.g., unusual metadata, slightly larger file size, a single modified pixel). This makes *every* image look suspicious under cursory analysis. Additionally, `strings` on any image reveals plausible-looking base64 fragments that decode to thematic nonsense.

**Anti-LLM analysis:**
- **LLM approach:** Run `zsteg` on all 10, run `binwalk` on all 10, run `strings` on all 10. This would find some real data and lots of noise. The PVD-encoded image would likely be missed entirely since PVD isn't in standard tool defaults. The LLM would struggle to determine which outputs are real vs. decoy.
- **Why LLM fails:** The volume of data (10 images × multiple tools × false positives) creates a decision problem that requires *judgment* — knowing which outputs look real. PVD stego is uncommon enough that an LLM might not suggest it. Even with all extractions, reassembling fragments in order requires understanding the embedded sequence numbers.
- **Why humans succeed:** Experienced stego players work methodically: check all images with `file`, `exiftool`, `xxd` for quick wins, then progressively apply more sophisticated tools. They recognize extraction output quality — real data "looks right."

> [!NOTE]
> 10 images is a *lot*. Ensure the triage phase is feasible — `file` command should show size anomalies for appended data, `exiftool` should flag the custom chunk. The PVD image should have a subtle statistical tell (chi-squared test would flag it). Players shouldn't need to brute-force all 10 × all techniques.

---

### M5: "Pym Particles" — OSINT

**Concept:** Players receive a "classified document" (PDF) about a research project. The document references a researcher by alias only ("Dr. Pym"). The challenge models **sockpuppet detection** — players must determine the real identity behind the alias using contradictory evidence across multiple platforms.

The CTF infrastructure hosts:
- A blog (Dr. Pym's technical blog with 3 posts)
- A social media profile (linked from blog, different alias)
- A conference proceeding abstract (matching the social media alias)
- A GitHub-like repo (linked from the conference abstract, *third* alias but same SSH key fingerprint as the blog)

The trail is: PDF → Blog → Social media → Conference → Repo → SSH key → match back to blog → the *real name* (which appears only in the repo commit history, specifically in a merge commit message from another contributor who uses the real name).

**Skill tested:** Identity verification, cross-platform correlation, understanding SSH key fingerprints, Git forensics.

**Layer structure:**
1. PDF → find blog URL in document metadata
2. Blog → find social media link
3. Social media → find conference reference
4. Conference abstract → find repo link
5. Repo → check SSH keys → match to blog
6. Repo git log → find merge commit → extract real name
7. Format as flag

**False flag:** Each platform shows a *different* alias. One of them (the social media alias) looks like it could be a real name. Players might submit that as the answer without doing the full chain to verify it's just another alias.

**Anti-LLM analysis:**
- **LLM approach:** Follow links mechanically, read text on each page, look for name-like strings. Likely submits the social media alias as the answer.
- **Why LLM fails:** The critical step is recognizing that SSH key fingerprints link two different-named accounts as the same person, then digging into git commit history for a merge commit where another contributor reveals the real name. An LLM wouldn't think to check SSH keys across platforms — that's a trained OSINT instinct.
- **Why humans succeed:** OSINT analysts know to check for shared identifiers (keys, email patterns, writing style). Git log deep-dives are standard procedure.

> [!WARNING]
> **Weakness:** This challenge requires significant CTF infrastructure (hosted blog, profile pages, conference abstract page, git repo). Ensure all these are stable and don't leak the answer through page source or directory listing. Consider using static HTML pages to minimize infrastructure complexity.

---

### M6: "Wakandan Encryption" — Misc

**Concept:** Players receive a binary file that `file` identifies as "data" (no recognized format). Using `xxd`, they find it starts with a custom magic number. The file is a custom archive format containing 3 "encrypted" payloads:

- **Payload 1:** XOR-encrypted with a single-byte key (easy to break, yields a hint: "The key is in the frequency")
- **Payload 2:** Appears encrypted but is actually just reversed + base85 encoded. Decodes to a partial flag.
- **Payload 3:** Encrypted with a multi-byte XOR key. The key is derived from Payload 1's plaintext — specifically, the character frequency distribution (most common char = first byte of key, etc.)

Players must reverse-engineer the custom format, parse the three payloads, and chain the decryption.

**Skill tested:** Reverse engineering file formats, XOR cryptanalysis, encoding identification, chained decryption.

**Layer structure:**
1. Analyze binary → identify custom format structure (header + 3 payloads with length fields)
2. Extract Payload 1 → single-byte XOR → break it → get hint
3. Extract Payload 2 → try common decodings → reversed base85 → partial flag
4. Use Payload 1 frequency analysis to derive multi-byte key → decrypt Payload 3
5. Combine Payload 2 + Payload 3 → full flag

**False flag:** Payload 1's decrypted text contains `KEY=vibraniuM_2049` as part of the hint message. This looks like it should decrypt Payload 3 directly, but using it as an XOR key yields plausible-looking but incorrect plaintext (garbled English words that look like a corrupted flag).

**Anti-LLM analysis:**
- **LLM approach:** Analyze the binary, potentially identify XOR patterns stat analysis. Might decode Payload 1, find the fake key, attempt to use it on Payload 3.
- **Why LLM fails:** The frequency-analysis-derived key is a meta-reasoning step. The hint says "the key is in the frequency" — an LLM would likely interpret this as "frequency = radio frequency" or literally look for a frequency value in the text, not perform character frequency analysis *on the plaintext itself* to derive the key. The misdirection is semantic.
- **Why humans succeed:** Crypto CTF players recognize "frequency" as a heavy hint toward frequency analysis. They'd perform character counts on Payload 1's plaintext and construct the key systematically.

> [!IMPORTANT]
> The frequency-derived key must be unambiguous. If two characters share the same frequency, the key becomes non-deterministic. Ensure the Payload 1 plaintext has a clear, unique frequency ordering for the key-length characters needed.

---

## 🔴 HARD CHALLENGES (2) — ~30-40 min each

---

### H1: "The Gauntlet" — Multi-domain

**Concept:** A single large file (~5MB) that is a multi-layer polyglot:
- **Layer 0:** Appears as a JPEG image (vacation photo, thematic but irrelevant)
- **Layer 1:** `binwalk` reveals an embedded ZIP → contains a WAV file
- **Layer 2:** WAV spectrogram → shows a URL and a hex string
- **Layer 3:** URL leads to a page with an RSA public key (small, breakable: 256-bit) → factor it → derive private key
- **Layer 4:** The hex string from the spectrogram is an RSA-encrypted message → decrypt with derived private key → but the plaintext is STILL encoded: Base32, with specific characters substituted (0→O, 1→I, 8→B — visually similar substitutions)
- **Layer 5:** Correct the substitutions → decode Base32 → flag

**Skill tested:** Polyglot analysis, spectrogram reading, RSA factoring (small key), encoding subtleties, attention to detail.

**Layer structure:** 6 layers, each requiring a different skill.

**False flag:** 
- The JPEG's EXIF comment field contains `flag{gauntlet_wielder_3000}` — immediate trap for anyone who starts with `exiftool`.
- The WAV spectrogram *also* shows a second, fainter hex string that decodes to another fake flag.
- The RSA decryption without fixing the Base32 substitutions produces almost-correct text with a plausible but wrong flag.

**Anti-LLM analysis:**
- **LLM approach:** Find EXIF flag → stop. If it goes deeper, it might reach the spectrogram but has multiple false extractions to choose from. RSA factoring of a 256-bit key is computationally trivial, but the Base32 visual substitution trick is a *perceptual* challenge — LLMs process characters literally and wouldn't recognize that `0` should be `O`.
- **Why LLM fails:** The visual substitution layer specifically targets LLM character processing. An LLM sees `0` as a digit and processes it as such. A human might notice that the Base32 output "looks weird" and try visually similar substitutions — a spatial reasoning task. Additionally, the 3 false flags at different layers create a branching problem.
- **Why humans succeed:** Each layer is individually tractable for an experienced player. The key insight at the final layer (visual substitution) is something humans do naturally — "this looks like it should be O, not 0."

> [!CAUTION]
> **6 layers is a lot.** Risk of players getting stuck at an intermediate layer and never reaching the actual hard parts. Consider providing a gentle hint mechanism after a time threshold, or ensure each intermediate layer provides visible confirmation of progress (e.g., "you're on the right track" in the decrypted intermediate output).

---

### H2: "Thanos Protocol" — Steganography + Misc

**Concept:** Players receive two seemingly unrelated files:
- A PNG image (`artifact_alpha.png`)
- A text file (`artifact_omega.txt`) containing a large block of hex data with a header claiming it's a "corrupted transmission log"

The catch: neither file is solvable alone. They are **complementary**.

- The PNG has steganographic data extracted via `zsteg` — but it's encrypted (AES-256-CBC). 
- The text file's hex data, when converted to binary, contains:
  - An AES key (bytes 128-160 of the binary)
  - An IV (bytes 256-272 of the binary)  
  - A large block of decoy "corrupted" data (random bytes with occasional readable strings)
  - A SHA-256 hash (last 32 bytes) that validates the correct key+IV selection

Players must:
1. Extract the encrypted blob from the PNG
2. Parse the hex data carefully (byte offsets matter — the header misleads about the format)
3. Identify the AES key and IV using the SHA-256 checksum to verify
4. Decrypt the stego extraction → but the result is a **password-protected 7z archive** (embedded as raw bytes)
5. The 7z password is derived from the PNG's palette: take every Nth palette entry (where N = number of unique colors mod 7), concatenate the R values as ASCII

**Skill tested:** Cross-file correlation, AES decryption with key extraction, binary parsing at specific offsets, 7z handling, creative key derivation.

**Layer structure:** Cross-file dependency ensures no single-path shortcut exists.

**False flag:**
- The hex file's readable strings include `DECRYPTION_KEY: 54 68 61 6E 6F 73` (spells "Thanos" in ASCII). Using this as the AES key produces decryptable-looking output that's actually pseudorandom.
- The `zsteg` output, before AES decryption, contains the string `flag{` followed by garbage — making it look like the flag is corrupted rather than encrypted.

**Anti-LLM analysis:**
- **LLM approach:** Extract stego data, see `flag{` + garbage, conclude the flag is corrupted. Alternatively, find the decoy key in the hex file, attempt decryption, see pseudorandom output, conclude the data is damaged. 
- **Why LLM fails:** The cross-file dependency is the killer. LLMs analyze files independently. The concept of "neither file makes sense alone, they complete each other" requires holistic thinking. The byte offset parsing requires precision — off by one byte and the key is wrong. The palette-derived password is deeply non-obvious.
- **Why humans succeed:** Experienced CTF players recognize the pattern of complementary files. They'd try cross-referencing early. The SHA-256 hash serves as a verification mechanism — "I know I have the right key when the hash matches."

> [!WARNING]
> **Complexity concern:** This has ~5 layers with cross-file dependencies. If a player misidentifies the byte offsets, they're completely stuck with no feedback. The SHA-256 verification step is critical — it's the only breadcrumb. Make sure the challenge description subtly mentions "integrity verification" to hint at the hash.

---

## 🟣 OPTIONAL META CHALLENGE

---

### Meta: "Endgame" — Interrogative / Multi-domain

**Concept:** Unlocked after completing at least 8/12 challenges. Players receive a "mission debrief" document that *summarizes* (with deliberate errors) the flags they've already found. The debrief contains 3 factual errors about the challenge solutions, 2 tampered flag values, and 1 additional clue hidden in the document's structure.

Players must:
1. Identify which parts of the debrief are wrong (requires remembering/re-checking their own solutions)
2. The 3 factual errors, when corrected, produce 3 words
3. The 2 tampered flags, when compared to real flags (XOR difference), produce 2 characters
4. The structural clue (specific paragraph lengths form a number in unary) gives a shift value
5. Combine and decode → meta flag

**Skill tested:** Verification, attention to detail, adversarial document analysis, cross-referencing past work.

**Anti-LLM analysis:**
- This is fundamentally anti-LLM because it requires *memory of previous work* and the ability to detect subtle factual errors in a document that's 95% correct. An LLM running fresh would have no baseline to compare against.

> [!NOTE]
> This challenge's difficulty scales with player count — early finishers get less help. However, it should NOT require all 12 challenges to be solved, only 8, to avoid bottlenecking on a particularly hard standalone challenge.

---

## Anti-LLM Design Patterns Summary

| Pattern | Used In | Description |
|---|---|---|
| **High-confidence false flag** | All | Plant an extraction that looks exactly like a correct answer |
| **Cross-file dependency** | H2 | Neither artifact is solvable independently |
| **Visual/perceptual reasoning** | H1, M2 | Requires seeing spatial patterns or visual similarity |
| **Semantic misdirection** | M6, E3 | A keyword means something different than its obvious interpretation |
| **Tool parameter sensitivity** | E2, M3, M4 | Default tool settings miss the real data |
| **Geographic/spatial intuition** | M1 | Recognizing impossible coordinates requires world knowledge |
| **Identity correlation** | M5 | Cross-platform identity verification |
| **Memory/verification** | Meta | Requires comparing against previously solved data |
| **Custom format parsing** | M6, H2 | Non-standard binary formats that tools don't auto-parse |

---

## Known Weaknesses & Open Questions

1. **Infrastructure complexity:** M5 and M1 require hosted pages. How many web services can the CTF infra support?
2. **Tool version sensitivity:** Stego challenges may behave differently across `zsteg` / `steghide` / `binwalk` versions. All challenges must be tested on a reference environment.
3. **Difficulty calibration:** The "30-minute solve" for mediums is optimistic for M4 (10 images) and M6 (custom format RE). Consider bumping one to Hard.
4. **Domain balance:** Currently 2 OSINT, 3 Stego (and one hard is stego-heavy), 2 Audio, 2 Misc, 2 Multi-domain. Is stego overrepresented?
5. **Meta challenge timing:** If unlocked too late, it adds time pressure. If too early, players might rush through standing challenges to unlock it.

---

> **Next steps:** Critique these concepts, identify which ones you want to develop further, and tell me which ideas feel too weak or too strong. I'll refine accordingly.
