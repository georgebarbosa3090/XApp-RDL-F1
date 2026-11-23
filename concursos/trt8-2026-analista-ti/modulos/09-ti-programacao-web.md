# Módulo 9 — TI: Programação (Python, Java, JavaScript, TypeScript), Web, Arquiteturas e Git

> Edital: *conhecimento profundo das linguagens Python, Java, JavaScript, TypeScript*; fundamentos (sintaxe, tipos, variáveis, literais, operadores e precedência, controle de fluxo, classes, interfaces, encapsulamento, packages, sobrecarga e sobrescrita, bibliotecas, exceções, acesso a banco, Git); web e mobile (HTML, CSS, Web Services); arquiteturas multicamadas, cliente-servidor, objetos distribuídos. Estimativa: 4–6 questões, **com código**.

## 1. Java
### Compilação e execução
- `javac Processo.java` → **bytecode** `Processo.class` → `java Processo` (executado pela **JVM**). Uma classe `public` deve estar em arquivo **com o mesmo nome**. Ponto de entrada: `public static void main(String[] args)`.
- **JDK** (ferramentas + JRE) ⊃ **JRE** (JVM + bibliotecas). Pacotes distribuídos em **.jar**. LTS: 8, 11, 17, 21, **25** (set/2025).

### Tipos primitivos (8)
| Tipo | Bits | Padrão (campo) | Literal |
|---|---:|---|---|
| `byte` | 8 | 0 | — |
| `short` | 16 | 0 | — |
| `int` | 32 | 0 | `42`, `0x2A`, `0b101010`, `1_000_000` |
| `long` | 64 | 0L | `42L` |
| `float` | 32 | 0.0f | `3.14f` |
| `double` | 64 | 0.0 | `3.14`, `1e3` |
| `char` | 16 (Unicode) | `'\u0000'` | `'a'` |
| `boolean` | — | `false` | `true` |
- **Variáveis locais não têm valor padrão** (devem ser inicializadas antes do uso — erro de compilação). Campos de objeto recebem padrão; referências → `null`.
- `String` é **imutável**; compare conteúdo com **`equals()`** (`==` compara **referência**). `StringBuilder` é mutável.
- Conversões: *widening* automático (int → long → double); *narrowing* exige cast `(int) 3.9` = **3** (trunca).
- `7 / 2` = **3** (divisão inteira); `7 / 2.0` = 3.5; `7 % 2` = 1.

### Precedência de operadores (da maior para a menor)
pós-fixos `x++ x--` → unários `++x --x + - ! ~ (cast)` → `* / %` → `+ -` → deslocamento `<< >> >>>` → relacionais `< > <= >= instanceof` → igualdade `== !=` → `&` → `^` → `|` → **`&&`** → **`||`** → ternário `?:` → atribuição `= += -=`…
- `&&` e `||` são **curto-circuito**; `&` e `|` avaliam os dois lados.
- `int x = 5; int y = x++ + ++x;` → 5 + 7 = **12** (x termina 7).

### Controle de fluxo
- `if/else`, `switch` (aceita `String` desde o Java 7; *switch expressions* com `->` e `yield` no Java 14+), `for`, *for-each* (`for (String s : lista)`), `while`, `do-while` (executa ao menos 1 vez), `break`, `continue`, rótulos.

