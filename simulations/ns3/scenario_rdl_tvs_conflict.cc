/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL Deterministica)
 * Arquivo: scenario_rdl_tvs_conflict.cc
 * Descricao: Cenario de Simulacao 5G-LENA + ns-O-RAN / NORI
 *            Avaliacao de Arbitragem de Conflitos Multiobjetivo (TVS: URLLC vs eMBB vs mMTC)
 * Topologia: 2 gNodeBs 5G NR (Macro + Micro), 30 UEs divididos em 3 Fatias de Rede
 * =========================================================================================
 */

// Inclusao dos modulos estruturais do simulador de eventos discretos ns-3
#include "ns3/core-module.h"             // Modulo central: gerenciador de eventos, agendamento temporal, logs e atributos
#include "ns3/network-module.h"          // Modulo de rede basico: abstracoes de nos (Node), pacotes (Packet) e interfaces
#include "ns3/internet-module.h"         // Modulo de pilha IP: protocolos IPv4/IPv6, tabelas de roteamento e sockets
#include "ns3/mobility-module.h"         // Modulo de mobilidade: posicionamento geografico e modelos de propagacao espacial
#include "ns3/antenna-module.h"          // Modulo de antenas: configuracao de diagramas de radiacao e matrizes de feixe
#include "ns3/point-to-point-module.h"   // Modulo de canal ponto a ponto: enlaces cabeados para interconexao e fallback
#include "ns3/applications-module.h"     // Modulo de aplicacoes de rede: clientes e servidores UDP/TCP
#include "ns3/flow-monitor-module.h"     // Modulo de monitoramento de fluxo: extracao analitica de metricas de QoS/QoE

// Inclusao condicional do modulo 5G-LENA (CTTC-LENA New Radio)
#if __has_include("ns3/nr-module.h")
#include "ns3/nr-module.h"               // Modulo 5G NR: camadas PHY, MAC, RLC, PDCP, SDAP, BWP e Beamforming
#define HAS_NR_MODULE 1                  // Flag de compilacao indicando suporte completo ao 5G NR
#else
#define HAS_NR_MODULE 0                  // Flag indicando operacao em modo alternativo
#endif

// Inclusao condicional dos cabecalhos de comunicacao O-RAN E2 (ns-O-RAN / NORI)
#if __has_include("ns3/oran-interface.h")
#include "ns3/oran-interface.h"          // Interface unificada ns-O-RAN
#define HAS_ORAN_MODULE 1                // Flag indicando disponibilidade de comunicacao E2
#elif __has_include("ns3/e2-agent-helper.h")
#include "ns3/e2-agent-helper.h"         // Helper de instanciacao do agente E2AP
#define HAS_ORAN_MODULE 1                // Flag indicando agente E2 disponivel
#else
#define HAS_ORAN_MODULE 0                // Flag indicando operacao sem conexao com Near-RT RIC
#endif

// Importacao do namespace global do ns-3
using namespace ns3;

// Definicao do componente de log do ns-3 para mensagens de depuracao e rastreamento
NS_LOG_COMPONENT_DEFINE ("ScenarioRdlTvsConflict");

#if HAS_NR_MODULE
// Funcao de callback para rastreamento de metricas de recepcao na camada PDCP (Packet Data Convergence Protocol)
void RxPdcpCallback (std::string path, uint16_t rnti, uint8_t lcid, uint32_t bytes, double delay)
{
    // Log estruturado com informacoes de RNTI do usuario, identificador de canal logico (LCID), bytes e latencia em ms
    NS_LOG_INFO ("[PDCP RX] RNTI: " << rnti << " LCID: " << (uint32_t)lcid << " Bytes: " << bytes << " Latencia: " << delay * 1000.0 << " ms");
}
#endif

