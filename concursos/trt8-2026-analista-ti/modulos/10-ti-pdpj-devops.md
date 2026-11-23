# Módulo 10 — TI: Arquitetura da PDPJ-Br, DevOps/DevSecOps e Normativos do CNJ

> Edital: *DevOps e DevSecOps: Maven; Git; CI/CD; Testes Automatizados. Arquitetura de desenvolvimento da PDPJ-Br: Java; microsserviços; API RESTful; JSON; Spring, Spring Cloud, Spring Boot, Spring Eureka, Zuul; MapStruct; Swagger; Service Discovery; API Gateway; JPA 2.0; Hibernate 4.3+; Hibernate Envers; Flyway; PostgreSQL; H2; SSO; Keycloak; OAuth2 (RFC 6749) e RFC 9700; mensageria e webhooks; RabbitMQ; evento negocial; APIs reversas; Docker; Kubernetes; Rancher; CI/CD. Normativos: Res. CNJ 522/2023, 335/2020, 396/2021; Portarias CNJ 252/2020, 253/2020, 131/2021, 162/2021.*
> **É o bloco mais característico desta prova.** Na prova FCC do TRT-15 (2023), caíram a **porta do Eureka (8761)** e a anotação **`@Mapper`** do MapStruct. Estimativa: 5–8 questões.

## 1. PDPJ-Br — visão geral
- **Plataforma Digital do Poder Judiciário Brasileiro**: instituída pela **Resolução CNJ 335/2020**; integra os tribunais em uma plataforma **única, colaborativa, modular** (microsserviços), **em nuvem**, com **código aberto** compartilhado entre tribunais e **APIs** para interoperabilidade. Mantém o **PJe** como sistema de processo eletrônico **prioritário** do CNJ (programa **Justiça 4.0**).
- Cada tribunal pode desenvolver **módulos/serviços** e **disponibilizá-los** a todos (*marketplace* da PDPJ-Br).
- **Stack de referência** (Portaria CNJ 253/2020 e documentação técnica da PDPJ-Br): **Java + Spring Boot/Spring Cloud**, **microsserviços** com **service discovery (Eureka)** e **API Gateway (Zuul)**, **REST/JSON** documentado com **Swagger/OpenAPI**, persistência **JPA/Hibernate** com auditoria **Envers** e migrações **Flyway**, banco **PostgreSQL** (H2 em testes), **SSO com Keycloak** (OAuth2/OIDC), **mensageria RabbitMQ** e **webhooks**, **contêineres Docker** orquestrados por **Kubernetes** e geridos com **Rancher**, **Git** e **CI/CD**.

## 2. Microsserviços com Spring Cloud
| Padrão | Função | Implementação na stack |
|---|---|---|
| **Service Discovery / Registry** | Serviços se **registram** e **descobrem** uns aos outros dinamicamente (sem IP fixo) | **Spring Cloud Netflix Eureka** |
| **API Gateway** | **Ponto único de entrada**: roteamento, autenticação, rate limiting, CORS, agregação | **Netflix Zuul** (legado) / Spring Cloud Gateway (sucessor) |
| Balanceamento no cliente | Distribui chamadas entre instâncias registradas | Ribbon (legado) / Spring Cloud LoadBalancer |
| Circuit Breaker | Evita falhas em cascata | Hystrix (legado) / **Resilience4j** |
| Cliente REST declarativo | Interface Java anotada vira cliente HTTP | **OpenFeign** (`@FeignClient`) |
| Configuração centralizada | Propriedades externas versionadas | Spring Cloud Config |
| Rastreamento distribuído | Correlação de chamadas | Micrometer Tracing / Zipkin |

### Eureka (cai!)
```properties
# Servidor Eureka — application.properties
spring.application.name=eureka-server
server.port=8761                                  # PORTA PADRÃO do Eureka
eureka.client.register-with-eureka=false          # o servidor não se registra nele mesmo
eureka.client.fetch-registry=false
```
```java
@SpringBootApplication
@EnableEurekaServer                               // transforma a aplicação em servidor Eureka
public class EurekaServerApplication { ... }
```
```properties
# Cliente (microsserviço) — application.properties
spring.application.name=servico-processos         # vira o ID do serviço no registro
eureka.client.service-url.defaultZone=http://localhost:8761/eureka/
```
- Dependências: `spring-cloud-starter-netflix-eureka-server` / `...-eureka-client`. O cliente envia **heartbeats** (renovação a cada 30 s, por padrão); o painel do Eureka fica em `http://host:8761`.

