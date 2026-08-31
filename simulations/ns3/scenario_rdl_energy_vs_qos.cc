/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL Deterministica)
 * Arquivo: scenario_rdl_energy_vs_qos.cc
 * Descricao: Cenario de Simulacao 5G-LENA + ns-O-RAN / NORI
 *            Avaliacao de Arbitragem EEVS (Eficiencia Energetica vs Garantia de SLA URLLC)
 * Topologia: 1 Macro gNB (Banda Alta) + 1 Micro gNB (Economia de Energia), 20 UEs com Carga Dinamica
 * =========================================================================================
 */

// Inclusao dos modulos nucleares do simulador ns-3
#include "ns3/core-module.h"             // Nucleo do ns-3: manipulacao de tempo, eventos, variaveis de configuracao e logs
#include "ns3/network-module.h"          // Estruturas de rede genericas: Node, Packet, NetDevice, Socket
#include "ns3/internet-module.h"         // Pilha TCP/IP: IPv4, IPv6, UDP, TCP e roteamento
#include "ns3/mobility-module.h"         // Modelos de mobilidade espacial e posicionamento cartesiano dos nos
#include "ns3/antenna-module.h"          // Modelos de radiacao de antenas (Isotropica, Parabolica, Matriz Planar)
#include "ns3/point-to-point-module.h"   // Links ponto-a-ponto para backhaul e modo fallback
#include "ns3/applications-module.h"     // Geradores de trafego de aplicacao (UdpClient, UdpServer, OnOffApplication)
#include "ns3/flow-monitor-module.h"     // Coletor estatistico de fluxo de rede (Throughput, Atraso, Perda, Jitter)

// Inclusao condicional do modulo 5G-LENA (CTTC-LENA New Radio)
#if __has_include("ns3/nr-module.h")
#include "ns3/nr-module.h"               // Modulo principal do 5G-LENA NR (PHY, MAC, RRC, BWP, Schedulers)
#define HAS_NR_MODULE 1                  // Flag indicando que o modulo 5G-LENA esta presente no build
#else
#define HAS_NR_MODULE 0                  // Flag indicando compilacao em modo fallback caso 5G-LENA esteja ausente
#endif

// Inclusao condicional dos cabecalhos da interface O-RAN E2 (ns-O-RAN / NORI)
#if __has_include("ns3/oran-interface.h")
#include "ns3/oran-interface.h"          // Interface unificada ns-O-RAN
#define HAS_ORAN_MODULE 1                // Flag indicando presenca da interface O-RAN
#elif __has_include("ns3/e2-agent-helper.h")
#include "ns3/e2-agent-helper.h"         // Helper de integracao E2 Agent
#define HAS_ORAN_MODULE 1                // Flag indicando presenca do E2 Agent
#else
#define HAS_ORAN_MODULE 0                // Flag indicando operacao sem conexao externa E2
#endif

// Utilizacao do namespace padrao do ns-3
using namespace ns3;

// Definicao do componente de log para depuracao e rastreamento de eventos no terminal
NS_LOG_COMPONENT_DEFINE ("ScenarioRdlEnergyVsQos");

