/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL Determinística)
 * Arquivo: scenario_rdl_tvs_conflict.cc
 * Descrição: Cenário de Simulação 5G-LENA + ns-O-RAN / NORI
 *            Avaliação de Arbitragem de Conflitos Multiobjetivo (TVS: URLLC vs eMBB vs mMTC)
 * Topologia: 2 gNodeBs 5G NR (Macro + Micro), 30 UEs divididos em 3 Fatias de Rede
 * =========================================================================================
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/nr-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"

// Inclusão condicional dos cabeçalhos do módulo E2 / ns-O-RAN
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

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlTvsConflict");

// Callbacks de Rastreamento de Métricas (PDCP / RLC)
void RxPdcpCallback (std::string path, uint16_t rnti, uint8_t lcid, uint32_t bytes, double delay)
{
    NS_LOG_INFO ("[PDCP RX] RNTI: " << rnti << " LCID: " << (uint32_t)lcid << " Bytes: " << bytes << " Latencia: " << delay * 1000.0 << " ms");
}

int main (int argc, char *argv[])
{
    // =========================================================================
    // 1. Parâmetros Configuráveis via Linha de Comando
    // =========================================================================
    uint16_t gNbNum = 2;                     // Número de estações base (gNBs)
    uint16_t ueNumPerGnb = 15;               // Número de UEs por gNB (Total = 30 UEs)
    double simTime = 30.0;                   // Tempo total de simulação (segundos)
    double centralFrequencyBand1 = 3.5e9;    // Banda 1: 3.5 GHz (FR1 n78)
    double bandwidthBand1 = 100e6;           // Largura de banda: 100 MHz
    uint16_t numerologyBwp1 = 1;             // Numerologia 5G NR: 1 (SCS = 30 kHz)
    std::string ricIpAddress = "172.18.0.4"; // Endereço IP do Near-RT RIC (E2Term)
    uint16_t ricPort = 36422;                // Porta SCTP do E2Term O-RAN
    bool enableE2Agent = true;               // Habilitar agente E2AP para Near-RT RIC

    CommandLine cmd (__FILE__);
    cmd.AddValue ("gNbNum", "Número de gNodeBs", gNbNum);
    cmd.AddValue ("ueNumPerGnb", "Número de UEs por gNB", ueNumPerGnb);
    cmd.AddValue ("simTime", "Tempo de simulação em segundos", simTime);
    cmd.AddValue ("centralFrequency", "Frequência central em Hz (padrão 3.5GHz)", centralFrequencyBand1);
    cmd.AddValue ("bandwidth", "Largura de banda em Hz (padrão 100MHz)", bandwidthBand1);
    cmd.AddValue ("ricIp", "IP do E2Term no Near-RT RIC", ricIpAddress);
    cmd.AddValue ("ricPort", "Porta SCTP do E2Term", ricPort);
    cmd.AddValue ("enableE2", "Ativar interface O-RAN E2", enableE2Agent);
    cmd.Parse (argc, argv);

    NS_LOG_INFO ("Iniciando Cenário RDL Fase 1 - TVS Conflict Mitigation...");
    NS_LOG_INFO ("gNBs: " << gNbNum << " | Total UEs: " << (gNbNum * ueNumPerGnb) << " | Banda: " << (bandwidthBand1 / 1e6) << " MHz");

    // =========================================================================
    // 2. Criação da Topologia e Grid de Nós
    // =========================================================================
    GridScenarioHelper gridScenario;
    gridScenario.SetRows (1);
    gridScenario.SetColumns (gNbNum);
    gridScenario.SetHorizontalBsDistance (80.0); // Distância de 80m entre gNBs (Área de sobreposição intensa)
    gridScenario.SetBsHeight (25.0);              // Altura das gNBs: 25m
    gridScenario.SetUtHeight (1.5);               // Altura dos terminais de usuário: 1.5m
    gridScenario.SetSectorization (GridScenarioHelper::SINGLE);
    gridScenario.SetBsNumber (gNbNum);
    gridScenario.SetUtNumber (ueNumPerGnb * gNbNum);
    gridScenario.SetScenarioHeight (120.0);
    gridScenario.SetScenarioLength (200.0);
    gridScenario.CreateScenario ();

    // =========================================================================
    // 3. Configuração dos Helpers 5G-LENA (NR & EPC)
    // =========================================================================
    Ptr<NrPointToPointEpcHelper> nrEpcHelper = CreateObject<NrPointToPointEpcHelper> ();
    Ptr<IdealBeamformingHelper> idealBeamformingHelper = CreateObject<IdealBeamformingHelper> ();
    Ptr<NrHelper> nrHelper = CreateObject<NrHelper> ();

    nrHelper->SetBeamformingHelper (idealBeamformingHelper);
    nrHelper->SetEpcHelper (nrEpcHelper);

    // Configuração de Bandwidth Part (BWP) e Canal 3GPP
    CcBwpCreator ccBwpCreator;
    const uint8_t numCcPerBand = 1;
    CcBwpCreator::SimpleOperationBandConf bandConf (centralFrequencyBand1,
                                                   bandwidthBand1,
                                                   numCcPerBand,
                                                   BandwidthPartInfo::UMi_StreetCanyon_LoS);
    OperationBandInfo band = ccBwpCreator.CreateOperationBandContiguousCc (bandConf);

    Config::SetDefault ("ns3::ThreeGppChannelModel::UpdatePeriod", TimeValue (MilliSeconds (100)));
    nrHelper->SetChannelConditionModelAttribute ("UpdatePeriod", TimeValue (MilliSeconds (100)));
    nrHelper->SetPathlossAttribute ("ShadowingEnabled", BooleanValue (true));
    nrHelper->SetSchedulerAttribute ("FixedMcsDl", BooleanValue (false)); // MCS adaptativo baseado em CQI

    nrHelper->InitializeOperationBand (&band);
    BandwidthPartInfoPtrVector allBwps = CcBwpCreator::GetAllBwps ({band});

    // Configuração de Antenas (MIMO / Beamforming)
    idealBeamformingHelper->SetAttribute ("BeamformingMethod", TypeIdValue (DirectPathBeamforming::GetTypeId ()));

    // Antenas UE: Matriz 2x4 (8 elementos)
    nrHelper->SetUeAntennaAttribute ("NumRows", UintegerValue (2));
    nrHelper->SetUeAntennaAttribute ("NumColumns", UintegerValue (4));
    nrHelper->SetUeAntennaAttribute ("AntennaElement", PointerValue (CreateObject<IsotropicAntennaModel> ()));

    // Antenas gNB: Matriz 4x8 (32 elementos)
    nrHelper->SetGnbAntennaAttribute ("NumRows", UintegerValue (4));
    nrHelper->SetGnbAntennaAttribute ("NumColumns", UintegerValue (8));
    nrHelper->SetGnbAntennaAttribute ("AntennaElement", PointerValue (CreateObject<IsotropicAntennaModel> ()));

    // =========================================================================
    // 4. Instalação dos Dispositivos de Rede (NetDevices)
    // =========================================================================
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

    // Instalação da Pilha de Internet e Atribuição de Endereços IP
    InternetStackHelper internet;
    internet.Install (gridScenario.GetUserTerminals ());
    Ipv4InterfaceContainer ueIpIface = nrEpcHelper->AssignUeIpv4Address (NetDeviceContainer (ueNetDev));

    // Associação dos UEs às gNBs mais próximas
    nrHelper->AttachToClosestGnb (ueNetDev, gnbNetDev);

    // =========================================================================
    // 5. Instalação do Agente O-RAN E2 (ns-O-RAN / NORI)
    // =========================================================================
#if HAS_ORAN_MODULE
    if (enableE2Agent)
    {
        NS_LOG_INFO ("Instalando E2 Agent nas gNBs conectando a " << ricIpAddress << ":" << ricPort);
        Ptr<E2AgentHelper> e2AgentHelper = CreateObject<E2AgentHelper> ();
        e2AgentHelper->SetAttribute ("RicIpAddress", Ipv4AddressValue (ricIpAddress.c_str ()));
        e2AgentHelper->SetAttribute ("RicPort", UintegerValue (ricPort));
        e2AgentHelper->SetAttribute ("KpmReportIntervalMs", UintegerValue (200)); // Intervalo alinhado à Decision Window (200ms)
        e2AgentHelper->Install (gridScenario.GetBaseStations ());
    }
#else
    NS_LOG_WARN ("Módulo ns-O-RAN não detectado no include path. Rodando simulação em modo RAN Standalone.");
#endif

    // =========================================================================
    // 6. Geração de Tráfego Diferenciado por Fatia de Serviço (Slicing)
    // =========================================================================
    uint16_t portBase = 1234;
    uint32_t totalUes = gridScenario.GetUserTerminals ().GetN ();

    for (uint32_t i = 0; i < totalUes; ++i)
    {
        Ptr<Node> ueNode = gridScenario.GetUserTerminals ().Get (i);
        Ipv4Address ueAddr = ueIpIface.GetAddress (i);

        if (i % 3 == 0)
        {
            // Fatia 1: URLLC (Ultra-Reliable Low-Latency Communication)
            // Pacotes pequenos (128B) em alta frequência (1ms) - Prioridade Máxima
            uint16_t port = portBase + i;
            UdpServerHelper server (port);
            ApplicationContainer serverApp = server.Install (ueNode);
            serverApp.Start (Seconds (1.0));
            serverApp.Stop (Seconds (simTime - 1.0));

            UdpClientHelper client (ueAddr, port);
            client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));
            client.SetAttribute ("Interval", TimeValue (MilliSeconds (1)));
            client.SetAttribute ("PacketSize", UintegerValue (128));
            ApplicationContainer clientApp = client.Install (gridScenario.GetBaseStations ().Get (0));
            clientApp.Start (Seconds (1.5));
            clientApp.Stop (Seconds (simTime - 1.0));
        }
        else if (i % 3 == 1)
        {
            // Fatia 2: eMBB (Enhanced Mobile Broadband)
            // Streaming de alta vazão (1400B a cada 0.2ms ~ 56 Mbps)
            uint16_t port = portBase + i;
            UdpServerHelper server (port);
            ApplicationContainer serverApp = server.Install (ueNode);
            serverApp.Start (Seconds (1.0));
            serverApp.Stop (Seconds (simTime - 1.0));

            UdpClientHelper client (ueAddr, port);
            client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));
            client.SetAttribute ("Interval", TimeValue (MicroSeconds (200)));
            client.SetAttribute ("PacketSize", UintegerValue (1400));
            ApplicationContainer clientApp = client.Install (gridScenario.GetBaseStations ().Get (0));
            clientApp.Start (Seconds (2.0));
            clientApp.Stop (Seconds (simTime - 1.0));
        }
        else
        {
            // Fatia 3: mMTC (Massive Machine Type Communication)
            // Telemetria IoT periódica (64B a cada 100ms)
            uint16_t port = portBase + i;
            UdpServerHelper server (port);
            ApplicationContainer serverApp = server.Install (ueNode);
            serverApp.Start (Seconds (1.0));
            serverApp.Stop (Seconds (simTime - 1.0));

            UdpClientHelper client (ueAddr, port);
            client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));
            client.SetAttribute ("Interval", TimeValue (MilliSeconds (100)));
            client.SetAttribute ("PacketSize", UintegerValue (64));
            ApplicationContainer clientApp = client.Install (gridScenario.GetBaseStations ().Get (1));
            clientApp.Start (Seconds (1.0));
            clientApp.Stop (Seconds (simTime - 1.0));
        }
    }

    // =========================================================================
    // 7. Rastreamento, FlowMonitor e Execução da Simulação
    // =========================================================================
    nrHelper->EnableTraces ();
    Config::Connect ("/NodeList/*/DeviceList/*/$ns3::NrUeNetDevice/ComponentCarrierMapUe/*/NrUePhy/ReportCurrentCellRsrpSinr",
                     MakeCallback (&RxPdcpCallback));

    FlowMonitorHelper flowHelper;
    Ptr<FlowMonitor> flowMonitor = flowHelper.InstallAll ();

    NS_LOG_INFO ("Executando simulação por " << simTime << " segundos...");
    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();

    flowMonitor->SerializeToXmlFile ("flowmonitor_results.xml", true, true);
    Simulator::Destroy ();

    NS_LOG_INFO ("Simulação concluída com sucesso. Métricas de fluxo salvas em flowmonitor_results.xml.");
    return 0;
}

