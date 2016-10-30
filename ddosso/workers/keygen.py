#!/usr/bin/env python
#
# Copyright 2016 Flavio Garcia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ddosso.util import generate_private_key

import firenado.conf
from firenado.config import load_yaml_config_file
import pika
import logging
import os
import time
import base64

logger = logging.getLogger(__name__)

rabbitmq_conf = load_yaml_config_file(os.path.join(
    firenado.conf.APP_CONFIG_PATH,'rabbitmq.yml'))

creds = pika.PlainCredentials(rabbitmq_conf['user'],rabbitmq_conf['pass'])

params = pika.ConnectionParameters(
    host=rabbitmq_conf['host'],
    port=rabbitmq_conf['port'],
    virtual_host='/',
    credentials=creds
)
# Based on: http://bit.ly/2eS1KYP

channel = None


# Step #2
def on_connected(connection):
    """Called when we are fully connected to RabbitMQ"""
    # Open a channel
    connection.channel(on_channel_open)

# Step #3
def on_channel_open(new_channel):
    """Called when our channel has opened"""
    global channel
    channel = new_channel
    channel.queue_declare(queue="ddosso_keygen_rpc_queue", durable=True,
                          exclusive=False, auto_delete=False,
                          callback=on_keygen_queue_declared)


# Step #4
def on_keygen_queue_declared(frame):
    """Called when RabbitMQ has told us our Queue has been declared, frame is
    the response from RabbitMQ"""
    channel.basic_consume(handle_keygen_delivery,
                          queue='ddosso_keygen_rpc_queue')


def handle_keygen_delivery(ch, method, props, body):
    print(body)
    logger.info("Generating private key for user %s." % body.decode('utf-8'))
    start = int(time.time() * 1000)
    private_key = generate_private_key()
    response = base64.b64encode(private_key.encode('ascii'))
    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(
                         correlation_id=props.correlation_id),
                     body=response)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    end = int(time.time() * 1000)
    logger.info("Private key for user %s generated in %i ms." % (
        body.decode('utf-8'), end - start))


connection = pika.SelectConnection(params, on_connected)

try:
    # Loop so we can communicate with RabbitMQ
    connection.ioloop.start()
except KeyboardInterrupt:
    # Gracefully close the connection
    connection.close()
    # Loop until we're fully closed, will stop on its own
    connection.ioloop.start()