int main (int argc, char *argv[])
{
    // =========================================================================
    // 1. Parametros Operacionais e Variaveis Configuraveis via CLI
    // =========================================================================
    uint16_t gNbNum = 2;                     // Quantidade total de estacoes radiobase (1 Macro gNB + 1 Small Cell)
    uint16_t ueNum = 20;                     // Quantidade total de terminais de usuario (UEs) distribuidos no cenario
    double simTime = 40.0;                   // Duracao total da simulacao em segundos simulados
    double centralFreq = 3.5e9;              // Frequencia central de operacao: 3.5 GHz (Banda n78 FR1)
    double bandwidth = 50e6;                 // Largura de banda do canal: 50 MHz
    std::string ricIp = "172.18.0.4";        // Endereco IP do Near-RT RIC (E2Term) na rede Docker/K8s
    uint16_t ricPort = 36422;                // Porta SCTP padrao da interface O-RAN E2 (E2AP)

    // Configuracao do parser de linha de comando para sobrescrita dinamica dos parametros
    CommandLine cmd (__FILE__);
    cmd.AddValue ("simTime", "Tempo total de simulacao em segundos", simTime);
    cmd.AddValue ("ricIp", "Endereco IP do Near-RT RIC E2Term", ricIp);
    cmd.AddValue ("ricPort", "Porta SCTP do servico E2Term", ricPort);
    cmd.Parse (argc, argv); // Processamento dos argumentos passados via terminal

    // Log de inicializacao do cenario com informacoes de topologia
    NS_LOG_INFO ("Iniciando Cenario RDL Fase 1 - EEVS (Energy Saving vs SLA URLLC)...");

#if HAS_NR_MODULE
    // =========================================================================
    // 2. Criacao da Topologia Espacial e Posicionamento no Grid 5G-LENA
    // =========================================================================
    GridScenarioHelper gridScenario;         // Helper para criacao de arranjo em grade de gNBs e UEs
    gridScenario.SetRows (1);                 // Arranjo em 1 linha de celulas
    gridScenario.SetColumns (gNbNum);         // Arranjo em 2 colunas (2 estacoes base adjacentes)
    gridScenario.SetHorizontalBsDistance (50.0); // Distancia de 50 metros entre as estacoes base (cobertura sobreposta)
    gridScenario.SetBsHeight (15.0);          // Altura das antenas das gNBs: 15 metros do solo
    gridScenario.SetUtHeight (1.5);           // Altura dos terminais de usuario: 1.5 metros do solo (nivel do pedestre)
    gridScenario.SetSectorization (GridScenarioHelper::SINGLE); // Configuracao omnidirecional (setor unico)
    gridScenario.SetBsNumber (gNbNum);        // Define o numero de estacoes base no grid
    gridScenario.SetUtNumber (ueNum);         // Define o numero de terminais de usuario distribuidos no grid
    gridScenario.SetScenarioHeight (80.0);    // Dimensoes verticais da area de simulacao: 80 metros
    gridScenario.SetScenarioLength (100.0);   // Dimensoes horizontais da area de simulacao: 100 metros
    gridScenario.CreateScenario ();           // Instancia os nos fisicos e calcula as coordenadas de mobilidade

    // =========================================================================
    // 3. Inicializacao dos Helpers do 5G-LENA (NR Stack & Core EPC)
    // =========================================================================
    Ptr<NrPointToPointEpcHelper> nrEpcHelper = CreateObject<NrPointToPointEpcHelper> (); // Helper da rede de nucleo EPC 5G
    Ptr<IdealBeamformingHelper> idealBeamformingHelper = CreateObject<IdealBeamformingHelper> (); // Helper de conformacao de feixe MIMO
    Ptr<NrHelper> nrHelper = CreateObject<NrHelper> ();                                 // Helper central da pilha de protocolos 5G NR

    nrHelper->SetBeamformingHelper (idealBeamformingHelper); // Associa o algoritmo de beamforming ao helper NR
    nrHelper->SetEpcHelper (nrEpcHelper);                   // Associa o nucleo de rede EPC para criacao de portadoras (bearers)

    // =========================================================================
    // 4. Divisao de Espectro e Configuracao de Bandwidth Parts (BWPs)
    // =========================================================================
    CcBwpCreator ccBwpCreator;                // Utilitario para geracao de portadoras componentes e BWPs
    // Configuracao da banda operacional: 3.5GHz, 50MHz de largura, 1 portadora componente (CC)
    CcBwpCreator::SimpleOperationBandConf bandConf (centralFreq, bandwidth, 1);
    // Criacao da estrutura de banda de operacao contigua
    OperationBandInfo band = ccBwpCreator.CreateOperationBandContiguousCc (bandConf);

    // Inicializacao dos modelos de canal no NrChannelHelper e vinculacao a banda
    Ptr<NrChannelHelper> channelHelper = CreateObject<NrChannelHelper> ();
    channelHelper->AssignChannelsToBands ({band});

    // Parametrizacao dos modelos de canal e propagacao 3GPP TR 38.901
    Config::SetDefault ("ns3::ThreeGppChannelModel::UpdatePeriod", TimeValue (MilliSeconds (100)));           // Atualizacao da matriz de canal a cada 100ms
    Config::SetDefault ("ns3::ThreeGppChannelConditionModel::UpdatePeriod", TimeValue (MilliSeconds (100)));  // Atualizacao de condicao LoS/NLoS a cada 100ms
    Config::SetDefault ("ns3::ThreeGppPropagationLossModel::ShadowingEnabled", BooleanValue (true));          // Ativa sombreamento log-normal (Shadowing)

    // Extracao dos ponteiros de todas as BWPs configuradas na banda de operacao
    BandwidthPartInfoPtrVector allBwps = CcBwpCreator::GetAllBwps ({band});

    // Configuracao do metodo de Beamforming para busca do caminho direto (Direct Path)
    idealBeamformingHelper->SetAttribute ("BeamformingMethod", TypeIdValue (DirectPathBeamforming::GetTypeId ()));

    // =========================================================================
    // 5. Instalacao dos Dispositivos de Rede (NetDevices) e Pilha Internet
    // =========================================================================
    // Instala a camada PHY/MAC 5G NR nas estacoes base
    NetDeviceContainer gnbNetDev = nrHelper->InstallGnbDevice (gridScenario.GetBaseStations (), allBwps);
    // Instala a camada PHY/MAC 5G NR nos terminais de usuario
    NetDeviceContainer ueNetDev = nrHelper->InstallUeDevice (gridScenario.GetUserTerminals (), allBwps);

    // Instala a pilha TCP/IP (Internet Stack) nos terminais de usuario
    InternetStackHelper internet;
    internet.Install (gridScenario.GetUserTerminals ());
    // Atribui enderecos IPv4 aos terminais atraves do gateway EPC
    Ipv4InterfaceContainer ueIpIface = nrEpcHelper->AssignUeIpv4Address (NetDeviceContainer (ueNetDev));

    // Associa cada terminal a estacao base mais proxima com base na potencia de sinal recebida (RSRP)
    nrHelper->AttachToClosestGnb (ueNetDev, gnbNetDev);

    // =========================================================================
    // 6. Integracao do Agente O-RAN E2 (ns-O-RAN / NORI)
    // =========================================================================
#if HAS_ORAN_MODULE
    Ptr<E2AgentHelper> e2AgentHelper = CreateObject<E2AgentHelper> ();       // Instancia o helper do agente E2AP
    e2AgentHelper->SetAttribute ("RicIpAddress", Ipv4AddressValue (ricIp.c_str ())); // Configura o IP de destino do Near-RT RIC
    e2AgentHelper->SetAttribute ("RicPort", UintegerValue (ricPort));                 // Configura a porta SCTP de comunicacao E2
    e2AgentHelper->SetAttribute ("KpmReportIntervalMs", UintegerValue (200));         // Intervalo de reporte KPM alinhado a Decision Window de 200ms
    e2AgentHelper->Install (gridScenario.GetBaseStations ());                         // Instala o agente E2 nas estacoes base para telemetria e controle
#endif

    // =========================================================================
    // 7. Geracao de Trafego Flutuante e Rajadas de Carga Critica
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

    double stopTrafficTime = (simTime > 2.0) ? (simTime - 1.0) : simTime;

    for (uint32_t i = 0; i < ueNum; ++i)
    {
        Ptr<Node> ueNode = gridScenario.GetUserTerminals ().Get (i); // Obtem o no correspondente ao terminal i
        Ipv4Address ueAddr = ueIpIface.GetAddress (i);              // Obtem o endereco IP do terminal i
        uint16_t port = 5000 + i;                                    // Porta de escuta UDP exclusiva para o fluxo

        // Instalacao do receptor UDP Server no terminal de usuario
        UdpServerHelper server (port);
        ApplicationContainer serverApp = server.Install (ueNode);
        serverApp.Start (Seconds (0.5));                             // Inicio da escuta aos 0.5s
        serverApp.Stop (Seconds (stopTrafficTime));                  // Fim da escuta

        // Configuracao do transmissor UDP Client a partir do Remote Host
        UdpClientHelper client (ueAddr, port);
        if (i < 10)
        {
            // Grupo 1 (UEs 0-9): Trafego de Alta Prioridade URLLC com Rajada Critica
            client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));          // Envio continuo de pacotes
            client.SetAttribute ("Interval", TimeValue (MilliSeconds (2)));          // Intervalo de 2ms entre pacotes (500 pkt/s)
            client.SetAttribute ("PacketSize", UintegerValue (256));                 // Tamanho do pacote: 256 Bytes
            ApplicationContainer clientApp = client.Install (remoteHost);            // Transmissao pelo Remote Host
            double burstStart = (simTime > 15.0) ? 10.0 : 1.0;
            double burstStop = (simTime > 25.0) ? 25.0 : stopTrafficTime;
            clientApp.Start (Seconds (burstStart));
            clientApp.Stop (Seconds (burstStop));
        }
        else
        {
            // Grupo 2 (UEs 10-19): Trafego de Fundo Estavel (Best-Effort / Telemetria)
            client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));          // Envio continuo de pacotes
            client.SetAttribute ("Interval", TimeValue (MilliSeconds (20)));         // Intervalo de 20ms entre pacotes (50 pkt/s)
            client.SetAttribute ("PacketSize", UintegerValue (512));                 // Tamanho do pacote: 512 Bytes
            ApplicationContainer clientApp = client.Install (remoteHost);            // Transmissao pelo Remote Host
            clientApp.Start (Seconds (1.0));                                         // Inicio do trafego nominal
            clientApp.Stop (Seconds (stopTrafficTime));                              // Termino do trafego nominal
        }
    }

    // Ativacao dos traces fisicos e de enlace do 5G-LENA
    nrHelper->EnableTraces ();
