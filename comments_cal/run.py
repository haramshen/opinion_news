# -*- coding: utf-8 -*-

import os
import csv
import time

from ad_filter import ad_filter

import sys
AB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../test/')
sys.path.append(AB_PATH)

from feature import extract_feature
from sort import text_weight_cal
from duplicate import duplicate
from clustering import kmeans, cluster_evaluation
from utils import cut_words, _default_mongo
from config import MONGO_DB_NAME, SUB_EVENTS_COLLECTION, \
    EVENTS_NEWS_COLLECTION_PREFIX, EVENTS_COLLECTION, EVENTS_COMMENTS_COLLECTION_PREFIX


if __name__=="__main__":
    # 聚类评价时选取TOPK_FREQ_WORD的高频词
    TOPK_FREQ_WORD = 50
    # 聚类评价时最小簇的大小
    LEAST_SIZE = 8
    topic = "APEC2014"
    topicid = "54916b0d955230e752f2a94e"
    mongo = _default_mongo(usedb=MONGO_DB_NAME)
    results = mongo[EVENTS_COMMENTS_COLLECTION_PREFIX + topicid].find()

    inputs = []
    for r in results:
        r['title'] = ''
        r['content'] = r['content168'].encode('utf-8')
        item = ad_filter(r)
        if item['ad_label'] == 0:
            inputs.append(item)

    # kmeans 聚类及评价
    kmeans_results = kmeans(inputs, k=10)
    reserve_num = 5
    final_cluster_results, tfidf_dict = cluster_evaluation(kmeans_results, top_num=reserve_num, topk_freq=TOPK_FREQ_WORD, least_size=LEAST_SIZE, min_tfidf=None)
    inputs = []
    for label, items in final_cluster_results.iteritems():
        if label != 'other':
            inputs.extend(items)

    #计算各簇特征词
    cluster_feature = extract_feature(inputs)
    for label, fwords in cluster_feature.iteritems():
        print label
        for k,v in fwords.iteritems():
            print k,v

    #计算文本权重
    for input in inputs:
        weight = text_weight_cal(input, cluster_feature[input['label']])
        input["weight"] = weight