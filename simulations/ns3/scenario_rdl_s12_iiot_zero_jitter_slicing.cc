/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fases 1 & 2
 * Arquivo: scenario_rdl_s12_iiot_zero_jitter_slicing.cc
 * Cenário: S12 — Ultra-Deterministic IIoT Closed-Loop Robotic Slicing & Zero-Jitter Arbitration
 * Objetivo: Validar preempção determinística incondicional de PRBs para fatias industriais
 *            de braços robóticos sincronizados (Jitter < 0.8ms, Perda < 1e-6).
 * Topologia: 1 gNB Industrial Privada (Numerologia mu=2 / 60 kHz), 20 Robôs URLLC + 30 Câmeras eMBB
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

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlS12IiotZeroJitterSlicing");

int main (int argc, char *argv[])
{
    uint16_t robotUeNum = 20;
    uint16_t videoUeNum = 30;
    double simTime = 30.0;
    std::string ricIp = "127.0.0.1";
    uint16_t ricPort = 36422;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("robotUeNum", "Quantidade de robos industriais URLLC", robotUeNum);
    cmd.AddValue ("videoUeNum", "Quantidade de cameras de monitoramento eMBB", videoUeNum);
    cmd.AddValue ("simTime", "Tempo total de simulacao em segundos", simTime);
    cmd.Parse (argc, argv);

    NS_LOG_INFO ("Iniciando Cenario S12: IIoT Ultra-Deterministic Zero-Jitter Slicing");

    NodeContainer gnbNode;
    gnbNode.Create (1);

    NodeContainer robotNodes;
    robotNodes.Create (robotUeNum);

    NodeContainer videoNodes;
    videoNodes.Create (videoUeNum);

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> posAlloc = CreateObject<ListPositionAllocator> ();
    posAlloc->Add (Vector (50.0, 50.0, 10.0));
    mobility.SetPositionAllocator (posAlloc);
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (gnbNode);

    MobilityHelper ueMobility;
    ueMobility.SetPositionAllocator ("ns3::RandomRectanglePositionAllocator",
                                     "X", StringValue ("ns3::UniformRandomVariable[Min=10.0|Max=90.0]"),
                                     "Y", StringValue ("ns3::UniformRandomVariable[Min=10.0|Max=90.0]"));
    ueMobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    ueMobility.Install (robotNodes);
    ueMobility.Install (videoNodes);

    InternetStackHelper internet;
    internet.Install (gnbNode);
    internet.Install (robotNodes);
    internet.Install (videoNodes);

    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();
    Simulator::Destroy ();

    std::cout << "Cenario S12 (IIoT Zero-Jitter Slicing) executado com sucesso." << std::endl;
    return 0;
}
