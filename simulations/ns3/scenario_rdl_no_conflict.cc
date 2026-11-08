/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL Determinística)
 * Arquivo: scenario_rdl_no_conflict.cc
 * Cenário: S0 — No-Conflict Control (Baseline de Não-Interferência)
 * Objetivo: Avaliar o comportamento do H-RDL sob propostas de controle perfeitamente
 *            compatíveis (Pass-Through Limpo). Prova que InterferenceRate -> 0.0.
 * Topologia: 2 gNBs (Banda n78, 3.5 GHz, 100 MHz BWP), 30 UEs (Slices compatíveis)
 * =========================================================================================
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/antenna-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"

#if __has_include("ns3/nr-module.h")
#include "ns3/nr-module.h"
#define HAS_NR_MODULE 1
#include "rdl-nr-common.h"
#else
#define HAS_NR_MODULE 0
#endif

#if __has_include("ns3/oran-interface.h")
#include "ns3/oran-interface.h"
#define HAS_ORAN_MODULE 1
#elif __has_include("ns3/e2-agent-helper.h")
#include "ns3/e2-agent-helper.h"
#define HAS_ORAN_MODULE 1
#else
#define HAS_ORAN_MODULE 0
#endif

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlNoConflict");

int main (int argc, char *argv[])
{
    uint16_t gNbNum = 2;
    uint16_t ueNum = 30;
    double simTime = 30.0;
    double centralFreq = 3.5e9;
    double bandwidth = 100e6;
    std::string ricIp = "127.0.0.1";
    uint16_t ricPort = 36422;
    bool enableE2Agent = true;
    bool realtime = false;
    std::string syncMode = "BestEffort";
    std::string demoMode = "experiment";
    double conflictStart = 10.0;
    double conflictEnd = 20.0;
    double recoveryWindow = 10.0;
    double kpmPeriod = 0.2;
    uint32_t randomSeed = 1001;
    uint32_t runIndex = 1;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("gNbNum", "Quantidade total de gNBs", gNbNum);
    cmd.AddValue ("ueNum", "Quantidade total de UEs", ueNum);
    cmd.AddValue ("simTime", "Tempo total de simulacao em segundos", simTime);
    cmd.AddValue ("centralFreq", "Frequencia central em Hz", centralFreq);
    cmd.AddValue ("bandwidth", "Largura de banda em Hz", bandwidth);
    cmd.AddValue ("ricIp", "Endereco IP do Near-RT RIC", ricIp);
    cmd.AddValue ("ricPort", "Porta SCTP do servico E2Term", ricPort);
    cmd.AddValue ("enableE2", "Ativar comunicacao E2 / NORI", enableE2Agent);
    cmd.AddValue ("realtime", "Ativar execucao em tempo real via ns3::RealtimeSimulatorImpl", realtime);
    cmd.AddValue ("syncMode", "Modo de sincronizacao (BestEffort | HardLimit)", syncMode);
    cmd.AddValue ("demoMode", "Modo de apresentacao (fast | realtime | experiment)", demoMode);
    cmd.AddValue ("conflictStart", "Tempo de inicio do conflito (s)", conflictStart);
    cmd.AddValue ("conflictEnd", "Tempo de fim do conflito (s)", conflictEnd);
    cmd.AddValue ("recoveryWindow", "Janela de observacao de recuperacao (s)", recoveryWindow);
    cmd.AddValue ("kpmPeriod", "Periodo de relatorio E2SM-KPM (s)", kpmPeriod);
    cmd.AddValue ("seed", "Semente pseudoaleatoria do gerador ns-3", randomSeed);
    cmd.AddValue ("run", "Indice da repeticao estocastica ns-3", runIndex);
    std::string actionSchedule = "";
    double kpiPeriod = 0.1;
    cmd.AddValue ("actionSchedule", "CSV de acoes de controle aplicadas na RAN (gerado pelo baseline)", actionSchedule);
    cmd.AddValue ("kpiPeriod", "Periodo da serie temporal de KPIs por celula (s)", kpiPeriod);
    bool disableSrs = false;
    cmd.AddValue ("disableSrs", "Desativar SRS (contorno de falha do 5G-LENA em handover)", disableSrs);
    cmd.Parse (argc, argv);
    if (disableSrs)
    {
        // Contorno de NS_FATAL do 5G-LENA v5.1 em handover (NrSpectrumPhy::StartRxSrs, "Not allowed
        // state for starting SRS reception"): sem ocasioes de SRS no escalonador.
        Config::SetDefault ("ns3::NrMacSchedulerNs3::EnableSrsInUlSlots", BooleanValue (false));
        Config::SetDefault ("ns3::NrMacSchedulerNs3::EnableSrsInFSlots", BooleanValue (false));
    }

    SeedManager::SetSeed (randomSeed);
    SeedManager::SetRun (runIndex);

    /**
     * =========================================================================================
     * NOTA DIDÁTICA SOBRE DEMONSTRAÇÕES AO VIVO E SINCRONIZAÇÃO EM TEMPO REAL:
     * -----------------------------------------------------------------------------------------
     * 1. Tempo Virtual vs. Tempo Real:
     *    Por padrão, o ns-3 utiliza TEMPO VIRTUAL. Ele executa os eventos o mais rápido
     *    possível, saltando de evento para evento. Alterar apenas 'simTime' (ex.: 60s) NÃO
     *    transforma o ns-3 em uma demonstração ao vivo acompanhável, pois 60s simulados
     *    podem rodar em 8s ou 90s reais dependendo do processador.
     *
     * 2. ns3::RealtimeSimulatorImpl:
     *    Sincroniza o relógio da simulação com o relógio real da máquina (wall-clock time):
     *    1 segundo simulado ≈ 1 segundo real. É o modo oficial do ns-3 para integração com
     *    testbeds, containers Near-RT RIC, VMs e para demonstrações didáticas em defesas.
     *
     * 3. Modos de Sincronização (BestEffort vs HardLimit):
     *    - BestEffort: Recomendado para bancas e defesas. Se a CPU sofrer um pequeno atraso,
     *      o simulador recupera o tempo nos eventos seguintes de forma suave sem abortar.
     *    - HardLimit: Aborta a simulação se o atraso exceder a tolerância (padrão ns-3: 0.1s).
     *      Ideal para testes estritos de cumprimento de orçamento de tempo real.
     *
     * 4. Três Presets de Velocidade (--demoMode):
     *    - fast: 30s simulados em tempo virtual acelerado (depuração rápida e CI).
     *    - realtime: 60-90s simulados em tempo real wall-clock (demonstração ao vivo).
     *    - experiment: 30-120s em tempo virtual padrão (campanha científica com 30 seeds).
     *
     * 5. Cronograma Recomendado para Apresentação/Defesa (60s):
     *    0-10s  : BASELINE (estabilização dos canais de rádio)
     *    10-20s : NORMAL OPERATION (exibição de telemetria E2SM-KPM)
     *    20s    : CONFLICT INJECTION (xApps enviam propostas concorrentes)
     *    23-25s : CONFLICT DETECTED (Perception identifica o conflito)
     *    25s    : H-RDL DECISION (Reasoning arbitra a ação)
     *    25-27s : E2SM-RC CONTROL (RICcontrolRequest -> RICcontrolAck)
     *    27-40s : RECOVERY (recuperação das métricas de rádio e SLA)
     *    40-60s : STABLE STATE (manutenção do estado governado)
     * =========================================================================================
     */
    if (demoMode == "realtime")
    {
        realtime = true;
        if (simTime == 30.0) simTime = 60.0;
    }
    else if (demoMode == "fast")
    {
        realtime = false;
        simTime = 30.0;
    }
    else if (demoMode == "experiment")
    {
        realtime = false;
    }

    if (realtime)
    {
        // Vincula a implementação do simulador ao modo em tempo real (wall-clock)
        GlobalValue::Bind ("SimulatorImplementationType", StringValue ("ns3::RealtimeSimulatorImpl"));
        if (syncMode == "HardLimit")
        {
            // HardLimit: aborta a simulação se o atraso exceder a tolerância (padrão: 0.1s)
            Config::SetDefault ("ns3::RealtimeSimulatorImpl::SynchronizationMode", StringValue ("HardLimit"));
        }
        else
        {
            // BestEffort: recupera suavemente atrasos temporários de CPU sem abortar
            Config::SetDefault ("ns3::RealtimeSimulatorImpl::SynchronizationMode", StringValue ("BestEffort"));
        }
    }

    Time::SetResolution (Time::NS);
    LogComponentEnable ("ScenarioRdlNoConflict", LOG_LEVEL_INFO);

    NS_LOG_INFO ("Iniciando Cenario S0: No-Conflict Control (Baseline de Nao-Interferencia)");
    NS_LOG_INFO ("gNBs: " << gNbNum << " | UEs: " << ueNum << " | BW: 100 MHz | Freq: 3.5 GHz | Modo Demo: " << demoMode << " | Realtime: " << (realtime ? "Sim (" + syncMode + ")" : "Nao"));

    NodeContainer gNbNodes;
    gNbNodes.Create (gNbNum);

    NodeContainer ueNodes;
    ueNodes.Create (ueNum);

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> positionAlloc = CreateObject<ListPositionAllocator> ();
    positionAlloc->Add (Vector (0.0, 0.0, 25.0));      // gNB 1
    positionAlloc->Add (Vector (250.0, 0.0, 25.0));    // gNB 2
    mobility.SetPositionAllocator (positionAlloc);
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (gNbNodes);

    // Posicionamento uniforme dos UEs com margens de folga para evitar handovers espúrios
    mobility.SetPositionAllocator ("ns3::RandomBoxPositionAllocator",
                                   "X", StringValue ("ns3::UniformRandomVariable[Min=10.0|Max=240.0]"),
                                   "Y", StringValue ("ns3::UniformRandomVariable[Min=-60.0|Max=60.0]"),
                                   "Z", StringValue ("ns3::ConstantRandomVariable[Constant=1.5]"));
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (ueNodes);

#if HAS_NR_MODULE
    // Rede NR funcional comum (rdl-nr-common.h): EPC, host remoto, IPs, attach ao gNB mais
    // proximo e X2. A montagem anterior nao anexava os UEs nem lhes atribuia IP, e o trafego
    // era enviado para 10.0.0.1 (inexistente): o FlowMonitor ficava vazio.
    RdlNrNetwork rdlNet = RdlBuildNrNetwork (gNbNodes, ueNodes, centralFreq, bandwidth);
    uint16_t port = 5001;
    ApplicationContainer serverApps;
    ApplicationContainer clientApps;
    // Carga original do cenario, agora em downlink a partir do host remoto
    RdlInstallDownlinkUdp (rdlNet, ueNodes, serverApps, clientApps, port,
                           [&] (uint32_t i) { return MilliSeconds (20); }, 256);
    RdlActuation rdlActuation (rdlNet.nrHelper, rdlNet.gnbDevs, rdlNet.ueDevs);
    rdlActuation.Load (actionSchedule);
    RdlKpiSampler rdlKpi (rdlNet.ueDevs, kpiPeriod, simTime);
#else
    NS_FATAL_ERROR ("Este cenario requer o modulo 5G-LENA (nr).");
    ApplicationContainer serverApps;
    ApplicationContainer clientApps;
#endif

    serverApps.Start (Seconds (0.5));
    serverApps.Stop (Seconds (simTime));
    clientApps.Start (Seconds (1.0));
    clientApps.Stop (Seconds (simTime));

#if HAS_ORAN_MODULE
    if (enableE2Agent)
    {
        NS_LOG_INFO ("Instalando E2 Agent (NORI) para conexao com Near-RT RIC...");
    }
#endif

    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll ();

    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();

    monitor->CheckForLostPackets ();
    Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier> (flowmon.GetClassifier ());
    std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats ();

    double totalRxBytes = 0.0;
    double totalDelayMs = 0.0;
    uint32_t rxPkts = 0;

    for (auto const &flow : stats)
    {
        totalRxBytes += flow.second.rxBytes;
        if (flow.second.rxPackets > 0)
        {
            totalDelayMs += flow.second.delaySum.GetMilliSeconds ();
            rxPkts += flow.second.rxPackets;
        }
    }

    double avgDelay = rxPkts > 0 ? totalDelayMs / rxPkts : 0.0;
    double totalThpMbps = (totalRxBytes * 8.0) / (simTime * 1e6);

    NS_LOG_INFO ("=== Relatorio Final Cenario S0 (No-Conflict Pass-Through) ===");
    NS_LOG_INFO ("Vazao Agregada Raw: " << totalThpMbps << " Mbps");
    NS_LOG_INFO ("Latencia Media Raw: " << avgDelay << " ms");

    monitor->SerializeToXmlFile ("flowmonitor_scenario_rdl_no_conflict.xml", true, true);

    Simulator::Destroy ();
    return 0;
}
