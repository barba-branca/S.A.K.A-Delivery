# Registro de Atualizações na Documentação

Este documento registra as principais mudanças recentes feitas na estrutura e no conteúdo da documentação do projeto **S.A.K.A Delivery KDS**.

## 1. Reorganização de Diretórios
Para melhor organização do repositório, foi criada a pasta raiz `/docs`. Os seguintes arquivos de documentação avulsos foram centralizados neste diretório:
- `DOCUMENTACAO_PAGAMENTOS.md`
- `PROJETO_SAKA_DELIVERY_KDS.md`
- `WEBHOOK_MERCADO_PAGO.md` (anteriormente localizado em `/backend`)

> **Nota:** Os arquivos `README.md` principais (da raiz e da pasta `/backend`) foram mantidos em seus locais originais por servirem como ponto de entrada padrão.

## 2. Atualização do README.md Principal
O arquivo `README.md` da raiz do projeto foi expandido para facilitar o *onboarding* de novos desenvolvedores que assumirem a manutenção do sistema. Foram adicionadas as seguintes seções:

### 🐳 Opção via Docker Compose
Foi documentado que a maneira recomendada de iniciar o Banco de Dados e o Backend em desenvolvimento é através do comando `docker-compose up -d`.

### 👨‍💻 Para Desenvolvedores (Contributing)
Esta seção estabelece as diretrizes básicas do projeto:
- **Padrões de Código**: Avisos sobre o uso de TypeScript e Tailwind no Frontend, e FastAPI/Pydantic/Alembic no Backend.
- **Fluxo de Trabalho Git**: Instruções para criar branches de banco e efetuar Pull Requests.
- **Scripts Úteis**: Lista de comandos usuais tanto do `npm` quanto do `python`/`alembic`.

### 🗺 Roadmap (Próximos Passos)
Adicionada uma visão das próximas entregas planejadas para a evolução do SaaS:
1. Gateways de Pagamento em Produção (OpenPix/Mercado Pago).
2. Atualização em Tempo Real via WebSockets.
3. Arquitetura Multi-Tenant para múltiplos estabelecimentos.
4. Notificações Push originárias do iFood.
