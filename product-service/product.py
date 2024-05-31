import os

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
    'host': 'db_product',
    'database': 'product_db'
}

# Print environment variables
print("PYTHONPATH:", os.getenv('PYTHONPATH'))

# Initialize the database and create tables
def init_db():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            price DECIMAL(10, 2) NOT NULL
        )
    """)
    cursor.execute("""
        INSERT INTO products (name, price) VALUES
        ('Product1', 10.00),
        ('Product2', 20.00),
        ('Product3', 30.00)
        ON DUPLICATE KEY UPDATE name=VALUES(name), price=VALUES(price)
    """)
    conn.commit()
    cursor.close()
    conn.close()


# gRPC ProductService implementation
class ProductService(product_pb2_grpc.ProductServiceServicer):
    def GetProductPrice(self, request, context):
        product_id = request.product_id
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT price FROM products WHERE id = %s", (product_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return product_pb2.ProductResponse(price=row[0])
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Product not found')
            return product_pb2.ProductResponse()


# Register gRPC server
def serve():
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    product_pb2_grpc.add_ProductServiceServicer_to_server(ProductService(), grpc_server)
    grpc_server.add_insecure_port('[::]:50051')
    grpc_server.start()
    grpc_server.wait_for_termination()


@app.route('/product/<int:product_id>/orders', methods=['GET'])
def get_orders_for_product(product_id):
    with grpc.insecure_channel('order:50052') as channel:
        stub = order_pb2_grpc.OrderServiceStub(channel)
        response = stub.GetOrderCount(order_pb2.OrderRequest(product_id=product_id))
        return jsonify({'product_id': product_id, 'order_count': response.order_count})


if __name__ == '__main__':
    init_db()
    grpc_process = Process(target=serve)
    grpc_process.start()
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        grpc_process.terminate()
