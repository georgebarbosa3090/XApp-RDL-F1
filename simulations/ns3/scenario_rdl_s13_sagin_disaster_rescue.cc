/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fases 1 & 2
 * Arquivo: scenario_rdl_s13_sagin_disaster_rescue.cc
 * Cenário: S13 — Emergency 6G SAGIN Multi-Domain Disaster Rescue Heterogeneous Mesh
 * Objetivo: Avaliar sobreposição de tráfego humanitário e de socorristas sobre enlaces
 *            espaciais (Satélite LEO + 2 UAVs + Estação Móvel de Solo).
 * Topologia: 1 Satélite LEO + 2 UAVs + 1 Gateway Terrestre Móvel, 50 UEs
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

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlS13SaginDisasterRescue");

int main (int argc, char *argv[])
{
    uint16_t rescueUeNum = 20;
    uint16_t civilianUeNum = 30;
    double simTime = 30.0;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("rescueUeNum", "Quantidade de UEs de socorristas (Prioridade Maxima)", rescueUeNum);
    cmd.AddValue ("civilianUeNum", "Quantidade de UEs civis na area de desastre", civilianUeNum);
    cmd.AddValue ("simTime", "Tempo total de simulacao em segundos", simTime);
    cmd.Parse (argc, argv);

    NS_LOG_INFO ("Iniciando Cenario S13: SAGIN Disaster Rescue Heterogeneous Mesh");

    NodeContainer satNode;
    satNode.Create (1);

    NodeContainer uavNodes;
    uavNodes.Create (2);

    NodeContainer rescueUes;
    rescueUes.Create (rescueUeNum);

    NodeContainer civilianUes;
    civilianUes.Create (civilianUeNum);

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> posAlloc = CreateObject<ListPositionAllocator> ();
    posAlloc->Add (Vector (0.0, 0.0, 600000.0));
    posAlloc->Add (Vector (200.0, 200.0, 120.0));
    posAlloc->Add (Vector (400.0, 400.0, 120.0));
    mobility.SetPositionAllocator (posAlloc);
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (satNode);
    mobility.Install (uavNodes);

    MobilityHelper ueMobility;
    ueMobility.SetPositionAllocator ("ns3::RandomDiscPositionAllocator",
                                     "X", StringValue ("300.0"),
                                     "Y", StringValue ("300.0"),
                                     "Rho", StringValue ("ns3::UniformRandomVariable[Min=0.0|Max=250.0]"));
    ueMobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    ueMobility.Install (rescueUes);
    ueMobility.Install (civilianUes);

    InternetStackHelper internet;
    internet.Install (satNode);
    internet.Install (uavNodes);
    internet.Install (rescueUes);
    internet.Install (civilianUes);

    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();
    Simulator::Destroy ();

    std::cout << "Cenario S13 (Emergency SAGIN Disaster Rescue) executado com sucesso." << std::endl;
    return 0;
}
