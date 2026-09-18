# Guia de Provisionamento de UEs Comerciais (COTS) e SIM Cards Físicos

Este documento orienta o provisionamento seguro de SIM cards programáveis e modems/smartphones 5G comerciais para validação da xApp-RDL em bancada físico-experimental.

---

## 1. Parâmetros de Rádio e Frequência (Banda n78)

- **Faixa de Frequência:** Banda 3GPP n78 (3.300 MHz a 3.800 MHz)
- **ARFCN Downlink:** `627340` (Frequência central: 3.410,1 MHz)
- **SSB GSCN:** `7711` (SSB Frequency: 3.410,88 MHz)
- **Largura de Banda:** 20 MHz (Numerologia $\mu = 1$, Subcarrier Spacing = 30 kHz)
- **Modo Duplex:** TDD (Configuração de padrão 3GPP: 7 Downlink, 2 Uplink, 1 Special slot)

---

## 2. Gravação de SIM Cards Programáveis (sysmoISIM-SJA2)

Utilizando a ferramenta oficial `pySim`:

```bash
# Gravar credenciais no cartão SIM usando leitor de smartcard USB
pySim-prog.py -p 0 \
  --mcc 999 --mnc 70 \
  --imsi 999700000000001 \
  --ki 465B5CE8B199B49FAA5F0A2EE238A6BC \
  --opc E8ED289DEBA952E4283B54E88E6183CA \
  --smsp "0000" \
  --name "Testbed_RDL_UE1"
```

---

## 3. Cadastro do Assinante no Open5GS Core (MongoDB / WebUI)

Acesse `http://localhost:9999` (ou execute via script API):
- **IMSI:** `999700000000001`
- **Chave Secreta K:** `465B5CE8B199B49FAA5F0A2EE238A6BC`
- **OPc:** `E8ED289DEBA952E4283B54E88E6183CA`
- **Algoritmo de Autenticação:** Milenage (5G AKA)
- **Fatias Autorizadas (S-NSSAI):**
  - Fatia 1 (eMBB): `SST = 1`, `SD = 000001` | DNN: `internet`
  - Fatia 2 (URLLC): `SST = 2`, `SD = 000002` | DNN: `urllc`

---

## 4. Requisitos de Potência e Conformidade Regulatória (Anatel)

1. **Atenuação Física Obrigatória:** Conectar atenuadores coaxiais de **30 dB a 40 dB** diretamente na saída RF da USRP antes de acoplar antenas ou conectar via cabo ao UE COTS.
2. **Ambiente Confinado:** Testes Over-the-Air devem ser realizados em **gaiola de Faraday** ou **câmara anecóica de bancada**.
3. **Potência Máxima Irradiada:** Não exceder $+10\text{ dBm}$ EIRP no ambiente de laboratório para garantir conformidade estrita com o Regulamento sobre Canalização e Condições de Uso de Radiofrequências.