### Zuul (API Gateway da Netflix)
```java
@SpringBootApplication
@EnableZuulProxy                                  // habilita o proxy reverso/gateway
public class GatewayApplication { ... }
```
```properties
zuul.routes.processos.path=/processos/**
zuul.routes.processos.serviceId=servico-processos # resolve via Eureka
```
- **Filtros Zuul**: tipos **`pre`** (antes do roteamento — autenticação, logs), **`route`** (encaminha), **`post`** (após resposta — cabeçalhos, métricas), **`error`**. Classe `ZuulFilter`: `filterType()`, `filterOrder()`, `shouldFilter()`, `run()`.
- Zuul 1 é bloqueante e foi removido do Spring Cloud a partir da versão 2020.0; o sucessor é o **Spring Cloud Gateway** (reativo, *predicates* e *filters*).

## 3. Spring Boot
- **Convenção sobre configuração** + **autoconfiguração**; **servidor embutido** (Tomcat, porta padrão **8080**); **JAR executável** (`java -jar app.jar` ou `mvn spring-boot:run`); **starters** (`spring-boot-starter-web`, `-data-jpa`, `-security`, `-actuator`, `-test`, `-amqp`, `-validation`).
- `@SpringBootApplication` = **`@Configuration` + `@EnableAutoConfiguration` + `@ComponentScan`**.
- Configuração: `application.properties` ou `application.yml`; **perfis** (`spring.profiles.active=dev` → `application-dev.properties`); `@Value("${chave}")`, `@ConfigurationProperties`.
- **Estereótipos**: `@Component`, `@Service`, `@Repository` (traduz exceções de persistência), `@Controller`, **`@RestController`** (= `@Controller` + `@ResponseBody`); `@Configuration` + `@Bean`.
- **Injeção de dependência**: `@Autowired` (preferir **injeção por construtor**); escopos `singleton` (padrão), `prototype`, `request`, `session`.
```java
@RestController
@RequestMapping("/api/processos")
public class ProcessoController {
    private final ProcessoService service;
    public ProcessoController(ProcessoService service) { this.service = service; }   // injeção por construtor

    @GetMapping("/{id}")
    public ProcessoDto buscar(@PathVariable Long id) { return service.buscar(id); }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ProcessoDto criar(@RequestBody @Valid ProcessoDto dto) { return service.criar(dto); }

    @GetMapping
    public List<ProcessoDto> listar(@RequestParam int ano) { return service.porAno(ano); }
}
```
- **Spring Data JPA**: `interface ProcessoRepository extends JpaRepository<Processo, Long> { List<Processo> findByAnoOrderByNumero(int ano); }` (consultas **derivadas do nome do método**; `@Query` para JPQL/SQL nativo); paginação `Pageable`.
- `@Transactional` (propagação `REQUIRED` padrão; rollback automático para *unchecked exceptions*).
- **Actuator**: `/actuator/health`, `/actuator/info`, `/actuator/metrics`, `/actuator/prometheus` (via Micrometer) — observabilidade.
- **Spring Security** + OAuth2 Resource Server (valida JWT emitido pelo Keycloak).

## 4. MapStruct (cai!)
- Gerador de **mapeadores entre objetos** (ex.: entidade ↔ DTO) por **processador de anotações em tempo de compilação** — código gerado é Java puro, **sem reflexão** (rápido e verificado pelo compilador).
```java
@Mapper(componentModel = "spring")                 // anotação OBRIGATÓRIA na interface; "spring" permite @Autowired
public interface ProcessoMapper {
    @Mapping(source = "numeroProcesso", target = "numero")
    @Mapping(target = "id", ignore = true)
    Processo toEntity(ProcessoDto dto);

    @InheritInverseConfiguration                  // reaproveita o mapeamento inverso
    ProcessoDto toDto(Processo entity);

    void atualizar(ProcessoDto dto, @MappingTarget Processo entity);   // atualiza objeto existente
}
// Sem Spring: ProcessoMapper m = Mappers.getMapper(ProcessoMapper.class);
```
- Campos com o **mesmo nome** são mapeados automaticamente; nomes diferentes exigem `@Mapping`.

