# For product service
cd product-service
python -m grpc_tools.protoc -Iproto --python_out=./proto/generated --grpc_python_out=./proto/generated proto/product.proto proto/order.proto

# For order service
cd order-service
python -m grpc_tools.protoc -Iproto --python_out=./proto/generated --grpc_python_out=./proto/generated proto/order.proto proto/product.proto
