#!/usr/bin/env python3
#-*- coding:utf-8 -*-
"数据获取与存储模块"
__author__="Jack.Wang"

import os
from zhihu_oauth import ZhihuClient
import  time

from zhihu_oauth.exception import GetDataErrorException,UnexpectedResponseException,NeedCaptchaException
from zhihu_oauth.helpers import shield, SHIELD_ACTION,ZhihuWarning

import requests
import sqlite3
import csv, codecs
import  io

import threading
import multiprocessing

class Crawler:
    # Initialize the crawler with the name of database
    def __init__(self, dbname,email,key):
        self.con = sqlite3.connect(dbname)
        self.cursor = self.con.cursor()
        TOKEN_FILE = 'token.pkl'
        self.zhclient = ZhihuClient()
        try:
            # self.zhclient.login_in_terminal(email, key)
            self.zhclient.login(email, key)
        except NeedCaptchaException:
            print("需要输入验证码，账号 %s 可能已失效" %(email))
        # if os.path.isfile(TOKEN_FILE):
        #     self.zhclient.load_token(TOKEN_FILE)
        # else:
        #     self.zhclient.login_in_terminal(email, key)
        #     self.zhclient.save_token(TOKEN_FILE)

    def __del__(self):
        self.con.close()

    def dbcommit(self):
        self.con.commit()

    #建立数据表
    def createindextables(self):
        self.cursor.execute('create table userinfo(id primary key NOT NULL ,name text,headline text,gender int,address text,business text,school_name text,job text,company text,answer_count int ,question_count int ,voteup_count int ,thanked_count int ,following_count int ,follower_count int ,following_question_count int ,following_topic_count,collected_count int,identity text,best_topics text,is_organization int,org_name text,org_home_page text,org_industry text,record_time text)')
        self.cursor.execute('create table answerinfo(id primary key NOT NULL,content text,author_id int ,voteup_count int,thanks_count int, created_time text,comment_count int,updated_time text,record_time text)')
        self.cursor.execute('create table questioninfo(id primary key NOT NULL,title text,follower_count int ,answer_count int,created_time text,updated_time text,record_time text)')
        self.cursor.execute('create table topicinfo(id primary key NOT NULL,title text,best_answer_count int ,follower_count int ,question_count int,record_time text)')

        self.cursor.execute('create table topic_questions(topic_id ,topic_name text,question_id ,question_title text,record_time text)')
        self.cursor.execute('create table topic_users(topic_id,topic_name text,user_id,user_name text,record_time text)')
        self.cursor.execute('create table question_users(question_id,question_title text,user_id,user_name text,record_time text)')
        self.cursor.execute('create table question_answers(question_id,question_title text,answer_id,author_id,record_time text)')
        self.cursor.execute('create table user_users(user_id,user_follower_id)')
        self.cursor.execute('create table question_topics(question_id,topic_id,topic_name text,record_time text)')
        self.cursor.execute('create table user_topics(user_id,user_name text,topic_id,topic_name text,record_time text)')

        self.cursor.execute('create index userinfoidx on userinfo(id)')
        self.cursor.execute('create index answerinfoidx on answerinfo(id)')
        self.cursor.execute('create index questioninfoidx on questioninfo(id)')
        self.cursor.execute('create index topicinfoidx on topicinfo(id)')

        self.cursor.execute('create index topic_questionsidx on topic_questions(topic_id,question_id)')
        self.cursor.execute('create index topic_usersidx on topic_users(topic_id,user_id)')
        self.cursor.execute('create index question_usersidx on question_users(question_id,user_id)')
        self.cursor.execute('create index question_answersidx on question_answers(question_id,answer_id)')
        self.cursor.execute('create index user_usersidx on user_users(user_id,user_follower_id)')
        self.cursor.execute('create index question_topicsidx on question_topics(question_id,topic_id)')
        self.cursor.execute('create index user_topicsidx on user_topics(user_id,topic_id)')

        self.dbcommit()

    # #多线程尝试
    # def crawl_data(self,work_set,table1,field1,table2,field2):
    #     if table2 == "userinfo":
    #         for subid in work_set:
    #             subid = subid[0]
    #             self.userinfo(subid)
    #     elif table2 == "answerinfo":
    #         for subid in work_set:
    #             subid = subid[0]
    #             self.answerinfo(subid)
    #             # time.sleep(0.8)
    #             # time.sleep(0.5)
    #     elif table2 == "questioninfo":
    #         for subid in work_set:
    #             subid = subid[0]
    #             self.questioninfo(subid)
    #     elif table2 == "topicinfo":
    #         for subid in work_set:
    #             subid = subid[0]
    #             self.topicinfo(subid)
    #     elif table2 == "question_answers":
    #         for subid in work_set:
    #             subid = subid[0]
    #             self.question_answers(subid)
    #     elif table2 == "question_topics":
    #         for subid in work_set:
    #             subid = subid[0]
    #             self.question_topics(subid)
    #     elif table2 == "question_users":
    #         for subid in work_set:
    #             subid = subid[0]
    #             self.question_users(subid)
    #     elif table2 == "topic_questions":
    #         for subid in work_set:
    #             subid = subid[0]
    #             self.topic_questions(subid)
    #     elif table2 == "topic_users":
    #         for subid in work_set:
    #             subid = subid[0]
    #             self.topic_users(subid)
    #     elif table2 == "user_users":
    #         for subid in work_set:
    #             subid = subid[0]
    #             self.user_users(subid)
    #     elif table2 == "user_topics":
    #         for subid in work_set:
    #             subid = subid[0]
    #             self.user_topics(subid)
    #     return None


    def justdoit(self,table1,field1,table2,field2):
        set2 =set(self.cursor.execute("select DISTINCT  {} from {}".format(field2,table2)).fetchall())
        set1 = set(self.cursor.execute("select DISTINCT {} from {}".format(field1,table1)).fetchall())
        work_set = set1-set2
        # work_set = list(set1 - set2)
        # splitlen = int(len(work_set) / 2)
        # subwork_set = [work_set[i:i + splitlen] for i in range(0, len(work_set), splitlen)]
        # threads = []
        # for i in range(0,len(subwork_set)):
        #     t = multiprocessing.Process(target=self.crawl_data,args=(subwork_set[i],table1,field1,table2,field2))
        #     threads.append(t)
        # for t in threads:
        #     t.start()
        #     t.join()
        if table2 == "userinfo":
            for subid in work_set:
                subid = subid[0]
                self.userinfo(subid)
        elif table2 == "answerinfo":
            for subid in work_set:
                subid = subid[0]
                self.answerinfo(subid)
                # time.sleep(1.0)
                time.sleep(0.1)
        elif table2 == "questioninfo":
            for subid in work_set:
                subid = subid[0]
                self.questioninfo(subid)
        elif table2 == "topicinfo":
            for subid in work_set:
                subid = subid[0]
                self.topicinfo(subid)
        elif table2 == "question_answers":
            for subid in work_set:
                subid = subid[0]
                self.question_answers(subid)
        elif table2 == "question_topics":
            for subid in work_set:
                subid = subid[0]
                self.question_topics(subid)
        elif table2 == "question_users":
            for subid in work_set:
                subid = subid[0]
                self.question_users(subid)
        elif table2 == "topic_questions":
            for subid in work_set:
                subid = subid[0]
                self.topic_questions(subid)
        elif table2 == "topic_users":
            for subid in work_set:
                subid = subid[0]
                self.topic_users(subid)
        elif table2 == "user_users":
            for subid in work_set:
                subid = subid[0]
                self.user_users(subid)
        elif table2 == "user_topics":
            for subid in work_set:
                subid = subid[0]
                self.user_topics(subid)
        return None

    #话题-(精华)问题关系
    def topic_questions(self,topic_id):
        try:
            topic = self.zhclient.topic(topic_id)
            record_time = self.logtime()
            ques_set = set()
            for hot_ques in shield(topic.best_answers,action=SHIELD_ACTION.PASS):
                status = self.isdupicaterel("topic_questions", "topic_id", "question_id", topic.id, hot_ques.question.id)
                if status == None:
                    if hot_ques.question.id not in ques_set:
                        ques_set.add(hot_ques.question.id)
                        values = (topic.id,topic.name,hot_ques.question.id,hot_ques.question.title,record_time)
                        self.cursor.execute("insert into topic_questions(topic_id,topic_name,question_id,question_title,record_time) VALUES (?,?,?,?,?)" ,values)
                        self.dbcommit()
                        print("正在处理", hot_ques.question.id)
                else:
                    print("已存在，正在跳过")
                    pass
        except GetDataErrorException:
            print("Pass the GetDataErrorException")
            raise
        except UnexpectedResponseException:
            print("Pass the UnexpectedResponseException")
            pass
    #话题-关注者关系
    def topic_users(self,topic_id,start_at = 0):
        try:
            topic = self.zhclient.topic(topic_id)
            record_time = self.logtime()
            user_set = set()
            for follower in shield(topic.followers,start_at=start_at,action=SHIELD_ACTION.PASS):
                status = self.isdupicaterel("topic_users", "topic_id", "user_id", topic.id, follower.id)
                if status == None:
                    if follower.id not in user_set:
                        user_set.add(follower.id)
                        values = (topic.id,topic.name,follower.id,follower.name,record_time)
                        self.cursor.execute("insert into topic_users(topic_id,topic_name,user_id,user_name,record_time) VALUES (?,?,?,?,?)" ,values)
                        self.dbcommit()
                        print("正在处理",topic.name,follower.name)
                        # time.sleep(0.3)
                else:
                    print("已存在，正在跳过")
                    pass
        except GetDataErrorException:
            print("Pass the GetDataErrorException")
            pass
        except UnexpectedResponseException:
            print("Pass the UnexpectedResponseException")
            pass
    # 问题-关注者关系
    def question_users(self, question_id):
        try:
            question = self.zhclient.question(question_id)
            record_time = self.logtime()
            user_set = set()
            for follower in shield(question.followers,action=SHIELD_ACTION.PASS):
                status = self.isdupicaterel("question_users", "question_id", "user_id", question.id, follower.id)
                if status == None:
                    if follower.id not in user_set:
                        user_set.add(follower.id)
                        values = (question.id, question.title, follower.id, follower.name,record_time)
                        self.cursor.execute(
                            "insert into question_users(question_id,question_title,user_id,user_name,record_time) VALUES (?,?,?,?,?)", values)
                        self.dbcommit()
                        print("正在处理",follower.name,question.title)
                else:
                    print("已存在，正在跳过")
                    pass
        except GetDataErrorException:
            print("Pass the GetDataErrorException")
            pass
        except UnexpectedResponseException:
            print("Pass the UnexpectedResponseException")
            pass
    # 问题-回答关系
    def question_answers(self, question_id):
        try:
            question = self.zhclient.question(question_id)
            record_time = self.logtime()
            answer_set = set()
            for answer in shield(question.answers):
                status = self.isdupicaterel("question_answers", "question_id", "answer_id", question.id, answer.id)
                if status == None:
                    if answer.id not in answer_set:
                        answer_set.add(answer.id)
                        values = (question.id, question.title, answer.id, answer.author.id,record_time)
                        self.cursor.execute("insert into question_answers(question_id,question_title,answer_id,author_id,record_time) VALUES (?,?,?,?,?)", values)
                        self.dbcommit()
                        print("正在处理", question.id, question.title, answer.id, answer.author.id)
                else:
                    print("已存在，正在跳过")
                    pass
        except GetDataErrorException:
            print("Pass the GetDataErrorException")
            pass
        except UnexpectedResponseException:
            print("Pass the UnexpectedResponseException")
            pass
        except ZhihuWarning:
            print("Pass the UnexpectedResponseException")
            pass

    #获取用户-用户关注关系，知乎有5020限制，api限制最多获取一个用户5020粉丝
    def user_users(self,user_id):
        try:
            people = self.zhclient.people(user_id)
            record_time = self.logtime()
            user_set = set()
            for follower in shield(people.followers,action=SHIELD_ACTION.PASS):
                status = self.isdupicaterel("user_users", "user_id", "user_follower_id", people.id, follower.id)
                if status == None:
                    if follower.id not in user_set:
                        user_set.add(follower.id)
                        valus = (people.id,follower.id,record_time)
                        self.cursor.execute("insert into user_users(user_id,user_follower_id,record_time) VALUES (?,?,?)",valus)
                        self.dbcommit()
                        print("正在处理",follower.name)
                else:
                    print("已存在，正在跳过")
                    pass
        except GetDataErrorException:
            print("Pass the GetDataErrorException")
            pass
        except UnexpectedResponseException:
            print("Pass the UnexpectedResponseException")
            pass
    #获取问题-话题关系
    def question_topics(self,question_id):
        try:
            question = self.zhclient.question(question_id)
            record_time = self.logtime()
            topic_set = set()
            for topic in shield(question.topics):
                status = self.isdupicaterel("question_topics", "question_id", "topic_id", question.id, topic.id)
                if status == None:
                    if topic.id not in topic_set:
                        topic_set.add(topic.id)
                        values = (question.id,topic.id,topic.name,record_time)
                        self.cursor.execute("insert into question_topics(question_id,topic_id,topic_name,record_time) VALUES (?,?,?,?)",values)
                        self.dbcommit()
                        print("正在处理", topic.name,question.title)
                else:
                    print("已存在，正在跳过")
                    pass
        except UnexpectedResponseException:
            print("Pass the UnexpectedResponseException")
            pass
        except GetDataErrorException:
            print("Pass the GetDataErrorException")
            pass

    # 获取用户-话题关系
    def user_topics(self, user_id):
        try:
            people = self.zhclient.people(user_id)
            record_time = self.logtime()
            topic_set = set()
            for topic in shield(people.following_topics):
                status = self.isdupicaterel("user_topics", "user_id", "topic_id", people.id, topic.id)
                if status == None:
                    if topic.id not in topic_set:
                        topic_set.add(topic.id)
                        values = (people.id, people.name, topic.id,topic.name, record_time)
                        self.cursor.execute(
                            "insert into user_topics(user_id,user_name,topic_id,topic_name,record_time) VALUES (?,?,?,?,?)",
                            values)
                        self.dbcommit()
                        print("正在处理", people.name ,topic.name)
                else:
                    print("已存在，正在跳过")
                    pass
        except UnexpectedResponseException:
            print("Pass the UnexpectedResponseException")
            pass
        except GetDataErrorException:
            print("Pass the GetDataErrorException")
            pass

    # 判断数据重复
    def isdupicateid(self, table, id):
        cur = self.cursor.execute(
            "select rowid from {} where id = ?".format(table), (id,))
        self.dbcommit()
        res = cur.fetchone()
        res = None if res == None else res[0]
        return res

    def isdupicaterel(self,table,field1,field2, id1,id2):
        cur = self.cursor.execute(
            "select rowid from {} where {}= ? And {} = ?".format(table,field1,field2), (id1,id2))
        res = cur.fetchone()
        self.dbcommit()
        res = None if res == None else res[0]
        return res

    #个人信息
    def userinfo(self,user_id):
        try:
            status = self.isdupicateid("userinfo",user_id)
            if status==None:
                people = self.zhclient.people(user_id)
                record_time = self.logtime()
                address = "|".join([location.name for location in people.locations])
                school_name = "|".join([education.school.name for education in people.educations if "school" in education])
                job = "|".join([employment.job.name for employment in people.employments if "job" in employment])
                company = "|".join([employment.company.name for employment in people.employments if "company" in employment])
                business = people.business.name if people.business else None
                #勋章判断
                if people.badge.has_identity:
                    identity = people.badge.identity
                else:
                    identity = None
                if people.badge.is_best_answerer:
                    best_topics = "".join([topic.name for topic in people.badge.topics])
                else:
                    best_topics = None
                if people.badge.is_organization:
                    is_organization = 1
                    org_name = people.badge.org_name
                    org_home_page = people.badge.org_home_page
                    org_industry = people.badge.org_industry
                else:
                    is_organization = 0
                    org_name = None
                    org_home_page = None
                    org_industry = None
                values = (
                people.id, people.name, people.headline, people.gender, address, business, school_name, job,company,
                people.answer_count, people.question_count, people.voteup_count, people.thanked_count,
                people.following_count, people.follower_count, people.following_question_count,
                people.following_topic_count, people.collected_count, identity,best_topics,is_organization,org_name,org_home_page,org_industry,record_time)
                self.cursor.execute(
                    "insert into userinfo(id,name,headline,gender,address,business,school_name,job,company,answer_count,question_count,voteup_count,thanked_count,following_count,follower_count,following_question_count,following_topic_count,collected_count,identity,best_topics,is_organization,org_name,org_home_page,org_industry,record_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    values)
                self.dbcommit()
                print("正在处理", people.name)
            else:
                print("重复，rowid",status)
        except GetDataErrorException:
            print("Pass the GetDataErrorException")
            pass
        except UnexpectedResponseException:
            print("Pass the UnexpectedResponseException")
            pass

    def answerinfo(self,answer_id):
        try:
            status = self.isdupicateid("answerinfo", answer_id)
            if status == None:
                answer = self.zhclient.answer(answer_id)
                record_time = self.logtime()
                values = (answer.id,answer.content,answer.author.id,answer.voteup_count,answer.thanks_count,answer.comment_count,answer.created_time,answer.updated_time,record_time)
                self.cursor.execute("insert into answerinfo(id,content,author_id,voteup_count,thanks_count,comment_count,created_time,updated_time,record_time) VALUES (?,?,?,?,?,?,?,?,?)",values)
                self.dbcommit()
                print("正在处理",answer.id)
            else:
                return ("重复，rowid",status)
        except GetDataErrorException:
            print("Pass the GetDataErrorException")
            self.cursor.execute("delete from question_answers where answer_id = ?",(answer_id,))##在从question_answer表中获取及时删除无效问题，方式切换帐号后反复爬去无效问题。
            pass
        except UnexpectedResponseException:
            print("Pass the UnexpectedResponseException")
            pass
    #问题信息
    def questioninfo(self,question_id):
        try:
            status = self.isdupicateid("questioninfo", question_id)
            if status == None:
                question = self.zhclient.question(question_id)
                record_time = self.logtime()
                values = (question.id,question.title,question.follower_count,question.answer_count,question.created_time,question.updated_time,record_time)
                self.cursor.execute("insert into questioninfo(id,title,follower_count,answer_count,created_time,updated_time,record_time) VALUES (?,?,?,?,?,?,?)",values)
                self.dbcommit()
                print("正在处理" ,question.title)
            else:
                return ("重复，rowid",status)
        except GetDataErrorException:
            print("Pass the GetDataErrorException")
            pass
        except UnexpectedResponseException:
            print("Pass the UnexpectedResponseException")
            pass
    #话题信息
    def topicinfo(self,topic_id):
        try:
            status = self.isdupicateid("topicinfo", topic_id)
            if status == None:
                topic = self.zhclient.topic(topic_id)
                record_time = self.logtime()
                values=(topic.id,topic.name,topic.best_answer_count,topic.follower_count,topic.question_count,record_time)
                self.cursor.execute("insert into topicinfo(id,title,best_answer_count,follower_count,question_count,record_time) VALUES (?,?,?,?,?,?)",values)
                self.dbcommit()
                print("正在处理", topic.name)
            else:
                return ("重复，rowid",status)
        except GetDataErrorException:
            print("Pass the GetDataErrorException")
            pass
        except UnexpectedResponseException:
            print("Pass the UnexpectedResponseException")
            pass
    #时间戳
    def logtime(self):
        fmt = '%Y-%m-%d'  # 定义时间显示格式
        Date = time.strftime(fmt, time.localtime(time.time()))
        return Date


    def add_counts(self,filepath = "logincounts.txt"):
        counts = []
        for line in open(filepath):
            count = {}
            count["count"], count["key"] = line.split("----")
            count["key"] = count["key"].strip("\n")
            counts.append(count)
        return counts

    def get_proxy(self):
        try:
            PROXY_POOL_URL = 'http://localhost:5000/get'
            response = requests.get(PROXY_POOL_URL)
            if response.status_code == 200:
                return response.text
        except ConnectionError:
            return None