## 5. Swagger / OpenAPI
- **OpenAPI Specification (OAS 3.x)** — padrão para **descrever APIs REST** (antes chamada *Swagger Specification* 2.0), em YAML/JSON.
- **Ferramentas Swagger**: **Swagger UI** (documentação interativa — testar endpoints no navegador), **Swagger Editor**, **Swagger Codegen** (gera clientes/servidores).
- No Spring Boot com **springdoc-openapi**: documento em **`/v3/api-docs`** e interface em **`/swagger-ui.html`** (`/swagger-ui/index.html`). Anotações (`io.swagger.v3.oas.annotations`): `@Operation(summary = "...")`, `@ApiResponse`, `@Tag`, `@Schema`, `@Parameter`.
- Legado **Springfox** (Swagger 2): `@EnableSwagger2`, `@Api`, `@ApiOperation`.

## 6. Persistência: JPA 2.0, Hibernate, Envers, Flyway, H2, PostgreSQL
### JPA (Java Persistence API)
- **Especificação** de ORM (mapeamento objeto-relacional); **JPA 2.0** = JSR 317 (2009, Java EE 6) — trouxe **Criteria API**, `@ElementCollection`, `orphanRemoval`, `@OrderColumn`, bloqueio pessimista e cache de 2º nível padronizado. JPA 3.x usa o pacote **`jakarta.persistence`** (antes `javax.persistence`).
- **Hibernate** é uma **implementação** (provedor) da JPA (outros: EclipseLink, OpenJPA).
```java
@Entity
@Table(name = "processo")
@Audited                                           // Hibernate Envers
public class Processo {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)   // IDENTITY, SEQUENCE, TABLE, AUTO
    private Long id;
    @Column(nullable = false, length = 25, unique = true)
    private String numero;
    @Enumerated(EnumType.STRING) private Situacao situacao;
    @Version private Integer versao;               // bloqueio OTIMISTA
    @ManyToOne(fetch = FetchType.LAZY) @JoinColumn(name = "orgao_id") private Orgao orgao;
    @OneToMany(mappedBy = "processo", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Movimento> movimentos;
    @Transient private String calculado;           // não persiste
}
```
- **Fetch padrão**: `@ManyToOne` e `@OneToOne` → **EAGER**; `@OneToMany` e `@ManyToMany` → **LAZY**.
- **Estados da entidade**: **novo/transiente** → **gerenciado** (*managed*, no contexto de persistência) → **destacado** (*detached*) → **removido**.
- **EntityManager**: `persist()` (novo → gerenciado), `merge()` (destacado → gerenciado; retorna cópia), `remove()`, `find()`, `getReference()` (proxy), `createQuery()` (JPQL), `flush()`, `refresh()`, `detach()`. Configuração em `persistence.xml` (unidade de persistência).
- **JPQL** consulta **entidades e atributos**, não tabelas: `SELECT p FROM Processo p WHERE p.ano = :ano`. **Problema N+1** → `JOIN FETCH` / `@EntityGraph`.
- **Hibernate**: `SessionFactory`/`Session` (API nativa), **HQL**, **cache de 1º nível** (por sessão/contexto — sempre ativo) e **de 2º nível** (por `SessionFactory` — opcional: Ehcache, Infinispan), `hibernate.dialect`, `hibernate.hbm2ddl.auto` (`none`, `validate`, `update`, `create`, `create-drop`), `LazyInitializationException` (acesso a coleção LAZY fora da sessão).

### Hibernate Envers — auditoria e versionamento de entidades
- Anote a entidade com **`@Audited`** (campos excluídos com `@NotAudited`).
- Cria, para cada entidade, a tabela **`<entidade>_AUD`** (sufixo padrão `_AUD`) com as colunas **`REV`** (revisão) e **`REVTYPE`** (**0 = inclusão, 1 = alteração, 2 = exclusão**), e a tabela global **`REVINFO`** (número da revisão e *timestamp*).
- Entidade de revisão personalizada (`@RevisionEntity` + `RevisionListener`) para gravar **quem** alterou. Consulta pelo **`AuditReader`** (`AuditReaderFactory.get(em).find(Processo.class, id, rev)`, `getRevisions(...)`).

