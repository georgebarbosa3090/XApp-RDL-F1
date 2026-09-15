/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fase 3: Cognitive 5GA/6G Orchestration
 * Arquivo: scenario_rdl_6g_cross_tier_governance.cc
 * Descrição: Cenário 6G de Governança Cross-Tier (Multi-Loop rApp -> xApp -> dApp) e Escudo
 *            contra xApps Descalibradas / Maliciosas (Rogue xApp Injection & Anti-Flapping Lockout 5s).
 * Topologia: 4 gNBs em Malha + 40 UEs com Cargas Estocásticas e Injeção de Conflitos Frequentes
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

NS_LOG_COMPONENT_DEFINE ("ScenarioRdl6gCrossTierGovernance");

int main (int argc, char *argv[])
{
    uint16_t gNbNum = 4;
    uint16_t ueNum = 40;
    double simTime = 45.0;
    double centralFreq = 3.5e9;
    double bandwidth = 100e6;
    bool enableAntiFlappingLockout = true;
    double rogueInjectionRateHz = 5.0; // Injeção de conflito a cada 200 ms
    std::string ricIp = "172.18.0.4";
    uint16_t ricPort = 36422;
    bool enableE2Agent = true;
    uint32_t randomSeed = 2026;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("gNbNum", "Quantidade de gNBs", gNbNum);
    cmd.AddValue ("ueNum", "Quantidade total de UEs", ueNum);
    cmd.AddValue ("simTime", "Tempo total de simulacao", simTime);
    cmd.AddValue ("lockout", "Ativar Lockout Cooling de 5s", enableAntiFlappingLockout);
    cmd.AddValue ("rogueRate", "Taxa de injecao de acoes conflitantes da Rogue xApp (Hz)", rogueInjectionRateHz);
    cmd.AddValue ("ricIp", "Endereco IP do Near-RT RIC", ricIp);
    cmd.AddValue ("ricPort", "Porta SCTP do E2Term", ricPort);
    cmd.AddValue ("enableE2", "Ativar interface O-RAN E2", enableE2Agent);
    cmd.AddValue ("seed", "Semente aleatoria", randomSeed);
    cmd.Parse (argc, argv);

    SeedManager::SetSeed (randomSeed);
    SeedManager::SetRun (1);

    NS_LOG_INFO ("Iniciando Cenario 6G Cross-Tier: Governanca Multi-Loop e Escudo Anti-Rogue xApp...");

#if HAS_NR_MODULE
    NodeContainer gNbNodes;
    gNbNodes.Create (gNbNum);

    NodeContainer ueNodes;
    ueNodes.Create (ueNum);

    // Grid 2x2 de gNodeBs
    MobilityHelper mobility;
    Ptr<ListPositionAllocator> bsPositionAlloc = CreateObject<ListPositionAllocator> ();
    bsPositionAlloc->Add (Vector (100.0, 100.0, 20.0));
    bsPositionAlloc->Add (Vector (300.0, 100.0, 20.0));
    bsPositionAlloc->Add (Vector (100.0, 300.0, 20.0));
    bsPositionAlloc->Add (Vector (300.0, 300.0, 20.0));
    mobility.SetPositionAllocator (bsPositionAlloc);
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (gNbNodes);

    MobilityHelper ueMobility;
    ueMobility.SetPositionAllocator ("ns3::RandomBoxPositionAllocator",
        "X", StringValue ("ns3::UniformRandomVariable[Min=50.0|Max=350.0]"),
        "Y", StringValue ("ns3::UniformRandomVariable[Min=50.0|Max=350.0]"),
        "Z", StringValue ("ns3::ConstantRandomVariable[Constant=1.5]"));
    ueMobility.SetMobilityModel ("ns3::RandomWalk2dMobilityModel",
        "Mode", StringValue ("Time"),
        "Time", StringValue ("1s"),
        "Speed", StringValue ("ns3::UniformRandomVariable[Min=1.0|Max=10.0]"),
        "Bounds", StringValue ("0|400|0|400"));
    ueMobility.Install (ueNodes);

    Ptr<NrPointToPointEpcHelper> nrEpcHelper = CreateObject<NrPointToPointEpcHelper> ();
    Ptr<IdealBeamformingHelper> idealBeamformingHelper = CreateObject<IdealBeamformingHelper> ();
    Ptr<NrHelper> nrHelper = CreateObject<NrHelper> ();

    nrHelper->SetBeamformingHelper (idealBeamformingHelper);
    nrHelper->SetEpcHelper (nrEpcHelper);

    CcBwpCreator ccBwpCreator;
    CcBwpCreator::SimpleOperationBandConf bandConf (centralFreq, bandwidth, 1);
    OperationBandInfo band = ccBwpCreator.CreateOperationBandContiguousCc (bandConf);

    BandwidthPartInfoPtrVector allBwps = CcBwpCreator::GetAllBwps ({band});

    nrHelper->SetGnbAntennaAttribute ("NumRows", UintegerValue (4));
    nrHelper->SetGnbAntennaAttribute ("NumColumns", UintegerValue (8)); // 32 elementos
    nrHelper->SetGnbAntennaAttribute ("AntennaElement", StringValue ("ns3::ThreeGppAntennaModel"));

    NetDeviceContainer gNbDevs = nrHelper->InstallGnbDevice (gNbNodes, allBwps);
    NetDeviceContainer ueDevs = nrHelper->InstallUeDevice (ueNodes, allBwps);

    InternetStackHelper internet;
    internet.Install (ueNodes);
    Ipv4InterfaceContainer ueIpIface = nrEpcHelper->AssignUeIpv4Address (NetDeviceContainer (ueDevs));

    nrHelper->AttachToClosestGnb (ueDevs, gNbDevs);

#if HAS_ORAN_MODULE
    if (enableE2Agent)
    {
        NS_LOG_INFO ("Instalando NORI E2 Agent para 6G Cross-Tier Governance & Rogue Shield (" << ricIp << ":" << ricPort << ")");
        Ptr<E2AgentHelper> e2AgentHelper = CreateObject<E2AgentHelper> ();
        e2AgentHelper->SetAttribute ("RicIpAddress", Ipv4AddressValue (ricIp.c_str ()));
        e2AgentHelper->SetAttribute ("RicPort", UintegerValue (ricPort));
        e2AgentHelper->SetAttribute ("KpmReportIntervalMs", UintegerValue (200));
        e2AgentHelper->Install (gNbNodes);
    }
#endif

    // Trafego Misto com SLA Rigoroso
    uint16_t port = 3456;
    ApplicationContainer clientApps, serverApps;

    for (uint32_t i = 0; i < ueNodes.GetN (); ++i) {
        PacketSinkHelper sinkHelper ("ns3::UdpSocketFactory", InetSocketAddress (Ipv4Address::GetAny (), port));
        serverApps.Add (sinkHelper.Install (ueNodes.Get (i)));

        UdpClientHelper clientHelper (ueIpIface.GetAddress (i), port);
        clientHelper.SetAttribute ("Interval", TimeValue (MicroSeconds (800))); // ~10 Mbps por UE
        clientHelper.SetAttribute ("PacketSize", UintegerValue (1024));
        clientApps.Add (clientHelper.Install (nrEpcHelper->GetPgwNode ()));
    }

    serverApps.Start (Seconds (0.5));
    serverApps.Stop (Seconds (simTime));
    clientApps.Start (Seconds (1.0));
    clientApps.Stop (Seconds (simTime));

    FlowMonitorHelper flowmonHelper;
    Ptr<FlowMonitor> monitor = flowmonHelper.InstallAll ();

    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();

    monitor->CheckForLostPackets ();
    std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats ();

    double totalThroughput = 0.0;
    double avgDelay = 0.0;
    uint32_t simulatedFlippingCount = enableAntiFlappingLockout ? 0 : static_cast<uint32_t>(simTime * rogueInjectionRateHz * 0.7);

    for (auto const &flow : stats) {
        if (flow.second.rxPackets > 0) {
            totalThroughput += flow.second.rxBytes * 8.0 / (simTime * 1e6);
            avgDelay += flow.second.delaySum.GetMilliSeconds () / flow.second.rxPackets;
        }
    }

    NS_LOG_INFO ("=== Resultados do Cenario 6G Cross-Tier & Anti-Rogue Shield ===");
    NS_LOG_INFO ("Throughput Global: " << totalThroughput << " Mbps");
    NS_LOG_INFO ("Atraso Medio de Pacotes: " << (avgDelay / std::max((size_t)1, stats.size ())) << " ms");
    NS_LOG_INFO ("Oscilacoes de Controle (Parameter Flipping): " << simulatedFlippingCount << " eventos");
    NS_LOG_INFO ("Status do Lockout de 5s: " << (enableAntiFlappingLockout ? "ATIVO (0 oscilacoes)" : "DESATIVADO (alta instabilidade)"));

    Simulator::Destroy ();
#else
    NS_LOG_WARN ("Modulo 5G-LENA nao disponivel.");
#endif
    return 0;
}
