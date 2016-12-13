# -*- coding: utf-8 -*-
import logging

from django.db import models
from django.db.models.query import QuerySet
from django.db.models.sql import EmptyResultSet

from .mixins import (
    CacheBackendMixin,
    CacheKeyMixin,
)

from .helpers import invalidate_modelqueryset_cache

logger = logging.getLogger(__name__)


class CacheManager(models.Manager):
    """
    Custom model manager that returns CachingQuerySet
    """

    # Use this manager when accessing objects that are related to from some other model.
    # Works only for one-to-one relationships not for many-to-many or foreign keys. See https://code.djangoproject.com/ticket/14891
    # so post_save, post_delete signals are used for cache invalidation. Signals can be removed when this bug is fixed.
    use_for_related_fields = True

    # django <=1.5
    def get_query_set(self):
        return CachingQuerySet(self.model, using=self._db)

    def get_queryset(self):
        return CachingQuerySet(self.model, using=self._db)


class CachingQuerySet(CacheBackendMixin, CacheKeyMixin, QuerySet):
    """
    Custom query set that caches results on load. This query set will force iteration of the result set
    so that the results can be cached for future calls.

    Query set invalidates model cache for any calls to bulk_create or update.
    """

    def iterator(self):
        try:
            key = self.generate_key()
        # workaround for Django bug # 12717
        except EmptyResultSet:
            return
        result_set = self.cache_backend.get(key)
        if not result_set:
            logger.debug('cache miss for key {0}'.format(key))
            result_set = list(super(CachingQuerySet, self).iterator())
            self.cache_backend.set(key, result_set)
        for result in result_set:
            yield result

    def bulk_create(self, *args, **kwargs):
        self.invalidate()
        return super(CachingQuerySet, self).bulk_create(*args, **kwargs)

    def update(self, **kwargs):
        self.invalidate()
        return super(CachingQuerySet, self).update(**kwargs)

    def invalidate(self):
        log_msg = self.get_log_msg
        invalidate_modelqueryset_cache(self.model, log_msg)

    @property
    def get_log_msg(self):
        msg = 'Invalidating cache for table'
        log_msg = '{}{}'.format(msg, self.model._meta.db_table)
        return log_msg
