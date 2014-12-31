# -*- coding: utf-8 -*-
import logging
import uuid

from django.db.models.signals import post_save, post_delete

from .model_cache_sharing.types import ModelCacheInfo
from .model_cache_sharing import model_cache_backend

"""
Signal receivers for django model post_save and post_delete. Used to evict a model cache when
an update or delete happens on the model.
For compatibility with Django 1.5 these receivers live in models.py
"""

logger = logging.getLogger(__name__)


def _invalidate(sender, instance, **kwargs):
    "Signal receiver for models"
    logger.debug('Received post_save/post_delete signal from sender {0}'.format(sender))
    model_cache_info = ModelCacheInfo(sender._meta.db_table, uuid.uuid4().hex)
    model_cache_backend.broadcast_model_cache_info(model_cache_info)

post_save.connect(_invalidate)
post_delete.connect(_invalidate)