### Classes, interfaces e modificadores
| Modificador | Classe | Pacote | Subclasse | Todos |
|---|:-:|:-:|:-:|:-:|
| `private` | ✔ | | | |
| *(default/package)* | ✔ | ✔ | | |
| `protected` | ✔ | ✔ | ✔ | |
| `public` | ✔ | ✔ | ✔ | ✔ |
- `static` (pertence à classe), `final` (classe não estendida; método não sobrescrito; variável constante), `abstract` (classe não instanciável; método sem corpo).
- **Herança simples** de classes (`extends`), **múltipla de interfaces** (`implements A, B`). Interfaces: métodos abstratos, **`default`** e `static` (Java 8), `private` (Java 9); atributos são `public static final`.
- Construtores: `this(...)` e `super(...)` devem ser a **primeira instrução**.
- **Sobrecarga** (*overload*): mesmo nome, **lista de parâmetros diferente** (tipo/quantidade/ordem) — resolvida em **compilação**; o tipo de retorno sozinho **não** diferencia.
- **Sobrescrita** (*override*): subclasse redefine método com **mesma assinatura**; `@Override`; **não pode reduzir a visibilidade**; retorno covariante permitido; não pode lançar exceções checadas mais amplas — resolvida em **execução** (polimorfismo dinâmico).
- **Encapsulamento**: atributos `private` + getters/setters. **Packages**: `package br.jus.trt8.sistema;` (primeira instrução) e `import`.
- Recursos modernos: `var` (10), `record` (16 — classe de dados imutável), `sealed` (17), *pattern matching* no `switch` (21), **virtual threads** (21).

### Exceções
```
Throwable
├── Error                (falhas graves da JVM: OutOfMemoryError, StackOverflowError — não tratar)
└── Exception            (CHECKED: IOException, SQLException — tratar ou declarar com throws)
    └── RuntimeException (UNCHECKED: NullPointerException, ArithmeticException,
                          ArrayIndexOutOfBoundsException, IllegalArgumentException, NumberFormatException)
```
```java
try (Connection c = ds.getConnection()) {        // try-with-resources: fecha AutoCloseable
    ...
} catch (SQLException | IOException e) {         // multi-catch
    throw new NegocioException("Falha", e);      // throw lança; throws declara
} finally {
    log.info("sempre executa");
}
```

### Acesso a banco (JDBC)
```java
String sql = "SELECT numero FROM processo WHERE ano = ?";
try (Connection conn = DriverManager.getConnection(url, usuario, senha);
     PreparedStatement ps = conn.prepareStatement(sql)) {
    ps.setInt(1, 2026);                          // índices começam em 1
    try (ResultSet rs = ps.executeQuery()) {     // executeQuery → SELECT
        while (rs.next()) System.out.println(rs.getString("numero"));
    }
}
// executeUpdate() → INSERT/UPDATE/DELETE (retorna nº de linhas); conn.setAutoCommit(false); conn.commit(); conn.rollback();
```
- **PreparedStatement** previne **SQL injection** e é pré-compilado. `Statement` concatena strings (vulnerável).

### Coleções e streams
- `List` (ArrayList, LinkedList — ordem, duplicatas), `Set` (HashSet, **TreeSet** ordenado — sem duplicatas), `Map` (HashMap, TreeMap — chave/valor), `Queue/Deque`. Generics: `List<String>`.
- `lista.stream().filter(p -> p.getAno() == 2026).map(Processo::getNumero).collect(Collectors.toList());`
- Recursão (cobrada pela FCC): férias = 15 dias até 5 anos + 15 a cada novo período de 5 → `return 15 + calcular(anosServico - 5);`