#else
    // =========================================================================
    // Modo Fallback: Execucao RAN Basica (Quando modulo 5G-LENA nao estiver presente)
    // =========================================================================
    NS_LOG_WARN ("Modulo 5G-LENA (nr) nao detectado. Executando cenario EEVS em modo Fallback.");
    NodeContainer gnbNodes;
    gnbNodes.Create (gNbNum);                                                // Cria nos genericos para estacoes base
    NodeContainer ueNodes;
    ueNodes.Create (ueNum);                                                  // Cria nos genericos para terminais

    MobilityHelper mobility;
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");        // Posicionamento estatico
    mobility.Install (gnbNodes);                                             // Instala mobilidade nas gNBs
    mobility.Install (ueNodes);                                              // Instala mobilidade nos UEs

    PointToPointHelper p2p;
    p2p.SetDeviceAttribute ("DataRate", StringValue ("10Gbps"));             // Link de alta velocidade (10 Gbps)
    p2p.SetChannelAttribute ("Delay", StringValue ("1ms"));                  // Latencia base de canal (1 ms)

    InternetStackHelper internet;
    internet.Install (gnbNodes);                                             // Instala pilha IP nas gNBs
    internet.Install (ueNodes);                                              // Instala pilha IP nos UEs

    Ipv4AddressHelper ipv4;
    ipv4.SetBase ("10.2.0.0", "255.255.0.0");                                // Sub-rede IPv4 do modo fallback

    for (uint32_t i = 0; i < ueNum; ++i)
    {
        NetDeviceContainer link = p2p.Install (gnbNodes.Get (i % gNbNum), ueNodes.Get (i)); // Conecta UE a gNB
        Ipv4InterfaceContainer iface = ipv4.Assign (link);                                   // Atribui enderecos IP

        uint16_t port = 5000 + i;                                                            // Porta de escuta UDP
        UdpServerHelper server (port);
        ApplicationContainer serverApp = server.Install (ueNodes.Get (i));                   // Servidor no UE
        serverApp.Start (Seconds (1.0));
        serverApp.Stop (Seconds (simTime - 1.0));

        UdpClientHelper client (iface.GetAddress (1), port);                                 // Cliente na gNB
        client.SetAttribute ("MaxPackets", UintegerValue (0xFFFFFFFF));
        client.SetAttribute ("Interval", TimeValue (MilliSeconds (i < 10 ? 2 : 20)));
        client.SetAttribute ("PacketSize", UintegerValue (i < 10 ? 256 : 512));
        ApplicationContainer clientApp = client.Install (gnbNodes.Get (i % gNbNum));
        clientApp.Start (Seconds (i < 10 ? 10.0 : 2.0));
        clientApp.Stop (Seconds (i < 10 ? 25.0 : simTime - 2.0));
    }
#endif

    // =========================================================================
    // 8. Monitoramento de Fluxos de Rede (FlowMonitor) e Execucao do Simulador
    // =========================================================================
    FlowMonitorHelper flowHelper;                                            // Helper para criacao de sondas de fluxo
    Ptr<FlowMonitor> flowMonitor = flowHelper.InstallAll ();                 // Instala sondas estatisticas em todos os nos

    NS_LOG_INFO ("Executando simulacao EEVS por " << simTime << "s...");
    Simulator::Stop (Seconds (simTime));                                     // Agenda o encerramento do relogio de eventos
    Simulator::Run ();                                                       // Dispara a execucao do laco de simulacao discreta

    // Exportacao dos resultados de Throughput, Atraso, Perda e Jitter em formato XML estruturado
    flowMonitor->SerializeToXmlFile ("flowmonitor_results.xml", true, true);
    Simulator::Destroy ();                                                   // Libera a memoria alocada pelas estruturas do simulador

    NS_LOG_INFO ("Simulacao EEVS concluida com sucesso. Metricas salvas em flowmonitor_results.xml.");
    return 0;                                                                // Retorno com codigo de sucesso
}
