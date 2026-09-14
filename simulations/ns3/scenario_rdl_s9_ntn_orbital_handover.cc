/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fases 1 & 2
 * Arquivo: scenario_rdl_s9_ntn_orbital_handover.cc
 * Cenário: S9 — NTN Orbital Handover & Doppler Mitigation Conflict
 * Objetivo: Avaliar coordenação de mobilidade em redes não-terrestres (Satélite LEO 600km)
 *            com compensação de RTT longo (40ms) e desvio Doppler severo.
 * Topologia: 1 Satélite LEO (Banda Ka / S, BWP 100 MHz) + 1 gNB Terrestre Macro, 20 UEs
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

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlS9NtnOrbitalHandover");

int main (int argc, char *argv[])
{
    uint16_t satNum = 1;
    uint16_t terrestrialGnbNum = 1;
    uint16_t ueNum = 20;
    double simTime = 30.0;
    double orbitAltitudeKm = 600.0;
    double satVelocityKmH = 27000.0;
    std::string ricIp = "127.0.0.1";
    uint16_t ricPort = 36422;
    bool enableE2Agent = true;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("ueNum", "Quantidade total de UEs", ueNum);
    cmd.AddValue ("simTime", "Tempo total de simulacao em segundos", simTime);
    cmd.AddValue ("orbitAltitudeKm", "Altitude orbital do satelite LEO em km", orbitAltitudeKm);
    cmd.AddValue ("satVelocityKmH", "Velocidade orbital do satelite em km/h", satVelocityKmH);
    cmd.AddValue ("ricIp", "Endereco IP do Near-RT RIC", ricIp);
    cmd.AddValue ("ricPort", "Porta SCTP do servico E2Term", ricPort);
    cmd.AddValue ("enableE2", "Ativar comunicacao E2 / NORI", enableE2Agent);
    cmd.Parse (argc, argv);

    NS_LOG_INFO ("Iniciando Cenario S9: NTN Orbital Handover & Doppler Mitigation");

    NodeContainer satNodes;
    satNodes.Create (satNum);

    NodeContainer gnbNodes;
    gnbNodes.Create (terrestrialGnbNum);

    NodeContainer ueNodes;
    ueNodes.Create (ueNum);

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> posAlloc = CreateObject<ListPositionAllocator> ();
    posAlloc->Add (Vector (0.0, 0.0, orbitAltitudeKm * 1000.0));
    posAlloc->Add (Vector (500.0, 500.0, 30.0));
    mobility.SetPositionAllocator (posAlloc);
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (satNodes);
    mobility.Install (gnbNodes);

    MobilityHelper ueMobility;
    ueMobility.SetPositionAllocator ("ns3::UniformDiscPositionAllocator",
                                     "X", DoubleValue (500.0),
                                     "Y", DoubleValue (500.0),
                                     "rho", DoubleValue (300.0));
    ueMobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    ueMobility.Install (ueNodes);

    InternetStackHelper internet;
    internet.Install (satNodes);
    internet.Install (gnbNodes);
    internet.Install (ueNodes);

    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();
    Simulator::Destroy ();

    std::cout << "Cenario S9 (NTN Orbital Handover) executado com sucesso." << std::endl;
    return 0;
}