int main (int argc, char *argv[])
{
    // =========================================================================
    // 1. Parametros Operacionais e Variaveis Configuraveis via CLI
    // =========================================================================
    uint16_t gNbNum = 2;                     // Numero de estacoes radiobase gNodeB (1 Macro gNB + 1 Small Cell)
    uint16_t ueNumPerGnb = 15;               // Quantidade de terminais de usuario por celula (Total = 30 UEs)
    double simTime = 30.0;                   // Duracao total da simulacao em segundos
    double centralFrequencyBand1 = 3.5e9;    // Frequencia central de operacao: 3.5 GHz (Banda n78 FR1)
    double bandwidthBand1 = 100e6;           // Largura de banda total do canal: 100 MHz
    uint16_t numerologyBwp1 = 1;             // Numerologia 3GPP NR: mu=1 correspondente a SCS de 30 kHz
    std::string ricIpAddress = "172.18.0.4"; // Endereco IP do Near-RT RIC (E2Term) no cluster Kubernetes
    uint16_t ricPort = 36422;                // Porta SCTP padrao para conexao da interface O-RAN E2
    bool enableE2Agent = true;               // Flag de controle para ativacao da comunicacao com o Near-RT RIC

    // Instanciacao do manipulador de linha de comando para sobrescrita de parametros em tempo de execucao
    CommandLine cmd (__FILE__);
    cmd.AddValue ("gNbNum", "Numero de gNodeBs no cenario", gNbNum);
    cmd.AddValue ("ueNumPerGnb", "Numero de UEs conectados por gNB", ueNumPerGnb);
    cmd.AddValue ("simTime", "Tempo total de simulacao em segundos", simTime);
    cmd.AddValue ("centralFrequency", "Frequencia central em Hz (padrao 3.5GHz)", centralFrequencyBand1);
    cmd.AddValue ("bandwidth", "Largura de banda em Hz (padrao 100MHz)", bandwidthBand1);
    cmd.AddValue ("numerology", "Numerologia 5G NR (0: 15kHz, 1: 30kHz, etc.)", numerologyBwp1);
    cmd.AddValue ("ricIp", "Endereco IP do E2Term no Near-RT RIC", ricIpAddress);
    cmd.AddValue ("ricPort", "Porta SCTP do servico E2Term", ricPort);
    cmd.AddValue ("enableE2", "Ativar comunicacao O-RAN E2 com o RIC", enableE2Agent);
    cmd.Parse (argc, argv); // Executa o parsing dos argumentos fornecidos pelo usuario

    // Mensagens de inicializacao exibindo a configuracao carregada
    NS_LOG_INFO ("Iniciando Cenario RDL Fase 1 - TVS Conflict Mitigation...");
    NS_LOG_INFO ("gNBs: " << gNbNum << " | Total UEs: " << (gNbNum * ueNumPerGnb) << " | Banda: " << (bandwidthBand1 / 1e6) << " MHz");

#if HAS_NR_MODULE
    // =========================================================================
    // 2. Topologia Espacial e Posicionamento em Grade (GridScenarioHelper)
    // =========================================================================
    GridScenarioHelper gridScenario;         // Helper para criacao de arranjo ordenado de celulas e terminais
    gridScenario.SetRows (1);                 // Topologia linear em 1 linha
    gridScenario.SetColumns (gNbNum);         // 2 celulas adjacentes
    gridScenario.SetHorizontalBsDistance (80.0); // Separacao de 80 metros entre gNBs (zona densa com interferencia intercelular)
    gridScenario.SetBsHeight (25.0);          // Altura das antenas das estacoes base: 25 metros do solo
    gridScenario.SetUtHeight (1.5);           // Altura das antenas dos terminais: 1.5 metros do solo
    gridScenario.SetSectorization (GridScenarioHelper::SINGLE); // Padrao de cobertura de setor unico omnidirecional
    gridScenario.SetBsNumber (gNbNum);        // Quantidade de estacoes base a serem instanciadas
    gridScenario.SetUtNumber (ueNumPerGnb * gNbNum); // Quantidade total de terminais no cenario (30 UEs)
    gridScenario.SetScenarioHeight (120.0);   // Dimensao vertical do grid de simulacao: 120 metros
    gridScenario.SetScenarioLength (200.0);   // Dimensao horizontal do grid de simulacao: 200 metros
    gridScenario.CreateScenario ();           // Instancia os nos no simulador e calcula suas coordenadas espaciais

    // =========================================================================
    // 3. Configuracao dos Helpers 5G-LENA (NR Protocol Stack & EPC Core)
    // =========================================================================
    Ptr<NrPointToPointEpcHelper> nrEpcHelper = CreateObject<NrPointToPointEpcHelper> (); // Helper da rede de nucleo 5G EPC
    Ptr<IdealBeamformingHelper> idealBeamformingHelper = CreateObject<IdealBeamformingHelper> (); // Helper de beamforming ideal MIMO
    Ptr<NrHelper> nrHelper = CreateObject<NrHelper> ();                                 // Helper principal da pilha 5G NR

    nrHelper->SetBeamformingHelper (idealBeamformingHelper); // Conecta o modulo de beamforming ao helper NR
    nrHelper->SetEpcHelper (nrEpcHelper);                   // Conecta o nucleo de pacotes ao helper NR

    // =========================================================================
    // 4. Divisao de Espectro e Configuracao de Bandwidth Parts (BWPs)
    // =========================================================================
    CcBwpCreator ccBwpCreator;                // Utilitario para composicao de portadoras componentes e BWPs
    const uint8_t numCcPerBand = 1;           // 1 portadora componente por banda de operacao
    // Configuracao da banda operacional com construtor universal de 3 parametros (3.5GHz, 100MHz, 1 CC)
    CcBwpCreator::SimpleOperationBandConf bandConf (centralFrequencyBand1,
                                                   bandwidthBand1,
                                                   numCcPerBand);
    // Cria a estrutura de banda contigua no 5G-LENA
    OperationBandInfo band = ccBwpCreator.CreateOperationBandContiguousCc (bandConf);

    // Inicializacao dos modelos de canal no NrChannelHelper e vinculacao a banda
    Ptr<NrChannelHelper> channelHelper = CreateObject<NrChannelHelper> ();
    channelHelper->AssignChannelsToBands ({band});

    // Parametrizacao dos modelos de propagacao de canal 3GPP TR 38.901
    Config::SetDefault ("ns3::ThreeGppChannelModel::UpdatePeriod", TimeValue (MilliSeconds (100)));          // Intervalo de atualizacao do canal: 100ms
    Config::SetDefault ("ns3::ThreeGppChannelConditionModel::UpdatePeriod", TimeValue (MilliSeconds (100))); // Intervalo de atualizacao de condicao LoS: 100ms
    Config::SetDefault ("ns3::ThreeGppPropagationLossModel::ShadowingEnabled", BooleanValue (true));         // Ativacao de desvanecimento por sombreamento (Shadowing)
    nrHelper->SetSchedulerAttribute ("FixedMcsDl", BooleanValue (false));                                     // Ativacao de adaptacao dinamica de enlace (MCS adaptativo via CQI)

    // Extracao dos ponteiros de todas as BWPs configuradas na banda de operacao
    BandwidthPartInfoPtrVector allBwps = CcBwpCreator::GetAllBwps ({band});

    // Configuracao do algoritmo de conformacao de feixe (Direct Path Beamforming)
    idealBeamformingHelper->SetAttribute ("BeamformingMethod", TypeIdValue (DirectPathBeamforming::GetTypeId ()));

    // Configuracao das matrizes de antenas dos Terminais de Usuario (UEs): Arranjo Planar 2x4 (8 elementos de antena)
    nrHelper->SetUeAntennaAttribute ("NumRows", UintegerValue (2));
    nrHelper->SetUeAntennaAttribute ("NumColumns", UintegerValue (4));
    nrHelper->SetUeAntennaAttribute ("AntennaElement", PointerValue (CreateObject<IsotropicAntennaModel> ()));

    // Configuracao das matrizes de antenas das Estacoes Base (gNBs): Arranjo Planar 4x8 (32 elementos de antena MIMO)
    nrHelper->SetGnbAntennaAttribute ("NumRows", UintegerValue (4));
    nrHelper->SetGnbAntennaAttribute ("NumColumns", UintegerValue (8));
    nrHelper->SetGnbAntennaAttribute ("AntennaElement", PointerValue (CreateObject<IsotropicAntennaModel> ()));

    // =========================================================================
    // 5. Instalacao dos Dispositivos de Rede (NetDevices) e Pilha Internet
    // =========================================================================
    // Instala a camada fisica e de enlace 5G NR nas estacoes base
    NetDeviceContainer gnbNetDev = nrHelper->InstallGnbDevice (gridScenario.GetBaseStations (), allBwps);
    // Instala a camada fisica e de enlace 5G NR nos terminais de usuario
    NetDeviceContainer ueNetDev = nrHelper->InstallUeDevice (gridScenario.GetUserTerminals (), allBwps);

    // Instala a pilha TCP/IP (Internet Stack) nos terminais de usuario
    InternetStackHelper internet;
    internet.Install (gridScenario.GetUserTerminals ());
    // Atribui enderecos IPv4 aos terminais via gateway do EPC
    Ipv4InterfaceContainer ueIpIface = nrEpcHelper->AssignUeIpv4Address (NetDeviceContainer (ueNetDev));

    // Associa cada terminal a estacao base com melhor nivel de sinal RSRP
    nrHelper->AttachToClosestGnb (ueNetDev, gnbNetDev);

    // =========================================================================
    // 6. Integracao do Agente O-RAN E2 (ns-O-RAN / NORI)
    // =========================================================================
#if HAS_ORAN_MODULE
    if (enableE2Agent)
    {
        NS_LOG_INFO ("Instalando E2 Agent nas gNBs conectando a " << ricIpAddress << ":" << ricPort);
        Ptr<E2AgentHelper> e2AgentHelper = CreateObject<E2AgentHelper> ();       // Instancia o helper do agente E2
        e2AgentHelper->SetAttribute ("RicIpAddress", Ipv4AddressValue (ricIpAddress.c_str ())); // Configura IP de destino do Near-RT RIC
        e2AgentHelper->SetAttribute ("RicPort", UintegerValue (ricPort));                 // Configura porta SCTP da interface E2
        e2AgentHelper->SetAttribute ("KpmReportIntervalMs", UintegerValue (200));         // Intervalo de telemetria KPM alinhado a Decision Window (200ms)
        e2AgentHelper->Install (gridScenario.GetBaseStations ());                         // Instala o agente E2 nas estacoes base
    }
#else
    NS_LOG_WARN ("Modulo ns-O-RAN nao detectado no include path. Rodando simulacao em modo RAN Standalone.");
#endif

    // =========================================================================
    // 7. Geracao de Trafego Diferenciado por Fatia de Servico (Network Slicing)
    // =========================================================================
    // Criacao do Remote Host no nucleo EPC para envio de trafego aos UEs
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

    uint16_t portBase = 1234;                                                // Porta base para distribuicao dos fluxos
    uint32_t totalUes = gridScenario.GetUserTerminals ().GetN ();            // Total de terminais conectados no cenario
    double stopTrafficTime = (simTime > 2.0) ? (simTime - 1.0) : simTime;

    for (uint32_t i = 0; i < totalUes; ++i)
    {
        Ptr<Node> ueNode = gridScenario.GetUserTerminals ().Get (i);         // Ponteiro para o no terminal i
        Ipv4Address ueAddr = ueIpIface.GetAddress (i);                      // Endereco IP do terminal i

        if (i % 3 == 0)
        {
            // Fatia 1: URLLC (Ultra-Reliable Low-Latency Communication)
            // Caracteristica: Pacotes pequenos (128B), alta frequencia (1ms = 1000 pkt/s), prioridade absoluta
            uint16_t port = portBase + i;
            UdpServerHelper server (port);
            ApplicationContainer serverApp = server.Install (ueNode);        // Servidor receptor no terminal
            serverApp.Start (Seconds (0.5));
            serverApp.Stop (Seconds (stopTrafficTime));

            UdpClientHelper client (ueAddr, port);
            client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));  // Transmissao ininterrupta
            client.SetAttribute ("Interval", TimeValue (MilliSeconds (1)));  // Intervalo de 1ms entre pacotes
            client.SetAttribute ("PacketSize", UintegerValue (128));         // Pacote de 128 Bytes
            ApplicationContainer clientApp = client.Install (remoteHost);    // Transmissao pelo Remote Host
            clientApp.Start (Seconds (1.0));                                 // Inicio aos 1.0s
            clientApp.Stop (Seconds (stopTrafficTime));                      // Fim da transmissao
        }
        else if (i % 3 == 1)
        {
            // Fatia 2: eMBB (Enhanced Mobile Broadband)
            // Caracteristica: Streaming de alta vazao (1400B a cada 200 microsegundos ~ 56 Mbps por fluxo)
            uint16_t port = portBase + i;
            UdpServerHelper server (port);
            ApplicationContainer serverApp = server.Install (ueNode);        // Servidor receptor no terminal
            serverApp.Start (Seconds (0.5));
            serverApp.Stop (Seconds (stopTrafficTime));

            UdpClientHelper client (ueAddr, port);
            client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));  // Transmissao ininterrupta
            client.SetAttribute ("Interval", TimeValue (MicroSeconds (200)));// Intervalo de 200us entre pacotes
            client.SetAttribute ("PacketSize", UintegerValue (1400));        // Pacote grande MTU de 1400 Bytes
            ApplicationContainer clientApp = client.Install (remoteHost);    // Transmissao pelo Remote Host
            clientApp.Start (Seconds (1.5));                                 // Inicio aos 1.5s
            clientApp.Stop (Seconds (stopTrafficTime));                      // Fim da transmissao
        }
        else
        {
            // Fatia 3: mMTC (Massive Machine Type Communication)
            // Caracteristica: Telemetria periodica de baixa vazao (64B a cada 100ms = 10 pkt/s)
            uint16_t port = portBase + i;
            UdpServerHelper server (port);
            ApplicationContainer serverApp = server.Install (ueNode);        // Servidor receptor no terminal
            serverApp.Start (Seconds (0.5));
            serverApp.Stop (Seconds (stopTrafficTime));

            UdpClientHelper client (ueAddr, port);
            client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));  // Transmissao ininterrupta
            client.SetAttribute ("Interval", TimeValue (MilliSeconds (100)));// Intervalo de 100ms entre transmissoes
            client.SetAttribute ("PacketSize", UintegerValue (64));          // Pacote reduzido de telemetria (64 Bytes)
            ApplicationContainer clientApp = client.Install (remoteHost);    // Transmissao pelo Remote Host
            clientApp.Start (Seconds (1.0));                                 // Inicio aos 1.0s
            clientApp.Stop (Seconds (stopTrafficTime));                      // Fim da transmissao
        }
    }

    // Ativacao dos traces fisicos e de enlace do 5G-LENA
    nrHelper->EnableTraces ();