## 2. Python
- Tipagem **dinâmica e forte**; indentação define blocos; CPython compila para **bytecode** (`.pyc`) interpretado pela PVM.
- **Tipos**: `int` (precisão arbitrária), `float`, `complex`, `bool`, `str` (**imutável**), `bytes`, `list` (**mutável**), `tuple` (**imutável**), `dict`, `set`, `frozenset`, `None`.
- **Literais**: `0b101`, `0o17`, `0xFF`, `1_000`, `f"Processo {n}"`, `r"C:\dir"`, `"""texto multilinha"""`.
- **Operadores**: `/` (divisão real: `7/2 = 3.5`), **`//`** (divisão inteira: `7//2 = 3`; `-7//2 = -4`), `%`, **`**`** (potência, associativa à direita; `-2**2 = -4`), `is` (identidade) × `==` (igualdade), `in`, `and/or/not` (curto-circuito), comparações encadeadas (`1 < x < 10`).
- **Precedência**: `**` → unários `+x -x ~x` → `* / // %` → `+ -` → deslocamentos → `&` → `^` → `|` → comparações (`in`, `is`, `<`…) → `not` → `and` → `or` → expressão condicional → `lambda`.
- **Controle**: `if/elif/else`; `for x in iteravel`; `while`; **`else` em laços** (executa se o laço terminar **sem `break`**); `match/case` (3.10).
- **Fatiamento**: `s[1:4]`, `s[-1]` (último), `s[::-1]` (inverte). **Compreensão**: `[x*2 for x in nums if x > 0]`, `{k: v for k, v in pares}`.
- **Funções**: `def f(a, b=2, *args, **kwargs)`; `lambda x: x+1`; retorno padrão `None`. ⚠️ **Default mutável** (`def f(l=[])`) é compartilhado entre chamadas.
- **Classes**: `class Processo(Base):`, `def __init__(self, numero):`, `super().__init__()`, herança **múltipla** (MRO). Encapsulamento por **convenção** (`_protegido`; `__privado` sofre *name mangling*); `@property`, `@staticmethod`, `@classmethod`; métodos especiais `__str__`, `__repr__`, `__eq__`, `__len__`.
- ⚠️ Python **não tem sobrecarga** de métodos (a última definição prevalece) — usa-se parâmetros padrão; **sobrescrita** sim.
- **Módulos e pacotes**: `import os`, `from math import sqrt`, pacote = diretório (com `__init__.py`); `if __name__ == "__main__":`.
- **Exceções**: `try / except ValueError as e / else (sem exceção) / finally`, `raise`, exceções próprias (`class NegocioError(Exception)`), `with open(...) as f:` (gerenciador de contexto). Comuns: `ValueError`, `TypeError`, `KeyError`, `IndexError`, `ZeroDivisionError`, `AttributeError`, `FileNotFoundError`.
- **Banco** (DB-API 2.0 — PEP 249):
```python
import psycopg2
conn = psycopg2.connect(host="db", dbname="pje", user="app", password="***")
with conn, conn.cursor() as cur:                     # commit automático ao sair do with
    cur.execute("SELECT numero FROM processo WHERE ano = %s", (2026,))  # parâmetro, não f-string!
    for (numero,) in cur.fetchall():
        print(numero)
# sqlite3 usa "?" como marcador; executemany() para lotes; conn.rollback() em caso de erro
```
- Ecossistema: `pip`, `venv`; Django/Flask/FastAPI (web); pandas, NumPy, scikit-learn (dados).

## 3. JavaScript
- **Tipos primitivos**: `string`, `number` (IEEE 754 de 64 bits), `bigint`, `boolean`, `undefined`, `null`, `symbol`; o resto é `object`. ⚠️ `typeof null === "object"`; `typeof [] === "object"` (use `Array.isArray`); `typeof function(){} === "function"`.
- **Declarações**: `var` (escopo de **função**, *hoisting* com `undefined`) × `let`/`const` (escopo de **bloco**, *temporal dead zone*). `const` impede **reatribuição**, não mutação do objeto.
- **Igualdade**: `==` faz **coerção** (`"5" == 5` → true; `null == undefined` → true; `0 == ""` → true) × `===` **estrita**. `NaN !== NaN` (use `Number.isNaN`).
- **Falsy**: `false`, `0`, `-0`, `0n`, `""`, `null`, `undefined`, `NaN`. Todo o resto é truthy (inclusive `"0"`, `[]`, `{}`).
- Coerção: `"3" + 4 = "34"`; `"3" * 4 = 12`; `[] + {} = "[object Object]"`.
- **Funções**: declaração (içada), expressão, **arrow** (`=>` — `this` **léxico**, sem `arguments`, não é construtor); **closures**; parâmetros padrão; *rest* `(...args)`; *spread* `[...a, ...b]`; desestruturação `const {numero, ano} = processo`.
- **Classes** (ES6): `class Processo extends Base { #segredo; static total = 0; constructor(n) { super(); this.n = n; } get numero() {...} }` (campos `#privados`). Herança baseada em **protótipos**.
- **Arrays**: `map`, `filter`, `reduce`, `forEach`, `find`, `some`, `every`, `includes`, `sort` (ordena como string por padrão!).
- **Assíncrono**: *event loop* — pilha de chamadas; **microtarefas** (Promises) executam **antes** das **macrotarefas** (`setTimeout`). `Promise` (pending → fulfilled/rejected), `.then/.catch/.finally`, `async/await`, `Promise.all` (falha se uma falhar), `Promise.allSettled`.
```js
console.log(1); setTimeout(() => console.log(2), 0);
Promise.resolve().then(() => console.log(3)); console.log(4);   // saída: 1 4 3 2
```
- **Módulos**: ES (`import/export`) × CommonJS do Node (`require/module.exports`). `JSON.parse` / `JSON.stringify`. `fetch(url).then(r => r.json())`.
- **Exceções**: `try/catch/finally`, `throw new Error("msg")`.
- **DOM**: `document.querySelector("#id")`, `addEventListener("click", fn)`, `textContent`, `innerHTML` (⚠️ XSS).
- **PWA / Service Worker**: script que roda **em segundo plano**, separado da página, intercepta requisições (`fetch`) e usa a **Cache API** para funcionar **offline**; eventos `install`, `activate`, `fetch`; exige **HTTPS**; o PWA tem também o **Web App Manifest** (`manifest.json`). (FCC/2023 mostrou `self.addEventListener('install', ... caches.open(...))` → **Service Worker de um PWA**.)

