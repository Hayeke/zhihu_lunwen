import sqlite3
import  pandas as pd
import math
import time
from itertools import combinations
import  os
import gc


class_mark_dict = {"class": [0, 1, 2, 3, 4, 5, 6, 7, 8],
                   "name": ["企业/品牌", "形式/类型", "观点/认知", "地理区域", "相关人物", "机构领域", "人群需求", "角色职业", "未分类"]}
class_mark_dict = dict(zip(class_mark_dict["class"], class_mark_dict["name"]))

def topic_mark_dicts(topicname,type = "question_topics",follower_count = 0):
    print("Function topic_mark_dicts type is ", type)
    Topics_Marked_Url = "Topics_Marks/Havemarked/{}_{}_fol{}.csv".format(topicname,type,follower_count)
    if os.path.exists(Topics_Marked_Url):
        topics_mark = pd.read_csv(Topics_Marked_Url, encoding="gb2312", engine='python')
    else:
        topics_mark = topis_withoutmark_init(topicname,type,follower_count)
    topics_mark = topics_mark[1:]
    topics_mark_dict = dict(zip(topics_mark["topic_name"], topics_mark["类型"]))
    return  topics_mark_dict


def read_sqlite_df(dbpath = "zhihu.db", tablename = "Questions_ETL"):
    con = sqlite3.connect(dbpath)
    cursor = con.cursor()
    data = cursor.execute("select * from {} ".format(tablename)).fetchall()
    df = pd.DataFrame(list(data))
    column_name = cursor.execute("pragma table_info([{}])".format(tablename)).fetchall()
    df.columns = [i[1] for i in column_name]
    cursor.close()
    con.close()
    return df


def topis_withoutmark_init(topicname,type = "question_topics",follower_count = 0):
    """
    设置初始化的话题类型字典；默认未分类类型为8:"未分类"
    """
    print("Function topis_withoutmark_init type is %s ,follower_count is %s" % (type,follower_count))
    Topics_Freq_Url = "Topics_Marks/Topic_freq/{}_{}_fol{}.csv".format(topicname,type,follower_count)
    Topics_notMarked_Url = "Topics_Marks/Notmark/{}_{}_fol{}.csv".format(topicname,type,follower_count)
    topics_freq = topics_tonodes(topicname,type,follower_count)
    topics_freq.to_csv(Topics_Freq_Url, index=None)
    topics_freq["类型"] = 8
    topics_mark = topics_freq[["topic_name","类型"]].reset_index(drop=True)
    topics_mark.to_csv(Topics_notMarked_Url,index = None)
    return topics_mark


def topics_tonodes(topicname,type = "question_topics",follower_count = 0,dbpath = "zhihu.db"):
    print("Function topics_tonodes  type is %s ,follower_count is %s  "%(type,follower_count))
    con = sqlite3.connect(dbpath)
    cursor = con.cursor()
    if type == "question_topics":
        data = cursor.execute("select tq.topic_name,tq.question_id,qt.topic_name from topic_questions as tq,question_topics as qt ,questioninfo as qi WHERE  tq.question_id = qt.question_id AND  tq.question_id = qi.id AND tq.topic_name = ? AND qi.follower_count > ? ",(topicname,follower_count)).fetchall()
        colname = "question_id"
    elif type == "user_topics":
        data = cursor.execute("select tu.topic_name,tu.user_id,ut.topic_name from topic_users as tu,user_topics as ut ,userinfo as ui  WHERE tu.user_id = ut.user_id AND tu.user_id = ui.id  AND  tu.topic_name = ? AND  ui.follower_count > ?",(topicname,follower_count)).fetchall()
        colname= "user_id"
    df = pd.DataFrame(list(data))
    df.columns = ("father_topic",colname,"topic_name")
    topics_freq = df.groupby("topic_name").size().reset_index(name="size").sort_values("size", ascending=False)
    topics_freq["size_log2"] = [round(math.log2(x), 2) for x in topics_freq["size"]]
    topics_freq = topics_freq.reset_index(drop=True)
    cursor.close()
    con.close()
    return topics_freq


