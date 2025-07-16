import json
import jieba
INTERNAL_STATISTICS='internal_statistics'
INTERNAL_NORMAL='internal_normal'
INTERNAL_STAGE='internal_stage'

def match_keywords(word_list,query):
    for word in word_list:
        if query.__contains__(word):
            return True
    return False

def match_keywords_dict(keyword_dict:dict,query):
    for keyword,stage in keyword_dict.items():
        if query.__contains__(keyword):
            return INTERNAL_STAGE,stage
    return INTERNAL_NORMAL,'验收'

def build_knn_vector_search_query(vector, top_k=10,
                                  knowledge_base_id=None,
                                  include_doc_ids=None,
                                  exclude_doc_ids=None):
    """
    构建KNN向量搜索查询（使用ES的KNN功能）
    
    Args:
        vector: 输入的向量，维度应为1536
        top_k: 返回的最大结果数量
        knowledge_base_id: 可选的知识库ID列表或单个ID
        include_doc_ids: 可选的文档ID列表，仅包含这些文档ID
        exclude_doc_ids: 可选的文档ID列表，排除这些文档ID
        
    Returns:
        dict: ES查询的字典表示
    """
    # 构建基本查询
    query = {
        "size": top_k,
        "_source":{
            "excludes":["content"]
            },
        
        "knn": {
            "field": "context_vector",
            "query_vector": vector,
            "k": top_k,
            "num_candidates": top_k*2
        }
    }
    
    # 添加过滤条件
    filter_conditions = {
        "bool": {
            "must": [{"term": {"valid": True}}],
            "must_not": []
        }
    }
    
    # 添加知识库ID过滤（支持单个ID或ID列表）
    if knowledge_base_id:
        if isinstance(knowledge_base_id, (list, tuple)) and len(knowledge_base_id) > 0:
            # 如果是非空列表，使用terms查询
            filter_conditions["bool"]["must"].append({
                "terms": {"knowledge_base_id": knowledge_base_id}
            })
        elif not isinstance(knowledge_base_id, (list, tuple)):
            # 如果是单个值，使用term查询
            filter_conditions["bool"]["must"].append({
                "term": {"knowledge_base_id": knowledge_base_id}
            })
    
    # 添加包含文档ID过滤
    if include_doc_ids and len(include_doc_ids) > 0:
        filter_conditions["bool"]["must"].append({
            "terms": {"doc_id": include_doc_ids}
        })
    
    # 添加排除文档ID过滤
    if exclude_doc_ids and len(exclude_doc_ids) > 0:
        filter_conditions["bool"]["must_not"].append({
            "terms": {"doc_id": exclude_doc_ids}
        })
    
    # 只有当过滤条件不为空时，才添加到查询中
    if filter_conditions["bool"]["must"] or filter_conditions["bool"]["must_not"]:
        query["knn"]["filter"] = filter_conditions
    
    return query



def doc_term_search_query(doc_id:str):
    query = {
        "size": 10,
        "query": {
            "term": {"doc_id": doc_id}
        }
    }
    return query


def internal_classify(query):
    statistics_query_keywords=['哪些',"统计"]
    stage_keywords={'预可':"预可","可研":"可研","验收":"验收","竣工":"竣工","技施":"技施","招标":"招标","初设":"初设","规划":"规划"}
    if match_keywords(statistics_query_keywords,query):
        return  INTERNAL_STATISTICS,"验收"
    return match_keywords_dict(stage_keywords,query)
    
def knn_search_internal(query,embedding,top_k=10):
    # 1. 通用query 只搜索 最后一个阶段的最后审定稿
    # 2.明确提出了 阶段要在对应阶段搜
    classify_tag,stage=internal_classify(query)
    if classify_tag==INTERNAL_STATISTICS:
            #  1. 统计类，检索 final doc为1的字段
            knn_query={
                    "field": "context_vector",
                    "query_vector": embedding,
                    'k': top_k, 'num_candidates': top_k * 2,"filter":{"term":{"is_final":True}    }
                        }
            request_body={
            "knn": knn_query,
            "_source": ["context_vector","content_view", "domain_ids", "meta_data", "doc_type", "doc_id","valid","publishtime"],
            "size":top_k}
        
    elif classify_tag==INTERNAL_NORMAL:
        knn_query={
                "field": "context_vector",
                "query_vector": embedding,
                'k': top_k, 'num_candidates': top_k * 2,"filter":{"term":{"is_final":True}    }
                    }
        request_body={
        "knn": knn_query,
        "_source": ["context_vector","content_view", "domain_ids", "meta_data", "doc_type", "doc_id","valid","publishtime"],
        "size":top_k}
    elif classify_tag==INTERNAL_STAGE:
        knn_query={
                "field": "context_vector",
                "query_vector": embedding,
                'k': top_k, 'num_candidates': top_k * 2,"filter":{"term":{"stage":stage}    }
                    }
        request_body={
        "knn": knn_query,
        "_source": ["context_vector","content_view", "domain_ids", "meta_data", "doc_type", "doc_id","valid","publishtime"],
        "size":top_k}
    return request_body