### Flyway — versionamento de banco (migrações)
| Tipo | Nome do arquivo | Comportamento |
|---|---|---|
| **Versionada** | **`V1__cria_tabela_processo.sql`** (V + versão + **dois underscores** + descrição) | Executa **uma vez**, em ordem de versão |
| **Repetível** | **`R__atualiza_view.sql`** | Reexecuta quando o **checksum** muda; roda após as versionadas |
| Undo | `U1__...sql` | Desfaz (edição paga) |
- Local padrão: **`classpath:db/migration`** (`src/main/resources/db/migration`). Tabela de controle: **`flyway_schema_history`**.
- Comandos: **`migrate`** (aplica pendentes), **`info`**, **`validate`** (confere checksums), **`baseline`** (adota banco existente), **`repair`** (corrige a tabela de histórico), **`clean`** (⚠️ apaga todos os objetos — desabilitado por padrão nas versões recentes).
- No Spring Boot, com a dependência `flyway-core`, as migrações rodam **automaticamente na inicialização**. Nunca altere uma migração já aplicada (erro de checksum) — crie uma nova versão. Alternativa: Liquibase.

### H2 Database
- Banco relacional **escrito em Java**, **embarcado** ou em modo servidor; **em memória** (`jdbc:h2:mem:testdb` — dados somem ao fechar a última conexão, salvo `DB_CLOSE_DELAY=-1`) ou em arquivo (`jdbc:h2:file:./dados`).
- **Console web** (`spring.h2.console.enabled=true` → `/h2-console`); modos de compatibilidade (`MODE=PostgreSQL`). Usado em **testes automatizados** e desenvolvimento; não em produção. Usuário padrão no Spring Boot: `sa`, senha vazia.

## 7. Autenticação: SSO, Keycloak, OAuth 2.0 (RFC 6749) e RFC 9700
### Keycloak
- Solução **open source de IAM** (Red Hat; projeto CNCF) que provê **SSO** com **OpenID Connect**, **OAuth 2.0** e **SAML 2.0**. Desde a versão 17, roda sobre **Quarkus** (antes, WildFly). Porta padrão **8080** (HTTPS 8443).
| Conceito | Significado |
|---|---|
| **Realm** | Espaço **isolado** de usuários, clientes e configurações (o realm `master` administra os demais) |
| **Client** | Aplicação que usa o Keycloak (confidencial — com segredo — ou pública, como SPA/mobile) |
| **Users / Groups / Roles** | Usuários, grupos e papéis (**realm roles** e **client roles**) |
| **Identity Providers** | *Identity brokering* — login federado (gov.br, Google, outro OIDC/SAML) |
| **User Federation** | Integração com **LDAP/Active Directory** e Kerberos |
| **Authentication flows** | Fluxos configuráveis (MFA com OTP, WebAuthn) |
- Emite **access token** e **ID token** em **JWT**, além do **refresh token**. Endpoints OIDC: `/realms/{realm}/protocol/openid-connect/auth`, `/token`, `/userinfo`, `/certs` (JWKS) e `/.well-known/openid-configuration`.

### OAuth 2.0 — RFC 6749 (*framework* de **autorização delegada**)
- **Papéis**: **resource owner**, **client**, **authorization server**, **resource server**.
- **Grants da RFC 6749**: **authorization code**, **implicit**, **resource owner password credentials**, **client credentials** (+ **refresh token**).
- **Endpoints**: **authorization endpoint** (interação com o usuário), **token endpoint** (troca código/credenciais por token), **redirection endpoint** (no client).
- **Tipos de client**: **confidencial** (guarda segredo — backend) × **público** (não guarda — SPA, mobile).
- Parâmetros: `response_type=code`, `client_id`, `redirect_uri`, **`scope`**, **`state`** (contra CSRF). Uso do token: `Authorization: Bearer <token>` (RFC 6750). **PKCE** (RFC 7636): `code_verifier` / `code_challenge` (método **S256**).
- **OpenID Connect** = camada de **autenticação** sobre o OAuth 2.0 (ID token).

### RFC 9700 (janeiro/2025) — *OAuth 2.0 Security Best Current Practice*
| Recomendação | Detalhe |
|---|---|
| **PKCE** | **Obrigatório para clients públicos** e **recomendado para todos** os que usam authorization code (também protege contra CSRF e injeção de código) |
| **Implicit grant** | **NÃO deve ser usado** (*SHOULD NOT*) — token exposto na URL |
| **Resource Owner Password Credentials** | **NÃO DEVE ser usado** (*MUST NOT*) |
| **Redirect URI** | Comparação **exata** de strings (sem curingas); evitar **open redirectors** |
| **Tokens com restrição de remetente** | *Sender-constrained*: **mTLS** (RFC 8705) ou **DPoP** (RFC 9449) |
| **Refresh tokens** de clients públicos | **Rotação** ou restrição ao remetente |
| Access tokens | **Escopo mínimo** (privilégio mínimo) e **restrição de audiência** |
| Tokens na URL | **Não** enviar tokens em query string |
| *Mix-up attacks* | Usar o parâmetro **`iss`** na resposta de autorização (RFC 9207) |
| Transporte | Sempre **TLS** |