## 4. TypeScript
- **Superconjunto tipado** do JavaScript; o compilador **`tsc`** verifica tipos e **transpila** para JS (os tipos **somem** em tempo de execução); configuração em **`tsconfig.json`** (`"strict": true`).
- **Tipagem estrutural** (*duck typing*): compatibilidade pela forma, não pelo nome.
- **Tipos**: `string`, `number`, `boolean`, `bigint`, `symbol`, `null`, `undefined`, **`any`** (desliga a checagem), **`unknown`** (seguro: exige *narrowing* antes de usar), **`never`** (nunca ocorre), `void`, arrays `number[]`/`Array<number>`, **tuplas** `[string, number]`, **literais** `'A' | 'B'`, **união** `|`, **interseção** `&`, opcional `?`, `readonly`.
- **Enum**:
```ts
enum TipoProcesso { Criminal = "Criminal", Civel = "Civel", Trabalhista = "Trabalhista" }
const tipo: TipoProcesso = TipoProcesso.Trabalhista;   // forma correta (FCC/2023)
enum Prioridade { Baixa, Media, Alta }                  // numérico: 0, 1, 2 (auto-incremento)
```
- **`interface` × `type`**: interface pode ser **estendida** (`extends`) e sofre **declaration merging**; `type` aceita uniões, interseções, tuplas e tipos mapeados.
- **Generics**: `function primeiro<T>(itens: T[]): T { return itens[0]; }`.
- **Classes**: modificadores `public`, `private`, `protected`, `readonly`; **parâmetros de propriedade** `constructor(private id: number) {}`; `abstract`; `implements`; `#privado` (JS) × `private` (só em compilação).
- **Narrowing**: `typeof x === "string"`, `instanceof`, `in`, *type guards* (`x is Tipo`), *discriminated unions*.
- **Utilitários**: `Partial<T>`, `Required<T>`, `Readonly<T>`, `Pick<T, K>`, `Omit<T, K>`, `Record<K, V>`, `ReturnType<F>`. Asserção: `valor as string`; *non-null* `x!`.

## 5. Desenvolvimento web
### HTML5
- `<!DOCTYPE html>`; elementos **semânticos**: `header`, `nav`, `main`, `article`, `section`, `aside`, `footer`, `figure`; formulários com tipos (`email`, `number`, `date`, `tel`, `url`), atributos `required`, `pattern`, `placeholder`; `audio`, `video`, `canvas`; Web Storage (`localStorage` persiste; `sessionStorage` até fechar a aba).
- Acessibilidade: `alt` em imagens, `label for`, ARIA, eMAG/WCAG.

