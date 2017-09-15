# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin

from CRlist.models import Course,Course_list,Trainer,Trainer_list
admin.site.register(Course)
admin.site.register(Course_list)
admin.site.register(Trainer)
admin.site.register(Trainer_list)
# Register your models here.
