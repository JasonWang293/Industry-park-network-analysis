import networkx as net
import csv
import matplotlib.pyplot as plot
import pandas as pd
from pandas import DataFrame
from pandas import Series
from datetime import datetime

#Generate edge list base on relation matrix
def creat_net_data(data_file,row_name_file):
    data_df=pd.read_csv(data_file+'.csv',index_col='Name')#Open the edge list file
    row_name=pd.read_csv(row_name_file+'.csv')#Read the row name
    same_num=0
    rel_data=[]
    for i in range(0,len(data_df.index)):
        for j in range(i+1,len(data_df.index)):
            for column in range(0,len(data_df.columns)):
                #If one column of the two row are both 1, count plus one
                if data_df.ix[i][column]==1 and data_df.ix[j][column]==1:
                    same_num=same_num+1
            if same_num:
                rel_data.append([row_name.ix[i]['Name'],row_name.ix[j]['Name'],same_num])#关系计数存入列表
            same_num=0#Set the relationship counter to zero
    return rel_data

#Generate network base on edge list
def create_net(g,filename,threshold):
    file=open(filename+'.csv','r',encoding='utf-8')
    file_reader=csv.reader(file)
    for line in file_reader:
        if int(line[2])>=threshold:
            g.add_edge(line[0].encode('utf-8').decode('utf-8-sig'),
                       line[1].encode('utf-8').decode('utf-8-sig'),
                       weight=int(line[2]),
                       reciprocal_weight=1/int(line[2]))

#Draw the network diagram
def plot_net(m,font_size=12):
    d=net.degree(m)
    pos=net.spring_layout(m)
    node_degree=[]
    edge_weight=[]
    for n in m.nodes:
        node_degree.append(d[n]*50)
    for (u,v,w) in m.edges(data=True):
        edge_weight.append(float(w['weight'])*1.8)
    #Draw the nodes
    net.draw_networkx_nodes(m,pos,node_size=node_degree,node_color='b',alpha=0.8)
    #Draw the edges
    net.draw_networkx_edges(m,pos,width=edge_weight,alpha=0.6)
    #Add the name of nodes
    net.draw_networkx_labels(m,pos,font_size=font_size)
    plot.axis('off')

#Write csv file
def csv_file_w(filename,data):
    csv_f=open(filename+'.csv','w',encoding='utf-8',newline='')
    csv_writer=csv.writer(csv_f)
    for i in data:
        csv_writer.writerow(i)
    csv_f.close()

#Write single column data to csv file
def csv_file_w_one(filename,data):
    csv_f=open(filename+'.csv','w',encoding='utf-8',newline='')
    csv_writer=csv.writer(csv_f)
    csv_writer.writerow(data)
    csv_f.close()

starttime=datetime.now()
file_name='park_net'
industrial_park_net=creat_net_data('park_industry_matrix','industrial_park_name')
csv_file_w(file_name,industrial_park_net)

threshold=1
font_size=20
g=net.Graph()
#Open the analysis result record file
data_f=open(str(threshold)+file_name+'analysis_result.txt','w',encoding='utf-8')
create_net(g,file_name,threshold)
fig_g=plot.figure()
plot_net(g,font_size=font_size)
plot.savefig(str(threshold)+file_name)
node_num=g.number_of_nodes()
data_f.write("number of nodes*"+str(node_num)+"\n")
edge_num=g.number_of_edges()
data_f.write("number of edges*"+str(edge_num)+"\n")
#Calculate network density
density=edge_num/(node_num*(node_num-1))
data_f.write("destiny*"+str(density)+"\n")
#Get connected subgraph
sub_gs=net.connected_component_subgraphs(g)
#Average shortest path length of each connected subgraph
ave_shortest_path=[net.algorithms.average_shortest_path_length
                   (sub,weight='reciprocal_weight') for sub in sub_gs]
data_f.write("average shortest path for each connected subgraph*"+str(ave_shortest_path)+"\n")
csv_file_w_one(str(threshold)+file_name+'average_shortest_path',ave_shortest_path)
#Community detection
communities=net.algorithms.community.greedy_modularity_communities(g,weight='reciprocal_weight')
communities=list(communities)
data_f.write("community*"+str(communities)+"\n")
communities_len=len(communities)
data_f.write("number of communities*"+str(communities_len)+"\n")
g_communities_len=list(len(x) for x in communities)
data_f.write("number of nodes in each community*"+str(g_communities_len)+"\n")
#Industry composition in each community
industrial_park_df=pd.read_csv('park_industry_matrix.csv',index_col='Name')#打开园区-产业文件
#Store the repeated industries in each community
repetitive_industry_list=[]
#Store the weighted degree of parks in each community
communities_weighting_degree=[]
community_num=0
for community in communities:
    community_num=community_num+1
    community_g=g.copy()
    community_g.remove_nodes_from(g.nodes-community)
    fig_g=plot.figure()
    plot_net(community_g,font_size=font_size)
    plot.savefig(str(threshold)+file_name+"_community"+str(community_num))
    #Weighted degree of nodes in the community
    community_weighting_degree=dict(net.degree(community_g,weight='weight'))
    sorted_community_weighting_degree=list(sorted(community_weighting_degree.items(),key=lambda x:x[1],reverse=True))
    communities_weighting_degree.append(sorted_community_weighting_degree)
    #Sort the repetition times of each industry in the cluster by descending order
    community_industrial_park_df=industrial_park_df.ix[community]
    repetitive_industry=community_industrial_park_df.sum()
    repetitive_industry=repetitive_industry[repetitive_industry>0].sort_values(ascending=False)
    repetitive_industry_list.append(dict(repetitive_industry))
    csv_file_w(str(threshold)+file_name+'community_detection',zip(g_communities_len,
                                               communities_weighting_degree,
                                               repetitive_industry_list))
    #write the park-industry matrix of each community
    community_industrial_park_df=community_industrial_park_df[repetitive_industry.index]
    community_industrial_park_df.to_csv(str(threshold)+file_name+"_community"+str(community_num)+"_matrix.csv")
data_f.write("weighted degree of parks in each community*"+
             str(communities_weighting_degree)+"\n")
data_f.write("repetitive industries in each community*"+str(repetitive_industry_list)+"\n")
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
data_f.close()
endtime=datetime.now()
runtime=(endtime-starttime).seconds
print(runtime)
plot.show()