from flask import Flask, jsonify, request
import pymysql
import pika
import dotenv
import time
import os
import json

app = Flask(__name__)

dotenv.load_dotenv()

def create_connection():
  for _ in range(10):
    try:
      return pymysql.connect(
      host=os.environ['DB_HOST'],
      user=os.environ['DB_USER'],
      password=os.environ['DB_PASSWORD'],
      database=os.environ['DB_NAME'],
      cursorclass=pymysql.cursors.DictCursor,
      )
    except pymysql.err.OperationalError:
      time.sleep(5)
  raise Exception("Não foi possível conectar ao MySQL.")

def publish_order(order_data):
  connection_parameters = pika.ConnectionParameters(
  host="host.docker.internal",
  port=5672,
  credentials=pika.PlainCredentials(
    username="guest",
    password="guest"
  )
)
  channel = pika.BlockingConnection(connection_parameters).channel()
  channel.basic_publish(
  exchange="checkout",
  routing_key="",
  body=json.dumps(order_data),
  properties=pika.BasicProperties(
    delivery_mode=2
  )
)
  
@app.route('/create-order', methods=['POST'])
def create_order():
  connection = create_connection()
  data_order = request.json
  with connection:
      with connection.cursor() as cursor:
        query = "INSERT INTO orders_data (product_id, quantity) VALUES (%s, %s)"
        values = (data_order['product_id'], data_order['quantity'])
        cursor.execute(query, values)
        connection.commit()
      order_id = cursor.lastrowid

      order_data = {'order_id': order_id}
      publish_order(order_data)
  return jsonify({'message': 'Order created', 'order_id': order_id}), 201


@app.route('/dados')
def dados():
  connection = create_connection()
  with connection:
      with connection.cursor() as cursor:
        query = "SELECT * FROM orders_data"
        cursor.execute(query)
        data = cursor.fetchall()
        connection.commit()
      return jsonify(data)



if __name__ == '__main__':
  app.run(host="0.0.0.0", port=8000)