#-*-coding=utf-8-*-

import math
import random
from utils import _default_mongo, cut_words
from config import MONGO_DB_NAME, EVENTS_NEWS_COLLECTION_PREFIX 


def tfidf_cal(keywords_dict_list, topk=100):
    '''计算tfidf
       input
           keywords_dict_list: 不同簇的关键词, list
       output
           不同簇的top tfidf词
    '''
    results = []
    for keywords_dict in keywords_dict_list:
        tf_idf_dict = dict()

        for keyword, count in keywords_dict.iteritems():
            tf = float(count) / float(sum(keywords_dict.values()))
            document_count = sum([1 for kd in keywords_dict_list if keyword in kd.keys()])
            idf = math.log(float(len(keywords_dict.keys())) / float(document_count))
            tf_idf = tf * idf
            tf_idf_dict[keyword] = tf_idf

        tf_idf_results = sorted(tf_idf_dict.iteritems(), key=lambda(k, v): v, reverse=False)
        tf_idf_results = tf_idf_results[len(tf_idf_results)-topk:]
        tf_idf_results.reverse()

        results.append(tf_idf_results)

    return results


def extract_feature(items, title_term_weight=5, content_term_weight=1):
    '''
    提取特征词函数: Tf-idf, 名词/动词/形容词, TOP100, 标题与内容权重区分 5:1
    input：
        items: 新闻数据, 不考虑时间段, 字典的序列, 输入数据示例：[{'feature_title': 新闻标题, 'feature_content': 新闻内容, 'label': 类别标签}]
        title_term_weight: title中出现词的权重
        content_term_weight: content中出现词的权重
    output:
        每类特征词及权重, 数据格式：字典 {'我们': 32, '他们': 43}
    '''
    def extract_keyword(items):
        keywords_weight = dict()
        for item in items:
            title = item['feature_title']
            content = item['feature_content']

            title_terms = cut_words(title)
            content_terms = cut_words(content)

            for term in title_terms:
                try:
                    keywords_weight[term] += title_term_weight
                except KeyError:
                    keywords_weight[term] = title_term_weight

            for term in content_terms:
                try:
                    keywords_weight[term] += content_term_weight
                except KeyError:
                    keywords_weight[term] = content_term_weight

        # 筛掉频率大于或等于0.8, 频数小于或等于3的词
        keywords_count = dict()
        total_weight = sum(keywords_weight.values())
        for keyword, weight in keywords_weight.iteritems():
            ratio = float(weight) / float(total_weight)
            if ratio >= 0.8 or weight <= 3:
                continue

            keywords_count[keyword] = weight

        return keywords_count

    items_dict = {}
    for item in items:
        try:
            items_dict[item['label']].append(item)
        except:
            items_dict[item['label']] = [item]

    keywords_count_list = []
    for label, one_items in items_dict.iteritems():
        keywords_count = extract_keyword(one_items)
        keywords_count_list.append(keywords_count)

    results = tfidf_cal(keywords_count_list)

    return results


if __name__ == '__main__':
    mongo = _default_mongo(usedb=MONGO_DB_NAME)
    topic = "APEC2014"
    topicid = "54916b0d955230e752f2a94e"
    results = mongo[EVENTS_NEWS_COLLECTION_PREFIX + topicid].find()
    inputs = []
    for r in results:
        inputs.append({"feature_title": r["title"].encode("utf-8"), "feature_content": r["content168"].encode("utf-8"), "label": random.randint(0, 10)})

    results = extract_feature(inputs, title_term_weight=5, content_term_weight=1)
    for k in results:
        print "-----------------------"
        for v0, v1 in k:
            print v0, v1

