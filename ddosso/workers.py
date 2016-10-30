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

from ddosso.util import captcha_data

import firenado.conf
from firenado.config import load_yaml_config_file
import pika
import logging
import os
import time

logger = logging.getLogger(__name__)

print(firenado.conf.APP_CONFIG_FILE)

rabbitmq_conf = load_yaml_config_file(os.path.join(
    firenado.conf.APP_CONFIG_PATH,'rabbitmq.yml'))

creds = pika.PlainCredentials(rabbitmq_conf['user'],rabbitmq_conf['pass'])
params = pika.ConnectionParameters(
    host=rabbitmq_conf['host'],
    port=rabbitmq_conf['port'],
    virtual_host='/',
    credentials=creds
)

connection = pika.BlockingConnection(params)

channel = connection.channel()

channel.queue_declare(queue='ddosso_keygen_rpc_queue')

channel.queue_declare(queue='ddosso_captcha_rpc_queue')


def on_keygen_request(ch, method, props, body):
    logger.info("Ping received from %s." % body)
    response = 'Pong'
    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(
                         correlation_id=props.correlation_id),
                     body=response)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def on_captcha_request(ch, method, props, body):
    logger.info("Generating captcha for %s." % body.decode('utf-8'))
    start = int(time.time() * 1000)
    response = captcha_data(body.decode('utf-8'))
    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(
                         correlation_id=props.correlation_id),
                     body=response)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    end = int(time.time() * 1000)
    logger.info("Captcha for %s generated in %i ms." % (body.decode('utf-8'),
                                                        end-start))

channel.basic_qos(prefetch_count=1)

channel.basic_consume(on_keygen_request, queue='ddosso_keygen_rpc_queue')
channel.basic_consume(on_captcha_request, queue='ddosso_captcha_rpc_queue')

logger.info(" [x] Awaiting RPC requests")

channel.start_consuming()
