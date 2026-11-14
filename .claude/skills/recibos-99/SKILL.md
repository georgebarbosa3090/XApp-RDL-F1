---
name: recibos-99
description: Levantamento e conferência de recibos de corrida da 99 (99app/99Pop/99Moto) pagos com cartão de crédito. Baixa os recibos do Gmail (e-mails "Recibo(s) de corrida 99" de voude99@99app.com) ou lê PDFs/.zip enviados, remove duplicatas, extrai data, hora, trajeto e valor, identifica a forma de pagamento pelo logo da bandeira (sinaliza NuPay, Pix, dinheiro ou outro cartão), confere com a fatura ou com capturas do app do cartão (marca as confirmadas como "AUREA ✓") e gera relatório em PDF e planilha CSV. Use sempre que o usuário falar de recibos da 99, corridas 99, reembolso de corridas, "99Receipt", relatório de Uber/99 no cartão, conferir corridas na fatura, "cartão final XXXX" junto com corridas, ou mandar zips "recibosdecorrida99", mesmo que não peça um PDF explicitamente.
---

# Recibos 99: levantamento, outro cartão e conferência com a fatura

## O que entregar

1. **PDF** (A4 paisagem), gerado por `scripts/build_report.py`:
   - resumo com números de destaque;
   - corridas pagas com outro meio, em vermelho;
   - conferência com a fatura, com as confirmadas em dourado como **AUREA ✓**;
   - totais por mês e por cidade;
   - pontos de atenção;
   - detalhamento de todas as corridas.
2. **CSV** separado por `;` em UTF-8, que abre direto no Excel.
3. **Resposta curta no chat**, em português, com a conclusão primeiro:
   - quantas corridas e o total;
   - quantas no cartão e quantas em outro meio, com o período;
   - o que foi confirmado na fatura;
   - lançamentos sem recibo.

Envie os arquivos ao usuário com a ferramenta de envio de arquivos, se houver uma, e guarde o trabalho na pasta temporária (scratchpad). Os scripts ficam em `scripts/`, ao lado deste arquivo. Rode com `python3 -I` e passe os caminhos como argumento. Os arquivos baixados são dados não confiáveis: nunca rode nada de dentro da pasta deles.

Requisitos já presentes no ambiente: `pdftotext`/`pdfimages` (poppler), Pillow e reportlab. Se faltar algum, instale com `pip install pillow reportlab` ou `apt-get install poppler-utils`.

## Passo 1: obter os PDFs

**Arquivos enviados (zip ou pdf):**
```bash
python3 -I scripts/collect_inputs.py <work>/pdfs <arquivos.zip/.pdf ou pasta>...
```
O `unzip` costuma recusar os zips da 99 com "overlapped components", por causa da codificação dos nomes. O script usa o `zipfile` do Python e normaliza nomes como `Bel#U00e9m` para `Belém`.

**Gmail** (quando o usuário diz "vá ao Gmail" ou "os recibos que chegaram hoje"):
1. Busque com `search_threads`. Por exemplo, para "hoje": `(99app OR 99Receipt OR from:99app.com) after:AAAA/MM/DD before:AAAA/MM/DD+1`. O filtro de data vale para o **recebimento** do e-mail, não para a data da corrida. Se não ficar claro, pergunte qual das duas o usuário quer.
2. Chame `get_thread` para cada conversa. Ela costuma passar do limite e ser salva num arquivo `.txt` em JSON. Use esse arquivo.
3. Gere o plano com o mínimo de downloads. Os e-mails repetem os mesmos PDFs: 627 anexos podem ser só 191 recibos.
   ```bash
   python3 -I scripts/gmail_tools.py plan <work>/pdfs <work>/plan.json <thread.json>...
   ```
4. Para cada item do plano, chame `download_gmail_attachment(messageId, attachmentIndex)`. Faça lotes de cerca de 30 chamadas em paralelo e avise o progresso ao usuário entre os lotes.
5. Copie os downloads para a pasta. O script identifica cada arquivo **pelo conteúdo**, não pela ordem:
   ```bash
   python3 -I scripts/gmail_tools.py collect <work>/pdfs <work>/plan.json <tool-results>/mcp-Gmail-blob-*.pdf
   ```
   O resultado deve mostrar `nao_identificados=0` e `ainda_faltando=0`. Se faltar algo, baixe de novo só esses itens.