# def user_topics_tonodes(topicname,dbpath = "zhihu.db"):
#     print("Function user_topics_tonodes ")
#     con = sqlite3.connect(dbpath)
#     cursor = con.cursor()
#     data =
#     df = pd.DataFrame(list(data))
#     df.columns = ("father_topic","user_id","topic_name")
#     topics_freq = df.groupby("topic_name").size().reset_index(name="size").sort_values("size", ascending=False)
#     topics_freq["size_log2"] = [round(math.log2(x), 2) for x in topics_freq["size"]]
#     topics_freq = topics_freq.reset_index(drop=True)
#     cursor.close()
#     con.close()
#     return topics_freq



def label_toclass(topicname ,type = "question_topics",follower_count = 0):
    """
    根据话题类型字典，将获得话题进行类型标记
    type：user_topics;question_topics
    """
    print("Function labeltoclass type is %s follower_count is %s " % (type,follower_count))
    topics_freq = topics_tonodes(topicname,type,follower_count)
    topics_mark_dict = topic_mark_dicts(topicname,type,follower_count)
    topics_freq["class"] = topics_freq["topic_name"].map(topics_mark_dict)
    topics_freq = topics_freq.dropna().rename(columns={"topic_name": "label"}).sort_values("class").reset_index(drop=True)
    topics_freq.index.name = "node_id"
    return topics_freq

def followinglink_combinations_write(topicname,type = "question_topics",follower_count = 0,dbpath = "zhihu.db"):
      '''
      following_topic is columns of dataframe
      following_topics:[[1,2,3],[12,34]] to [(1,2),(1,3)...]
      '''
      Links_File_Url = "output/gexf_output/{}{}_fol{}_links.txt".format(topicname, type, follower_count)
      if type == "question_topics":
          tablename = "Question_view"
      elif type == "user_topics":
          tablename = "usertopics_bytopic"
      print("Function topics_tolinks use table %s  ,follower_count is %s " % (tablename,follower_count))
      ori_df = read_sqlite_df(dbpath, tablename)
      df1 = ori_df.loc[ori_df.topic_name == topicname]
      df = df1.loc[df1.follower_count > follower_count]
      df = list(df["following_topics"])

      question_topic = []
      for i in range(0, len(df)):
          question_topic.append([x for x in df[i].split(",")])
          del i
      gc.collect()
      print("links has read completed")

      with open(Links_File_Url, "a", encoding="utf-8") as f:
          for i in question_topic:
              temp = list(combinations(i, 2))
              f.write(str(temp))
              f.write("\n")
              del temp
              gc.collect()
      f.close()
      print("Linksfile has write  completd")

def followinglink_combinations_read(topicname,type = "question_topics",follower_count = 0):
    Links_File_Url = "output/gexf_output/{}{}_fol{}_links.txt".format(topicname, type, follower_count)
    links = []
    with open(Links_File_Url, "r", encoding="utf-8") as f:
        for line in f:
            for item in eval(line):
                links.append(item)
    f.close()
    print("Linksfile has read completd,follower_count is",follower_count)

    links = pd.DataFrame(links, columns=("Source", "Target"))
    print("links has computed completed")
    return links

def topics_tolinks(topicname,type = "question_topics",follower_count = 0,dbpath = "zhihu.db"):
    Links_File_Url = "output/gexf_output/{}{}_fol{}_links.txt".format(topicname, type, follower_count)
    if os.path.exists(Links_File_Url):
        links = followinglink_combinations_read(topicname,type,follower_count)
    else:
        followinglink_combinations_write(topicname,type,follower_count,dbpath)
        links = followinglink_combinations_read(topicname, type, follower_count)
    return  links

# def df_topics_onehot(topicname,dbpath = "zhihu.db", tablename = "Question_view"):
#     ori_df = read_sqlite_df(dbpath,tablename)
#     df = ori_df.loc[ori_df.topic_name == topicname]
#     # df = list(df["following_topics"])
#     Topics_all = set()  ##
#     # global Topics_all
#     topics_list = []
#     for i in range(0, len(df)):
#         topics_list.append([x for x in df[i].split(",")])
#     df["topics_list"] = topics_list
#     for i in topics_list:
#         Topics_all.update(topic  for topic in i)
#     Topics_all = sorted(Topics_all)
#     for topic in Topics_all:
#         df[topic] = [topic in  item   for item in df["topics_list"]]
#     return df

