#!/usr/bin/env python3
"""
Build script for "The Snap" CTF Challenge
Constructs the multi-layered challenge file from i_am_iron_man.mp3

Layers:
  1. Spectrogram text in MP3 (high-freq tones) -> Part 1: MYTHIX{I_
  2. Embedded PNG + decoy TXT in MP3 (via binwalk/concat)
  3. PNG with EXIF false flag + LSB stego (3 base64 strings, 2 decoys)
  4. WAV embedded in PNG with dual-frequency morse (800Hz decoy + 6000Hz real)

Flag: MYTHIX{I_4m_Ir0n_M4n_6000}
"""

import struct
import wave
import io
import os
import sys
import base64
import zlib
import math
import random

# numpy for audio signal generation
import numpy as np
from PIL import Image, PngImagePlugin

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_MP3 = os.path.join(BASE_DIR, "i_am_iron_man.mp3")
OUTPUT_DIR = os.path.join(BASE_DIR, "challenge_output")
FINAL_FILE = os.path.join(OUTPUT_DIR, "the_snap.mp3")

# Flag parts
FLAG_PART1 = "MYTHIX{I_"       # Hidden in spectrogram
FLAG_PART2 = "4m_Ir0n_"        # LSB -> base64 -> hex -> ASCII
FLAG_PART3 = "M4n_6000}"       # Morse @ 6kHz -> hex -> ASCII

# False flags
FALSE_FLAG_TXT = "MYTHIX{sn4p_complete_3000}"
FALSE_FLAG_EXIF = "flag_candidate: MYTHIX{r3ality_st0ne_activated}"
FALSE_FLAG_LSB1 = "MYTHIX{sn4p_complete_3000}"  # same as txt, reinforces
FALSE_FLAG_LSB2 = "flag{not_the_real_one}"

# Audio parameters
SAMPLE_RATE = 44100
MORSE_WPM_DECOY = 20
MORSE_WPM_REAL = 15

# Morse code dictionary
MORSE_CODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', ' ': ' ', '_': '..--.-', '{': '-.--.',
    '}': '-.--.-', '#': '', '$': '', '@': ''
}


# ─────────────────────────────────────────────
# Step 1: Generate the PNG Image
# ─────────────────────────────────────────────
def generate_gauntlet_image(width=800, height=600):
    """Generate an abstract 'gauntlet energy' image with swirling colors."""
    print("[*] Generating gauntlet.png image...")
    img = Image.new('RGB', (width, height))
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            # Create swirling abstract pattern
            cx, cy = width / 2, height / 2
            dx, dy = x - cx, y - cy
            dist = math.sqrt(dx * dx + dy * dy)
            angle = math.atan2(dy, dx)

            # Purple-gold-orange galaxy swirl
            r = int(128 + 127 * math.sin(dist * 0.03 + angle * 3))
            g = int(80 + 80 * math.sin(dist * 0.025 - angle * 2 + 1.5))
            b = int(140 + 115 * math.sin(dist * 0.02 + angle * 4 + 3.0))

            # Ensure even values for LSB embedding later (clear LSB)
            r = r & 0xFE
            g = g & 0xFE
            b = b & 0xFE

            pixels[x, y] = (r, g, b)

    return img


# ─────────────────────────────────────────────
# Step 2: LSB Steganography (Red Channel)
# ─────────────────────────────────────────────
def encode_lsb_red_channel(img, message_bytes):
    """Encode data into the LSB of the red channel."""
    print(f"[*] Encoding {len(message_bytes)} bytes into red channel LSB...")
    pixels = img.load()
    width, height = img.size

    # Convert message to bits
    bits = []
    for byte in message_bytes:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)

    # Check capacity
    max_bits = width * height
    if len(bits) > max_bits:
        raise ValueError(f"Message too large: {len(bits)} bits > {max_bits} capacity")

    bit_idx = 0
    for y in range(height):
        for x in range(width):
            if bit_idx >= len(bits):
                break
            r, g, b = pixels[x, y]
            # Set LSB of red channel
            r = (r & 0xFE) | bits[bit_idx]
            pixels[x, y] = (r, g, b)
            bit_idx += 1

    print(f"[+] Encoded {bit_idx} bits into image")
    return img


