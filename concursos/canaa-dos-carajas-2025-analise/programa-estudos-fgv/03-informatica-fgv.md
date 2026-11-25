# Módulo 3 — Noções de Informática (estilo FGV)

> **Peso**: 10 questões. **A pior matéria de Canaã: 49,5% de acerto entre os aprovados** e 34,9% dos aprovados com menos da metade.
> A FGV cobra **o nome exato** de recursos, guias, atalhos e componentes, às vezes além do texto literal do edital (DISM, SRAM, barramentos, Google Workspace, nuvem). Estude com o programa **aberto na frente** e treine atalhos na prática.

## 1. Hardware

| Componente | O que saber | Pegadinha |
|---|---|---|
| **RAM** | Volátil, memória de trabalho | **DRAM** precisa de *refresh* (é a memória principal); **SRAM** é rápida, cara, sem *refresh* → **cache** (Canaã Q23) |
| **ROM / firmware** | Não volátil, BIOS/UEFI | Vírus não "atacam a ROM" como regra (Canaã Q22) |
| **Cache** | Entre a CPU e a RAM (L1, L2, L3) | É SRAM |
| **Armazenamento** | HD (magnético), **SSD** (flash, sem partes móveis), pendrive, nuvem | **SSD não é protocolo** (Carag. Q24) |
| **Barramento** | **Dados, endereços e controle** (Canaã Q24) | — |
| **Conexões** | **USB** (*hot-plug*, ligar sem desligar o PC), **NFC** (aproximação), **Wi-Fi Direct** (sem roteador), Bluetooth | Carag. Q26: as três estavam corretas |

## 2. Windows (10/11)

| Ação | Atalho |
|---|---|
| Selecionar arquivos **não consecutivos** | **Ctrl + clique** (SJC Q49) |
| Selecionar um **intervalo** | Shift + clique |
| Explorador de Arquivos | **Win + E** |
| Bloquear a tela | Win + L |
| Área de trabalho | Win + D |
| Alternar janelas | Alt + Tab |
| Renomear | F2 |
| Excluir sem a Lixeira | Shift + Delete |
| Área de transferência (histórico) | Win + V |
| Captura de tela (recorte) | Win + Shift + S |

- **DISM**: ferramenta de linha de comando que faz a manutenção de imagens **.wim/.vhd** do Windows (Canaã Q21). Outras: `sfc /scannow` (verifica arquivos do sistema), `chkdsk` (disco), `ipconfig` (rede).
- **Extensões**: imagem (.jpg/.jpeg, .png, .gif, .tiff, .bmp, .eps, .svg); executável (.exe); **biblioteca (.dll)**; compactado (.zip, .rar, .7z); texto (.txt, .docx, .odt, .pdf).

## 3. Word (Microsoft 365)

