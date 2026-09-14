/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fases 1 & 2
 * Arquivo: scenario_rdl_s11_v2x_highway_platooning.cc
 * Cenário: S11 — High-Speed V2X Highway Platooning & Multi-Cell Ping-Pong Storm
 * Objetivo: Avaliar handover preditivo contínuo para comboios de veículos (Platooning)
 *            a 120 km/h com small cells rodoviárias a cada 500m.
 * Topologia: 4 RSUs (Roadside Units / gNBs), 10 veículos em comboio (distância 10m)
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

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlS11V2xHighwayPlatooning");

int main (int argc, char *argv[])
{
    uint16_t rsuNum = 4;
    uint16_t vehicleNum = 10;
    double simTime = 30.0;
    double vehicleSpeedKmh = 120.0;
    std::string ricIp = "127.0.0.1";
    uint16_t ricPort = 36422;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("vehicleNum", "Quantidade de veiculos no comboio", vehicleNum);
    cmd.AddValue ("vehicleSpeedKmh", "Velocidade dos veiculos em km/h", vehicleSpeedKmh);
    cmd.AddValue ("simTime", "Tempo total de simulacao em segundos", simTime);
    cmd.Parse (argc, argv);

    NS_LOG_INFO ("Iniciando Cenario S11: High-Speed V2X Highway Platooning");

    NodeContainer rsuNodes;
    rsuNodes.Create (rsuNum);

    NodeContainer vehicleNodes;
    vehicleNodes.Create (vehicleNum);

    MobilityHelper rsuMobility;
    Ptr<ListPositionAllocator> rsuPos = CreateObject<ListPositionAllocator> ();
    for (uint16_t i = 0; i < rsuNum; ++i)
    {
        rsuPos->Add (Vector (i * 500.0, 10.0, 15.0));
    }
    rsuMobility.SetPositionAllocator (rsuPos);
    rsuMobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    rsuMobility.Install (rsuNodes);

    double speedMs = vehicleSpeedKmh / 3.6;
    MobilityHelper vehicleMobility;
    vehicleMobility.SetMobilityModel ("ns3::ConstantVelocityMobilityModel");
    vehicleMobility.Install (vehicleNodes);

    for (uint16_t j = 0; j < vehicleNum; ++j)
    {
        Ptr<ConstantVelocityMobilityModel> cvm = vehicleNodes.Get (j)->GetObject<ConstantVelocityMobilityModel> ();
        cvm->SetPosition (Vector (j * (-15.0), 0.0, 1.5));
        cvm->SetVelocity (Vector (speedMs, 0.0, 0.0));
    }

    InternetStackHelper internet;
    internet.Install (rsuNodes);
    internet.Install (vehicleNodes);

    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();
    Simulator::Destroy ();

    std::cout << "Cenario S11 (High-Speed V2X Highway Platooning) executado com sucesso." << std::endl;
    return 0;
}
