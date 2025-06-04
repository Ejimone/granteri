from flask import Flask, request, jsonify

app = Flask(__name__)
# Handle real-time events for both client and server
@app.route('/webhook/vapi', methods=['POST'])
def handle_vapi_webhook():
    payload = request.get_json()
    message = payload.get('message', {})
    
    if message.get('type') == 'status-update':
        call = message.get('call', {})
        print(f"Call {call.get('id')}: {call.get('status')}")
        
    elif message.get('type') == 'transcript':
        print(f"{message.get('role')}: {message.get('transcript')}")
        
    elif message.get('type') == 'function-call':
        return handle_function_call(message)
    
    return jsonify({"received": True}), 200

def handle_function_call(message):
    function_call = message.get('functionCall', {})
    function_name = function_call.get('name')
    
    if function_name == 'lookup_order':
        order_data = {
            "orderId": function_call.get('parameters', {}).get('orderId'),
            "status": "shipped"
        }
        return jsonify({"result": order_data})
    
    return jsonify({"error": "Unknown function"}), 400

if __name__ == '__main__':
    app.run(port=5000)
