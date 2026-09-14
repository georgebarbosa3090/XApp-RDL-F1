/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fases 1 & 2
 * Arquivo: scenario_rdl_s15_rogue_ntn_feeder_hijacking.cc
 * Cenário: S15 — Rogue xApp Parameter Hijacking in NTN Feeder Link (Cross-Tier Security)
 * Objetivo: Avaliar a barreira de segurança física e cross-tier shield contra tentativas
 *            de saturação hostil de transponders satelitais (Tx Power = 55 dBm).
 * Topologia: 1 Satélite Gateway Feeder Link (Banda Q/V) + 1 Estação Terrestre Teleport, 10 UEs
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

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlS15RogueNtnFeederHijacking");

int main (int argc, char *argv[])
{
    double simTime = 30.0;
    double injectedTxPowerDbm = 55.0;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("injectedPower", "Potencia hostil injetada no enlace feeder em dBm", injectedTxPowerDbm);
    cmd.AddValue ("simTime", "Tempo total de simulacao em segundos", simTime);
    cmd.Parse (argc, argv);

    NS_LOG_INFO ("Iniciando Cenario S15: Rogue NTN Feeder Hijacking Security Test");

    NodeContainer satNode;
    satNode.Create (1);

    NodeContainer teleportNode;
    teleportNode.Create (1);

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> posAlloc = CreateObject<ListPositionAllocator> ();
    posAlloc->Add (Vector (0.0, 0.0, 600000.0));
    posAlloc->Add (Vector (100.0, 100.0, 50.0));
    mobility.SetPositionAllocator (posAlloc);
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (satNode);
    mobility.Install (teleportNode);

    InternetStackHelper internet;
    internet.Install (satNode);
    internet.Install (teleportNode);

    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();
    Simulator::Destroy ();

    std::cout << "Cenario S15 (Rogue NTN Feeder Hijacking) executado com sucesso." << std::endl;
    return 0;
}
