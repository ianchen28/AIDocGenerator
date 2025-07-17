```mermaid
graph TD
    subgraph "用户与网关"
        U[External Users] -->|HTTPS| GW[API Gateway]
    end

    GW -->|路由到 AI 任务<br/>(e.g., /qna, /generate)| AIService
    GW -->|路由到核心业务任务<br/>(e.g., /users, /orders)| CoreService

    subgraph "AI 服务域 (Python / FastAPI)"
        style AIService fill:#f0f8ff,stroke:#4a90e2,stroke-width:2px
        AIService[Python Service]
        subgraph "内部结构"
          direction LR
          A_Ctrl[1. API Controller] --> A_Svc[2. Service Orchestration] --> A_Client[3. Infrastructure Clients]
        end
    end

    subgraph "核心业务服务域 (Java / Spring Boot)"
        style CoreService fill:#f0fff0,stroke:#50e3c2,stroke-width:2px
        CoreService[Java Service]
        subgraph "内部结构"
          direction LR
          J_Ctrl[1. API Controller<br/>@RestController] --> J_Svc[2. Business Service<br/>@Service] --> J_Repo[3. Data Repository<br/>@Repository]
        end
    end

    subgraph "底层基础设施"
        DB[(Databases<br/>PostgreSQL)]
        ES[(Search Service<br/>Elasticsearch)]
        LLM[(LLM Infrastructure)]
    end

    %% 定义服务间交互
    A_Svc -->|通过 REST/gRPC 调用<br/>获取业务数据| J_Ctrl
    A_Client -->|调用 AI 能力| LLM
    A_Client -->|调用搜索能力| ES
    J_Repo -->|JPA/JDBC| DB

    %% 样式定义
    classDef default fill:#fff,stroke:#333,stroke-width:1px;
    classDef gateway fill:#fffbe6,stroke:#f5a623;
    classDef infra fill:#f3f3f3,stroke:#555,stroke-dasharray: 5 5;
    class GW gateway;
    class DB,ES,LLM infra;
```
