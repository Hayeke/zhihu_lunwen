from importlib import reload
reload(crawl)
import  crawl
import  itertools
from  urllib3.exceptions  import  MaxRetryError
from  requests.exceptions import RetryError,ChunkedEncodingError
from zhihu_oauth.exception import NeedCaptchaException,NeedLoginException

# crawler.con.close()
# crawler.dbcommit()

#init,初始化
crawler = crawl.Crawler("zhihu.db","+8613739192506","qiangge521")
#counts = crawler.add_counts("logincounts.txt")#读取账户

#count2
counts=[
        {"count":"1990feixiang@163.com","key":"2010feixiang"},
        {"count":"909521500@qq.com","key":"2010feixiang"},
        {"count":"+8617805005808","key":"loveuwhp"},
        {"count": "+8613770314187", "key": "xzc3394350"},
        {"count": "+8613739192506", "key": "qiangge521"},
        {"count": "759484664@qq.com", "key": "zyz8591650"},
        {"count": "769724271@qq.com", "key": "769724271"}]

counts = itertools.cycle(counts)
count = (count for count in counts)
unvaild_count = []

#中继时执行
# crawler = crawl.Crawler("zhihu.db",login_count["count"],login_count["key"])

flag = 1
while flag == 1:
    try:
        flag = 0
        login_count = next(count)
        print("已切换到帐号",login_count["count"])
        crawler.con.close()
        crawler = crawl.Crawler("zhihu.db", login_count["count"], login_count["key"])
        # crawler.zhclient.set_proxy("socks5://127.0.0.1:1080")
        # crawler.justdoit("topic_users", "user_id", "userinfo", "id")#完成
        # crawler.justdoit("question_users", "user_id", "userinfo", "id") # 进行中，数据较大
        # crawler.justdoit("topic_users", "user_id", "user_topics", "user_id")#完成
        # crawler.justdoit("topic_questions", "question_id", "question_users", "question_id")#完成
        # crawler.justdoit("question_users", "user_id", "user_topics", "user_id")#数据大，暂不获取
        # crawler.justdoit("topic_questions", "question_id", "question_answers", "question_id")#完成
        # crawler.justdoit("question_answers", "answer_id", "answerinfo", "id")#完成
        # crawler.justdoit("question_answers", "author_id", "userinfo", "id")#完成
        # crawler.justdoit("topic_questions", "question_id", "question_topics", "question_id")#完成
        # crawler.justdoit("question_topics", "topic_id", "topicinfo", "id")#完成
    except (RetryError,MaxRetryError,ChunkedEncodingError):
        flag = 1
        crawler.con.close()
        print("帐号 %s 已失效 ，正切换下一个 " % (login_count["count"]))
        unvaild_count.append(login_count)
        pass
    except (NeedCaptchaException,NeedLoginException):
        flag = 1
        crawler.con.close()
        print("帐号 %s 需输入验证码 ，正切换下一个 " % ( login_count["count"]))
        unvaild_count.append(login_count)
        pass


### gephi output,问题话题共现网络

from importlib import reload
reload(ForGephi)
import  ForGephi

ForGephi.gexf_output("魅族科技",type = "question_topics")
ForGephi.gexf_output("华为",type = "question_topics")
ForGephi.gexf_output("小米科技",type = "question_topics")
ForGephi.gexf_output("苹果公司 (Apple Inc.)",type = "question_topics")
ForGephi.gexf_output("传销",type = "question_topics")


ForGephi.gexf_output("魅族科技",type = "user_topics",follower_count=100000)
ForGephi.gexf_output("华为",type = "user_topics",follower_count=100000)
ForGephi.gexf_output("小米科技",type = "user_topics",follower_count=100000)
#ForGephi.gexf_output("苹果公司 (Apple Inc.)",type = "user_topics",follower_count=200000)
ForGephi.gexf_output("传销",type = "user_topics",follower_count=100000)



##test
crawler = crawl.Crawler("zhihu.db","709683915@qq.com","bei091616")



#创建表
crawler.createindextables()


##从话题开始，数据seed，justdoit函数处理表id是一对一的，如果不是，使用单函数。
crawler.topic_questions(19565956)#huawei
crawler.topic_questions(19551762)#apple
crawler.topic_questions(19552917)#meizu
crawler.topic_questions(19552883)#小米
crawler.topic_questions(19596997)#传销
##完成5个话题

#容易反作弊中断
crawler.justdoit("topic_questions","question_id","questioninfo","id") #完成

#为防止中断导致查重失效，独立获取话题粉丝数据？
crawler.topic_users(19565956)#to-do:到10020和粉丝5020问题截止问题；
crawler.topic_users(19551762)
crawler.topic_users(19552917)
crawler.topic_users(19552883)
#以上部分完成
crawler.topic_users(19596997)##待获取


#取得
import sqlite3
import  pandas as pd
con = sqlite3.connect("zhihu.db")
cursor = con.cursor()

data  = cursor.execute("select * FROM  Question_view").fetchall()

cursor.close()
con.close()
