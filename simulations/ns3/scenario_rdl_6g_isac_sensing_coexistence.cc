/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fase 3: Cognitive 5GA/6G Orchestration
 * Arquivo: scenario_rdl_6g_isac_sensing_coexistence.cc
 * Descrição: Cenário 6G ISAC (Integrated Sensing and Communication) em mmWave / Sub-THz (28 GHz)
 *            Arbitragem de Contenção entre Feixes de Sensoriamento Radar e Dados Ultrarrápidos (XR/URLLC).
 * Topologia: 2 gNBs ISAC Dual-Function + 30 UEs + 10 Alvos de Sensoriamento em Movimento
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

NS_LOG_COMPONENT_DEFINE ("ScenarioRdl6gIsacSensingCoexistence");

int main (int argc, char *argv[])
{
    uint16_t gNbNum = 2;
    uint16_t ueNum = 30;
    double simTime = 30.0;
    double centralFreq = 28.0e9;     // 28 GHz mmWave
    double bandwidth = 400e6;        // 400 MHz (Largura de banda 6G ISAC)
    double sensingPowerRatio = 0.3;  // Quota inicial de potencia/recurso para sensoriamento radar
    std::string ricIp = "127.0.0.1";
    uint16_t ricPort = 36422;
    bool enableE2Agent = true;
    uint32_t randomSeed = 101;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("gNbNum", "Quantidade de gNBs ISAC", gNbNum);
    cmd.AddValue ("ueNum", "Quantidade total de UEs", ueNum);
    cmd.AddValue ("simTime", "Tempo total de simulacao", simTime);
    cmd.AddValue ("sensingRatio", "Fracao de potencia/tempo para sensoriamento", sensingPowerRatio);
    cmd.AddValue ("ricIp", "Endereco IP do Near-RT RIC", ricIp);
    cmd.AddValue ("ricPort", "Porta SCTP do E2Term", ricPort);
    cmd.AddValue ("enableE2", "Ativar interface O-RAN E2", enableE2Agent);
    cmd.AddValue ("seed", "Semente aleatoria", randomSeed);
    cmd.Parse (argc, argv);

        SeedManager::SetSeed (randomSeed);
    SeedManager::SetRun (1);

    NS_LOG_INFO ("Iniciando Cenario 6G ISAC: Coexistencia Radar-Comunicacao em 28 GHz...");

#if HAS_NR_MODULE
    NodeContainer gNbNodes;
    gNbNodes.Create (gNbNum);

    NodeContainer ueNodes;
    ueNodes.Create (ueNum);

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> bsPositionAlloc = CreateObject<ListPositionAllocator> ();
    bsPositionAlloc->Add (Vector (50.0, 100.0, 10.0));
    bsPositionAlloc->Add (Vector (250.0, 100.0, 10.0));
    mobility.SetPositionAllocator (bsPositionAlloc);
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (gNbNodes);

    MobilityHelper ueMobility;
    ueMobility.SetPositionAllocator ("ns3::RandomBoxPositionAllocator",
        "X", StringValue ("ns3::UniformRandomVariable[Min=0.0|Max=300.0]"),
        "Y", StringValue ("ns3::UniformRandomVariable[Min=0.0|Max=200.0]"),
        "Z", StringValue ("ns3::ConstantRandomVariable[Constant=1.5]"));
    ueMobility.SetMobilityModel ("ns3::RandomWalk2dMobilityModel",
        "Mode", StringValue ("Time"),
        "Time", StringValue ("1s"),
        "Speed", StringValue ("ns3::UniformRandomVariable[Min=1.0|Max=15.0]"),
        "Bounds", StringValue ("0|300|0|200"));
    ueMobility.Install (ueNodes);

    // Helpers 5G-LENA
    Ptr<NrPointToPointEpcHelper> nrEpcHelper = CreateObject<NrPointToPointEpcHelper> ();
    Ptr<IdealBeamformingHelper> idealBeamformingHelper = CreateObject<IdealBeamformingHelper> ();
    Ptr<NrHelper> nrHelper = CreateObject<NrHelper> ();

    nrHelper->SetBeamformingHelper (idealBeamformingHelper);
    nrHelper->SetEpcHelper (nrEpcHelper);

    CcBwpCreator ccBwpCreator;
    CcBwpCreator::SimpleOperationBandConf bandConf (centralFreq, bandwidth, 1);
    OperationBandInfo band = ccBwpCreator.CreateOperationBandContiguousCc (bandConf);

    Config::SetDefault ("ns3::ThreeGppChannelModel::UpdatePeriod", TimeValue (MilliSeconds (50)));
    Config::SetDefault ("ns3::ThreeGppPropagationLossModel::ShadowingEnabled", BooleanValue (true));
    nrHelper->SetSchedulerAttribute ("FixedMcsDl", BooleanValue (false));

    BandwidthPartInfoPtrVector allBwps = CcBwpCreator::GetAllBwps ({band});

    // Antenas Phased-Array 6G mmWave
    nrHelper->SetGnbAntennaAttribute ("NumRows", UintegerValue (8));
    nrHelper->SetGnbAntennaAttribute ("NumColumns", UintegerValue (8)); // 64 elementos
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
        NS_LOG_INFO ("Instalando NORI E2 Agent para 6G ISAC Sensing Coexistence (" << ricIp << ":" << ricPort << ")");
        Ptr<E2AgentHelper> e2AgentHelper = CreateObject<E2AgentHelper> ();
        e2AgentHelper->SetAttribute ("RicIpAddress", Ipv4AddressValue (ricIp.c_str ()));
        e2AgentHelper->SetAttribute ("RicPort", UintegerValue (ricPort));
        e2AgentHelper->SetAttribute ("KpmReportIntervalMs", UintegerValue (200));
        e2AgentHelper->Install (gNbNodes);
    }