def build_lsb_payload():
    """Build the LSB payload with 3 base64 strings (2 decoys + 1 real)."""

    # Decoy 1: Encodes to same false flag as mission_log.txt
    decoy1 = base64.b64encode(FALSE_FLAG_LSB1.encode()).decode()

    # Decoy 2: Wrong flag format
    decoy2 = base64.b64encode(FALSE_FLAG_LSB2.encode()).decode()

    # Real: Part 2 encoded as hex, then base64
    # 4m_Ir0n_ -> hex -> 346d5f4972306e5f -> base64
    part2_hex = FLAG_PART2.encode().hex()  # "346d5f4972306e5f"
    real_b64 = base64.b64encode(part2_hex.encode()).decode()

    # Build payload: newline-separated base64 strings
    # Order: decoy1, real (hidden in the middle), decoy2
    payload = f"{decoy1}\n{real_b64}\n{decoy2}"

    print(f"[*] LSB Payload constructed:")
    print(f"    Decoy 1 (b64): {decoy1}")
    print(f"      -> decodes to: {FALSE_FLAG_LSB1}")
    print(f"    Real   (b64): {real_b64}")
    print(f"      -> decodes to hex: {part2_hex}")
    print(f"      -> hex decodes to: {FLAG_PART2}")
    print(f"    Decoy 2 (b64): {decoy2}")
    print(f"      -> decodes to: {FALSE_FLAG_LSB2}")

    return payload.encode()


# ─────────────────────────────────────────────
# Step 3: Generate Morse Code Audio (WAV)
# ─────────────────────────────────────────────
def text_to_morse(text):
    """Convert text to morse code string."""
    result = []
    for char in text.upper():
        if char in MORSE_CODE:
            result.append(MORSE_CODE[char])
    return ' '.join(result)


