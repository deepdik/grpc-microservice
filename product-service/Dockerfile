FROM python:3.9-slim

WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

ENV PYTHONPATH="${PYTHONPATH}:/app/proto/generated"

# # Generate gRPC code
RUN python -m grpc_tools.protoc -Iproto --python_out=./proto/generated --grpc_python_out=./proto/generated proto/product.proto

RUN python -m grpc_tools.protoc -Iproto --python_out=./proto/generated --grpc_python_out=./proto/generated proto/order.proto


CMD ["python", "product.py"]