#endif

    // Trafego de Dados Ultrarrapido
    uint16_t port = 2345;
    ApplicationContainer clientApps, serverApps;

    for (uint32_t i = 0; i < ueNodes.GetN (); ++i) {
        PacketSinkHelper sinkHelper ("ns3::UdpSocketFactory", InetSocketAddress (Ipv4Address::GetAny (), port));
        serverApps.Add (sinkHelper.Install (ueNodes.Get (i)));

        UdpClientHelper clientHelper (ueIpIface.GetAddress (i), port);
        clientHelper.SetAttribute ("Interval", TimeValue (MicroSeconds (200)));
        clientHelper.SetAttribute ("PacketSize", UintegerValue (1400));
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

    double totalCommThp = 0.0;
    double avgDelay = 0.0;

    for (auto const &flow : stats) {
        if (flow.second.rxPackets > 0) {
            totalCommThp += flow.second.rxBytes * 8.0 / (simTime * 1e6); // Mbps
            avgDelay += flow.second.delaySum.GetMilliSeconds () / flow.second.rxPackets;
        }
    }

    // Calculo Sintetico de Desempenho de Sensoriamento ISAC
    double radarResolutionMeters = 3.0e8 / (2.0 * bandwidth * (1.0 - sensingPowerRatio)); // Delta R = c / (2B)
    double detectionProbability = 0.98 * (1.0 - exp(-sensingPowerRatio * 10.0));

    NS_LOG_INFO ("=== Resultados do Cenario 6G ISAC (Sensoriamento vs Comunicacao) ===");
    NS_LOG_INFO ("Throughput de Comunicacao: " << totalCommThp << " Mbps");
    NS_LOG_INFO ("Atraso Medio de Pacotes: " << (avgDelay / std::max((size_t)1, stats.size ())) << " ms");
    NS_LOG_INFO ("Resolucao de Distancia do Radar (Delta R): " << radarResolutionMeters << " metros");
    NS_LOG_INFO ("Probabilidade de Deteccao de Alvo (Pd): " << (detectionProbability * 100.0) << " %");

    Simulator::Destroy ();
#else
    NS_LOG_WARN ("Modulo 5G-LENA nao disponivel.");
#endif
    return 0;
}
