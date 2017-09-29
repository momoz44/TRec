# coding:utf8
import json
import numpy as np
import pymysql.cursors
import time
import datetime
import pandas as pd
from aip import AipNlp
import jieba
from re import split
import re

# member数据库的连接配置
config_m = {
          'host':'mysql.rdsmqrkpb1zjtls.rds.gz.baidubce.com',
          'port':3306,
          'user':'dynamic_rec_wr',
          'password':'w0aV681Nh41j9YSD',
          'db':'doraemon_member',
          'charset':'utf8mb4',
          'cursorclass':pymysql.cursors.DictCursor,
          }
# orgnazation数据库的连接配置
config_o = {
          'host':'mysql.rdsmqrkpb1zjtls.rds.gz.baidubce.com',
          'port':3306,
          'user':'dynamic_rec_wr',
          'password':'w0aV681Nh41j9YSD',
          'db':'xkdsys',
          'charset':'utf8mb4',
          'cursorclass':pymysql.cursors.DictCursor,
          }
# news data的连接配置  这个的权限需要时读写权限
config_d = {
          'host':'mysql.rdsmqrkpb1zjtls.rds.gz.baidubce.com',
          'port':3306,
          'user':'dynamic_rec_wr',
          'password':'w0aV681Nh41j9YSD',
          'db':'doraemon_dynamic',
          'charset':'utf8mb4',
          'cursorclass':pymysql.cursors.DictCursor,
          }

APP_ID1 = '9841197'
API_KEY1 = 'moVFsrwITCyEiSHwtKlGYAdi'
SECRET_KEY1 = '7HvHgXlYXHGPz2zFxqM3cOq2GoozruYa'
aipNlp = AipNlp(APP_ID1, API_KEY1, SECRET_KEY1)

f = open("vocabulary_vec_v2.json", "r")
for line in f:
    vocabulary_vec_v2 = json.loads(line)
f.close()
stopwords = ['的', '了', '和', '是', '就', '都', '而', '及', '与', '或']
loss2 = []
with open('loss2.txt') as f:
    data = f.readlines()
for i in data:
    items = split(' ',i.strip())
    loss2.append(items[0])
#这个latet用来获取最新资讯的时间
latet=0

def get_data(config_m,config_o,config_d):

    connection_m = pymysql.connect(**config_m)
    try:
        with connection_m.cursor() as cursor:
            sql = '''select a.user_id,b.ucenter_id,c.member_type,a.org_id,c.main_org_id from  dor_org_members a
            LEFT JOIN dor_user b on a.user_id = b.user_id
            left join dor_member c
            on a.target_id=c.target_id
            where c.`status` =1
            and b.is_disable = 0
            and c.member_type != 1
            and c.main_org_id > 0
            '''
            cursor.execute(sql)
            result_m = cursor.fetchall()
            # print result
        connection_m.commit()

    except:
        connection_m.close()

    connection_o = pymysql.connect(**config_o)
    try:
        with connection_o.cursor() as cursor:
            sql1 = '''SELECT A.org_id,A.org_name,C.keyword,C.source_type,C.type FROM auth_organization A
            JOIN auth_archive B ON A.org_id=B.org_id
            JOIN auth_archive_keyword C ON B.archive_id=C.archive_id
            '''
            cursor.execute(sql1)
            result_o1 = cursor.fetchall()
            # 行业关键字
            sql2 = '''SELECT a.org_id,a.org_name,b.area_name as cn,c.area_name as pn,d.area_name as cin,e.area_name as dn FROM auth_organization a
            left join dic_area_code	b on a.nation_id=b.official_code
            left join dic_area_code c on a.province_id=c.official_code
            left join dic_area_code d on a.city_id=d.official_code
            left join dic_area_code e on a.district_id=e.official_code
            '''
            cursor.execute(sql2)
            result_o2 = cursor.fetchall()
            # 办公地址
            sql3 = '''SELECT A.org_id,A.org_name,C.area_name as cn,D.area_name as pn,E.area_name as cin,F.area_name as dn FROM auth_organization A
            JOIN auth_org_cover_area B ON A.org_id=B.org_id
            left join dic_area_code	C on B.nation_id=C.official_code
            left join dic_area_code D on B.province_id=D.official_code
            left join dic_area_code E on B.city_id=E.official_code
            left join dic_area_code F on B.district_id=F.official_code
            '''
            cursor.execute(sql3)
            result_o3 = cursor.fetchall()
            # 业务覆盖范围
        connection_o.commit()

    finally:
        connection_o.close()


    connection_d = pymysql.connect(**config_d)
    try:
        with connection_d.cursor() as cursor:
            sql1 = 'SELECT user_id,tags,keywords from user_tags_keywords'
            cursor.execute(sql1)
            result_d = cursor.fetchall()
            # 用户的关注标签、兴趣标签
            # print result
            sql2 = 'SELECT id,news_type,keywords,tags,upd_time from news_list where upd_time > %s'
            global latet
            cursor.execute(sql2, (str(latet)))
            result_dl = cursor.fetchall()
            # 资讯的关键字，标签
        connection_d.commit()

    finally:
        connection_d.close()

    return result_m, result_o1, result_o2, result_o3, result_d, result_dl