def generate_morse_tone(morse_str, frequency, wpm, sample_rate=44100):
    """Generate audio samples for morse code at given frequency and WPM."""
    # Timing based on WPM (PARIS standard)
    dot_duration = 1.2 / wpm  # seconds per dot

    samples = []

    for i, char in enumerate(morse_str):
        if char == '.':
            duration = dot_duration
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            tone = np.sin(2 * np.pi * frequency * t)
            # Apply envelope to avoid clicks
            envelope = np.ones_like(t)
            ramp = min(int(0.005 * sample_rate), len(t) // 4)
            if ramp > 0:
                envelope[:ramp] = np.linspace(0, 1, ramp)
                envelope[-ramp:] = np.linspace(1, 0, ramp)
            samples.extend(tone * envelope)
            # Inter-element gap (1 dot)
            gap = int(sample_rate * dot_duration)
            samples.extend([0.0] * gap)

        elif char == '-':
            duration = dot_duration * 3
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            tone = np.sin(2 * np.pi * frequency * t)
            envelope = np.ones_like(t)
            ramp = min(int(0.005 * sample_rate), len(t) // 4)
            if ramp > 0:
                envelope[:ramp] = np.linspace(0, 1, ramp)
                envelope[-ramp:] = np.linspace(1, 0, ramp)
            samples.extend(tone * envelope)
            # Inter-element gap
            gap = int(sample_rate * dot_duration)
            samples.extend([0.0] * gap)

        elif char == ' ':
            # Check if word gap (double space) or letter gap
            # Letter gap = 3 dots (already 1 from inter-element, so add 2 more)
            if i + 1 < len(morse_str) and morse_str[i + 1] == ' ':
                continue  # skip, next space handles word gap
            elif i > 0 and morse_str[i - 1] == ' ':
                # Word gap = 7 dots (already 3 from letter, so add 4 more)
                gap = int(sample_rate * dot_duration * 4)
                samples.extend([0.0] * gap)
            else:
                # Letter gap
                gap = int(sample_rate * dot_duration * 2)
                samples.extend([0.0] * gap)

    return np.array(samples)


def generate_morse_wav():
    """Generate WAV with dual-frequency morse: 800Hz decoy + 6000Hz real."""
    print("[*] Generating morse_signal.wav...")

    # Decoy morse at 800 Hz (obvious frequency)
    decoy_text = "ENDGAME"
    decoy_morse = text_to_morse(decoy_text)
    print(f"    Decoy morse ({decoy_text}): {decoy_morse}")
    decoy_samples = generate_morse_tone(decoy_morse, 800, MORSE_WPM_DECOY, SAMPLE_RATE)

    # Real morse at 6000 Hz (requires filtering/spectrogram analysis)
    # Part 3 as hex: M4n_6000} -> hex
    part3_hex = FLAG_PART3.encode().hex()  # "4d346e5f36303030fD" wait no
    # Actually let's make the morse decode directly to the part3 text
    # But encode it as hex to add the extra decode step
    real_text = part3_hex.upper()
    real_morse = text_to_morse(real_text)
    print(f"    Real morse (hex of '{FLAG_PART3}'): {real_text}")
    print(f"    Real morse: {real_morse}")
    real_samples = generate_morse_tone(real_morse, 6000, MORSE_WPM_REAL, SAMPLE_RATE)

    # Make both signals the same length (pad shorter one)
    max_len = max(len(decoy_samples), len(real_samples))
    decoy_padded = np.zeros(max_len)
    real_padded = np.zeros(max_len)
    decoy_padded[:len(decoy_samples)] = decoy_samples
    real_padded[:len(real_samples)] = real_samples

    # Mix: decoy louder (0.7), real quieter (0.3)
    mixed = decoy_padded * 0.7 + real_padded * 0.3

    # Add subtle background noise
    noise = np.random.normal(0, 0.02, max_len)
    mixed = mixed + noise

    # Normalize
    mixed = mixed / np.max(np.abs(mixed)) * 0.9

    # Convert to 16-bit PCM
    pcm = (mixed * 32767).astype(np.int16)

    # Write WAV
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())

    wav_data = wav_buffer.getvalue()
    print(f"[+] Generated morse WAV: {len(wav_data)} bytes")
    return wav_data


# ─────────────────────────────────────────────
# Step 4: Generate Spectrogram Text for MP3
# ─────────────────────────────────────────────

# Simple bitmap font for spectrogram text (5x7 pixel characters)
FONT = {
    'M': [
        [1,0,0,0,1],
        [1,1,0,1,1],
        [1,0,1,0,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
    ],
    'Y': [
        [1,0,0,0,1],
        [1,0,0,0,1],
        [0,1,0,1,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
    ],
    'T': [
        [1,1,1,1,1],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
    ],
    'H': [
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,1,1,1,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
        [1,0,0,0,1],
    ],
    'I': [
        [1,1,1,1,1],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [1,1,1,1,1],
    ],
    'X': [
        [1,0,0,0,1],
        [0,1,0,1,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,1,0,1,0],
        [1,0,0,0,1],
    ],
    '{': [
        [0,0,1,1,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,1,0,0,0],
        [0,0,1,0,0],
        [0,0,1,0,0],
        [0,0,1,1,0],
    ],
    '_': [
        [0,0,0,0,0],
        [0,0,0,0,0],
        [0,0,0,0,0],
        [0,0,0,0,0],
        [0,0,0,0,0],
        [0,0,0,0,0],
        [1,1,1,1,1],
    ],
}


def generate_spectrogram_audio(text, duration_sec=None):
    """
    Generate audio where the spectrogram visually shows text.
    Each text column becomes a set of frequency bins that are 'on'.
    Text appears in the 15-19 kHz range.
    """
    print(f"[*] Generating spectrogram text: '{text}'")

    # Build bitmap for the full text
    bitmap = []
    for ch in text:
        if ch in FONT:
            for row_idx in range(7):
                if row_idx >= len(bitmap):
                    bitmap.append([])
                bitmap[row_idx].extend(FONT[ch][row_idx])
                bitmap[row_idx].append(0)  # gap between chars
        else:
            # Unknown char: blank space
            for row_idx in range(7):
                if row_idx >= len(bitmap):
                    bitmap.append([])
                bitmap[row_idx].extend([0, 0, 0, 0, 0, 0])

    text_width = len(bitmap[0]) if bitmap else 0
    text_height = len(bitmap)  # 7 rows

    print(f"    Bitmap size: {text_width} x {text_height}")

    # Map rows to frequencies (15 kHz to 19 kHz, bottom row = 15kHz)
    freq_low = 15000
    freq_high = 19000
    freqs = [freq_low + (freq_high - freq_low) * (text_height - 1 - r) / (text_height - 1)
             for r in range(text_height)]

    # Each column lasts for a short time
    col_duration = 0.04  # 40ms per column
    if duration_sec is None:
        duration_sec = col_duration * text_width + 0.5  # small padding

    total_samples = int(SAMPLE_RATE * duration_sec)
    samples = np.zeros(total_samples)

    # For each column in the bitmap
    for col_idx in range(text_width):
        t_start = col_idx * col_duration
        t_end = t_start + col_duration
        n_start = int(t_start * SAMPLE_RATE)
        n_end = min(int(t_end * SAMPLE_RATE), total_samples)

        if n_start >= total_samples:
            break

        t = np.arange(n_end - n_start) / SAMPLE_RATE

        for row_idx in range(text_height):
            if bitmap[row_idx][col_idx]:
                freq = freqs[row_idx]
                # Add sine wave at this frequency
                samples[n_start:n_end] += 0.15 * np.sin(2 * np.pi * freq * t)

    # Normalize
    max_val = np.max(np.abs(samples))
    if max_val > 0:
        samples = samples / max_val * 0.3  # Keep amplitude low
    
    print(f"[+] Generated spectrogram audio: {len(samples)} samples ({duration_sec:.1f}s)")
    return samples


# ─────────────────────────────────────────────
# Step 5: Embed WAV Inside PNG (after IEND)
# ─────────────────────────────────────────────
def embed_in_png(png_data, embedded_data, marker=b"WAV_EMBED"):
    """Append data after the PNG IEND chunk so binwalk can find it."""
    # Find the IEND chunk
    iend_pos = png_data.rfind(b'IEND')
    if iend_pos < 0:
        raise ValueError("No IEND chunk found in PNG data")

    # IEND chunk is: length(4) + 'IEND'(4) + CRC(4) = 12 bytes
    # The length field is 4 bytes before 'IEND'
    iend_end = iend_pos + 4 + 4  # past 'IEND' + CRC

    print(f"[*] Embedding {len(embedded_data)} bytes after PNG IEND at offset {iend_end}")

    # The embedded data is a valid WAV, so binwalk will find the RIFF header
    result = png_data[:iend_end] + embedded_data
    return result


# ─────────────────────────────────────────────
# Step 6: Build the Decoy mission_log.txt
# ─────────────────────────────────────────────
def build_mission_log():
    """Create the decoy mission_log.txt with false flag."""
    fake_b64 = base64.b64encode(FALSE_FLAG_TXT.encode()).decode()

    content = f"""=== STARK INDUSTRIES - CLASSIFIED ===
Mission: Operation Temporal Reversion
Status: COMPROMISED
Date: [REDACTED]

Agent, we've intercepted the following encoded transmission from 
the Quantum Realm stabilizer array. Decode immediately.

ENCODED PAYLOAD:
{fake_b64}

NOTE: This was recovered from Sector 7-G before the snap event.
All other data in this sector has been decimated.
Handle with extreme caution.

=== END TRANSMISSION ===
"""
    print(f"[*] Built mission_log.txt (decoy)")
    print(f"    Contains base64: {fake_b64}")
    print(f"    Decodes to: {FALSE_FLAG_TXT}")
    return content.encode()


# ─────────────────────────────────────────────
# Step 7: Mix Spectrogram into MP3 Audio
# ─────────────────────────────────────────────
def mix_spectrogram_into_mp3(mp3_path, spec_samples, output_wav_path):
    """
    Convert MP3 to WAV, mix in spectrogram tones, save as WAV.
    The final step converts back to MP3 via ffmpeg.
    """
    import subprocess

    # Convert MP3 to WAV
    temp_wav = output_wav_path + ".temp.wav"
    print(f"[*] Converting MP3 to WAV...")
    subprocess.run([
        'ffmpeg', '-y', '-i', mp3_path,
        '-ar', str(SAMPLE_RATE), '-ac', '1', '-f', 'wav', temp_wav
    ], capture_output=True, check=True)

    # Read the WAV
    with wave.open(temp_wav, 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        audio_data = wf.readframes(n_frames)

    # Convert to numpy
    if sampwidth == 2:
        audio = np.frombuffer(audio_data, dtype=np.int16).astype(np.float64)
    else:
        raise ValueError(f"Unexpected sample width: {sampwidth}")

    audio = audio / 32768.0  # normalize to [-1, 1]

    # Pad or trim spectrogram to match audio length
    if len(spec_samples) > len(audio):
        spec_samples = spec_samples[:len(audio)]
    else:
        padded = np.zeros(len(audio))
        # Place spectrogram in the middle of the audio
        offset = (len(audio) - len(spec_samples)) // 2
        padded[offset:offset + len(spec_samples)] = spec_samples
        spec_samples = padded

    # Mix
    mixed = audio + spec_samples

    # Normalize
    mixed = mixed / np.max(np.abs(mixed)) * 0.95

    # Convert to 16-bit
    pcm = (mixed * 32767).astype(np.int16)

    # Write mixed WAV
    with wave.open(output_wav_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())

    # Clean up
    os.remove(temp_wav)
    print(f"[+] Mixed spectrogram into audio: {output_wav_path}")


# ─────────────────────────────────────────────
# Step 8: Assemble Final Challenge
# ─────────────────────────────────────────────
def assemble_challenge():
    """Main build function — assembles all layers into the final challenge file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("  Building 'The Snap' CTF Challenge")
    print("=" * 60)
    print()

    # ── Step 1: Generate PNG image ──
    img = generate_gauntlet_image(800, 600)

    # ── Step 2: Build LSB payload and encode ──
    lsb_payload = build_lsb_payload()
    img = encode_lsb_red_channel(img, lsb_payload)

    # ── Step 3: Save PNG with EXIF false flag ──
    png_buffer = io.BytesIO()
    # Add text metadata (EXIF-like) as PNG tEXt chunk
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", FALSE_FLAG_EXIF)
    meta.add_text("Author", "S.H.I.E.L.D. Quantum Division")
    meta.add_text("Description", "Gauntlet energy signature scan - classified")
    img.save(png_buffer, format='PNG', pnginfo=meta)
    png_data = png_buffer.getvalue()
    print(f"[+] PNG with LSB + metadata: {len(png_data)} bytes")

    # ── Step 4: Generate Morse WAV ──
    wav_data = generate_morse_wav()

    # Save standalone WAV for testing
    wav_test_path = os.path.join(OUTPUT_DIR, "morse_signal_test.wav")
    with open(wav_test_path, 'wb') as f:
        f.write(wav_data)

    # Save clean PNG (for testing)
    png_test_path = os.path.join(OUTPUT_DIR, "gauntlet.png")
    with open(png_test_path, 'wb') as f:
        f.write(png_data)

    # ── Step 5: Generate spectrogram audio ──
    spec_samples = generate_spectrogram_audio(FLAG_PART1)

    # ── Step 6: Mix spectrogram into MP3 ──
    mixed_wav_path = os.path.join(OUTPUT_DIR, "mixed_audio.wav")
    mix_spectrogram_into_mp3(INPUT_MP3, spec_samples, mixed_wav_path)

    # ── Step 7: Convert mixed WAV back to MP3 ──
    import subprocess
    mixed_mp3_path = os.path.join(OUTPUT_DIR, "mixed_audio.mp3")
    print(f"[*] Converting mixed audio to MP3...")
    subprocess.run([
        'ffmpeg', '-y', '-i', mixed_wav_path,
        '-codec:a', 'libmp3lame', '-b:a', '128k',
        mixed_mp3_path
    ], capture_output=True, check=True)

    # ── Step 8: Build mission_log.txt ──
    mission_log_data = build_mission_log()

    # Save for testing
    with open(os.path.join(OUTPUT_DIR, "mission_log.txt"), 'wb') as f:
        f.write(mission_log_data)

    # ── Step 9: Assemble final file ──
    # Architecture: MP3 + PNG + ZIP(WAV) + TXT all concatenated at top level.
    # binwalk v3 detects PNG and ZIP natively.
    # The ZIP contains the morse WAV, requiring an extra extraction step.
    print(f"[*] Assembling final challenge file...")
    with open(mixed_mp3_path, 'rb') as f:
        mp3_data = f.read()

    # Wrap WAV in a ZIP archive (binwalk v3 detects ZIP reliably, but not raw RIFF/WAV)
    import zipfile
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("quantum_signal.wav", wav_data)
    zip_data = zip_buffer.getvalue()
    print(f"[+] WAV wrapped in ZIP: {len(zip_data)} bytes")

    # Build final file: MP3 data + PNG + ZIP(WAV) + mission_log.txt
    # All separate — binwalk finds each independently
    final_data = mp3_data + png_data + zip_data + mission_log_data

    with open(FINAL_FILE, 'wb') as f:
        f.write(final_data)

    print()
    print("=" * 60)
    print(f"[✓] Challenge built successfully!")
    print(f"    Output: {FINAL_FILE}")
    print(f"    Size: {len(final_data)} bytes ({len(final_data)/1024:.1f} KB)")
    print("=" * 60)
    print()
    print("Solve path summary:")
    print(f"  1. Spectrogram (15-19 kHz)  -> '{FLAG_PART1}'")
    print(f"  2. binwalk MP3 -> extracts PNG + WAV + mission_log.txt")
    print(f"     mission_log.txt -> false flag (DECOY): {FALSE_FLAG_TXT}")
    print(f"  3. PNG metadata -> false flag (DECOY): MYTHIX{{r3ality_st0ne_activated}}")
    print(f"  4. PNG LSB red channel -> 3 base64 strings (2 decoys)")
    print(f"     Real base64 -> hex -> '{FLAG_PART2}'")
    print(f"  5. WAV spectrogram/audio analysis:")
    print(f"     800 Hz morse -> 'ENDGAME' (DECOY)")
    print(f"     6000 Hz morse -> hex -> '{FLAG_PART3}'")
    print(f"  FULL FLAG: MYTHIX{{I_4m_Ir0n_M4n_6000}}")

    # Clean up intermediate files
    os.remove(mixed_wav_path)
    os.remove(mixed_mp3_path)
    print("\n[*] Cleaned up intermediate files.")

    return FINAL_FILE


if __name__ == '__main__':
    assemble_challenge()
