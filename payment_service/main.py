from flask import Flask, jsonify
import pymysql
import pika
import dotenv
import time
import os
import json
import threading 

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

def process_order(ch, method, properties, body):
    try:
        order_data = json.loads(body)

        if 'order_id' not in order_data:
            print("Erro: 'order_id' não encontrado na mensagem.")
            return
        
        connection = create_connection()

        with connection:
            with connection.cursor() as cursor:
                query = "INSERT INTO payment_data (order_id) VALUES (%s)"
                cursor.execute(query, (order_data['order_id'],))
            connection.commit()
        
        print(f"Order {order_data['order_id']} processada com sucesso.")
    
    except Exception as e:
        print(f"Erro ao processar a ordem: {e}")



def consumer_order():
  connection_parameters = pika.ConnectionParameters(
  host="host.docker.internal",
  port=5672,
  credentials=pika.PlainCredentials(
    username="guest",
    password="guest"
  )
)
  channel = pika.BlockingConnection(connection_parameters).channel()
  channel.queue_declare(
    queue="checkout_queue",
    durable=True
  )
  channel.basic_consume(
    queue="checkout_queue",
    auto_ack=True,
    on_message_callback=process_order
  )

  channel.start_consuming()


@app.route('/dados')
def dados():
  connection = create_connection()
  with connection:
      with connection.cursor() as cursor:
        query = "SELECT * FROM payment_data"
        cursor.execute(query)
        data = cursor.fetchall()
        connection.commit()
      return jsonify(data)
  


if __name__ == '__main__':
  consumer_thread = threading.Thread(target=consumer_order)
  consumer_thread.start()

  app.run(host="0.0.0.0", port=5000)