## 8. Mensageria, eventos e webhooks
### RabbitMQ
- **Message broker** que implementa o **AMQP 0-9-1** (também MQTT, STOMP e AMQP 1.0). Fluxo: **producer → exchange → (binding + routing key) → queue → consumer**.
| Exchange | Roteamento |
|---|---|
| **Direct** | **Routing key exata** (a *default exchange* é direct e sem nome) |
| **Fanout** | **Todas** as filas vinculadas (ignora a routing key) — broadcast |
| **Topic** | **Padrões**: `*` = exatamente uma palavra, `#` = zero ou mais (ex.: `processo.*.distribuido`) |
| **Headers** | Pelos cabeçalhos da mensagem |
- Confiabilidade: **acknowledgments** (`ack`/`nack`; *auto-ack* arrisca perda), **filas duráveis + mensagens persistentes**, *prefetch* (QoS), **Dead Letter Exchange (DLX)**, TTL, **quorum queues** (replicadas com Raft), *streams*.
- Portas: **5672** (AMQP), **15672** (painel de gerenciamento), 5671 (AMQP/TLS). No Spring: `RabbitTemplate` (envio) e `@RabbitListener` (consumo).
- **RabbitMQ × Kafka**: RabbitMQ é broker de **filas** (push, mensagem sai após o ack, roteamento rico); Kafka é **log distribuído** (pull, retenção configurável, reprocessamento, *consumer groups*).

### Evento negocial, webhooks e APIs reversas
- **Evento negocial**: fato **relevante para o negócio** (ex.: "processo distribuído", "petição juntada", "audiência designada") **publicado** para que outros serviços reajam de forma **desacoplada e assíncrona** (arquitetura orientada a eventos).
- **Webhook** (**API reversa**): em vez de o cliente consultar periodicamente (*polling*), o **servidor chama** uma URL cadastrada pelo cliente (**HTTP POST** com o evento) quando algo acontece. Boas práticas: **assinatura HMAC** para autenticidade, **HTTPS**, **reentregas** com *backoff*, **idempotência** no receptor, resposta rápida (2xx) e processamento assíncrono.

## 9. Contêineres e orquestração (Docker, Kubernetes, Rancher)
- **Docker**: imagem (camadas, imutável) → contêiner; `Dockerfile` (`FROM`, `RUN`, `COPY`, `WORKDIR`, `ENV`, `EXPOSE`, `CMD`, `ENTRYPOINT`, `USER`); `docker build -t app:1.0 .`, `docker run -d -p 8080:8080 app:1.0`, `docker ps`, `docker logs`, `docker exec -it`; **multi-stage build** (imagem final menor, sem ferramentas de build); **Docker Compose**.
- **Kubernetes**: **Pod** (menor unidade), **Deployment** (réplicas, *rolling update*, rollback), **Service** (ClusterIP, NodePort, LoadBalancer), **Ingress**, **ConfigMap**, **Secret**, **Namespace**, **StatefulSet**, **DaemonSet**, **Job/CronJob**, **HPA**, PV/PVC; *probes* **liveness** (reinicia), **readiness** (tira do balanceamento), **startup**; plano de controle (**kube-apiserver, etcd, kube-scheduler, kube-controller-manager**) e nós (**kubelet, kube-proxy, container runtime**). `kubectl apply -f`, `get pods`, `describe`, `logs`, `rollout undo`.
- **Rancher** (SUSE): plataforma **open source de gerenciamento de múltiplos clusters Kubernetes** — interface web, **autenticação e RBAC centralizados**, provisionamento de clusters (**RKE2** — distribuição *hardened* para governo; **K3s** — leve, para *edge*) e importação de clusters (EKS, AKS, GKE), catálogo de aplicações **Helm**, **Fleet** (GitOps), monitoramento integrado (Prometheus/Grafana).

