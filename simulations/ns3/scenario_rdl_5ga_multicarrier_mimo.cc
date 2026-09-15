/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fase 3: Cognitive 5GA/6G Orchestration
 * Arquivo: scenario_rdl_5ga_multicarrier_mimo.cc
 * Descrição: Cenário 5G-Advanced de Simulação Multi-Portadora (FR1 3.5 GHz + FR3 Upper Mid-Band),
 *            Massive MIMO UPA (16x4 gNB com Downtilt e 2x2 UE) e Fatiamento Dinâmico (COMIX / ORIGAMI).
 * Topologia: 3 gNBs Interconectadas (ISD 500m) + 60 UEs (Mobilidade Mista)
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

NS_LOG_COMPONENT_DEFINE ("ScenarioRdl5gaMulticarrierMimo");

int main (int argc, char *argv[])
{
    // 1. Parametros Operacionais e Variaveis de Linha de Comando
    uint16_t gNbNum = 3;
    uint16_t ueNum = 60;
    double simTime = 50.0;
    double centralFreqFr1 = 3.5e9;   // FR1: 3.5 GHz
    double bandwidthFr1 = 100e6;     // 100 MHz (273 PRBs em SCS 15 kHz)
    double centralFreqFr3 = 10.5e9;  // FR3 (Upper Mid-Band): 10.5 GHz
    double bandwidthFr3 = 200e6;     // 200 MHz
    std::string ricIp = "127.0.0.1";
    uint16_t ricPort = 36422;
    bool enableE2Agent = true;
    uint32_t randomSeed = 42;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("gNbNum", "Quantidade de gNBs", gNbNum);
    cmd.AddValue ("ueNum", "Quantidade total de UEs", ueNum);
    cmd.AddValue ("simTime", "Tempo total de simulacao", simTime);
    cmd.AddValue ("ricIp", "IP do Near-RT RIC", ricIp);
    cmd.AddValue ("ricPort", "Porta SCTP do E2Term", ricPort);
    cmd.AddValue ("enableE2", "Ativar interface O-RAN E2", enableE2Agent);
    cmd.AddValue ("seed", "Semente do gerador aleatorio", randomSeed);
    cmd.Parse (argc, argv);

    SeedManager::SetSeed (randomSeed);
    SeedManager::SetRun (1);

    NS_LOG_INFO ("Iniciando Cenario 5G-Advanced: Multi-Carrier FR1/FR3 + Massive MIMO UPA + RDL Slicing...");

#if HAS_NR_MODULE
    // 2. Criacao da Topologia Espacial (Corredor Urbano UMi 1000m x 400m)
    NodeContainer gNbNodes;
    gNbNodes.Create (gNbNum);

    NodeContainer ueNodes;
    ueNodes.Create (ueNum);

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> bsPositionAlloc = CreateObject<ListPositionAllocator> ();
    bsPositionAlloc->Add (Vector (100.0, 200.0, 25.0)); // gNB 1
    bsPositionAlloc->Add (Vector (500.0, 200.0, 25.0)); // gNB 2
    bsPositionAlloc->Add (Vector (900.0, 200.0, 25.0)); // gNB 3
    mobility.SetPositionAllocator (bsPositionAlloc);
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (gNbNodes);

    // Mobilidade Mista para UEs: 20 Estaticos, 20 Pedestres (3-5 km/h), 20 Veiculares (36-72 km/h)
    NodeContainer staticUes, pedUes, vehUes;
    for (uint16_t i = 0; i < ueNum; ++i) {
        if (i < 20) staticUes.Add (ueNodes.Get (i));
        else if (i < 40) pedUes.Add (ueNodes.Get (i));
        else vehUes.Add (ueNodes.Get (i));
    }

    // UEs Estaticos
    MobilityHelper staticMobility;
    staticMobility.SetPositionAllocator ("ns3::RandomBoxPositionAllocator",
        "X", StringValue ("ns3::UniformRandomVariable[Min=50.0|Max=950.0]"),
        "Y", StringValue ("ns3::UniformRandomVariable[Min=50.0|Max=350.0]"),
        "Z", StringValue ("ns3::ConstantRandomVariable[Constant=1.5]"));
    staticMobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    staticMobility.Install (staticUes);

    // UEs Pedestres (RandomWalk2d)
    MobilityHelper pedMobility;
    pedMobility.SetPositionAllocator ("ns3::RandomBoxPositionAllocator",
        "X", StringValue ("ns3::UniformRandomVariable[Min=50.0|Max=950.0]"),
        "Y", StringValue ("ns3::UniformRandomVariable[Min=50.0|Max=350.0]"),
        "Z", StringValue ("ns3::ConstantRandomVariable[Constant=1.5]"));
    pedMobility.SetMobilityModel ("ns3::RandomWalk2dMobilityModel",
        "Mode", StringValue ("Time"),
        "Time", StringValue ("2s"),
        "Speed", StringValue ("ns3::UniformRandomVariable[Min=0.8|Max=1.4]"), // ~3 a 5 km/h
        "Bounds", StringValue ("0|1000|0|400"));
    pedMobility.Install (pedUes);

    // UEs Veiculares (ConstantVelocity)
    MobilityHelper vehMobility;
    vehMobility.SetPositionAllocator ("ns3::RandomBoxPositionAllocator",
        "X", StringValue ("ns3::UniformRandomVariable[Min=50.0|Max=950.0]"),
        "Y", StringValue ("ns3::UniformRandomVariable[Min=50.0|Max=350.0]"),
        "Z", StringValue ("ns3::ConstantRandomVariable[Constant=1.5]"));
    vehMobility.SetMobilityModel ("ns3::ConstantVelocityMobilityModel");
    vehMobility.Install (vehUes);
    for (uint32_t i = 0; i < vehUes.GetN (); ++i) {
        vehUes.Get (i)->GetObject<ConstantVelocityMobilityModel> ()->SetVelocity (Vector (15.0, 0.0, 0.0)); // ~54 km/h
    }

    // 3. Configuracao do Espectro 5G-LENA e Component Carriers (FR1 + FR3)
    Ptr<NrPointToPointEpcHelper> nrEpcHelper = CreateObject<NrPointToPointEpcHelper> ();
    Ptr<IdealBeamformingHelper> idealBeamformingHelper = CreateObject<IdealBeamformingHelper> ();
    Ptr<NrHelper> nrHelper = CreateObject<NrHelper> ();

    nrHelper->SetBeamformingHelper (idealBeamformingHelper);
    nrHelper->SetEpcHelper (nrEpcHelper);

    // Bandwidth Parts: Multi-Carrier FR1 (3.5 GHz, 100 MHz) e FR3 (10.5 GHz, 200 MHz)
    CcBwpCreator ccBwpCreator;
    CcBwpCreator::SimpleOperationBandConf bandConfFr1 (centralFreqFr1, bandwidthFr1, 1);
    CcBwpCreator::SimpleOperationBandConf bandConfFr3 (centralFreqFr3, bandwidthFr3, 1);
    OperationBandInfo bandFr1 = ccBwpCreator.CreateOperationBandContiguousCc (bandConfFr1);
    OperationBandInfo bandFr3 = ccBwpCreator.CreateOperationBandContiguousCc (bandConfFr3);

    Config::SetDefault ("ns3::ThreeGppChannelModel::UpdatePeriod", TimeValue (MilliSeconds (100)));
    Config::SetDefault ("ns3::ThreeGppPropagationLossModel::ShadowingEnabled", BooleanValue (true));
    nrHelper->SetSchedulerAttribute ("FixedMcsDl", BooleanValue (false));

    BandwidthPartInfoPtrVector allBwps = CcBwpCreator::GetAllBwps ({bandFr1, bandFr3});

    // 4. Antenas UPA e Beamforming
    nrHelper->SetGnbAntennaAttribute ("NumRows", UintegerValue (4));
    nrHelper->SetGnbAntennaAttribute ("NumColumns", UintegerValue (16)); // 64 elementos
    nrHelper->SetGnbAntennaAttribute ("AntennaElement", StringValue ("ns3::ThreeGppAntennaModel"));

    nrHelper->SetUeAntennaAttribute ("NumRows", UintegerValue (2));
    nrHelper->SetUeAntennaAttribute ("NumColumns", UintegerValue (2)); // 4 elementos
    nrHelper->SetUeAntennaAttribute ("AntennaElement", StringValue ("ns3::ThreeGppAntennaModel"));

    NetDeviceContainer gNbDevs = nrHelper->InstallGnbDevice (gNbNodes, allBwps);
    NetDeviceContainer ueDevs = nrHelper->InstallUeDevice (ueNodes, allBwps);

    // 5. Associacao de UEs e Configuracao de IP
    InternetStackHelper internet;
    internet.Install (ueNodes);
    Ipv4InterfaceContainer ueIpIface = nrEpcHelper->AssignUeIpv4Address (NetDeviceContainer (ueDevs));

    nrHelper->AttachToClosestGnb (ueDevs, gNbDevs);

#if HAS_ORAN_MODULE
    if (enableE2Agent)
    {
        NS_LOG_INFO ("Instalando NORI E2 Agent para 5G-Advanced Massive MIMO / Carrier Aggregation (" << ricIp << ":" << ricPort << ")");
        Ptr<E2AgentHelper> e2AgentHelper = CreateObject<E2AgentHelper> ();
        e2AgentHelper->SetAttribute ("RicIpAddress", Ipv4AddressValue (ricIp.c_str ()));
        e2AgentHelper->SetAttribute ("RicPort", UintegerValue (ricPort));
        e2AgentHelper->SetAttribute ("KpmReportIntervalMs", UintegerValue (200));
        e2AgentHelper->Install (gNbNodes);
    }
#endif

    // 6. Aplicacoes e Fatiamento de Trafego (URLLC, eMBB, mMTC)
    uint16_t port = 1234;
    ApplicationContainer clientApps, serverApps;

    for (uint32_t i = 0; i < ueNodes.GetN (); ++i) {
        PacketSinkHelper sinkHelper ("ns3::UdpSocketFactory", InetSocketAddress (Ipv4Address::GetAny (), port));
        serverApps.Add (sinkHelper.Install (ueNodes.Get (i)));

        UdpClientHelper clientHelper (ueIpIface.GetAddress (i), port);
        if (i < 20) {
            // Fatia 1: URLLC (CBR 5 Mbps, pacotes a cada 1.6 ms)
            clientHelper.SetAttribute ("Interval", TimeValue (MicroSeconds (1639)));
            clientHelper.SetAttribute ("PacketSize", UintegerValue (1024));
        } else if (i < 40) {
            // Fatia 2: eMBB (CBR 20 Mbps)
            clientHelper.SetAttribute ("Interval", TimeValue (MicroSeconds (400)));
            clientHelper.SetAttribute ("PacketSize", UintegerValue (1024));
        } else {
            // Fatia 3: mMTC (Mensagens periodicas esparsas)
            clientHelper.SetAttribute ("Interval", TimeValue (MilliSeconds (100)));
            clientHelper.SetAttribute ("PacketSize", UintegerValue (256));
        }
        clientApps.Add (clientHelper.Install (nrEpcHelper->GetPgwNode ()));
    }

    serverApps.Start (Seconds (0.5));
    serverApps.Stop (Seconds (simTime));
    clientApps.Start (Seconds (1.0));
    clientApps.Stop (Seconds (simTime));

    // 7. Monitoramento de Fluxos
    FlowMonitorHelper flowmonHelper;
    Ptr<FlowMonitor> monitor = flowmonHelper.InstallAll ();

    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();

    monitor->CheckForLostPackets ();
    Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier> (flowmonHelper.GetClassifier ());
    std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats ();

    double totalThroughput = 0.0;
    double totalDelay = 0.0;
    uint64_t totalRxPackets = 0;

    for (auto const &flow : stats) {
        if (flow.second.rxPackets > 0) {
            double thp = flow.second.rxBytes * 8.0 / (simTime * 1e6); // Mbps
            double delay = flow.second.delaySum.GetMilliSeconds () / flow.second.rxPackets;
            totalThroughput += thp;
            totalDelay += delay;
            totalRxPackets += flow.second.rxPackets;
        }
    }

    NS_LOG_INFO ("=== Resultados do Cenario 5G-Advanced Multi-Carrier / MIMO ===");
    NS_LOG_INFO ("Throughput Total: " << totalThroughput << " Mbps");
    NS_LOG_INFO ("Atraso Medio: " << (totalDelay / stats.size ()) << " ms");
    NS_LOG_INFO ("Pacotes Recebidos: " << totalRxPackets);

    Simulator::Destroy ();
#else
    NS_LOG_WARN ("Modulo 5G-LENA nao disponivel no build atual.");
#endif
    return 0;
}
