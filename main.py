import socket
import struct
import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # GitHub Pagesからのアクセスを許可！

SIG_HELPER_HOST = '127.0.0.1'
print(f"SIG_HELPER_HOST:{SIG_HELPER_HOST}")
SIG_HELPER_PORT = 12999
print(f"SIG_HELPER_PORT:{SIG_HELPER_PORT}")

def talk_to_rust(opcode, input_str):
    print(f"--- Sending to Rust (Opcode: {hex(opcode)}) ---")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SIG_HELPER_HOST, SIG_HELPER_PORT))
        
        req_id = 1
        print(f"req_id:{req_id}")
        payload_bytes = input_str.encode('utf-8')
        print(f"payload_bytes_len:{len(payload_bytes)}")
        
        # [opcode(1), req_id(4), data_size(2)] + data
        header = struct.pack('>BIH', opcode, req_id, len(payload_bytes))
        s.sendall(header + payload_bytes)
        
        # 受信: [req_id(4), total_size(4), res_str_size(2)] + data
        res_header = s.recv(10)
        _, _, res_str_size = struct.unpack('>IIH', res_header)
        print(f"res_str_size:{res_str_size}")
        
        result = s.recv(res_str_size).decode('utf-8')
        print(f"result:{result}")
        return result

@app.route('/<type>/<text>')
def handle_request(type, text):
    print(f"Request: type={type}, text={text[:20]}...")
    try:
        if type == 'n':
            res = talk_to_rust(0x01, text)
        elif type == 'sig':
            res = talk_to_rust(0x02, text)
        elif type == 'time':
            # タイムスタンプはOpcode 0x03 (引数不要だが関数は共通化)
            res = talk_to_rust(0x03, "")
        else:
            return jsonify({"status": "error", "msg": "Unknown type"}), 400
        
        return jsonify({"status": "ok", "result": res})
    except Exception as e:
        print(f"Error:{e}")
        return jsonify({"status": "error", "msg": str(e)}), 500

if __name__ == '__main__':
    # Renderのポート環境変数に対応（デフォルト10000）
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting Flask on port:{port}")
    app.run(host='0.0.0.0', port=port)
