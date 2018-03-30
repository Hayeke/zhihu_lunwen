library(DBI)
library(lubridate)
library(ggplot2)
conn <- DBI::dbConnect(RSQLite::SQLite(),dbname='C:\\Data\\OneDrive\\Pythonspace\\zhihu_new\\zhihu.db')



questioninfo<-dbGetQuery(conn,"select * from Questions_View")
questioninfo$topic_name<-as.factor(questioninfo$topic_name)
#class(questioninfo$created_time) = "POSIXct"
#questioninfo$created_time<-as.Date(format(questioninfo$created_time,format="%Y-%m-%d"))



'''
按话题根据fol_ratio和ans_ratio 分类；
按话题关注和回答数的中位数作为阈值。

'''

library(dplyr)
library(reshape2)
judge_Type<-function(inputdata,topicname){
  temp<-inputdata%>%
    filter(topic_name==topicname)%>%
    mutate(fol_ratio_type = as.factor(if_else(.$fol_max_ratio<=median(.$fol_max_ratio),"low","high")),
           ans_ratio_type = as.factor(if_else(.$ans_max_ratio<=median(.$ans_max_ratio),"low","high")))
  for (i in 1:nrow(temp)){
    if(temp$fol_ratio_type[i]=="low" && temp$ans_ratio_type[i] =="low"){
      temp$que_type[i] = "沉默点" }
    else if(temp$fol_ratio_type[i]=="low" && temp$ans_ratio_type[i] =="high"){
      temp$que_type[i] = "潜在点"}
    else if(temp$fol_ratio_type[i]=="high" && temp$ans_ratio_type[i] =="low"){
      temp$que_type[i] = "关注焦点"
    }else if(temp$fol_ratio_type[i]=="high" && temp$ans_ratio_type[i] =="high"){
      temp$que_type[i] = "舆论焦点"}
  }
  temp$que_type<-as.factor(temp$que_type)
  return(temp)
}



'''
另一种数据归一化方法,
'''

library(dplyr)
library(reshape2)
judge_Type<-function(inputdata,topicname){
  temp<-inputdata%>%
    filter(topic_name==topicname)%>%
    mutate(folcount_scale = (follower_count-median(follower_count))/(max(follower_count)-min(follower_count)),
           anscount_scale = (answer_count-median(answer_count))/(max(answer_count)-min(answer_count)))
  return(temp)
}

judge_Type<-function(inputdata,topicname){
  temp<-inputdata%>%
    filter(topic_name==topicname)%>%
    mutate(folcount_scale = scale(follower_count,TRUE,TRUE),
           anscount_scale = scale(answer_count,TRUE,TRUE))
  return(temp)
}




'''
类型处理完毕后存入数据库，表名为“Question_ETL”
'''
xiaomi<-judge_Type(questioninfo,"小米科技")
huawei<-judge_Type(questioninfo,"华为")
meizu<-judge_Type(questioninfo,"魅族科技")
apple<-judge_Type(questioninfo,"苹果公司 (Apple Inc.)")
temp<-rbind(xiaomi,huawei,meizu,apple)

dbWriteTable(conn,"Questions_ETL2",temp)


"""
visualization
"""
temp$topic_name<-as.factor(temp$topic_name)

ggplot(temp,aes(x=temp$folcount_scale,y=temp$anscount_scale,color = temp$topic_name))+
  geom_point()+
  xlim(-0.75,0.75)+
  ylim(-0.75,0.75)+
  geom_smooth(method = "auto")


temp$topic_name<-as.factor(temp$topic_name)

ggplot(temp,aes(x=temp$folcount_scale,y=temp$anscount_scale,color = temp$topic_name))+
  geom_point()+
  geom_smooth(method = "loess")






