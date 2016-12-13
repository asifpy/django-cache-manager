# -*- coding: utf-8 -*-
import logging
from django.db.models.signals import post_save, post_delete, m2m_changed

from .helpers import (
    invalidate_modelqueryset_cache,
    update_model_cache
)

"""
Signal receivers for django model post_save and post_delete. Used to evict a model cache when
an update or delete happens on the model.
For compatibility with Django 1.5 these receivers live in models.py
"""

logger = logging.getLogger(__name__)


def invalidate_model_cache(sender, instance, **kwargs):
    """
    Signal receiver for models to invalidate model cache of sender and related models.
    Model cache is invalidated by generating new key for each model.

    Parameters
    ~~~~~~~~~~
    sender
        The model class
    instance
        The actual instance being saved.
    """
    msg = 'Received post_save/post_delete signal from sender'
    log_msg = '{}{}'.format(msg, sender)

    # invalidate model cache
    invalidate_modelqueryset_cache(sender, log_msg)


def invalidate_m2m_cache(sender, instance, model, **kwargs):
    """
    Signal receiver for models to invalidate model cache for many-to-many relationship.

    Parameters
    ~~~~~~~~~~
    sender
        The model class
    instance
        The instance whose many-to-many relation is updated.
    model
        The class of the objects that are added to, removed from or cleared from the relation.
    """
    logger.debug('Received m2m_changed signals from sender {0}'.format(sender))
    update_model_cache(instance._meta.db_table)
    update_model_cache(model._meta.db_table)


post_save.connect(invalidate_model_cache)
post_delete.connect(invalidate_model_cache)
m2m_changed.connect(invalidate_m2m_cache)