def trans_time(timestamp):
    time_local = time.localtime(timestamp)
    dt = time.strftime("%Y/%m/%d", time_local)
    return dt


def gexf_output(topicname,type = "question_topics",follower_count = 0):
    Gexf_File_Url = "output/gexf_output/{}{}_fol{}.gexf".format(topicname,type,follower_count)
    print("Function gexf_output type is %s , Gexf_File_Url is %s,follower_count is %s "% (type,Gexf_File_Url,follower_count))
    '''
    生成话题关系图，及简单类型分布分析
    '''
    # 根据话题类型标记字典，标记话题类型
    topics_freq = label_toclass(topicname,type,follower_count)
    # 问题的话题是生成组合，构造边数据
    links = topics_tolinks(topicname,type,follower_count)
    # 根据筛选的分类目录整理边连接关系，去除不在分类的话题
    links = links[(links.Source.isin(topics_freq["label"])) & (links.Target.isin(topics_freq["label"]))]
    links = links.groupby(["Source", "Target"]).size().reset_index(name="weight").sort_values("weight", ascending=False)
    print("links transform links to Source and Target")
    # links的Source和Target转成id,label转成id
    label_id = dict(zip(topics_freq["label"], topics_freq.index))
    links["Source_id"] = links["Source"].map(label_id)
    links["Target_id"] = links["Target"].map(label_id)
    print("begin to wirte the gexf file")
    with open(Gexf_File_Url, "w", encoding="utf-8") as f:
        nodes_txt = ""
        for i in range(0, len(topics_freq)):
            str0 = "{}".format(topics_freq.index[i])
            str1 = "{}".format(topics_freq.iloc[i]["label"])
            str2 = "{}".format(int(topics_freq.iloc[i]["class"]))
            str3 = "{}".format(topics_freq.iloc[i]["size_log2"])
            str4 = "{}".format(topics_freq.iloc[i]["size"])
            p = "<node id= " + "\"" + str0 + "\"" + " " + "label=" + "\"" + str1 + "\"" + " >\n" \
                + "<attvalues>" + '<attvalue for ="modularity_class" ' + " " + "value = " + "\"" + str2 + "\"" + "></attvalue >\n" \
                + '<attvalue for ="1" ' + " " + "value = " + "\"" + str4 + "\"" + "></attvalue ></attvalues>\n" \
                + "<viz:size value =" + "\"" + str3 + "\"" + "> </viz:size>\n" + "</node> \n"
            nodes_txt = nodes_txt + p

        links_txt = ""
        for i in range(0, len(links)):
            edge_id = str(i)
            str1 = "{}".format(links.iloc[i]["Source_id"])
            str2 = "{}".format(links.iloc[i]["Target_id"])
            str3 = "{}".format(int(links.iloc[i]["weight"]))
            p = '<edge id= ' + "\"" + edge_id + "\"" + " " + "source=" + "\"" + str1 + "\"" + " " + "target =" + "\"" + str2 + "\"" + " " + "weight = " + "\"" + str3 + "\"" + "></edge >\n"
            links_txt = links_txt + p
        head_txt = '''<?xml version="1.0" encoding="UTF-8"?><gexf xmlns="http://www.gexf.net/1.2draft" version="1.2" xmlns:viz="http://www.gexf.net/1.2draft/viz" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.gexf.net/1.2draft http://www.gexf.net/1.2draft/gexf.xsd">
    <graph defaultedgetype="undirected" mode="static">
      <attributes class="node" mode="static">
        <attribute id="modularity_class" title="Modularity Class" type="integer"></attribute>
        <attribute id="1" title="Size" type="integer"></attribute>
      </attributes>
      <nodes>'''
        all = head_txt + nodes_txt + "</nodes>\n" + "<edges>" + links_txt + "</edges>\n</graph>\n</gexf>"
        f.write(all)
    f.close()

