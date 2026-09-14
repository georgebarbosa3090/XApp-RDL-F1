/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fases 1 & 2
 * Arquivo: scenario_rdl_s10_uav_swarm_battery.cc
 * Cenário: S10 — UAV Flying gNodeB Swarm & Battery Depletion Emergency Handover
 * Objetivo: Avaliar arbitragem de emergência para descarregamento em cascata de UEs
 *            quando um UAV atinge nível crítico de bateria (< 10%).
 * Topologia: 4 UAVs gNodeBs formando malha aérea (100m altitude), 40 UEs no solo
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

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlS10UavSwarmBattery");

int main (int argc, char *argv[])
{
    uint16_t uavNum = 4;
    uint16_t ueNum = 40;
    double simTime = 30.0;
    double uavAltitudeMeters = 100.0;
    std::string ricIp = "127.0.0.1";
    uint16_t ricPort = 36422;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("uavNum", "Quantidade de UAVs no enxame", uavNum);
    cmd.AddValue ("ueNum", "Quantidade total de UEs no solo", ueNum);
    cmd.AddValue ("simTime", "Tempo total de simulacao em segundos", simTime);
    cmd.AddValue ("ricIp", "Endereco IP do Near-RT RIC", ricIp);
    cmd.AddValue ("ricPort", "Porta SCTP do servico E2Term", ricPort);
    cmd.Parse (argc, argv);

    NS_LOG_INFO ("Iniciando Cenario S10: UAV Swarm Battery Emergency Handover");

    NodeContainer uavNodes;
    uavNodes.Create (uavNum);

    NodeContainer ueNodes;
    ueNodes.Create (ueNum);

    MobilityHelper uavMobility;
    Ptr<ListPositionAllocator> posAlloc = CreateObject<ListPositionAllocator> ();
    posAlloc->Add (Vector (100.0, 100.0, uavAltitudeMeters));
    posAlloc->Add (Vector (300.0, 100.0, uavAltitudeMeters));
    posAlloc->Add (Vector (100.0, 300.0, uavAltitudeMeters));
    posAlloc->Add (Vector (300.0, 300.0, uavAltitudeMeters));
    uavMobility.SetPositionAllocator (posAlloc);
    uavMobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    uavMobility.Install (uavNodes);

    MobilityHelper ueMobility;
    ueMobility.SetPositionAllocator ("ns3::RandomRectanglePositionAllocator",
                                     "X", StringValue ("ns3::UniformRandomVariable[Min=50.0|Max=350.0]"),
                                     "Y", StringValue ("ns3::UniformRandomVariable[Min=50.0|Max=350.0]"));
    ueMobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    ueMobility.Install (ueNodes);

    InternetStackHelper internet;
    internet.Install (uavNodes);
    internet.Install (ueNodes);

    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();
    Simulator::Destroy ();

    std::cout << "Cenario S10 (UAV Swarm Battery Emergency) executado com sucesso." << std::endl;
    return 0;
}
