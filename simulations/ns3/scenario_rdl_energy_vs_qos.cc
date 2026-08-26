/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL Determinística)
 * Arquivo: scenario_rdl_energy_vs_qos.cc
 * Descrição: Cenário de Simulação 5G-LENA + ns-O-RAN / NORI
 *            Avaliação de Arbitragem EEVS (Eficiência Energética vs Garantia de SLA URLLC)
 * Topologia: 1 Macro gNB (Banda Alta) + 1 Micro gNB (Economia de Energia), 20 UEs com Carga Dinâmica
 * =========================================================================================
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/nr-module.h"
#include "ns3/applications-module.h"

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

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlEnergyVsQos");

int main (int argc, char *argv[])
{
    uint16_t gNbNum = 2;
    uint16_t ueNum = 20;
    double simTime = 40.0;
    double centralFreq = 3.5e9;
    double bandwidth = 50e6;
    std::string ricIp = "172.18.0.4";
    uint16_t ricPort = 36422;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("simTime", "Tempo de simulação em segundos", simTime);
    cmd.AddValue ("ricIp", "IP do Near-RT RIC E2Term", ricIp);
    cmd.AddValue ("ricPort", "Porta SCTP do E2Term", ricPort);
    cmd.Parse (argc, argv);

    NS_LOG_INFO ("Iniciando Cenário RDL Fase 1 - EEVS (Energy Saving vs SLA URLLC)...");

    // Grid com 2 células (Macro + Small Cell com 50m de separação)
    GridScenarioHelper gridScenario;
    gridScenario.SetRows (1);
    gridScenario.SetColumns (gNbNum);
    gridScenario.SetHorizontalBsDistance (50.0);
    gridScenario.SetBsHeight (15.0);
    gridScenario.SetUtHeight (1.5);
    gridScenario.SetSectorization (GridScenarioHelper::SINGLE);
    gridScenario.SetBsNumber (gNbNum);
    gridScenario.SetUtNumber (ueNum);
    gridScenario.SetScenarioHeight (80.0);
    gridScenario.SetScenarioLength (100.0);
    gridScenario.CreateScenario ();

    Ptr<NrPointToPointEpcHelper> nrEpcHelper = CreateObject<NrPointToPointEpcHelper> ();
    Ptr<IdealBeamformingHelper> idealBeamformingHelper = CreateObject<IdealBeamformingHelper> ();
    Ptr<NrHelper> nrHelper = CreateObject<NrHelper> ();

    nrHelper->SetBeamformingHelper (idealBeamformingHelper);
    nrHelper->SetEpcHelper (nrEpcHelper);

    CcBwpCreator ccBwpCreator;
    CcBwpCreator::SimpleOperationBandConf bandConf (centralFreq, bandwidth, 1, BandwidthPartInfo::UMi_StreetCanyon_LoS);
    OperationBandInfo band = ccBwpCreator.CreateOperationBandContiguousCc (bandConf);

    nrHelper->InitializeOperationBand (&band);
    BandwidthPartInfoPtrVector allBwps = CcBwpCreator::GetAllBwps ({band});

    idealBeamformingHelper->SetAttribute ("BeamformingMethod", TypeIdValue (DirectPathBeamforming::GetTypeId ()));

    NetDeviceContainer gnbNetDev = nrHelper->InstallGnbDevice (gridScenario.GetBaseStations (), allBwps);
    NetDeviceContainer ueNetDev = nrHelper->InstallUeDevice (gridScenario.GetUserTerminals (), allBwps);

    for (auto it = gnbNetDev.Begin (); it != gnbNetDev.End (); ++it)
    {
        DynamicCast<NrGnbNetDevice> (*it)->UpdateConfig ();
    }
    for (auto it = ueNetDev.Begin (); it != ueNetDev.End (); ++it)
    {
        DynamicCast<NrUeNetDevice> (*it)->UpdateConfig ();
    }

    InternetStackHelper internet;
    internet.Install (gridScenario.GetUserTerminals ());
    Ipv4InterfaceContainer ueIpIface = nrEpcHelper->AssignUeIpv4Address (NetDeviceContainer (ueNetDev));

    nrHelper->AttachToClosestGnb (ueNetDev, gnbNetDev);

#if HAS_ORAN_MODULE
    Ptr<E2AgentHelper> e2AgentHelper = CreateObject<E2AgentHelper> ();
    e2AgentHelper->SetAttribute ("RicIpAddress", Ipv4AddressValue (ricIp.c_str ()));
    e2AgentHelper->SetAttribute ("RicPort", UintegerValue (ricPort));
    e2AgentHelper->SetAttribute ("KpmReportIntervalMs", UintegerValue (200));
    e2AgentHelper->Install (gridScenario.GetBaseStations ());
#endif

    // Tráfego Flutuante com Rajadas de Alta Prioridade
    for (uint32_t i = 0; i < ueNum; ++i)
    {
        Ptr<Node> ueNode = gridScenario.GetUserTerminals ().Get (i);
        Ipv4Address ueAddr = ueIpIface.GetAddress (i);
        uint16_t port = 5000 + i;

        UdpServerHelper server (port);
        ApplicationContainer serverApp = server.Install (ueNode);
        serverApp.Start (Seconds (1.0));
        serverApp.Stop (Seconds (simTime - 1.0));

        // Metade dos UEs recebem rajada crítica entre 10s e 25s
        UdpClientHelper client (ueAddr, port);
        if (i < 10)
        {
            client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));
            client.SetAttribute ("Interval", TimeValue (MilliSeconds (2))); // URLLC
            client.SetAttribute ("PacketSize", UintegerValue (256));
            ApplicationContainer clientApp = client.Install (gridScenario.GetBaseStations ().Get (1));
            clientApp.Start (Seconds (10.0));
            clientApp.Stop (Seconds (25.0));
        }
        else
        {
            client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));
            client.SetAttribute ("Interval", TimeValue (MilliSeconds (20))); // Tráfego de Fundo
            client.SetAttribute ("PacketSize", UintegerValue (512));
            ApplicationContainer clientApp = client.Install (gridScenario.GetBaseStations ().Get (0));
            clientApp.Start (Seconds (2.0));
            clientApp.Stop (Seconds (simTime - 2.0));
        }
    }

    nrHelper->EnableTraces ();

    NS_LOG_INFO ("Executando simulação EEVS por " << simTime << "s...");
    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();
    Simulator::Destroy ();
    NS_LOG_INFO ("Simulação EEVS concluída.");
    return 0;
}
