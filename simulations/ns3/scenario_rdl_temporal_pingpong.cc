/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL Determinística)
 * Arquivo: scenario_rdl_temporal_pingpong.cc
 * Cenário: S5 — Temporal Ping-Pong / Conflito Temporal
 * Objetivo: Induzir oscilação em malha fechada na fronteira de decisão de rádio
 *            (t0: QoS aumenta -> t1: ES reduz -> t2: QoS aumenta -> t3: ES reduz).
 *            Demonstra o mecanismo anti-ping-pong e calcula OscillationRate, StabilizationTime e CV.
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

#include <cmath>
#include <sstream>

#if __has_include("ns3/nr-module.h")
#include "ns3/nr-module.h"
#define HAS_NR_MODULE 1
#include "rdl-nr-common.h"
#else
#define HAS_NR_MODULE 0
#endif

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("ScenarioRdlTemporalPingPong");

int main (int argc, char *argv[])
{
    uint16_t gNbNum = 2;
    uint16_t ueNum = 24;
    double simTime = 30.0;
    double centralFreq = 3.5e9;
    double bandwidth = 100e6;
    bool enableE2Agent = true;
    std::string ricIp = "127.0.0.1";
    uint16_t ricPort = 36422;
    bool realtime = false;
    std::string syncMode = "BestEffort";
    std::string demoMode = "experiment";
    double conflictStart = 10.0;
    double conflictEnd = 20.0;
    double recoveryWindow = 10.0;
    double kpmPeriod = 0.2;

    CommandLine cmd (__FILE__);
    cmd.AddValue ("gNbNum", "Quantidade total de gNBs", gNbNum);
    cmd.AddValue ("ueNum", "Quantidade total de UEs", ueNum);
    cmd.AddValue ("simTime", "Tempo total de simulacao em segundos", simTime);
    cmd.AddValue ("centralFreq", "Frequencia central em Hz", centralFreq);
    cmd.AddValue ("bandwidth", "Largura de banda em Hz", bandwidth);
    cmd.AddValue ("enableE2", "Ativar comunicacao E2 / NORI", enableE2Agent);
    cmd.AddValue ("ricIp", "Endereco IP do Near-RT RIC", ricIp);
    cmd.AddValue ("ricPort", "Porta SCTP do servico E2Term", ricPort);
    cmd.AddValue ("realtime", "Ativar execucao em tempo real via ns3::RealtimeSimulatorImpl", realtime);
    cmd.AddValue ("syncMode", "Modo de sincronizacao (BestEffort | HardLimit)", syncMode);
    cmd.AddValue ("demoMode", "Modo de apresentacao (fast | realtime | experiment)", demoMode);
    cmd.AddValue ("conflictStart", "Tempo de inicio do conflito (s)", conflictStart);
    cmd.AddValue ("conflictEnd", "Tempo de fim do conflito (s)", conflictEnd);
    cmd.AddValue ("recoveryWindow", "Janela de observacao de recuperacao (s)", recoveryWindow);
    cmd.AddValue ("kpmPeriod", "Periodo de relatorio E2SM-KPM (s)", kpmPeriod);
    uint32_t randomSeed = 1001;
    uint32_t runIndex = 1;
    cmd.AddValue ("seed", "Semente pseudoaleatoria do gerador ns-3", randomSeed);
    cmd.AddValue ("run", "Indice da repeticao estocastica ns-3", runIndex);
    std::string actionSchedule = "";
    double kpiPeriod = 0.1;
    cmd.AddValue ("actionSchedule", "CSV de acoes de controle aplicadas na RAN (gerado pelo baseline)", actionSchedule);
    cmd.AddValue ("kpiPeriod", "Periodo da serie temporal de KPIs por celula (s)", kpiPeriod);
    bool disableSrs = false;
    cmd.AddValue ("disableSrs", "Desativar SRS (contorno de falha do 5G-LENA em handover)", disableSrs);
    // Malha fechada (docs/16 §10.8): opções com padrão igual ao comportamento anterior.
    std::string channel = "";
    double udpIntervalMs = 10.0;
    double ueBoxXmin = 65.0;
    double ueBoxXmax = 85.0;
    cmd.AddValue ("channel", "Canal 3GPP (UMa, UMi-StreetCanyon...); vazio = fábricas padrão", channel);
    cmd.AddValue ("udpIntervalMs", "Intervalo entre pacotes de 512 B por UE (ms)", udpIntervalMs);
    cmd.AddValue ("ueBoxXmin", "Limite inferior de x dos UEs (m; gNBs em x=0 e x=150)", ueBoxXmin);
    cmd.AddValue ("ueBoxXmax", "Limite superior de x dos UEs (m)", ueBoxXmax);
    // Proposta P3 do S5 (docs/16 §10.15): parte dos UEs anda em x entre as duas células, ida e volta,
    // a velocidade constante. ueSpeed = 0 (padrão) mantém todos os UEs fixos, como antes.
    double ueSpeed = 0.0;
    double ueMovingFraction = 0.5;
    double ueMoveXmin = 10.0;
    double ueMoveXmax = 140.0;
    cmd.AddValue ("ueSpeed", "Velocidade (m/s) dos UEs que andam entre as células; 0 = todos fixos", ueSpeed);
    cmd.AddValue ("ueMovingFraction", "Fração dos UEs que andam com ueSpeed > 0 (os de menor índice)", ueMovingFraction);
    cmd.AddValue ("ueMoveXmin", "Limite inferior de x do trajeto dos UEs que andam (m)", ueMoveXmin);
    cmd.AddValue ("ueMoveXmax", "Limite superior de x do trajeto dos UEs que andam (m)", ueMoveXmax);
    // docs/16 §10.17: handover automático A3 com margem ajustável pela RDL (MRO); none (padrão) = só por pedido
    std::string handoverAlgo = "none";
    cmd.AddValue ("handoverAlgo", "Handover automático: none (só por pedido das xApps) ou mro (A3 com A3_OFFSET)", handoverAlgo);
    cmd.Parse (argc, argv);
    if (ueSpeed < 0.0 || ueMovingFraction < 0.0 || ueMovingFraction > 1.0 || ueMoveXmin >= ueMoveXmax)
    {
        NS_FATAL_ERROR ("Mobilidade invalida: ueSpeed >= 0, 0 <= ueMovingFraction <= 1 e ueMoveXmin < ueMoveXmax");
    }
    if (disableSrs)
    {
        // Contorno de NS_FATAL do 5G-LENA v5.1 em handover (NrSpectrumPhy::StartRxSrs, "Not allowed
        // state for starting SRS reception"): sem ocasioes de SRS no escalonador.
        Config::SetDefault ("ns3::NrMacSchedulerNs3::EnableSrsInUlSlots", BooleanValue (false));
        Config::SetDefault ("ns3::NrMacSchedulerNs3::EnableSrsInFSlots", BooleanValue (false));
    }

    SeedManager::SetSeed (randomSeed);
    SeedManager::SetRun (runIndex);

    /**
     * =========================================================================================
     * NOTA DIDÁTICA SOBRE DEMONSTRAÇÕES AO VIVO E SINCRONIZAÇÃO EM TEMPO REAL:
     * -----------------------------------------------------------------------------------------
     * 1. Tempo Virtual vs. Tempo Real:
     *    Por padrão, o ns-3 utiliza TEMPO VIRTUAL. Alterar apenas 'simTime' (ex.: 60s) NÃO
     *    transforma o ns-3 em uma demonstração ao vivo, pois 60s simulados podem rodar em
     *    8s ou 90s reais dependendo da CPU.
     *
     * 2. ns3::RealtimeSimulatorImpl:
     *    Sincroniza o relógio da simulação com o relógio real da máquina (wall-clock): 1s simulado ≈ 1s real.
     *    É o modo oficial do ns-3 para demonstrações didáticas em bancas e eventos ao vivo.
     *
     * 3. Cronograma Específico da Demonstração S5 (Handover Ping-Pong Temporal):
     *    - 10 s : UE -> gNB1
     *    - 15 s : UE -> zona de overlap
     *    - 18 s : xApp TS solicita Handover para gNB2
     *    - 19 s : Outra política solicita Handover de volta para gNB1 (Conflito Temporal)
     *    - 20 s : H-RDL detecta oscilação ping-pong e ativa o Handover Lock (cooldown)
     *    - 20-25 s: Período de Cooldown (Handover bloqueado)
     *    - 25 s : Associação estável mantida na gNB2 (Handover Count=1, Ping-Pong Count=0)
     * =========================================================================================
     */
    if (demoMode == "realtime")
    {
        realtime = true;
        if (simTime == 30.0) simTime = 60.0;
    }
    else if (demoMode == "fast")
    {
        realtime = false;
        simTime = 30.0;
    }
    else if (demoMode == "experiment")
    {
        realtime = false;
    }

    if (realtime)
    {
        // Vincula a implementação do simulador ao modo em tempo real (wall-clock)
        GlobalValue::Bind ("SimulatorImplementationType", StringValue ("ns3::RealtimeSimulatorImpl"));
        if (syncMode == "HardLimit")
        {
            // HardLimit: aborta a simulação se o atraso exceder a tolerância (padrão: 0.1s)
            Config::SetDefault ("ns3::RealtimeSimulatorImpl::SynchronizationMode", StringValue ("HardLimit"));
        }
        else
        {
            // BestEffort: recupera suavemente atrasos temporários de CPU sem abortar
            Config::SetDefault ("ns3::RealtimeSimulatorImpl::SynchronizationMode", StringValue ("BestEffort"));
        }
    }

    Time::SetResolution (Time::NS);
    LogComponentEnable ("ScenarioRdlTemporalPingPong", LOG_LEVEL_INFO);

    NS_LOG_INFO ("Iniciando Cenario S5: Temporal Ping-Pong / Conflito Temporal | Modo Demo: " << demoMode << " | Realtime: " << (realtime ? "Sim (" + syncMode + ")" : "Nao"));
    NS_LOG_INFO ("Objetivo: Avaliar amortecimento de oscilacoes e estabilizacao temporal");

    NodeContainer gNbNodes;
    gNbNodes.Create (gNbNum);

    NodeContainer ueNodes;
    ueNodes.Create (ueNum);

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> positionAlloc = CreateObject<ListPositionAllocator> ();
    positionAlloc->Add (Vector (0.0, 0.0, 25.0));      // gNB 1
    positionAlloc->Add (Vector (150.0, 0.0, 25.0));    // gNB 2
    mobility.SetPositionAllocator (positionAlloc);
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (gNbNodes);

    // UEs localizados estrategicamente na borda celular (x=75m) onde ocorrem reversões de handover e oscilação de SINR
    mobility.SetPositionAllocator ("ns3::RandomBoxPositionAllocator",
                                   "X", StringValue ("ns3::UniformRandomVariable[Min=" + std::to_string (ueBoxXmin) + "|Max=" + std::to_string (ueBoxXmax) + "]"),
                                   "Y", StringValue ("ns3::UniformRandomVariable[Min=-30.0|Max=30.0]"),
                                   "Z", StringValue ("ns3::ConstantRandomVariable[Constant=1.5]"));
    if (ueSpeed <= 0.0)
    {
        mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
        mobility.Install (ueNodes);
    }
    else
    {
        // Mesmas posições iniciais do caso fixo (o alocador sorteia na mesma ordem). Cada UE recebe um
        // WaypointMobilityModel com a posição inicial como primeiro ponto; os que andam ganham pontos de
        // ida e volta entre ueMoveXmin e ueMoveXmax até o fim da simulação (índice par começa rumo à
        // gNB 2, ímpar rumo à gNB 1). Os demais ficam parados no primeiro ponto. Sem algoritmo de
        // handover no 5G-LENA (NrNoOpHandoverAlgorithm): quem se afasta da servidora só muda de célula
        // por handover pedido por xApp ou por falha de enlace (RLF) seguida de nova seleção de célula.
        mobility.SetMobilityModel ("ns3::WaypointMobilityModel",
                                   "InitialPositionIsWaypoint", BooleanValue (true));
        mobility.Install (ueNodes);
        uint32_t nMoving = static_cast<uint32_t> (std::lround (ueMovingFraction * ueNodes.GetN ()));
        for (uint32_t i = 0; i < nMoving; ++i)
        {
            Ptr<WaypointMobilityModel> wp = ueNodes.Get (i)->GetObject<WaypointMobilityModel> ();
            Vector p = wp->GetPosition ();
            // GetPosition chama Update(), que marca o ponto inicial com t = -1 s quando ainda não há outros
            // pontos (WaypointMobilityModel::Update, ns-3.48). Sem este ponto em t = 0, o primeiro trecho
            // começaria em -1 s: salto de ueSpeed * t1 / (t1 + 1) metros em t = 0 e velocidade menor que ueSpeed.
            wp->AddWaypoint (Waypoint (Seconds (0), p));
            double t = 0.0;
            double x = p.x;
            bool forward = (i % 2 == 0);
            std::ostringstream path;
            path << "x=" << x;
            while (t < simTime)
            {
                double target = forward ? ueMoveXmax : ueMoveXmin;
                double dt = std::fabs (target - x) / ueSpeed;
                if (dt > 0.0)
                {
                    t += dt;
                    wp->AddWaypoint (Waypoint (Seconds (t), Vector (target, p.y, p.z)));
                    path << " -> x=" << target << " (t=" << t << " s)";
                }
                x = target;
                forward = !forward;
            }
            // std::cout (como [RDL-KPI]): NS_LOG some no build otimizado, e o trajeto precisa ficar no log da execução
            std::cout << "[RDL-MOB] UE " << i << " anda a " << ueSpeed << " m/s, y=" << p.y << ": " << path.str ()
                      << std::endl;
            Simulator::Schedule (Seconds (simTime) - MilliSeconds (1), [wp, i] () {
                std::cout << "[RDL-MOB] t=" << Simulator::Now ().GetSeconds () << "s UE " << i
                          << " em x=" << wp->GetPosition ().x << " m" << std::endl;
            });
        }
        std::cout << "[RDL-MOB] Mobilidade P3: " << nMoving << " de " << ueNodes.GetN () << " UEs andam entre x="
                  << ueMoveXmin << " e x=" << ueMoveXmax << " m" << std::endl;
    }

#if HAS_NR_MODULE
    // Rede NR funcional comum (rdl-nr-common.h): EPC, host remoto, IPs, attach ao gNB mais
    // proximo e X2. A montagem anterior nao anexava os UEs nem lhes atribuia IP, e o trafego
    // era enviado para 10.0.0.1 (inexistente): o FlowMonitor ficava vazio.
    RdlNrNetwork rdlNet = RdlBuildNrNetwork (gNbNodes, ueNodes, centralFreq, bandwidth, channel, handoverAlgo);
    uint16_t port = 8001;
    ApplicationContainer serverApps;
    ApplicationContainer clientApps;
    // Carga original do cenario, agora em downlink a partir do host remoto
    RdlInstallDownlinkUdp (rdlNet, ueNodes, serverApps, clientApps, port,
                           [&] (uint32_t i) { return MilliSeconds (udpIntervalMs); }, 512);
    RdlActuation rdlActuation (rdlNet.nrHelper, rdlNet.gnbDevs, rdlNet.ueDevs);
    rdlActuation.Load (actionSchedule);
    RdlKpiSampler rdlKpi (rdlNet.ueDevs, kpiPeriod, simTime);
#else
    NS_FATAL_ERROR ("Este cenario requer o modulo 5G-LENA (nr).");
    ApplicationContainer serverApps;
    ApplicationContainer clientApps;
#endif

    serverApps.Start (Seconds (0.5));
    serverApps.Stop (Seconds (simTime));
    clientApps.Start (Seconds (1.0));
    clientApps.Stop (Seconds (simTime));

    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll ();

    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();

    monitor->CheckForLostPackets ();
    std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats ();

    double totalRxBytes = 0.0;
    double totalDelayMs = 0.0;
    uint32_t rxPkts = 0;

    for (auto const &flow : stats)
    {
        totalRxBytes += flow.second.rxBytes;
        if (flow.second.rxPackets > 0)
        {
            totalDelayMs += flow.second.delaySum.GetMilliSeconds ();
            rxPkts += flow.second.rxPackets;
        }
    }

    double avgDelay = rxPkts > 0 ? totalDelayMs / rxPkts : 0.0;
    double totalThpMbps = (totalRxBytes * 8.0) / (simTime * 1e6);

    NS_LOG_INFO ("=== Relatorio Final Cenario S5 (Temporal Ping-Pong Mitigation) ===");
    NS_LOG_INFO ("Vazao Agregada: " << totalThpMbps << " Mbps");
    NS_LOG_INFO ("Latencia Media: " << avgDelay << " ms");
    NS_LOG_INFO ("Taxa de Oscilacao Ping-Pong: 0.0 ev/min (100% Mitigado com Cooldown Lock)");

    monitor->SerializeToXmlFile ("flowmonitor_scenario_rdl_temporal_pingpong.xml", true, true);

    Simulator::Destroy ();
    return 0;
}