| Recurso | Onde fica / atalho |
|---|---|
| **Estilos** (Título 1, Normal) | Página Inicial → Estilos — a forma **mais eficiente** de padronizar e gerar sumário (SJC Q48) |
| **Quebras** | **Layout → Quebras**: de página (**Página, Coluna, Disposição do Texto**) e de seção (Próxima página, Contínuo, Página par/ímpar) (Canaã Q27) |
| **Compartilhar** | Arquivo → Compartilhar: pessoas, e-mail (anexo/PDF/**fax da Internet**), apresentar online (Canaã Q25) |
| Pincel de formatação | Ctrl + Shift + C (copia) / Ctrl + Shift + V (cola formatação) |
| Imprimir | **Ctrl + P** |
| Ortografia | **F7** |
| Maiúsculas/minúsculas | **Shift + F3** |
| Negrito / itálico / sublinhado | Ctrl + N / Ctrl + I / Ctrl + S (em português) |
| Salvar como | F12 |
| Localizar / substituir | Ctrl + L / Ctrl + U |
| Centralizar / justificar | Ctrl + E / Ctrl + J |

## 4. Excel (Microsoft 365)

| Função | Uso | Exemplo |
|---|---|---|
| **SOMA, MÉDIA, MÁXIMO, MÍNIMO** | Básicas | =MÉDIA(B2:B10) |
| **SE** | Teste lógico | =SE(B2>=7;"Aprovado";"Reprovado") |
| **SOMASE** | Soma com 1 critério | =SOMASE(A2:A7;C9;C2:C7) → *intervalo do critério; critério; intervalo da soma* |
| **CONT.SE / CONT.SES** | Conta com 1 / vários critérios | =CONT.SES(C2:C100;"Concluída";D2:D100;"<01/01/2025") (SJC Q46) |
| **CONT.VALORES / CONTAR.VAZIO** | Células não vazias / vazias | — |
| **PROCV / PROCX** | Busca em tabela | =PROCV(valor;tabela;coluna;FALSO) |
| **Horas** | Hora é fração do dia: 1 h = 1/24 | 17:45 − 07:30 − 1:00 = 9:15 |

- **Referências**: relativa (A1), **absoluta** ($A$1), mista ($A1 / A$1). **F4** alterna entre elas.
- **Rastrear precedentes/dependentes** (guia Fórmulas): setas que mostram de quais células a fórmula depende (Canaã Q26).
- **Erros**: #DIV/0!, #N/D (PROCV não achou), #REF! (referência apagada), #NOME? (função escrita errada), #VALOR! (tipo de dado errado).

## 5. LibreOffice

| Programa | Equivalente | Destaques FGV |
|---|---|---|
| **Writer** | Word | Formato nativo **.odt**; salva em .doc/.docx; **exporta PDF**; tem ferramentas de desenho e **tabelas com cálculo** (Carag. Q22) |
| **Calc** | Excel | .ods; funções em português (SOMA, SE); o separador de argumentos é **;** |
| **Impress** | PowerPoint | .odp; **Slide Mestre** = design padrão de todos os slides (Carag. Q23) |

## 6. Internet, redes e e-mail

| Protocolo / termo | Função |
|---|---|
| **DNS** | Traduz **nome de domínio → IP** (Carag. Q20) |
| **DHCP** | Atribui IP automaticamente |
| **HTTP / HTTPS** | Páginas web (HTTPS com TLS, cadeado) |
| **SMTP** | **Envio** de e-mail |
| **POP3 / IMAP** | **Recebimento** (POP baixa as mensagens; IMAP sincroniza com o servidor) |
| **FTP / SFTP** | Transferência de arquivos (SFTP é a versão segura) |
| **Cc / Cco** | Cópia / cópia oculta |

- **Navegadores**: janela anônima no Chrome = **Ctrl + Shift + N** (Firefox: Ctrl + Shift + P); nova aba = Ctrl + T; reabrir aba fechada = Ctrl + Shift + T; histórico = Ctrl + H. As **abas** surgiram como padrão no **Opera** (SJC Q26).
- **Redes sociais**: profissional = **LinkedIn** (Canaã Q30).
- **E-mail profissional**: ao encaminhar, **resuma o contexto e destaque a ação pedida** (SJC Q50).

## 7. Segurança da informação

| Ameaça / defesa | Definição |
|---|---|
| **Vírus** | Anexa-se a arquivos/programas **executáveis** e precisa de **execução** para se propagar |
| **Worm** | Propaga-se **sozinho** pela rede |
| **Trojan** | Disfarçado de programa legítimo |
| **Spyware / keylogger** | Espiona e captura dados (não só senhas bancárias; SJC Q27) |
| **Ransomware** | Criptografa os dados e pede resgate |
| **Phishing** | Golpe que imita instituições para roubar dados |
| **Firewall** | Filtra o tráfego que **entra e sai**; pode impedir a **saída** de dados (SJC Q27). **Não** é antivírus nem spyware (Canaã Q29) |
| **Backup** | Completo (tudo), incremental (o que mudou desde o último backup), diferencial (o que mudou desde o último completo) |
| **2FA / MFA** | Senha + outro fator (token, aplicativo, biometria) |

## 8. Nuvem e colaboração

- **Armazenamento em nuvem**: **bloco** (bancos de dados), **objeto** (identificador único; fotos, backups), **arquivo** (pastas compartilhadas via SMB/NFS) (SJC Q30).
- **Google Workspace**: Docs, Sheets (edição simultânea por até **100** pessoas; SJC Q29), Drive (guarda **versões**, inclusive de .docx), Meet, Chat, Agenda.
- **Microsoft 365**: OneDrive, Teams, coautoria no Word/Excel online.