### CSS3
- **Especificidade**: inline (1000) > **#id** (100) > **.classe / [atributo] / :pseudo-classe** (10) > **elemento / ::pseudo-elemento** (1); `!important` sobrepõe; empate → **última regra declarada** vence.
- **Seletores**: descendente `div p`, filho `div > p`, irmão adjacente `h1 + p`, irmãos `h1 ~ p`, `:hover`, `:nth-child(2n)`, `::before`.
- **Box model**: content → padding → border → margin; `box-sizing: border-box` inclui padding e border na largura.
- `display` (block, inline, inline-block, **flex**, **grid**, none), `position` (static, relative, absolute — relativo ao ancestral posicionado, fixed, sticky).
- **Flexbox**: `justify-content` (eixo principal), `align-items` (eixo cruzado), `flex-direction`, `flex-wrap`. **Grid**: `grid-template-columns: repeat(3, 1fr)`.
- **Cores**: `#RRGGBB`, `rgb()`, `rgba()`, **`hsl(matiz, saturação, luminosidade)`** — matiz em graus: **0 = vermelho, 120 = verde, 240 = azul**. Unidades: `px`, `em` (relativo ao pai), `rem` (relativo à raiz), `%`, `vw/vh`. Responsividade: `@media (max-width: 768px) {...}`.

### Web Services
| | **SOAP** | **REST** |
|---|---|---|
| Natureza | **Protocolo** (W3C) | **Estilo arquitetural** |
| Formato | **XML** (Envelope → Header + Body; Fault) | JSON, XML, outros |
| Contrato | **WSDL** (descrição) · UDDI (registro) | OpenAPI/Swagger (opcional) |
| Transporte | HTTP, SMTP, JMS… | HTTP |
| Segurança | **WS-Security** | HTTPS + OAuth2/JWT |
| Estado | Pode ser *stateful* | **Stateless** |
- REST: recursos identificados por URI, verbos HTTP (GET, POST, PUT, PATCH, DELETE), códigos de status (200, 201, 204, 400, 401, 403, 404, 409, 500), HATEOAS (nível 3 do modelo de Richardson).
- **Mobile**: nativo (Kotlin/Swift), híbrido/multiplataforma (React Native, Flutter, Ionic), **PWA**.

## 6. Arquiteturas de sistemas
| Arquitetura | Características |
|---|---|
| **Cliente-servidor** (2 camadas) | Cliente (interface + parte da lógica — "cliente gordo") acessa servidor (dados) diretamente |
| **Multicamadas** (3/N camadas) | **Apresentação** → **aplicação/negócio** → **dados**; cada camada pode escalar e ser trocada independentemente; cliente fino (navegador) |
| **Objetos distribuídos** | Objetos em máquinas diferentes invocam métodos remotos como se fossem locais (**transparência de localização**): **CORBA** (ORB, **IDL**, IIOP — independente de linguagem), **Java RMI** (stub no cliente, skeleton no servidor, `rmiregistry`), DCOM; envolve *marshalling/unmarshalling* |
| Microsserviços / SOA / eventos | Ver Módulo 10 (PDPJ-Br) |

## 7. Git
| Comando | Efeito |
|---|---|
| `git clone https://<TOKEN>@github.com/<usuario>/<repo>.git` | Clona usando **Personal Access Token** no lugar da senha (ou `https://<usuario>:<TOKEN>@github.com/...`) |
| `git config --global user.name "..."` | Identidade |
| `git status` / `git log --oneline --graph` / `git diff` (`--staged`) | Inspeção |
| `git add .` → `git commit -m "msg"` | Staging → commit; `--amend` corrige o último commit |
| `git branch nome` / `git switch -c nome` / `git checkout nome` | Ramos |
| `git merge ramo` | Fast-forward (linear) ou merge de 3 vias (commit de merge) |
| `git rebase main` | Reaplica commits sobre outra base (histórico linear) — não use em ramo público |
| `git fetch` / `git pull` (= fetch + merge; `--rebase`) / `git push -u origin main` | Remoto |
| `git stash` / `git stash pop` | Guardar alterações temporariamente |
| `git reset --soft/--mixed/--hard HEAD~1` | Move o ponteiro: soft mantém staging; **mixed** (padrão) mantém arquivos, tira do staging; **hard descarta tudo** |
| `git revert <hash>` | **Novo commit** que desfaz outro (seguro em ramos compartilhados) |
| `git cherry-pick <hash>` | Aplica um commit específico |
| `git tag -a v1.0 -m "..."` | Tag anotada (leve: sem `-a`) |
| `git bisect`, `git blame`, `git reflog` | Busca binária do bug, autoria por linha, histórico de referências |
- Áreas: **working directory → staging (index) → repositório local → remoto**. `.gitignore`. `HEAD` aponta para o commit atual (*detached HEAD* quando aponta direto para um commit).

