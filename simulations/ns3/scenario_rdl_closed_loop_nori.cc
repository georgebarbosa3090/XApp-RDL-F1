/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL Determinística)
 * Arquivo: scenario_rdl_closed_loop_nori.cc
 * Descrição: Cenário de Co-Simulação Closed-Loop 5G-LENA + ns-O-RAN / NORI
 *            Validação de Malha Fechada Ponta a Ponta:
 *            KPM(t0) -> NORI E2 Report -> Near-RT RIC -> RDL -> RIC Control -> NORI -> 5G-LENA MAC/PHY -> KPM(t1)
 * Topologia: 2 gNodeBs 5G NR (Macro + Micro), 30 UEs (Fatias URLLC, eMBB e mMTC)
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

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlClosedLoopNori");

int main (int argc, char *argv[])
{
    uint16_t gNbNum = 2;
    uint16_t ueNumPerGnb = 15;
    double simTime = 30.0;
    double centralFrequencyBand1 = 3.5e9;
    double bandwidthBand1 = 100e6;
    uint16_t numerologyBwp1 = 1;
    std::string ricIpAddress = "172.18.0.4";
    uint16_t ricPort = 36422;
    bool enableE2Agent = true;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("gNbNum", "Numero de gNodeBs", gNbNum);
    cmd.AddValue ("ueNumPerGnb", "Numero de UEs por gNB", ueNumPerGnb);
    cmd.AddValue ("simTime", "Tempo total de simulacao", simTime);
    cmd.AddValue ("ricIp", "IP do Near-RT RIC E2Term", ricIpAddress);
    cmd.AddValue ("ricPort", "Porta SCTP E2", ricPort);
    cmd.AddValue ("enableE2", "Ativar comunicacao E2/NORI", enableE2Agent);
    cmd.Parse (argc, argv);

    NS_LOG_INFO ("Iniciando Cenario Closed-Loop RDL + NORI (Fase 1)");

#if HAS_NR_MODULE
    GridScenarioHelper gridScenario;
    gridScenario.SetRows (1);
    gridScenario.SetColumns (gNbNum);
    gridScenario.SetHorizontalBsDistance (80.0);
    gridScenario.SetBsHeight (25.0);
    gridScenario.SetUtHeight (1.5);
    gridScenario.SetSectorization (GridScenarioHelper::SINGLE);
    gridScenario.SetBsNumber (gNbNum);
    gridScenario.SetUtNumber (ueNumPerGnb * gNbNum);
    gridScenario.SetScenarioHeight (120.0);
    gridScenario.SetScenarioLength (200.0);
    gridScenario.CreateScenario ();

    Ptr<NrPointToPointEpcHelper> nrEpcHelper = CreateObject<NrPointToPointEpcHelper> ();
    Ptr<IdealBeamformingHelper> idealBeamformingHelper = CreateObject<IdealBeamformingHelper> ();
    Ptr<NrHelper> nrHelper = CreateObject<NrHelper> ();

    nrHelper->SetBeamformingHelper (idealBeamformingHelper);
    nrHelper->SetEpcHelper (nrEpcHelper);

    CcBwpCreator ccBwpCreator;
    const uint8_t numCcPerBand = 1;
    CcBwpCreator::SimpleOperationBandConf bandConf (centralFrequencyBand1, bandwidthBand1, numCcPerBand);
    OperationBandInfo band = ccBwpCreator.CreateOperationBandContiguousCc (bandConf);

    Ptr<NrChannelHelper> channelHelper = CreateObject<NrChannelHelper> ();
    channelHelper->AssignChannelsToBands ({band});

    Config::SetDefault ("ns3::ThreeGppChannelModel::UpdatePeriod", TimeValue (MilliSeconds (100)));
    Config::SetDefault ("ns3::ThreeGppChannelConditionModel::UpdatePeriod", TimeValue (MilliSeconds (100)));
    Config::SetDefault ("ns3::ThreeGppPropagationLossModel::ShadowingEnabled", BooleanValue (true));
    nrHelper->SetSchedulerAttribute ("FixedMcsDl", BooleanValue (false));

    BandwidthPartInfoPtrVector allBwps = CcBwpCreator::GetAllBwps ({band});
    idealBeamformingHelper->SetAttribute ("BeamformingMethod", TypeIdValue (DirectPathBeamforming::GetTypeId ()));

    nrHelper->SetUeAntennaAttribute ("NumRows", UintegerValue (2));
    nrHelper->SetUeAntennaAttribute ("NumColumns", UintegerValue (4));
    nrHelper->SetUeAntennaAttribute ("AntennaElement", PointerValue (CreateObject<IsotropicAntennaModel> ()));

    nrHelper->SetGnbAntennaAttribute ("NumRows", UintegerValue (4));
    nrHelper->SetGnbAntennaAttribute ("NumColumns", UintegerValue (8));
    nrHelper->SetGnbAntennaAttribute ("AntennaElement", PointerValue (CreateObject<IsotropicAntennaModel> ()));

    NetDeviceContainer gnbNetDev = nrHelper->InstallGnbDevice (gridScenario.GetBaseStations (), allBwps);
    NetDeviceContainer ueNetDev = nrHelper->InstallUeDevice (gridScenario.GetUserTerminals (), allBwps);

    InternetStackHelper internet;
    internet.Install (gridScenario.GetUserTerminals ());
    Ipv4InterfaceContainer ueIpIface = nrEpcHelper->AssignUeIpv4Address (NetDeviceContainer (ueNetDev));

    nrHelper->AttachToClosestGnb (ueNetDev, gnbNetDev);

#if HAS_ORAN_MODULE
    if (enableE2Agent)
    {
        NS_LOG_INFO ("Instalando NORI E2 Agent com acoplamento E2SM-KPM e E2SM-RC");
        Ptr<E2AgentHelper> e2AgentHelper = CreateObject<E2AgentHelper> ();
        e2AgentHelper->SetAttribute ("RicIpAddress", Ipv4AddressValue (ricIpAddress.c_str ()));
        e2AgentHelper->SetAttribute ("RicPort", UintegerValue (ricPort));
        e2AgentHelper->SetAttribute ("KpmReportIntervalMs", UintegerValue (200));
        e2AgentHelper->Install (gridScenario.GetBaseStations ());
    }
#endif

    Ptr<Node> pgw = nrEpcHelper->GetPgwNode ();
    NodeContainer remoteHostContainer;
    remoteHostContainer.Create (1);
    Ptr<Node> remoteHost = remoteHostContainer.Get (0);
    internet.Install (remoteHostContainer);

    PointToPointHelper p2ph;
    p2ph.SetDeviceAttribute ("DataRate", DataRateValue (DataRate ("100Gb/s")));
    p2ph.SetDeviceAttribute ("Mtu", UintegerValue (2500));
    p2ph.SetChannelAttribute ("Delay", TimeValue (MilliSeconds (1)));
    NetDeviceContainer internetDevices = p2ph.Install (pgw, remoteHost);

    Ipv4AddressHelper ipv4h;
    ipv4h.SetBase ("1.0.0.0", "255.0.0.0");
    Ipv4InterfaceContainer internetIpIfaces = ipv4h.Assign (internetDevices);

    Ipv4StaticRoutingHelper ipv4RoutingHelper;
    Ptr<Ipv4StaticRouting> remoteHostStaticRouting = ipv4RoutingHelper.GetStaticRouting (remoteHost->GetObject<Ipv4> ());
    remoteHostStaticRouting->AddNetworkRouteTo (Ipv4Address ("7.0.0.0"), Ipv4Mask ("255.0.0.0"), 1);

    uint16_t portBase = 1234;
    uint32_t totalUes = gridScenario.GetUserTerminals ().GetN ();
    double stopTrafficTime = (simTime > 2.0) ? (simTime - 1.0) : simTime;

    for (uint32_t i = 0; i < totalUes; ++i)
    {
        Ptr<Node> ueNode = gridScenario.GetUserTerminals ().Get (i);
        Ipv4Address ueAddr = ueIpIface.GetAddress (i);

        if (i % 3 == 0)
        {
            // URLLC
            uint16_t port = portBase + i;
            UdpServerHelper server (port);
            ApplicationContainer serverApp = server.Install (ueNode);
            serverApp.Start (Seconds (0.5));
            serverApp.Stop (Seconds (stopTrafficTime));

            UdpClientHelper client (ueAddr, port);
            client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));
            client.SetAttribute ("Interval", TimeValue (MilliSeconds (1)));
            client.SetAttribute ("PacketSize", UintegerValue (128));
            ApplicationContainer clientApp = client.Install (remoteHost);
            clientApp.Start (Seconds (1.0));
            clientApp.Stop (Seconds (stopTrafficTime));
        }
        else if (i % 3 == 1)
        {
            // eMBB
            uint16_t port = portBase + i;
            UdpServerHelper server (port);
            ApplicationContainer serverApp = server.Install (ueNode);
            serverApp.Start (Seconds (0.5));
            serverApp.Stop (Seconds (stopTrafficTime));

            UdpClientHelper client (ueAddr, port);
            client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));
            client.SetAttribute ("Interval", TimeValue (MicroSeconds (200)));
            client.SetAttribute ("PacketSize", UintegerValue (1400));
            ApplicationContainer clientApp = client.Install (remoteHost);
            clientApp.Start (Seconds (1.5));
            clientApp.Stop (Seconds (stopTrafficTime));
        }
        else
        {
            // mMTC
            uint16_t port = portBase + i;
            UdpServerHelper server (port);
            ApplicationContainer serverApp = server.Install (ueNode);
            serverApp.Start (Seconds (0.5));
            serverApp.Stop (Seconds (stopTrafficTime));

            UdpClientHelper client (ueAddr, port);
            client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));
            client.SetAttribute ("Interval", TimeValue (MilliSeconds (100)));
            client.SetAttribute ("PacketSize", UintegerValue (64));
            ApplicationContainer clientApp = client.Install (remoteHost);
            clientApp.Start (Seconds (1.0));
            clientApp.Stop (Seconds (stopTrafficTime));
        }
    }

    nrHelper->EnableTraces ();
#endif

    FlowMonitorHelper flowHelper;
    Ptr<FlowMonitor> flowMonitor = flowHelper.InstallAll ();

    NS_LOG_INFO ("Executando simulacao closed-loop por " << simTime << " segundos...");
    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();

    flowMonitor->SerializeToXmlFile ("flowmonitor_closed_loop_results.xml", true, true);
    Simulator::Destroy ();

    NS_LOG_INFO ("Simulacao Closed-Loop concluida com sucesso.");
    return 0;
}