def get_dfmember(result_m):
    user_list = []
    org_id_list = []
    org_linkid_list = []
    for i in result_m:
        user_list.append(i['user_id'])
        org_id_list.append(i['org_id'])
        org_linkid_list.append(i['main_org_id'])
    dfmember = pd.DataFrame({'user_id': user_list, 'org_id': org_id_list, 'org_linkid': org_linkid_list})

    return dfmember

def get_dforg(result_o1,result_o2,result_o3):
    org_key = {}
    # 项目信息，行业，产品   需求关键字
    for i in result_o1:
        if not i['org_id'] in org_key:
            org_key[i['org_id']] = {}
            org_key[i['org_id']]['industry_keys'] = []
            org_key[i['org_id']]['demand_keys'] = []
            org_key[i['org_id']]['add_keys'] = []
        if (i['source_type'] == 1) | (i['type'] == 3) | (i['type'] == 8):
            org_key[i['org_id']]['industry_keys'].append(i['keyword'])
        if i['type'] == 10:
            org_key[i['org_id']]['demand_keys'].append(i['keyword'])

    # 办公地址的关键字
    for i in result_o2:
        if not i['org_id'] in org_key:
            org_key[i['org_id']] = {}
            org_key[i['org_id']]['industry_keys'] = []
            org_key[i['org_id']]['demand_keys'] = []
            org_key[i['org_id']]['add_keys'] = []
        if i['pn'] and i['pn'] not in org_key[i['org_id']]['add_keys']:
            org_key[i['org_id']]['add_keys'].append(i['pn'])
        if i['cin'] and i['cin'] not in org_key[i['org_id']]['add_keys']:
            org_key[i['org_id']]['add_keys'].append(i['cin'])
        if i['dn'] and i['dn'] not in org_key[i['org_id']]['add_keys']:
            org_key[i['org_id']]['add_keys'].append(i['dn'])
            # cn 仅有中国，先取消
            # if i['cn'] and i['cn'] not in org_key[i['org_id']]['add_keys']:
            #    org_key[i['org_id']]['add_keys'].append(i['cn'])

    # 业务覆盖范围的关键字
    for i in result_o3:
        if not i['org_id'] in org_key:
            org_key[i['org_id']] = {}
            org_key[i['org_id']]['industry_keys'] = []
            org_key[i['org_id']]['demand_keys'] = []
            org_key[i['org_id']]['add_keys'] = []
        if i['pn'] and i['pn'] not in org_key[i['org_id']]['add_keys']:
            org_key[i['org_id']]['add_keys'].append(i['pn'])
        if i['cin'] and i['cin'] not in org_key[i['org_id']]['add_keys']:
            org_key[i['org_id']]['add_keys'].append(i['cin'])
        if i['dn'] and i['dn'] not in org_key[i['org_id']]['add_keys']:
            org_key[i['org_id']]['add_keys'].append(i['dn'])
            # cn 仅有中国，先取消
            # if i['cn'] and i['cn'] not in org_key[i['org_id']]['add_keys']:
            #    org_key[i['org_id']]['add_keys'].append(i['cn'])

    org_linkid_list = []
    industry_keys = []
    demand_keys = []
    add_keys = []
    for i in org_key:
        org_linkid_list.append(i)
        industry_keys.append(org_key[i]['industry_keys'])
        demand_keys.append(org_key[i]['demand_keys'])
        add_keys.append(org_key[i]['add_keys'])
    dforg = pd.DataFrame(
        {'org_linkid': org_linkid_list, 'in_keys': industry_keys, 'de_keys': demand_keys, 'add_keys': add_keys})

    return dforg

def get_dffav(result_d):
    user_list = []
    fav_list = []
    com_list = []
    for i in result_d:
        user_list.append(i['user_id'])
        if i['keywords']:
            fav_list.append(i['keywords'].split(','))
        else:
            fav_list.append([])
        if i['tags']:
            com_list.append(i['tags'].split(','))
        else:
            com_list.append([])
    dffav = pd.DataFrame({'user_id': user_list, 'fav_keys': fav_list, 'com_keys': com_list})
    return dffav