def standard_search_query(query,top_k=10):
    query_str = " ".join(jieba.lcut(query))
    
    request_body={"query":{"match":{"content":{"query":query_str,"boost":1.0}}},"size":top_k}

    return request_body

def oa_search_query(vector, top_k=10):
    query = {
        "size": top_k,
        "_source": {
            "excludes": ["content"]
        },
        "query": {
            "function_score": {
                "query": {
                    "knn": {
                        "field": "context_vector",
                        "query_vector": vector,
                        "num_candidates": top_k
                    }
                },
                "functions": [
                    {
                        "script_score": {
                            "script": {
                                "source": """
                                    // 获取 publishtime 的 Unix 时间戳
                                    def publishtime = doc['publishtime'].value;
                                    // 获取当前时间的 Unix 时间戳
                                    def current_time = System.currentTimeMillis() / 1000; // 转换为秒
                                    // 计算 publishtime 与当前时间的年数差
                                    def years_diff = (current_time - publishtime) / (365 * 24 * 60 * 60);
                                    // 计算时间分数调整值
                                    def time_score = 0;
                                    if (years_diff < 10) {
                                      time_score = (10 - years_diff) * 0.1;
                                    } else {
                                      time_score = (years_diff - 10) * -0.1;
                                    }
                                    // 返回原始分数加上时间分数调整值
                                    return _score + time_score;
                                """
                            }
                        }
                    }
                ],
                "score_mode": "sum" 
            }
        }
    }
    
    return query

def oa_keyword_search_query(query,top_k=10):
    query_str = " ".join(jieba.lcut(query))
    query = {
        "size": top_k,
        "_source": {
            "excludes": ["content"]
        },
        "query":{"match":{"content":{"query":query_str,"boost":1.0}}}
    }
    return query    



def build_oa_org_search_query(vector, top_k=10,
                                  org=None):
    """
    构建KNN向量搜索查询（使用ES的KNN功能）
    
    Args:
        vector: 输入的向量，维度应为1536
        top_k: 返回的最大结果数量
        org: 可选的组织/部门名称，用于过滤文档
        
    Returns:
        dict: ES查询的字典表示
    """
    # 构建基本查询
    query = {
        "size": top_k,
        "_source":{
            "excludes":["content"]
            },
        
        "knn": {
            "field": "context_vector",
            "query_vector": vector,
            "k": top_k,
            "num_candidates": top_k
        }
    }
    
    # 添加过滤条件
    filter_conditions = {
        "bool": {
            "must": [{"term": {"valid": True}}],
            "must_not": []
        }
    }
    
    # 添加组织/部门过滤
    if org:
        filter_conditions["bool"]["must"].append({
            "term": {"pub_org": org}
        })
    
    # 只有当过滤条件不为空时，才添加到查询中
    if filter_conditions["bool"]["must"] or filter_conditions["bool"]["must_not"]:
        query["knn"]["filter"] = filter_conditions
    
    return query





def create_oa_search_query(vector, top_k=10,start_timestamp=None, end_timestamp=None):
    query = {
        "size": top_k,
        "_source": {
            "excludes": ["content"]
        },
        "knn": {
            "field": "context_vector",
            "query_vector": vector,
            "k": top_k,
            "num_candidates": top_k
        }
    }
    if start_timestamp and end_timestamp:
        query["knn"]["filter"] = {
            "range": {
                "publish_time": {
                    "gte": start_timestamp,
                    "lte": end_timestamp
                }
            }
        }
        return query
    else:
        return query
