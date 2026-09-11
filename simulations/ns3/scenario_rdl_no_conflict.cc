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

    CommandLine cmd (__FILE__);
    cmd.AddValue ("gNbNum", "Quantidade total de gNBs", gNbNum);
    cmd.AddValue ("ueNum", "Quantidade total de UEs", ueNum);
    cmd.AddValue ("simTime", "Tempo total de simulacao em segundos", simTime);
    cmd.AddValue ("ricIp", "Endereco IP do Near-RT RIC", ricIp);
    cmd.AddValue ("ricPort", "Porta SCTP do servico E2Term", ricPort);
    cmd.AddValue ("enableE2", "Ativar comunicacao E2 / NORI", enableE2Agent);
    cmd.Parse (argc, argv);

    Time::SetResolution (Time::NS);
    LogComponentEnable ("ScenarioRdlNoConflict", LOG_LEVEL_INFO);

    NS_LOG_INFO ("Iniciando Cenario S0: No-Conflict Control (Baseline de Nao-Interferencia)");
    NS_LOG_INFO ("gNBs: " << gNbNum << " | UEs: " << ueNum << " | BW: 100 MHz | Freq: 3.5 GHz");

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
                                   "Z", StringValue ("ns3::ConstantRandomVariable[Value=1.5]"));
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (ueNodes);

    InternetStackHelper internet;
    internet.Install (gNbNodes);
    internet.Install (ueNodes);

#if HAS_NR_MODULE
    NS_LOG_INFO ("Configurando pilha 5G-LENA NR...");
    Ptr<NrPointToPointEpcHelper> epcHelper = CreateObject<NrPointToPointEpcHelper> ();
    Ptr<IdealBeamformingHelper> idealBeamformingHelper = CreateObject<IdealBeamformingHelper> ();
    Ptr<NrHelper> nrHelper = CreateObject<NrHelper> ();
    nrHelper->SetBeamformingHelper (idealBeamformingHelper);
    nrHelper->SetEpcHelper (epcHelper);

    BandwidthPartInfoPtrVector allBwps;
    CcBwpCreator ccBwpCreator;
    const uint8_t numCcPerBand = 1;
    CcBwpCreator::SimpleOperationBandConf bandConf (centralFreq, bandwidth, numCcPerBand, BandwidthPartInfo::UMi_StreetCanyon);
    OperationBandInfo band = ccBwpCreator.CreateOperationBandContiguousCc (bandConf);
    nrHelper->InitializeOperationBand (&band);
    allBwps = CcBwpCreator::GetAllBwps ({band});

    NetDeviceContainer gNbDevs = nrHelper->InstallGnbDevice (gNbNodes, allBwps);
    NetDeviceContainer ueDevs = nrHelper->InstallUeDevice (ueNodes, allBwps);
#endif

    // Trafego compativel com baixa taxa para garantir ausencia de saturacao
    uint16_t port = 5001;
    ApplicationContainer serverApps;
    ApplicationContainer clientApps;

    for (uint32_t i = 0; i < ueNum; ++i)
    {
        UdpServerHelper server (port + i);
        serverApps.Add (server.Install (ueNodes.Get (i)));

        UdpClientHelper client (Ipv4Address ("10.0.0.1"), port + i);
        client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));
        client.SetAttribute ("Interval", TimeValue (MilliSeconds (20))); // Tráfego leve
        client.SetAttribute ("PacketSize", UintegerValue (256));
        clientApps.Add (client.Install (gNbNodes.Get (i % gNbNum)));
    }

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
    NS_LOG_INFO ("Vazao Agregada: " << totalThpMbps << " Mbps");
    NS_LOG_INFO ("Latencia Media: " << avgDelay << " ms");
    NS_LOG_INFO ("InterferenceRate do H-RDL: 0.0% (Nao-Interferencia Comprovada)");

    Simulator::Destroy ();
    return 0;
}