## 10. DevOps e DevSecOps: Maven, Git, CI/CD, testes automatizados
### Maven
- Ferramenta de **build e gerenciamento de dependências** do Java baseada no **`pom.xml`** (*Project Object Model*).
- **Coordenadas GAV**: **`groupId`**, **`artifactId`**, **`version`** (+ `packaging`: jar, war, pom). Versões **`-SNAPSHOT`** = em desenvolvimento.
- **Escopos de dependência**: **`compile`** (padrão), **`provided`** (fornecida pelo contêiner — ex.: Servlet API), **`runtime`** (ex.: driver JDBC), **`test`**, `system`, `import`.
- **Ciclo de vida *default*** (fases em ordem): **validate → compile → test → package → verify → install → deploy**. Executar uma fase executa **todas as anteriores**. Outros ciclos: **clean** e **site**.
  - `install` copia o artefato para o **repositório local** (`~/.m2/repository`); `deploy` publica no **repositório remoto** (Nexus/Artifactory).
- Comandos: `mvn clean install`, `mvn test`, `mvn package -DskipTests`, `mvn dependency:tree`, `./mvnw` (wrapper). Estrutura padrão: `src/main/java`, `src/main/resources`, `src/test/java`, `target/`.
- **Projetos multimódulo** (POM pai com `<modules>`), `<dependencyManagement>`, `<properties>`, plugins e *goals*.

### CI/CD e testes
- **CI**: a cada push, *build* + testes automatizados + análise estática (SonarQube) + varredura de segurança. **Continuous Delivery** (pronto para produção, deploy com aprovação) × **Continuous Deployment** (deploy automático).
- **Pipeline típico**: checkout → `mvn verify` (testes unitários/integração) → **SAST/SCA** → build da imagem Docker → varredura da imagem → push no registry → deploy no Kubernetes (homologação → produção) → testes de fumaça.
- Ferramentas: **GitLab CI** (`.gitlab-ci.yml`), Jenkins (`Jenkinsfile`), GitHub Actions; **Argo CD** (GitOps).
- **DevSecOps**: segurança desde o início (*shift-left*): SAST, DAST, **SCA** (dependências vulneráveis — OWASP Dependency-Check), varredura de contêineres (Trivy), gestão de segredos (Vault), *policy as code*.
- **Testes automatizados**: unitários (**JUnit 5** + **Mockito**), integração (`@SpringBootTest`, H2 ou **Testcontainers**), contrato, **E2E** (Selenium/Cypress), carga (JMeter). Pirâmide: muitos unitários, poucos E2E.

## 11. Normativos da PDPJ-Br e de segurança cibernética do CNJ
| Norma | Conteúdo |
|---|---|
| **Resolução CNJ 335/2020** | Institui a **política pública para governança e gestão do processo judicial eletrônico**; **cria a PDPJ-Br**, integrando todos os tribunais; mantém o **PJe** como sistema prioritário; diretrizes: plataforma **colaborativa**, **modular (microsserviços)**, **nuvem**, **código aberto**, compartilhamento de soluções entre tribunais e **vedação a novas contratações de sistemas privados que gerem dependência tecnológica** e não permitam o compartilhamento não oneroso na plataforma (confirmar redação) |
| **Portaria CNJ 252/2020** | Dispõe sobre o **modelo de governança e gestão da PDPJ-Br** (instâncias, papéis do CNJ e dos tribunais) — alterada pela Portaria 284/2021 |
| **Portaria CNJ 253/2020** | Estabelece **critérios e diretrizes técnicas** para o **processo de desenvolvimento de módulos e serviços** na PDPJ-Br (arquitetura em microsserviços, APIs REST documentadas, contêineres, autenticação centralizada, versionamento de código no repositório do CNJ etc.) |
| **Portaria CNJ 131/2021** | Institui o **Grupo Revisor de Código-Fonte** das soluções da PDPJ-Br e do PJe (revisão de qualidade e segurança antes da integração) |
| **Resolução CNJ 396/2021** | Institui a **Estratégia Nacional de Segurança Cibernética do Poder Judiciário (ENSEC-PJ)** — objetivos de tornar o Judiciário mais **seguro e resiliente** no ambiente digital, governança de segurança cibernética, continuidade dos serviços, cooperação; cria o **Comitê Gestor de Segurança Cibernética do Poder Judiciário (CGSC-PJ)** e prevê a rede de cooperação, ETIRs nos tribunais e capacitação |
| **Portaria CNJ 162/2021** | **Aprova os protocolos e manuais** previstos na Res. 396/2021 — entre eles o **Protocolo de Prevenção de Incidentes Cibernéticos (PPINC-PJ)**, o **Protocolo de Gerenciamento de Crises Cibernéticas (PGCC-PJ)**, o **Protocolo de Investigação para Ilícitos Cibernéticos (PIILC-PJ)** e manuais de referência (proteção de infraestruturas críticas de TIC, prevenção e mitigação de ameaças, gestão de identidades e controle de acesso) (confirmar lista) |
| **Resolução CNJ 522/2023** | Institui o **Modelo de Requisitos para Sistemas Informatizados de Gestão de Processos e Documentos do Poder Judiciário (MoReq-Jus)**, de observância **obrigatória** no desenvolvimento e na manutenção desses sistemas (gestão documental, segurança, preservação, metadados) (confirmar) |
> Leia os textos no portal de **atos normativos do CNJ** — a FCC costuma cobrar **qual norma trata de quê** e termos literais.