#计算news基于关键字的向量特征
def get_news_vec(keys):
    num = 0
    vector = np.zeros((1024,),dtype='float32')
    for word in keys:
        if word in vocabulary_vec_v2:
            vec = vocabulary_vec_v2[word]
            vector = np.add(vector,vec)
            
        elif word in loss2:
            num += 1
        else:
            jiebas = jieba.cut(word, cut_all=True)
            words = [word for word in jiebas if word not in stopwords]
            vector2 = np.zeros((1024,), dtype='float32')
            for i in words:
                if i in vocabulary_vec_v2:
                    vec = vocabulary_vec_v2[i]
                    vector2 = np.add(vector2, vec)
                elif i in loss2:
                    continue
                else:
                    time.sleep(0.5)
                    msg = aipNlp.wordEmbedding(i)
                    try:
                        vec = msg['vec']
                        vector2 = np.add(vector2, vec)
                        vocabulary_vec_v2[i] = vec
                    except:
                        print (i, msg['error_msg'])
                        loss2.append(i)
                        continue
            if not (vector2 == 0).all():
                vec = list(vector2)
                vocabulary_vec_v2[word] = vec
                vector = np.add(vector, vec)
            else:
                num += 1
    if (len(keys)-num) > 0:
        vector = np.divide(vector, (len(keys)-num))
    #return vector
    #else:
        #直接取0
        #news_vector[news] = vector
    if (vector==0).all():
        return 'nothing'
    else:
        return vector

def get_final_user_list(dfmember, dforg, dffav):
    #先合并成总的dataframe
    res = pd.merge(dfmember, dforg, how='left', on='org_linkid')
    res_final = pd.merge(res, dffav, how='outer', on='user_id')
    res_final = res_final.fillna(-1)
    #再生成dict
    final_user_list = {}
    for i in range(res_final.shape[0]):
        user = ','.join([str(res_final['user_id'][i]), str(int(res_final['org_id'][i]))])
        if not user in final_user_list:
            final_user_list[user] = {}
        final_user_list[user]['add_keys'] = []
        if res_final['add_keys'][i] and res_final['add_keys'][i] != -1:
            final_user_list[user]['add_keys'] = res_final['add_keys'][i]
        final_user_list[user]['de_keys'] = {}
        final_user_list[user]['in_keys'] = {}
        final_user_list[user]['com_keys'] = {}
        final_user_list[user]['fav_keys'] = {}
        if res_final['de_keys'][i] and res_final['de_keys'][i] != -1:
            vector = get_news_vec(res_final['de_keys'][i])
            final_user_list[user]['de_keys']['keys'] = res_final['de_keys'][i]
            final_user_list[user]['de_keys']['vec'] = vector
        if res_final['in_keys'][i] and res_final['in_keys'][i] != -1:
            vector = get_news_vec(res_final['in_keys'][i])
            final_user_list[user]['in_keys']['keys'] = res_final['in_keys'][i]
            final_user_list[user]['in_keys']['vec'] = vector
        if res_final['com_keys'][i] and res_final['com_keys'][i] != -1:
            vector = get_news_vec(res_final['com_keys'][i])
            final_user_list[user]['com_keys']['keys'] = res_final['com_keys'][i]
            final_user_list[user]['com_keys']['vec'] = vector
        if res_final['fav_keys'][i] and res_final['fav_keys'][i] != -1:
            vector = get_news_vec(res_final['fav_keys'][i])
            final_user_list[user]['fav_keys']['keys'] = res_final['fav_keys'][i]
            final_user_list[user]['fav_keys']['vec'] = vector
    return final_user_list

def get_news_list(result_dl):
    news_list = {}
    for news in result_dl:
        title = str(news['id']) + 't' + str(news['news_type'])
        # string = ','.join([])
        # 有unicode不能join
        keys = []
        if news['keywords']:
            for word in news['keywords'].split(','):
                if word not in keys:
                    keys.append(word)
        if news['tags']:
            for word in news['keywords'].split(','):
                if word not in keys:
                    keys.append(word)
        vector = get_news_vec(keys)

        if not title in news_list:
            news_list[title] = {}
        news_list[title]['keys'] = keys
        news_list[title]['vec'] = vector
    return news_list

def jaccard_dis(x, y):
    try:
        inter = len(set.intersection(*[set(x),set(y)]))
        union = len(set.union(*[set(x),set(y)]))
        return round(inter/float(union),7)
    except:
        return -1

