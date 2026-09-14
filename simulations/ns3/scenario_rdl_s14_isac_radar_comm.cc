/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fases 1 & 2
 * Arquivo: scenario_rdl_s14_isac_radar_comm.cc
 * Cenário: S14 — ISAC-Coordinated Aerial Radar-Communication Beamforming Trade-off
 * Objetivo: Avaliar divisão ótima de Pareto entre energia/feixe de radar de sensoriamento (ISAC)
 *            e capacidade de transmissão de dados eMBB (Massive MIMO 64T64R).
 * Topologia: 1 gNB 6G Massive MIMO ISAC, 20 UEs eMBB + 5 Alvos Móveis de Sensoriamento
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

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlS14IsacRadarComm");

int main (int argc, char *argv[])
{
    uint16_t commUeNum = 20;
    uint16_t radarTargetNum = 5;
    double simTime = 30.0;
    double sensingRatio = 0.30;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("commUeNum", "Quantidade de UEs de comunicacao eMBB", commUeNum);
    cmd.AddValue ("radarTargetNum", "Quantidade de alvos de sensoriamento radar", radarTargetNum);
    cmd.AddValue ("sensingRatio", "Fracao de potencia e tempo dedicada ao sensoriamento (0.0 a 0.6)", sensingRatio);
    cmd.AddValue ("simTime", "Tempo total de simulacao em segundos", simTime);
    cmd.Parse (argc, argv);

    NS_LOG_INFO ("Iniciando Cenario S14: ISAC Radar-Comm Beamforming Trade-off");

    NodeContainer isacGnb;
    isacGnb.Create (1);

    NodeContainer commUes;
    commUes.Create (commUeNum);

    NodeContainer radarTargets;
    radarTargets.Create (radarTargetNum);

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> posAlloc = CreateObject<ListPositionAllocator> ();
    posAlloc->Add (Vector (0.0, 0.0, 25.0));
    mobility.SetPositionAllocator (posAlloc);
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (isacGnb);

    MobilityHelper ueMobility;
    ueMobility.SetPositionAllocator ("ns3::RandomDiscPositionAllocator",
                                     "X", StringValue ("0.0"),
                                     "Y", StringValue ("0.0"),
                                     "Rho", StringValue ("ns3::UniformRandomVariable[Min=30.0|Max=200.0]"));
    ueMobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    ueMobility.Install (commUes);

    MobilityHelper targetMobility;
    targetMobility.SetMobilityModel ("ns3::ConstantVelocityMobilityModel");
    targetMobility.Install (radarTargets);

    for (uint16_t i = 0; i < radarTargetNum; ++i)
    {
        Ptr<ConstantVelocityMobilityModel> cvm = radarTargets.Get (i)->GetObject<ConstantVelocityMobilityModel> ();
        cvm->SetPosition (Vector (50.0 + i * 20.0, 50.0 + i * 20.0, 50.0));
        cvm->SetVelocity (Vector (15.0, 10.0, 0.0));
    }

    InternetStackHelper internet;
    internet.Install (isacGnb);
    internet.Install (commUes);
    internet.Install (radarTargets);

    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();
    Simulator::Destroy ();

    std::cout << "Cenario S14 (ISAC Radar-Comm Beamforming) executado com sucesso." << std::endl;
    return 0;
}
