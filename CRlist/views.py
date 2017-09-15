# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render,render_to_response,HttpResponse,HttpResponseRedirect
from CRlist.models import Course,Course_list,Trainer,Trainer_list
from django import forms
from CRlist.models import location_list,language_list,status_list
from django.db.models import Q

#cl = Course.objects.all()


def get_object():
    r = [('', 'please choose a course')]
    for obj in Course.objects.all():
        r = r + [(obj.id, obj.title)]
    return r

class CourseF(forms.Form):
    #course = forms.ChoiceField(choices=cl1, label='Course Name')
    cc = get_object()
    #course = forms.CharField(label='Course Name',widget=forms.Select(choices =cc))
    course = forms.ChoiceField(label='Course name', choices=cc)



def index(req):
    if req.method == 'POST':
        cf = CourseF(req.POST)
        if cf.is_valid():
            cid = cf.cleaned_data['course']
            print cid
            response = HttpResponseRedirect('../clist/%s' % cid)
            return response

        else:
            return HttpResponseRedirect('./')
            #return HttpResponse('show list for course %s' %cid)
            #
            #


        #print cf.cleaned_data
        #return HttpResponse('show list')

        ''' 
        if cf.is_valid():
            cid =cf.cleaned_data['course']
            print cid
            #response = HttpResponseRedirect('../index')
            return HttpResponse('show list')
        '''
    else:
        cf = CourseF()
        #cf.fields['course'].choices = get_object(req)
        #return render_to_response('index.html', {'cf': cf})
        return render_to_response('index.html', {'cf': cf})
    ''' 
    cc = CourseF()
    cc.fields['course'].choices = get_object(req)
    return render_to_response('index.html',{'cc':cc})
    '''
score_list = (
    ('','----'),
    (0.8,'above 0.8'),
    (0.5,'above 0.5'),
    (0.0,'all')
)

trained_list =(
    ('','----'),
    #(0,'Not Matter'),
    (1,'Yes'),
)


class FilterF(forms.Form):
    score = forms.ChoiceField(label='score',choices=score_list,required=False)
    location = forms.MultipleChoiceField(label='location',choices=location_list,required=False)
    language = forms.MultipleChoiceField(label='language',choices=language_list,required=False)
    trained = forms.ChoiceField(label='trained course before',choices=trained_list,required=False)
    status = forms.ChoiceField(label='status',choices=status_list,required=False)



def clist(req, cid):
    if req.method == 'POST':
        ff = FilterF(req.POST)
        if ff.is_valid():
            fdata = ff.cleaned_data
            result = Trainer.objects.all()
            title = Course.objects.filter(id=cid)[0]
            if fdata['score']:
                result = result.filter(Q(score__gte=float(fdata['score'])))
            if fdata['location']:
                for fc in fdata['location']:
                    result = result.filter(Q(location__contains=fc))
            if fdata['language']:
                for fc in fdata['language']:
                    result = result.filter(Q(language__contains=fc))
            if fdata['status']:
                result = result.filter(Q(status=fdata['status']))

            flist = [a for a in result]
            '''  
            if fdata['trained']:
                #result = result.filter(Q(trained_course__contains=title))
                for i in result:
                    if title in i.trained_course.all():
                        #print '!'
                        result = result.delete(i)
            '''

            list = Course_list.objects.filter(course_id__exact=cid)
            #get recommend list
            tlist = []
            if list:
                cl1 = list[0].clist.split(',')
                # print cl1
                #rec list

                title = Course.objects.filter(id=cid)[0]
                for tid in cl1:
                    a = Trainer.objects.filter(id=int(tid))
                    # print a[0].trained_course.all()
                    tlist += a
            #fin list
            l1 =[]
            #fout list
            l2 =[]
            for tr in tlist:
                if tr not in flist:
                    l2.append(tr)
                elif not fdata['trained']:
                    l1.append(tr)
                else:
                    if title in tr.trained_course.all():
                        l1.append(tr)
                    else:
                        l2.append(tr)

            #print l1
            #print l2
        #return render_to_response('test.html', {'tlist': l1, 'flist': l2, 'ff': ff, 'title': title})
        return render_to_response('CRlist.html',{'tlist':l1,'flist':l2,'ff':ff,'title':title})
        #return HttpResponse('TBD')


    else:
        ff = FilterF()
        list = Course_list.objects.filter(course_id__exact=cid)
        if list:
            cl1 =  list[0].clist.split(',')
            #print cl1
            tlist =[]
            title = Course.objects.filter(id=cid)[0]
            for tid in cl1:
                a = Trainer.objects.filter(id=int(tid))
                #print a[0].trained_course.all()
                tlist += a
            #print tlist[0].Course_set.all
            #return render_to_response('test.html', {'tlist': tlist, 'title': title, 'ff': ff})
            return render_to_response('CRlist.html',{'tlist':tlist,'title':title,'ff':ff})
            #return HttpResponse('Show list for c %s'%cid)
        else:
            return HttpResponse('No list for %s generated!'%cid)

# Create your views here.
def tpage(req, uid):

    tr = Trainer.objects.filter(id=uid)[0]
    if req.method == 'POST':
        ff = FilterF(req.POST)
        if ff.is_valid():
            fdata = ff.cleaned_data
            result = Trainer.objects.all()

            if fdata['score']:
                result = result.filter(Q(score__gte=float(fdata['score'])))
            if fdata['location']:
                for fc in fdata['location']:
                    result = result.filter(Q(location__contains=fc))
            if fdata['language']:
                for fc in fdata['language']:
                    result = result.filter(Q(language__contains=fc))
            if fdata['status']:
                result = result.filter(Q(status=fdata['status']))

            flist = [a for a in result]
            '''  
            if fdata['trained']:
                #result = result.filter(Q(trained_course__contains=title))
                for i in result:
                    if title in i.trained_course.all():
                        #print '!'
                        result = result.delete(i)
            '''

            list = Trainer_list.objects.filter(trainer_id__exact=uid)
            #get recommend list
            slist = []
            if list:
                cl1 = list[0].tlist.split(',')
                # print cl1
                #rec list


                for tid in cl1:
                    a = Trainer.objects.filter(id=int(tid))
                    slist += a
            #fin list
            l1 =[]
            #fout list
            l2 =[]
            for tr in slist:
                if tr not in flist:
                    l2.append(tr)
                else:
                    l1.append(tr)


            #print l1
            #print l2
        return render_to_response('TPage.html',{'slist':l1,'flist':l2,'ff':ff,'title':tr})
        #return HttpResponse('TBD')


    else:
        ff = FilterF()
        list = Trainer_list.objects.filter(trainer_id__exact=uid)
        if list:
            tl1 = list [0].tlist.split(',')

            slist= []
            for tid in tl1:
                a = Trainer.objects.filter(id=int(tid))
                slist += a

            return render_to_response('TPage.html',{'slist':slist,'title':tr,'ff':ff})


def test(req):
    return render_to_response('123.html',{})