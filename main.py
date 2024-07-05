from flask import Flask, request, jsonify
import consul
from dotenv import load_dotenv  
import os
import re

load_dotenv()

app = Flask(__name__)

consul_client = consul.Consul(
    host=os.getenv('CONSUL_HOST'),
    port=int(os.getenv('CONSUL_PORT'))
)

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        service_name = data.get('service_name')
        service_id = data.get('service_id', service_name)
        service_address = data.get('service_address')
        service_port = data.get('service_port')
        tags = data.get('tags', [])

        if not any([service_name, service_address, service_port]):
            return jsonify({'message': 'Service name, address and port are required'}), 400

        if re.match('^[a-zA-Z0-9_-]+$', service_id) is None:
            return jsonify({'message': 'Service ID must contain only letters, numbers, hyphens and underscores'}), 400
        
        service_port = int(service_port)
        
        if consul_client.agent.services().get(service_id):
            return jsonify({'message': 'Service already registered'}), 204
        
        consul_client.agent.service.register(
            name=service_name,
            service_id=service_id,
            address=service_address,
            port=service_port,
            tags=tags
        )

        return jsonify({'message': f'Service {service_id} registered'}), 201
    
    except Exception as e:
        print(e)
        return jsonify({'message': 'Error registering service'}), 500


@app.route('/deregister', methods=['POST'])
def deregister():
    data = request.json
    service_id = data.get('service_id')
    if not service_id:
        return jsonify({'message': 'Service ID is required'}), 400
    
    if not consul_client.agent.services().get(service_id):
        return jsonify({'message': 'Service not found'}), 404

    consul_client.agent.service.deregister(service_id)

    return jsonify({'message': f'Service {service_id} deregistered'}), 200

@app.route('/services', methods=['GET'])
def get_services():
    services = consul_client.agent.services()
    return jsonify(services), 200

@app.route('/service/<service_id>', methods=['GET'])
def get_service(service_id):
    service = consul_client.agent.services().get(service_id)
    if not service:
        return jsonify({'message': 'Service not found'}), 404
    
    return jsonify(service), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'message': 'Service Registry is running'}), 200

if __name__ == '__main__':
    app.run(host=os.getenv('SERVICE_REGISTRY_HOST'), port=os.getenv('SERVICE_REGISTRY_PORT'))