#else
    // =========================================================================
    // Modo Fallback: Topologia RAN Padrao (Caso modulo 5G-LENA esteja ausente)
    // =========================================================================
    NS_LOG_WARN ("Modulo 5G-LENA (nr) nao detectado no build ns-3. Executando em modo RAN Fallback.");
    NodeContainer gnbNodes;
    gnbNodes.Create (gNbNum);                                                // Cria nos genericos para as estacoes base
    NodeContainer ueNodes;
    ueNodes.Create (ueNumPerGnb * gNbNum);                                   // Cria nos genericos para os terminais

    MobilityHelper mobility;
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");        // Posicionamento estatico no plano
    mobility.Install (gnbNodes);                                             // Instala mobilidade nas estacoes base
    mobility.Install (ueNodes);                                              // Instala mobilidade nos terminais

    PointToPointHelper p2p;
    p2p.SetDeviceAttribute ("DataRate", StringValue ("10Gbps"));             // Link de alta velocidade (10 Gbps)
    p2p.SetChannelAttribute ("Delay", StringValue ("1ms"));                  // Latencia de canal de 1ms

    InternetStackHelper internet;
    internet.Install (gnbNodes);                                             // Instala pilha IP nas estacoes base
    internet.Install (ueNodes);                                              // Instala pilha IP nos terminais

    Ipv4AddressHelper ipv4;
    ipv4.SetBase ("10.1.0.0", "255.255.0.0");                                // Sub-rede IPv4 do modo fallback

    for (uint32_t i = 0; i < ueNodes.GetN (); ++i)
    {
        NetDeviceContainer link = p2p.Install (gnbNodes.Get (i % gNbNum), ueNodes.Get (i)); // Conecta terminal a gNB
        Ipv4InterfaceContainer iface = ipv4.Assign (link);                                   // Atribui enderecos IP

        uint16_t port = 1234 + i;                                                            // Porta de escuta UDP
        UdpServerHelper server (port);
        ApplicationContainer serverApp = server.Install (ueNodes.Get (i));                   // Servidor no terminal
        serverApp.Start (Seconds (1.0));
        serverApp.Stop (Seconds (simTime - 1.0));

        UdpClientHelper client (iface.GetAddress (1), port);                                 // Cliente na estacao base
        client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));
        client.SetAttribute ("Interval", TimeValue (MilliSeconds (i % 3 == 0 ? 1 : 10)));
        client.SetAttribute ("PacketSize", UintegerValue (i % 3 == 0 ? 128 : 1024));
        ApplicationContainer clientApp = client.Install (gnbNodes.Get (i % gNbNum));
        clientApp.Start (Seconds (1.5));
        clientApp.Stop (Seconds (simTime - 1.0));
    }
#endif

    // =========================================================================
    // 8. Rastreamento, FlowMonitor e Execucao da Simulacao
    // =========================================================================
    FlowMonitorHelper flowHelper;                                            // Helper para sondas de monitoramento de fluxo
    Ptr<FlowMonitor> flowMonitor = flowHelper.InstallAll ();                 // Instala sondas estatisticas em todos os nos

    NS_LOG_INFO ("Executando simulacao por " << simTime << " segundos...");
    Simulator::Stop (Seconds (simTime));                                     // Agenda o fim da simulacao
    Simulator::Run ();                                                       // Executa os eventos discretos no simulador

    // Serializa todos os fluxos de Throughput, Atraso, Perda e Jitter em arquivo XML
    flowMonitor->SerializeToXmlFile ("flowmonitor_results.xml", true, true);
    Simulator::Destroy ();                                                   // Libera todos os recursos alocados na memoria

    NS_LOG_INFO ("Simulacao concluida com sucesso. Metricas de fluxo salvas em flowmonitor_results.xml.");
    return 0;                                                                // Encerramento com codigo de sucesso
}
