import logging
import uuid

import django
from django.db.models.fields.related import RelatedField

from .model_cache_sharing.types import ModelCacheInfo
from .model_cache_sharing import model_cache_backend

logger = logging.getLogger(__name__)


def update_model_cache(table_name):
    """
    Updates model cache by generating a new key for the model
    """
    model_cache_info = ModelCacheInfo(table_name, uuid.uuid4().hex)
    model_cache_backend.share_model_cache_info(model_cache_info)


def is_related_field(field):
    return issubclass(type(field), RelatedField)


def invalidate_modelqueryset_cache(model, log_msg):
    logger.debug(log_msg)

    if django.VERSION >= (1, 8):
        all_fields = model._meta.get_fields()

        related_tables = set([
            f.related_model._meta.db_table for f in all_fields
            if ((f.one_to_many or f.one_to_one) and f.auto_created) or
            f.many_to_one or (f.many_to_many and not f.auto_created)]
        )
    else:
        related_objs = model._meta.get_all_related_objects()
        related_tables = set([
            rel.model._meta.db_table for rel in related_objs
        ])

        # temporary fix for m2m relations with an intermediate model, goes
        # away after better join caching

        model_fields = model._meta.fields
        related_tables |= set([
            field.rel.to._meta.db_table for field in model_fields if is_related_field()]
        )

    logger.debug(
        'Related tables of sender {0} are {1}'.format(model, related_tables)
    )

    update_model_cache(model._meta.db_table)
    for related_table in related_tables:
        update_model_cache(related_table)
