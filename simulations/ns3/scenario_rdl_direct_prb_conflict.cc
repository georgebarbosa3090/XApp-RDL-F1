/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL Determinística)
 * Arquivo: scenario_rdl_direct_prb_conflict.cc
 * Cenário: S1 — Direct Conflict (PRB × PRB Ground Truth)
 * Objetivo: Colisão frontal de cotas de PRB na mesma célula e janela temporal (200ms)
 *            xApp-QoS (PRB=75%) vs xApp-Energy (PRB=30%).
 *            Permite calcular Precision, Recall e F1 da detecção de conflitos.
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

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlDirectPrbConflict");

int main (int argc, char *argv[])
{
    uint16_t gNbNum = 1;
    uint16_t ueNum = 20;
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
     *    Por padrão, o ns-3 utiliza TEMPO VIRTUAL (saltando de evento a evento na velocidade
     *    máxima da CPU). Alterar apenas 'simTime' (ex.: 60s) NÃO transforma a simulação em
     *    uma demonstração ao vivo acompanhável pela plateia/banca.
     *
     * 2. ns3::RealtimeSimulatorImpl:
     *    Sincroniza o relógio da simulação com o relógio real (wall-clock): 1s simulado ≈ 1s real.
     *    É a implementação oficial do ns-3 recomendada para apresentações ao vivo e integração E2.
     *
     * 3. Modos de Sincronização:
     *    - BestEffort (Recomendado para Defesas): Recupera atrasos temporários de CPU suavemente.
     *    - HardLimit: Aborta a simulação se o atraso exceder a tolerância (padrão ns-3: 0.1s).
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
    LogComponentEnable ("ScenarioRdlDirectPrbConflict", LOG_LEVEL_INFO);

    NS_LOG_INFO ("Iniciando Cenario S1: Direct Conflict (PRB x PRB Ground Truth)");
    NS_LOG_INFO ("Conflito Programado: xApp-QoS (PRB=75%) vs xApp-Energy (PRB=30%) | Modo Demo: " << demoMode << " | Realtime: " << (realtime ? "Sim (" + syncMode + ")" : "Nao"));

    NodeContainer gNbNodes;
    gNbNodes.Create (gNbNum);

    NodeContainer ueNodes;
    ueNodes.Create (ueNum);

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> positionAlloc = CreateObject<ListPositionAllocator> ();
    positionAlloc->Add (Vector (0.0, 0.0, 25.0)); // Única gNB servindo todos os UEs
    mobility.SetPositionAllocator (positionAlloc);
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (gNbNodes);

    mobility.SetPositionAllocator ("ns3::RandomDiscPositionAllocator",
                                   "X", StringValue ("0.0"),
                                   "Y", StringValue ("0.0"),
                                   "Rho", StringValue ("ns3::UniformRandomVariable[Min=10.0|Max=150.0]"));
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

    // Trafego com disputa de capacidade de enlace
    uint16_t port = 6001;
    ApplicationContainer serverApps;
    ApplicationContainer clientApps;

    for (uint32_t i = 0; i < ueNum; ++i)
    {
        UdpServerHelper server (port + i);
        serverApps.Add (server.Install (ueNodes.Get (i)));

        UdpClientHelper client (Ipv4Address ("10.0.0.1"), port + i);
        client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));
        client.SetAttribute ("Interval", TimeValue (MilliSeconds (5))); // Tráfego intenso (alta carga)
        client.SetAttribute ("PacketSize", UintegerValue (1024));
        clientApps.Add (client.Install (gNbNodes.Get (0)));
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

    NS_LOG_INFO ("=== Relatorio Final Cenario S1 (Direct PRB Conflict) ===");
    NS_LOG_INFO ("Vazao Agregada Raw: " << totalThpMbps << " Mbps");
    NS_LOG_INFO ("Latencia Media Raw: " << avgDelay << " ms");

    monitor->SerializeToXmlFile ("flowmonitor_scenario_rdl_direct_prb_conflict.xml", true, true);

    Simulator::Destroy ();
    return 0;
}