## ⚠️ Pegadinhas
1. Porta padrão do **Eureka = 8761**; do Spring Boot = 8080; do RabbitMQ = 5672 (painel 15672); PostgreSQL 5432.
2. `@EnableEurekaServer` (servidor) × cliente registra via `defaultZone`; Zuul = `@EnableZuulProxy`.
3. MapStruct = **`@Mapper`** (+ `componentModel = "spring"`), gera código **em compilação**.
4. Flyway: **`V1__desc.sql`** (dois underscores); tabela **`flyway_schema_history`**.
5. Envers: **`@Audited`**, tabela **`_AUD`**, **REVINFO**, REVTYPE 0/1/2.
6. JPA: `@ManyToOne` **EAGER** por padrão; `@OneToMany` **LAZY**.
7. RFC 9700: **implicit (não usar)** e **password grant (MUST NOT)**; **PKCE para todos**.
8. Fanout ignora routing key; topic usa `*` e `#`.
9. Maven: `install` = repositório **local**; `deploy` = **remoto**; `provided` = o contêiner fornece.

## Questões comentadas (inéditas, estilo FCC)

**Q1.** Em uma aplicação Spring Boot que atuará como servidor de registro de serviços, a anotação a ser incluída na classe principal e a porta convencionalmente utilizada são, respectivamente:
(A) `@EnableDiscoveryClient` e 8080. (B) `@EnableZuulProxy` e 8761. (C) **`@EnableEurekaServer` e 8761.** (D) `@EnableEurekaClient` e 9090. (E) `@EnableConfigServer` e 8888.
✅ **C.**

**Q2.** Um desenvolvedor criou o script de migração Flyway que deve ser executado uma única vez, como a terceira versão do banco. O nome de arquivo correto é:
(A) `R3_cria_indice.sql`. (B) `V3-cria_indice.sql`. (C) **`V3__cria_indice.sql`.** (D) `3__V_cria_indice.sql`. (E) `U3__cria_indice.sql`.
✅ **C.**

**Q3.** No Hibernate Envers, ao anotar a entidade `Processo` com `@Audited`, as alterações passam a ser registradas, por padrão, na tabela:
(A) `PROCESSO_HIST`. (B) `AUDIT_PROCESSO`. (C) **`PROCESSO_AUD`**, com referência à tabela `REVINFO`. (D) `flyway_schema_history`. (E) `PROCESSO_LOG`.
✅ **C.**

**Q4.** Segundo a RFC 9700 (boas práticas de segurança do OAuth 2.0):
(A) o fluxo implícito é o recomendado para aplicações SPA. (B) o *resource owner password credentials grant* deve ser preferido em aplicações móveis. (C) **o PKCE deve ser usado por clients públicos e é recomendado para todos os clients que usam o authorization code.** (D) as URIs de redirecionamento podem usar curingas. (E) os tokens devem trafegar na query string para facilitar o cache.
✅ **C.**

**Q5.** No RabbitMQ, o tipo de exchange que entrega uma cópia da mensagem a todas as filas a ela vinculadas, ignorando a routing key, é:
(A) direct. (B) topic. (C) headers. (D) **fanout.** (E) default.
✅ **D.**

**Q6.** No ciclo de vida *default* do Maven, ao executar `mvn install`, são executadas, entre outras, as fases:
(A) apenas install. (B) clean e install. (C) **validate, compile, test, package, verify e install.** (D) compile, deploy e install. (E) site e install.
✅ **C.**
