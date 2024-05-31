from flask import Flask, jsonify, request
import mysql.connector
import grpc
from concurrent import futures
from multiprocessing import Process
import proto.generated.order_pb2 as order_pb2
import proto.generated.order_pb2_grpc as order_pb2_grpc
import proto.generated.product_pb2 as product_pb2
import proto.generated.product_pb2_grpc as product_pb2_grpc

app = Flask(__name__)

# MySQL configuration
db_config = {
    'user': 'root',
    'password': 'password',
    'host': 'db_order',
    'database': 'order_db'
}


# Initialize the database and create tables
def init_db():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            quantity INT NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        INSERT INTO orders (product_id, quantity) VALUES
        (1, 2),
        (2, 1),
        (3, 5)
        ON DUPLICATE KEY UPDATE product_id=VALUES(product_id), quantity=VALUES(quantity)
    """)
    conn.commit()
    cursor.close()
    conn.close()


# gRPC OrderService implementation
class OrderService(order_pb2_grpc.OrderServiceServicer):
    def GetOrderCount(self, request, context):
        product_id = request.product_id
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders WHERE product_id = %s", (product_id,))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return order_pb2.OrderResponse(order_count=count)


# Register gRPC server
def serve():
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    order_pb2_grpc.add_OrderServiceServicer_to_server(OrderService(), grpc_server)
    grpc_server.add_insecure_port('[::]:50052')
    grpc_server.start()
    grpc_server.wait_for_termination()


@app.route('/orders/<int:product_id>/price', methods=['GET'])
def get_order_price(product_id):
    with grpc.insecure_channel('product:50051') as channel:
        stub = product_pb2_grpc.ProductServiceStub(channel)
        response = stub.GetProductPrice(product_pb2.ProductRequest(product_id=product_id))
        return jsonify({'product_id': product_id, 'price': response.price})


if __name__ == '__main__':
    init_db()
    grpc_process = Process(target=serve)
    grpc_process.start()
    try:
        app.run(host='0.0.0.0', port=5001, debug=True)
    finally:
        grpc_process.terminate()
