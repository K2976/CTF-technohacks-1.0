const input = document.getElementById('input');
const consoleDiv = document.getElementById('console');

input.addEventListener('keypress', async (e) => {
    if (e.key === 'Enter') {
        const val = input.value;
        input.value = '';
        consoleDiv.innerHTML += `\n> Submitting: ${val}`;

        const res = await fetch('/ctf/jailbreak/api/challenge', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ payload: val })
        });
        
        const data = await res.json();
        if (data.success) {
            consoleDiv.innerHTML += `\n[SUCCESS] ${data.message}\nFLAG: ${data.flag}`;
        } else {
            consoleDiv.innerHTML += `\n[DENIED] Stripped to: "${data.stripped}"\nHash: ${data.hash_received}`;
        }
        consoleDiv.scrollTop = consoleDiv.scrollHeight;
    }
});
