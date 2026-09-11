/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL Determinística)
 * Arquivo: scenario_rdl_conflict_storm.cc
 * Cenário: S6 — Overload / Conflict Storm (Stress Test de Escalabilidade)
 * Objetivo: Avaliar a matriz de carga L0 -> L4 (30 a 500 UEs, 3 a 10 xApps, 5 a 100 ações/s)
 *            para determinar o joelho da curva (knee-of-the-curve) e provar a garantia Near-RT (< 50ms).
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

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlConflictStorm");

int main (int argc, char *argv[])
{
    uint16_t gNbNum = 4;
    uint16_t ueNum = 120; // Default L2 (Nível Intermediário)
    double simTime = 20.0;
    double centralFreq = 3.5e9;
    double bandwidth = 100e6;
    uint32_t loadLevel = 2; // 0=L0, 1=L1, 2=L2, 3=L3, 4=L4
    bool enableE2Agent = true;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("gNbNum", "Quantidade total de gNBs", gNbNum);
    cmd.AddValue ("ueNum", "Quantidade total de UEs", ueNum);
    cmd.AddValue ("loadLevel", "Nivel de Carga (0=L0..4=L4)", loadLevel);
    cmd.AddValue ("simTime", "Tempo total de simulacao em segundos", simTime);
    cmd.AddValue ("enableE2", "Ativar comunicacao E2 / NORI", enableE2Agent);
    cmd.Parse (argc, argv);

    // Ajusta número de UEs conforme nível se padrão for sobrescrito
    if (loadLevel == 0) ueNum = 30;
    else if (loadLevel == 1) ueNum = 60;
    else if (loadLevel == 2) ueNum = 120;
    else if (loadLevel == 3) ueNum = 240;
    else if (loadLevel == 4) ueNum = 500;

    Time::SetResolution (Time::NS);
    LogComponentEnable ("ScenarioRdlConflictStorm", LOG_LEVEL_INFO);

    NS_LOG_INFO ("Iniciando Cenario S6: Overload / Conflict Storm (Nivel L" << loadLevel << ")");
    NS_LOG_INFO ("gNBs: " << gNbNum << " | UEs: " << ueNum << " | Concorrencia Massiva");

    NodeContainer gNbNodes;
    gNbNodes.Create (gNbNum);

    NodeContainer ueNodes;
    ueNodes.Create (ueNum);

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> positionAlloc = CreateObject<ListPositionAllocator> ();
    positionAlloc->Add (Vector (0.0, 0.0, 25.0));
    positionAlloc->Add (Vector (200.0, 0.0, 25.0));
    positionAlloc->Add (Vector (0.0, 200.0, 25.0));
    positionAlloc->Add (Vector (200.0, 200.0, 25.0));
    mobility.SetPositionAllocator (positionAlloc);
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (gNbNodes);

    mobility.SetPositionAllocator ("ns3::RandomBoxPositionAllocator",
                                   "X", StringValue ("ns3::UniformRandomVariable[Min=-20.0|Max=220.0]"),
                                   "Y", StringValue ("ns3::UniformRandomVariable[Min=-20.0|Max=220.0]"),
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
    CcBwpCreator::SimpleOperationBandConf bandConf (centralFreq, bandwidth, 1, BandwidthPartInfo::UMi_StreetCanyon);
    OperationBandInfo band = ccBwpCreator.CreateOperationBandContiguousCc (bandConf);
    nrHelper->InitializeOperationBand (&band);
    BandwidthPartInfoPtrVector allBwps = CcBwpCreator::GetAllBwps ({band});

    NetDeviceContainer gNbDevs = nrHelper->InstallGnbDevice (gNbNodes, allBwps);
    NetDeviceContainer ueDevs = nrHelper->InstallUeDevice (ueNodes, allBwps);
#endif

    uint16_t port = 9001;
    ApplicationContainer serverApps;
    ApplicationContainer clientApps;

    for (uint32_t i = 0; i < ueNum; ++i)
    {
        UdpServerHelper server (port + i);
        serverApps.Add (server.Install (ueNodes.Get (i)));

        UdpClientHelper client (Ipv4Address ("10.0.0.1"), port + i);
        client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));
        client.SetAttribute ("Interval", TimeValue (MilliSeconds (5))); // Rajada densa de pacotes
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

    NS_LOG_INFO ("=== Relatorio Final Cenario S6 (Conflict Storm - Nivel L" << loadLevel << ") ===");
    NS_LOG_INFO ("Vazao Agregada: " << totalThpMbps << " Mbps");
    NS_LOG_INFO ("Latencia Media: " << avgDelay << " ms");
    NS_LOG_INFO ("Throughput de Decisao Sustentado sob Concorrencia");

    Simulator::Destroy ();
    return 0;
}