def cosine_dis(x,y):
    #num = sum(map(float, x*y))
    num = sum(float(a*b) for a, b in zip(x, y))
    denom = np.linalg.norm(x)*np.linalg.norm(y)
    #print num
    #print denom
    if denom == 0:
        return -1
    else:
        return round(num/float(denom), 7)

#根据权重排序，取前5，并且转化成我们需要的形式
def get_top5(lis):
    num = min([5,len(lis)])
    new_list=[]
    #需要设定阈值的时候，这边来！
    for i in sorted(lis,reverse=True)[0:num]:
        if i[0]>0:
            id_type = i[1].split('t')
        #这样分开才能确定写入数据库的时候是
            new_list.append([int(id_type[0]),int(id_type[1])])
    return new_list

def replace_list(keywords):
    new_keywords = [re.sub('省|市|区|县','',word) for word in keywords]
    #new_keywords = [re.sub('市', '', word) for word in new_keywords]
    return new_keywords

#生成最终列表
#若数据量大，这一步消耗的时间大
def get_final_list(final_user_list,news_list):
    final_list = {}
    for user in final_user_list:
        final_list[user] = {}
        final_list[user]['add_list'] = []
        final_list[user]['in_list'] = []
        final_list[user]['de_list'] = []
        final_list[user]['com_list'] = []
        final_list[user]['fav_list'] = []
        for news in news_list:
            # 通过地址计算
            if final_user_list[user]['add_keys']:
                newsk=replace_list(news_list[news]['keys'])
                userk=replace_list(final_user_list[user]['add_keys'])
                sim = jaccard_dis(newsk, userk)
                #sim = jaccard_dis(news_list[news]['keys'], final_user_list[user]['add_keys'])
                final_list[user]['add_list'].append([sim, news])
            # 通过行业关键字计算,有向量用cosine，没有就用jaccard
            if final_user_list[user]['in_keys']:
                if (len(final_user_list[user]['in_keys']['vec']) == 128) and (len(news_list[news]['vec']) == 128):
                    sim = cosine_dis(news_list[news]['vec'], final_user_list[user]['in_keys']['vec'])
                else:
                    sim = jaccard_dis(news_list[news]['keys'], final_user_list[user]['in_keys']['keys'])
                final_list[user]['in_list'].append([sim, news])
            # 需求
            if final_user_list[user]['de_keys']:
                if (len(final_user_list[user]['de_keys']['vec']) == 128) and (len(news_list[news]['vec']) == 128):
                    sim = cosine_dis(news_list[news]['vec'], final_user_list[user]['de_keys']['vec'])
                else:
                    sim = jaccard_dis(news_list[news]['keys'], final_user_list[user]['de_keys']['keys'])
                final_list[user]['de_list'].append([sim, news])
            # 关注企业
            if final_user_list[user]['com_keys']:
                if (len(final_user_list[user]['com_keys']['vec']) == 128) and (len(news_list[news]['vec']) == 128):
                    sim = cosine_dis(news_list[news]['vec'], final_user_list[user]['com_keys']['vec'])
                else:
                    sim = jaccard_dis(news_list[news]['keys'], final_user_list[user]['com_keys']['keys'])
                final_list[user]['com_list'].append([sim, news])
            # 兴趣
            if final_user_list[user]['fav_keys']:
                if (len(final_user_list[user]['fav_keys']['vec']) == 128) and (len(news_list[news]['vec']) == 128):
                    sim = cosine_dis(news_list[news]['vec'], final_user_list[user]['fav_keys']['vec'])
                else:
                    sim = jaccard_dis(news_list[news]['keys'], final_user_list[user]['fav_keys']['keys'])
                final_list[user]['fav_list'].append([sim, news])
        # 遍历完了，分别对5个list排序然后取前5个
        final_list[user]['add_list'] = get_top5(final_list[user]['add_list'])
        final_list[user]['in_list'] = get_top5(final_list[user]['in_list'])
        final_list[user]['de_list'] = get_top5(final_list[user]['de_list'])
        final_list[user]['com_list'] = get_top5(final_list[user]['com_list'])
        final_list[user]['fav_list'] = get_top5(final_list[user]['fav_list'])
    return final_list

def insert_data(final_list):
    # 先插入，插入报错就更新
    j = 0
    for i in final_list:
        ids = i.split(',')
        user_id = int(ids[0])
        org_id = int(ids[1])
        # 获取此时的时间戳
        ts = int(time.time())
        connection_d = pymysql.connect(**config_d)
        try:
            with connection_d.cursor() as cursor:
                sql = 'insert into user_news_recomment_batch (user_id,org_id,batch_time,branch_related,area_related,interest_related,peers_related,needs_related) values(%s,%s,%s,%s,%s,%s,%s,%s)'
                cursor.execute(sql, (user_id, org_id, ts, str(final_list[i]['in_list']), str(final_list[i]['add_list']),
                                     str(final_list[i]['fav_list']), str(final_list[i]['com_list']),
                                     str(final_list[i]['de_list'])));

            connection_d.commit()

        except:
            j += 1
            #print (j)
            connection_d.close();