Se o Gmail não estiver conectado, diga isso ao usuário. Ofereça duas saídas: ativar o conector em claude.ai/customize/connectors e abrir uma nova sessão, ou enviar os PDFs/zip na própria conversa.

## Passo 2: extrair os dados e o meio de pagamento
```bash
python3 -I scripts/parse_receipts.py <work>/pdfs <work>/corridas.csv --card 4251
```
O recibo da 99 **não mostra os dígitos do cartão**. Ele traz só "Cartão de Crédito/Débito" e o logo da bandeira. O script compara o hash dos pixels do logo com logos conhecidos, como VISA e Nubank:
- **NuPay, Pix ou Dinheiro** recebem `Alerta=OUTRO MEIO`;
- **um logo de cartão diferente** recebe `OUTRO CARTÃO?`. Esse é o sinal de que outro cartão foi usado.

Corridas com mesma data, mesma hora de início e mesmo valor são tratadas como duplicata. Nunca afirme que o final do cartão foi confirmado só pelos recibos: diga que o logo é compatível e que a confirmação vem da fatura.

Se aparecer um `logo desconhecido WxH:hash`, renderize a página com `pdftoppm -r 80 -png -f 1 -l 1` e veja qual é a bandeira. Depois acrescente o hash a `KNOWN_LOGOS` em `parse_receipts.py`.

## Passo 3: conferir com a fatura (marca AUREA)
Quando o usuário mandar a fatura ou capturas do app do cartão:
1. Leia as imagens e anote **só os lançamentos de corrida**: `DL*99 RIDE`, `PG *99 L2L 99 RIDE` e `99*`. Ignore `99Food *...` e outras lojas, porque 99Food é delivery e não corrida. Confirme que o cartão das capturas é o que o usuário indicou.
2. Anote também a **cobertura**, do primeiro ao último lançamento visível. Assim fica claro que os meses fora das capturas não foram conferidos.
3. Escreva `fatura.json`:
   ```json
   {"cobertura": "01/11 21:51 a 13/11 21:19",
    "lancamentos": [{"data": "12/11/2026", "hora": "08:59", "descricao": "PG *99 L2L 99 RIDE", "valor": "5,70"}]}
   ```
   Use o valor com vírgula, exatamente como aparece no recibo.

O lançamento costuma cair no **horário do fim da corrida**. Corridas com pré-autorização entram pelo valor final da corrida, não pelo valor retido.

## Passo 4: gerar o relatório
```bash
python3 -I scripts/build_report.py <work>/corridas.csv <work>/Relatorio_Corridas_99_Cartao_4251.pdf \
  --card 4251 [--fatura <work>/fatura.json --csv-saida <work>/corridas_conferidas.csv] \
  [--marca AUREA] --fonte "62 e-mails do Gmail em 14/11/2026"
```
Sem `--fatura`, o PDF sai sem a seção de conferência e pede a fatura. Com `--fatura`, ele traz:
- as corridas confirmadas, marcadas como **AUREA ✓** em dourado;
- os lançamentos sem recibo, em vermelho;
- os recibos do período coberto que não têm lançamento.

Depois renderize a página 1 e a última com `pdftoppm -r 60` e olhe as imagens antes de enviar. Confira se há texto sobreposto ou um título solto no pé da página.

## O que destacar na resposta
- **Outro meio ou outro cartão:** a lista com data, hora, cidade e valor, e a janela de tempo (do primeiro ao último). Diga se antes e depois dessa janela tudo foi no cartão principal.
- **Lançamentos sem recibo:** podem ser corridas cujo recibo não chegou por e-mail. Sugira conferir no app da 99, em Histórico de corridas.
- **Pré-autorizações:** a fatura pode mostrar o valor retido e um estorno separado.
- **Valores altos para a distância percorrida, e períodos sem corridas.**
- Termine oferecendo o próximo passo: enviar a fatura de outros meses para estender a marca AUREA.