## ⚠️ Pegadinhas
1. Java: `==` em `String` compara referência; variável local sem valor = erro de compilação; `7/2 = 3`.
2. Sobrecarga = compilação (parâmetros); sobrescrita = execução (mesma assinatura); retorno sozinho não sobrecarrega.
3. Checked (`IOException`, `SQLException`) × unchecked (`RuntimeException` e filhas).
4. Python: `//` arredonda **para baixo** (`-7//2 = -4`); `-2**2 = -4`; não há sobrecarga.
5. JS: `typeof null === "object"`; Promises antes de `setTimeout`; `==` faz coerção.
6. TS: tipos desaparecem no JS gerado; `unknown` é o "any seguro".
7. CSS: `#id` vence `.classe`; HSL 0° vermelho, 120° verde, 240° azul.

## Questões comentadas (inéditas, estilo FCC)

**Q1.** Considere o código Java:
```java
int a = 10, b = 4;
double r = a / b;
System.out.println(r + " " + (a % b) + " " + (a > b && b++ > 4) + " " + b);
```
A saída é:
(A) 2.5 2 false 5 (B) **2.0 2 false 5** (C) 2.0 2 true 5 (D) 2.5 2 false 4 (E) 2.0 2 false 4
✅ **B.** `a / b` é divisão inteira (2) convertida para 2.0; `b++ > 4` compara 4 > 4 (false) e depois incrementa b para 5 (o `&&` avaliou o lado direito porque o esquerdo era true).

**Q2.** Em Python, o resultado de `print(-7 // 2, 2 ** 3 ** 2, [1, 2, 3][::-1])` é:
(A) -3 64 [3, 2, 1] (B) **-4 512 [3, 2, 1]** (C) -4 64 [1, 2, 3] (D) -3 512 [3, 2, 1] (E) -4 512 [1, 2, 3]
✅ **B.** `//` arredonda para baixo; `**` é associativo à direita (3² = 9; 2⁹ = 512).

**Q3.** Em JavaScript, o trecho `console.log(typeof null, "5" == 5, "5" === 5, [] ? "sim" : "não")` exibe:
(A) null true false não (B) object false false sim (C) **object true false sim** (D) undefined true true sim (E) object true false não
✅ **C.**

**Q4.** Em TypeScript, o tipo que aceita qualquer valor, mas obriga a verificação do tipo antes de seu uso, é:
(A) any. (B) never. (C) void. (D) **unknown.** (E) object.
✅ **D.**

**Q5.** Em CSS, considerando `p { color: black }`, `.destaque { color: blue }`, `#aviso { color: red }` e `<p id="aviso" class="destaque">`, o texto será exibido na cor:
(A) black. (B) blue. (C) **red.** (D) a cor definida por último no arquivo. (E) a cor padrão do navegador.
✅ **C.** ID (100) > classe (10) > elemento (1).

**Q6.** Para desfazer, em um ramo compartilhado, as alterações de um commit já enviado ao repositório remoto, sem reescrever o histórico, deve-se usar:
(A) `git reset --hard`. (B) **`git revert`.** (C) `git rebase -i`. (D) `git commit --amend`. (E) `git stash drop`.
✅ **B.**
