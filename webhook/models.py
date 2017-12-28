# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import redis
# Create your models here.


class RedisClient(object):
    CONVERSATION_TAG = 'cryptobot'

    def __init__(self):
        self.redis = redis.StrictRedis(host='localhost', port=6379, db=0)

    def append(self, key, value):
        return self.redis.set(key, value)

    def get(self, key):
        return self.redis.get(key)

    def exist(self, key):
        return self.redis.exists(self.CONVERSATION_TAG + '-' + key)

    def delete(self, key):
        return self.redis.delete(self.CONVERSATION_TAG + '-' + key)

    def append_to_dict(self, user_id, key, value):
        return self.redis.hmset(self.CONVERSATION_TAG + '-' + user_id, {'user_id': user_id, key: value})

    def get_dict(self, user_id):
        return self.redis.hgetall(self.CONVERSATION_TAG + user_id)

    def increment_by(self, user_id, key, value):
        return self.redis.hincrby(self.CONVERSATION_TAG + '-' + user_id, key, value)

    def get_value_dict(self, user_id, key):
        return self.redis.hget(self.CONVERSATION_TAG + '-' + user_id, key)

    def expire(self, key, time):
        return self.redis.expire(key, time)

redisCli = RedisClient()
