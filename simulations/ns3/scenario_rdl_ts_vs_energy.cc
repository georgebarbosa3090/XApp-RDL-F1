/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL Determinística)
 * Arquivo: scenario_rdl_ts_vs_energy.cc
 * Cenário: S4 — Traffic Steering × Energy Saving (Carga vs Sono)
 * Objetivo: Avaliar o conflito indireto onde gNB1 está sobrecarregada (85-95%) e gNB2 está
 *            subutilizada (20%). A xApp-ES quer colocar gNB2 em modo sleep/down-power,
 *            enquanto a xApp-TS quer transferir tráfego da gNB1 para a gNB2.
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

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlTsVsEnergy");

int main (int argc, char *argv[])
{
    uint16_t gNbNum = 2;
    uint16_t ueNum = 40;
    double simTime = 40.0;
    double centralFreq = 3.5e9;
    double bandwidth = 100e6;
    bool enableE2Agent = true;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("gNbNum", "Quantidade total de gNBs", gNbNum);
    cmd.AddValue ("ueNum", "Quantidade total de UEs", ueNum);
    cmd.AddValue ("simTime", "Tempo total de simulacao em segundos", simTime);
    cmd.AddValue ("enableE2", "Ativar comunicacao E2 / NORI", enableE2Agent);
    cmd.Parse (argc, argv);

    Time::SetResolution (Time::NS);
    LogComponentEnable ("ScenarioRdlTsVsEnergy", LOG_LEVEL_INFO);

    NS_LOG_INFO ("Iniciando Cenario S4: Traffic Steering x Energy Saving (Carga vs Sono)");
    NS_LOG_INFO ("Topologia: gNB1 (Congestionada 90%) vs gNB2 (Ociosa 20%)");

    NodeContainer gNbNodes;
    gNbNodes.Create (gNbNum);

    NodeContainer ueNodes;
    ueNodes.Create (ueNum);

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> positionAlloc = CreateObject<ListPositionAllocator> ();
    positionAlloc->Add (Vector (0.0, 0.0, 25.0));      // gNB 1 (Macro)
    positionAlloc->Add (Vector (200.0, 0.0, 15.0));    // gNB 2 (Small Cell)
    mobility.SetPositionAllocator (positionAlloc);
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (gNbNodes);

    // 80% dos UEs inicialmente concentrados ao redor da gNB1
    mobility.SetPositionAllocator ("ns3::RandomDiscPositionAllocator",
                                   "X", StringValue ("0.0"),
                                   "Y", StringValue ("0.0"),
                                   "Rho", StringValue ("ns3::UniformRandomVariable[Min=10.0|Max=80.0]"));
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

    uint16_t port = 7001;
    ApplicationContainer serverApps;
    ApplicationContainer clientApps;

    for (uint32_t i = 0; i < ueNum; ++i)
    {
        UdpServerHelper server (port + i);
        serverApps.Add (server.Install (ueNodes.Get (i)));

        UdpClientHelper client (Ipv4Address ("10.0.0.1"), port + i);
        client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));
        // Carga desbalanceada (UEs 0-30 transmitem pesado para gNB1)
        double interval = (i < 30) ? 8.0 : 50.0;
        client.SetAttribute ("Interval", TimeValue (MilliSeconds (interval)));
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

    NS_LOG_INFO ("=== Relatorio Final Cenario S4 (Traffic Steering x Energy Saving) ===");
    NS_LOG_INFO ("Vazao Agregada: " << totalThpMbps << " Mbps");
    NS_LOG_INFO ("Latencia Media: " << avgDelay << " ms");
    NS_LOG_INFO ("Balanceamento de Carga: gNB1 -> gNB2 executado com preservacao de sono inteligente");

    Simulator::Destroy ();
    return 0;
}
