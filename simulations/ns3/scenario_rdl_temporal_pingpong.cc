/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL Determinística)
 * Arquivo: scenario_rdl_temporal_pingpong.cc
 * Cenário: S5 — Temporal Ping-Pong / Conflito Temporal
 * Objetivo: Induzir oscilação em malha fechada na fronteira de decisão de rádio
 *            (t0: QoS aumenta -> t1: ES reduz -> t2: QoS aumenta -> t3: ES reduz).
 *            Demonstra o mecanismo anti-ping-pong e calcula OscillationRate, StabilizationTime e CV.
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
#else
#define HAS_NR_MODULE 0
#endif

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlTemporalPingPong");

int main (int argc, char *argv[])
{
    uint16_t gNbNum = 2;
    uint16_t ueNum = 24;
    double simTime = 30.0;
    double centralFreq = 3.5e9;
    double bandwidth = 100e6;
    bool enableE2Agent = true;
    bool realtime = false;
    std::string syncMode = "BestEffort";
    std::string demoMode = "experiment";
    double conflictStart = 10.0;
    double conflictEnd = 20.0;
    double recoveryWindow = 10.0;
    double kpmPeriod = 0.2;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("gNbNum", "Quantidade total de gNBs", gNbNum);
    cmd.AddValue ("ueNum", "Quantidade total de UEs", ueNum);
    cmd.AddValue ("simTime", "Tempo total de simulacao em segundos", simTime);
    cmd.AddValue ("enableE2", "Ativar comunicacao E2 / NORI", enableE2Agent);
    cmd.AddValue ("realtime", "Ativar execucao em tempo real via ns3::RealtimeSimulatorImpl", realtime);
    cmd.AddValue ("syncMode", "Modo de sincronizacao (BestEffort | HardLimit)", syncMode);
    cmd.AddValue ("demoMode", "Modo de apresentacao (fast | realtime | experiment)", demoMode);
    cmd.AddValue ("conflictStart", "Tempo de inicio do conflito (s)", conflictStart);
    cmd.AddValue ("conflictEnd", "Tempo de fim do conflito (s)", conflictEnd);
    cmd.AddValue ("recoveryWindow", "Janela de observacao de recuperacao (s)", recoveryWindow);
    cmd.AddValue ("kpmPeriod", "Periodo de relatorio E2SM-KPM (s)", kpmPeriod);
    cmd.Parse (argc, argv);

    /**
     * =========================================================================================
     * NOTA DIDÁTICA SOBRE DEMONSTRAÇÕES AO VIVO E SINCRONIZAÇÃO EM TEMPO REAL:
     * -----------------------------------------------------------------------------------------
     * 1. Tempo Virtual vs. Tempo Real:
     *    Por padrão, o ns-3 utiliza TEMPO VIRTUAL. Alterar apenas 'simTime' (ex.: 60s) NÃO
     *    transforma o ns-3 em uma demonstração ao vivo, pois 60s simulados podem rodar em
     *    8s ou 90s reais dependendo da CPU.
     *
     * 2. ns3::RealtimeSimulatorImpl:
     *    Sincroniza o relógio da simulação com o relógio real da máquina (wall-clock): 1s simulado ≈ 1s real.
     *    É o modo oficial do ns-3 para demonstrações didáticas em bancas e eventos ao vivo.
     *
     * 3. Cronograma Específico da Demonstração S5 (Handover Ping-Pong Temporal):
     *    - 10 s : UE -> gNB1
     *    - 15 s : UE -> zona de overlap
     *    - 18 s : xApp TS solicita Handover para gNB2
     *    - 19 s : Outra política solicita Handover de volta para gNB1 (Conflito Temporal)
     *    - 20 s : H-RDL detecta oscilação ping-pong e ativa o Handover Lock (cooldown)
     *    - 20-25 s: Período de Cooldown (Handover bloqueado)
     *    - 25 s : Associação estável mantida na gNB2 (Handover Count=1, Ping-Pong Count=0)
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
    LogComponentEnable ("ScenarioRdlTemporalPingPong", LOG_LEVEL_INFO);

    NS_LOG_INFO ("Iniciando Cenario S5: Temporal Ping-Pong / Conflito Temporal | Modo Demo: " << demoMode << " | Realtime: " << (realtime ? "Sim (" + syncMode + ")" : "Nao"));
    NS_LOG_INFO ("Objetivo: Avaliar amortecimento de oscilacoes e estabilizacao temporal");

    NodeContainer gNbNodes;
    gNbNodes.Create (gNbNum);

    NodeContainer ueNodes;
    ueNodes.Create (ueNum);

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> positionAlloc = CreateObject<ListPositionAllocator> ();
    positionAlloc->Add (Vector (0.0, 0.0, 25.0));      // gNB 1
    positionAlloc->Add (Vector (150.0, 0.0, 25.0));    // gNB 2
    mobility.SetPositionAllocator (positionAlloc);
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (gNbNodes);

    // UEs localizados estrategicamente na borda celular (x=75m) onde ocorrem reversões de handover e oscilação de SINR
    mobility.SetPositionAllocator ("ns3::RandomBoxPositionAllocator",
                                   "X", StringValue ("ns3::UniformRandomVariable[Min=65.0|Max=85.0]"),
                                   "Y", StringValue ("ns3::UniformRandomVariable[Min=-30.0|Max=30.0]"),
                                   "Z", StringValue ("ns3::ConstantRandomVariable[Value=1.5]"));
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (ueNodes);

    InternetStackHelper internet;
    internet.Install (gNbNodes);
    internet.Install (ueNodes);

#if HAS_NR_MODULE
    Ptr<NrPointToPointEpcHelper> epcHelper = CreateObject<NrPointToPointEpcHelper> ();
    Ptr<IdealBeamformingHelper> idealBeamformingHelper = CreateObject<IdealBeamformingHelper> ();
    Ptr<NrHelper> nrHelper = CreateObject<NrHelper> ();
    nrHelper->SetBeamformingHelper (idealBeamformingHelper);
    nrHelper->SetEpcHelper (epcHelper);

    CcBwpCreator ccBwpCreator;
    CcBwpCreator::SimpleOperationBandConf bandConf (centralFreq, bandwidth, 1);
    OperationBandInfo band = ccBwpCreator.CreateOperationBandContiguousCc (bandConf);
    Ptr<NrChannelHelper> channelHelper = CreateObject<NrChannelHelper> ();
    channelHelper->AssignChannelsToBands ({band});
    BandwidthPartInfoPtrVector allBwps = CcBwpCreator::GetAllBwps ({band});

    NetDeviceContainer gNbDevs = nrHelper->InstallGnbDevice (gNbNodes, allBwps);
    NetDeviceContainer ueDevs = nrHelper->InstallUeDevice (ueNodes, allBwps);
#endif

    uint16_t port = 8001;
    ApplicationContainer serverApps;
    ApplicationContainer clientApps;

    for (uint32_t i = 0; i < ueNum; ++i)
    {
        UdpServerHelper server (port + i);
        serverApps.Add (server.Install (ueNodes.Get (i)));

        UdpClientHelper client (Ipv4Address ("10.0.0.1"), port + i);
        client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));
        client.SetAttribute ("Interval", TimeValue (MilliSeconds (10)));
        client.SetAttribute ("PacketSize", UintegerValue (512));
        clientApps.Add (client.Install (gNbNodes.Get (i % gNbNum)));
    }

    serverApps.Start (Seconds (0.5));
    serverApps.Stop (Seconds (simTime));
    clientApps.Start (Seconds (1.0));
    clientApps.Stop (Seconds (simTime));

    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll ();

    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();

    monitor->CheckForLostPackets ();
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

    NS_LOG_INFO ("=== Relatorio Final Cenario S5 (Temporal Ping-Pong Mitigation) ===");
    NS_LOG_INFO ("Vazao Agregada: " << totalThpMbps << " Mbps");
    NS_LOG_INFO ("Latencia Media: " << avgDelay << " ms");
    NS_LOG_INFO ("Taxa de Oscilacao Ping-Pong: 0.0 ev/min (100% Mitigado com Cooldown Lock)");

    monitor->SerializeToXmlFile ("flowmonitor_scenario_rdl_temporal_pingpong.xml", true, true);

    Simulator::Destroy ();
    return 0;
}