def get_latetime(result_dl):
    times = []
    for i in result_dl:
        times.append(i['upd_time'])
    global latet
    if max(times)>latet:
        latet=max(times)

def get_news_keywords(result1,result2):
    news_keywords = {}
    for i in result1:
        news = i['id']
        # keywords = i['keywords'].decode('utf8').split(',')
        keywords = i['keywords'].split(',')
        news_keywords[news] = keywords
    for i in result2:
        news = i['news_id']
        word = i['name']
        if news in news_keywords:
            if not word in news_keywords[news]:
                news_keywords[news].append(word)
        else:
            news_keywords[news] = []
            news_keywords[news].append(word)
    return news_keywords

def initial_news_order(news_vector):
    news_order = {}
    for news1 in news_vector:
        news_order[news1] = {}
        for news2 in news_vector:
            if news1 != news2:
                sim = cosine_dis(news_vector[news1],news_vector[news2])
                news_order[news1][news2] = sim
    # 排序
    for i in news_order:
        order = []
        #ituple = sorted(news_order[i].iteritems(), key=lambda d: d[1], reverse=True)
        ituple = sorted(news_order[i].items(), key=lambda d: d[1], reverse=True)
        for j in ituple:
            order.append([j[0], j[1]])
        news_order[i] = order
    return news_order

def insert_news(news_order):
    for i in news_order:
        connection_d = pymysql.connect(**config_d)
        try:
            with connection_d.cursor() as cursor:
                sql = 'insert into news_sim (id,sim) values(%s,%s)'
                cursor.execute(sql, (int(i), str(news_order[i])));
                connection_d.commit()
        except:
            with connection_d.cursor() as cursor:
                sql = 'update news_sim set sim = %s where id = %s'
                cursor.execute(sql, (str(news_order[i]), int(i)));
                connection_d.commit()

        finally:
            connection_d.close()

def run_Task2():
    connection_d = pymysql.connect(**config_d)
    try:
        with connection_d.cursor() as cursor:
            sql1 = 'Select id, keywords from news_inner '
            cursor.execute(sql1)
            tags1 = cursor.fetchall()
            #资讯的手动关键字
            sql2 = 'Select news_id, name, weight from news_inner_tags'
            cursor.execute(sql2)
            tags2 = cursor.fetchall()
            #资讯的生成关键字
        connection_d.commit()

    finally:
        connection_d.close()

    news_keywords = get_news_keywords(tags1,tags2)
    news_vector = {}
    for news in news_keywords:
        news_vector[news]=get_news_vec(news_keywords[news])

    news_order = initial_news_order(news_vector)
    insert_news(news_order)




def run_Task():
    result_m, result_o1, result_o2, result_o3, result_d, result_dl = get_data(config_m, config_o, config_d)


    dfmember = get_dfmember(result_m)
    dforg = get_dforg(result_o1, result_o2, result_o3)
    dffav = get_dffav(result_d)
    final_user_list = get_final_user_list(dfmember, dforg, dffav)
    news_list = get_news_list(result_dl)
    final_list = get_final_list(final_user_list, news_list)
    #全部处理完，进行数据插入
    if result_dl:
        # 更新全局变量latet的时间
        print ('No news added.')
        get_latetime(result_dl)
        insert_data(final_list)

def timerFun(sched_Timer):
    flag=0
    run_Task()
    run_Task2()
    while True:
        now = datetime.datetime.now()
        #测试用
        #if flag == 0:
        if (now > sched_Timer) and (flag==0):
            run_Task()
            #print ('\n Rec list finished. \n')
            run_Task2()
            #print('\n News sim finished. \n')
            flag = now.hour
            #测试用
            #global latet
            #print (latet)
        else:
            # 分别定在 8点 14点 和21点生成一遍
            if flag==8:
                sched_Timer=sched_Timer+datetime.timedelta(hours=6)
                flag=0
            elif flag==14:
                sched_Timer=sched_Timer+datetime.timedelta(hours=7)
                flag=0
            elif flag==21:
                sched_Timer=sched_Timer+datetime.timedelta(hours=11)
                flag=0
            else:
                continue

if __name__ == "__main__":
    #定义好下次修改的时间
    sched_Timer=datetime.datetime(2017,8,17,8,00,00)
    timerFun(sched_Timer)


