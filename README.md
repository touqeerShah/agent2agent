# Agent-to-Agent Learning Project

This project explores how one application can work with agents that belong to different business areas.

MCP lets an agent connect to existing tools without building every tool integration from scratch. A2A lets separate agents communicate with each other. Each agent can keep its own business logic and run on its own server.

An orchestration agent receives the user’s request and decides which agent should handle it. For this project, we will connect three agents:

| Agent | Example setup |
|---|---|
| Insurance agent | Claude on Vertex AI |
| Health research agent | Google SDK |
| Doctor provider agent | LangGraph |

These setups are examples, not a requirement to use three different frameworks or models. The agents could share the same technical structure while handling different business tasks.

```mermaid
flowchart TD
    U["User request"] --> O["Agent orchestration server"]
    O --> I["Insurance agent client"]
    O --> R["Health research agent client"]
    O --> D["Doctor provider agent client"]
    I --> IS["Insurance agent server"]
    R --> RS["Health research agent server"]
    D --> DS["Doctor provider agent server"]
```

The orchestration server uses an agent client to contact the right agent server. A request may go to one agent or involve several agents, depending on what the user needs. This gives us a practical way to learn how A2A works across agents with different responsibilities.



Discovery , neotiation task and stat managment collborations 
Discovery-> agent must adverions their capabililties so cient know when and hwo to utilize thema for specifu task 
neotiation->clent and agent nee to agree on communications methode like text forms , ifrome or audio/video to ensure proper user interaticon.
task and stat managment -> client and agent need  mechanisms to communicate task status , changes and dpeendeicies throughout task executions 
collborations -> client and agent must support dynamic interatio enabling agent to request cleaification , information or sub-actions from client other agent or users


Agent can communicate with standard web technologies like HTP , JSON-RPC , GRPC anf SSR 
Agent Card is json object which tell other agent what they do and how to connect  protocel
/ like passport of agent or card 

connect  with syn , asun , steam and push notifications


Doc
https://github.com/a2aproject/a2a-samples
https://agentstack.beeai.dev/stable/introduction/welcome
https://a2a-protocol.org/latest/



```mermaid
graph TD
    %% User / Client Layer
    User
    
    %% Main Orchestrator Layer (Lesson 9)
    subgraph OrchestratorLayer [Router/Requirement Agent]
        Concierge["<b>Healthcare Concierge Agent</b><br/>(BeeAI Framework)<br/><code>Port: 9996</code>"]
    end

    subgraph SubAgents [A2A Agent Servers]
        direction LR

        PolicyAgent["<b>Policy Agent</b><br/>(Anthropic Claude with A2A SDK)<br/><code>Port: 9999</code>"]
        ResearchAgent["<b>Research Agent</b><br/>(Google ADK)<br/><code>Port: 9998</code>"]

        ProviderAgent["<b>Provider Agent</b><br/>(LangGraph + LangChain)<br/><code>Port: 9997</code>"]
    end

    %% Data & Tools Layer
    subgraph DataLayer [Data Sources & Tools]
        PDF["Policy PDF"]
        Google[Google Search Tool]
        MCPServer["FastMCP Server<br/>(doctors.json)"]
    end
    
    Label_UA["Sends Query - A2A"]
    Label_CP["A2A"]
    Label_CR["A2A"]
    Label_CProv["A2A"]
    Label_MCP["MCP (stdio)"]

    %% -- CONNECTIONS --
    
    User --- Label_UA --> Concierge

    Concierge <--- Label_CP --> PolicyAgent
    Concierge <--- Label_CR --> ResearchAgent
    Concierge <--- Label_CProv --> ProviderAgent
    
    PolicyAgent -- "Reads" --> PDF
    ResearchAgent -- "Calls" --> Google
    
    ProviderAgent --- Label_MCP --> MCPServer

    classDef orchestrator fill:#f9f,stroke:#333,stroke-width:2px;
    classDef agent fill:#e1f5fe,stroke:#0277bd,stroke-width:2px;
    classDef tool fill:#fff3e0,stroke:#ef6c00,stroke-width:1px,stroke-dasharray: 5 5;
    
    classDef protocolLabel fill:#ffffff,stroke:none,color:#000;
    
    class Concierge orchestrator;
    class PolicyAgent,ResearchAgent,ProviderAgent agent;
    class PDF,Google,MCPServer tool;
    
    class Label_UA,Label_CP,Label_CR,Label_CProv,Label_MCP protocolLabel;
```