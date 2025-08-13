def build_knn_vector_search_query(vector,
                                  top_k=10,
                                  knowledge_base_id=None,
                                  include_doc_ids=None,
                                  exclude_doc_ids=None,
                                  exclude_ids=None,
                                  start_publish_time=None,
                                  end_publish_time=None):
    """
    构建KNN向量搜索查询（使用ES的KNN功能）
    Args:
        vector: 输入的向量，维度应为1536
        top_k: 返回的最大结果数量
        knowledge_base_id: 可选的知识库ID列表或单个ID
        include_doc_ids: 可选的文档ID列表，仅包含这些文档ID
        exclude_doc_ids: 可选的文档ID列表，排除这些文档ID
        exclude_ids: 可选的ID列表，排除这些ID
        start_publish_time: 可选的开始发布时间
        end_publish_time: 可选的结束发布时间
    Returns:
        dict: ES查询的字典表示
    """
    # 构建基本查询
    query = {
        "size": top_k,
        "_source": {
            "excludes": ["content"]
        },
        "knn": {
            "field": "context_vector",
            "query_vector": vector,
            "k": top_k,
            "num_candidates": top_k * 2
        }
    }
    # 添加过滤条件
    filter_conditions = {
        "bool": {
            "must": [{
                "term": {
                    "valid": True
                }
            }],
            "must_not": []
        }
    }
    # 添加知识库ID过滤（支持单个ID或ID列表）
    if knowledge_base_id:
        if isinstance(knowledge_base_id,
                      (list, tuple)) and len(knowledge_base_id) > 0:
            # 如果是非空列表，使用terms查询
            filter_conditions["bool"]["must"].append(
                {"terms": {
                    "knowledge_base_id": knowledge_base_id
                }})
        elif not isinstance(knowledge_base_id, (list, tuple)):
            # 如果是单个值，使用term查询
            filter_conditions["bool"]["must"].append(
                {"term": {
                    "knowledge_base_id": knowledge_base_id
                }})
    # 添加包含文档ID过滤
    if include_doc_ids and len(include_doc_ids) > 0:
        filter_conditions["bool"]["must"].append(
            {"terms": {
                "doc_id": include_doc_ids
            }})
    # 添加排除文档ID过滤
    if exclude_doc_ids and len(exclude_doc_ids) > 0:
        filter_conditions["bool"]["must_not"].append(
            {"terms": {
                "doc_id": exclude_doc_ids
            }})
    # 添加排除ID过滤
    if exclude_ids and len(exclude_ids) > 0:
        filter_conditions["bool"]["must_not"].append(
            {"ids": {
                "values": exclude_ids
            }})
    publish_time_range_filter = {}
    if start_publish_time is not None:
        publish_time_range_filter["gte"] = start_publish_time
    if end_publish_time is not None:
        publish_time_range_filter["lte"] = end_publish_time
    if len(publish_time_range_filter) > 0:
        filter_conditions["bool"]["must"].append(
            {"range": {
                "publish_time": publish_time_range_filter
            }})
    # 只有当过滤条件不为空时，才添加到查询中
    if filter_conditions["bool"]["must"] or filter_conditions["bool"][
            "must_not"]:
        query["knn"]["filter"] = filter_conditions
    return query
