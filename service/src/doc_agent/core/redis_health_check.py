# service/src/doc_agent/core/redis_health_check.py

from redis import Redis
from redis.cluster import RedisCluster, ClusterNode
from doc_agent.core.config import settings
from doc_agent.core.logging_config import logger

# 1. 创建一个全局变量来存储主事件循环
main_event_loop = None
# 2. 将 redis_client 初始化为 None
redis_client = None
# 3. 将 redis_cluster 初始化为 None
redis_cluster = None


def init_redis_pool():
    """
    在应用启动时初始化 Redis 连接。
    支持单节点和集群模式，统一使用原生redis。
    """
    global redis_client, redis_cluster

    redis_config = settings.redis_config
    mode = redis_config.get('mode', 'single')

    if mode == 'cluster':
        # 集群模式
        if redis_cluster is None:
            logger.info("正在初始化 Redis 集群连接...")
            cluster_config = redis_config.get('cluster', {})

            # 构建集群连接参数 - 使用ClusterNode对象
            startup_nodes = []
            for node in cluster_config.get('nodes', []):
                host, port = node.split(':')
                startup_nodes.append(ClusterNode(host, int(port)))

            # 创建集群连接 - 使用最简单的配置
            redis_cluster = RedisCluster(
                startup_nodes=startup_nodes,
                decode_responses=True,
                password=cluster_config.get('password'),
                skip_full_coverage_check=True)
            logger.info("Redis 集群连接初始化成功。")
    else:
        # 单节点模式
        if redis_client is None:
            logger.info("正在初始化 Redis 连接...")
            single_config = redis_config.get('single', {})
            host = single_config.get('host', '127.0.0.1')
            port = single_config.get('port', 6379)
            db = single_config.get('db', 0)
            password = single_config.get('password', '')

            redis_client = Redis(host=host,
                                 port=port,
                                 db=db,
                                 password=password if password else None,
                                 decode_responses=True,
                                 socket_connect_timeout=30,
                                 socket_timeout=30,
                                 retry_on_timeout=True,
                                 max_connections=50)
            logger.info("Redis 连接初始化成功。")


def close_redis_pool():
    """
    在应用关闭时关闭 Redis 连接。
    """
    global redis_client, redis_cluster

    if redis_cluster:
        logger.info("正在关闭 Redis 集群连接...")
        redis_cluster.close()
        redis_cluster = None
        logger.info("Redis 集群连接已关闭。")

    if redis_client:
        logger.info("正在关闭 Redis 连接...")
        redis_client.close()
        redis_client = None
        logger.info("Redis 连接已关闭。")


def get_redis_client():
    """
    获取一个 Redis 客户端实例。
    支持单节点和集群模式，统一使用原生redis。
    """
    redis_config = settings.redis_config
    mode = redis_config.get('mode', 'single')

    if mode == 'cluster':
        if redis_cluster is None:
            raise RuntimeError("Redis 集群连接尚未初始化。请在应用启动时调用 init_redis_pool。")
        return redis_cluster
    else:
        if redis_client is None:
            raise RuntimeError("Redis 连接尚未初始化。请在应用启动时调用 init_redis_pool。")
        return redis_client


# 2. 创建一个函数来获取保存的主循环
def get_main_event_loop():
    """
    返回在应用启动时捕获的主事件循环。
    """
    if main_event_loop is None:
        raise RuntimeError("主事件循环尚未被捕获。")
    return main_event_loop


def check_redis_connection():
    """
    检查与 Redis 的连接。
    支持单节点和集群模式。
    """
    try:
        # 使用 get_redis_client 来确保我们从池中获取连接
        client = get_redis_client()

        # 检查连接类型并执行相应的ping操作
        if hasattr(client, 'cluster_nodes'):
            # 集群模式
            client.ping()
            logger.info("Redis 集群连接测试成功。")
        else:
            # 单节点模式
            client.ping()
            logger.info("Redis 连接测试成功。")

        return True
    except Exception as e:
        logger.error(f"Redis 连接测试失败: {e}")
        return False
