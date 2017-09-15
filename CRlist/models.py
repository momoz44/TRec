# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from multiselectfield import MultiSelectField

class Course(models.Model):
    courseid = models.CharField(max_length=30)
    title = models.CharField(max_length=100)
    cate = models.CharField(max_length=30)
    overview = models.CharField(max_length=300)

    def __unicode__(self):
        return self.courseid


class Course_list(models.Model):
    course = models.OneToOneField(Course)
    #course = models.ForeignKey(Course,unique=True)
    clist = models.CharField(max_length=300)
    def __unicode__(self):
        return self.course.courseid+'\'list'
status_list =(
    ('','----'),
    ('s1','status1'),
    ('s2','status2'),
    ('s3','status3'),
)
location_list =(
    #('','----'),
    ('CN','China'),
    ('UK','United Kingdom'),
    ('PL','Poland'),
)
language_list =(
    #('','----'),
    ('cn','Chinese'),
    ('en','English'),
    ('pl','Polish'),
)

class Trainer(models.Model):
    fn = models.CharField(max_length=20)
    ln = models.CharField(max_length=20)
    #many
    location = MultiSelectField(choices=location_list)
    language = MultiSelectField(choices=language_list)
    score = models.FloatField(max_length=2,blank=True)
    status = models.CharField(max_length=10,choices=status_list)
    email = models.EmailField(max_length=100,blank=True)
    skype = models.CharField(max_length=30,blank=True)
    cv = models.FileField(upload_to='./upload/',blank=True)
    comments = models.TextField(blank=True)
    trained_course = models.ManyToManyField(Course,blank=True)

    def __unicode__(self):
        return self.ln+' '+self.fn

class Trainer_list(models.Model):
    trainer = models.OneToOneField(Trainer)
    tlist = models.CharField(max_length=300)
    def __unicode__(self):
        return self.trainer.ln+' '+self.trainer.fn+'\'list'
''' 
class TManager(models.Manager):
    def incomplete(self):
        return self.filter(-----)

Todo.objects.all().incomplete()
'''
# Create your models here.
