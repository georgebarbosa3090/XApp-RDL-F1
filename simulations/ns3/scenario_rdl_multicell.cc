/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer)
 * Arquivo: scenario_rdl_multicell.cc
 *
 * Cenário paramétrico multicélula (ns-3.48 + 5G-LENA v5.1) usado pelos cenários S9–S15 e
 * pelos cenários GreenRAN (G1–G3) do catálogo (conflicts/catalog.json). Cada entrada do
 * catálogo fixa a topologia e o tráfego por argumentos:
 *
 *   --gnbs="x,y,z;x,y,z;..."            posições dos gNBs (m)
 *   --ueGroups="n,cx,cy,rmin,rmax,intervalMs,vx,vy,z;..."
 *                                        grupos de UEs: quantidade, centro e raio do disco,
 *                                        intervalo entre pacotes (ms), velocidade constante
 *                                        (m/s; 0,0 = parado) e altura (m)
 *   --channel=UMa|UMi|RMa|InH|InH-OfficeMixed|NTN-Rural|NTN-Suburban|NTN-Urban|NTN-DenseUrban
 *                                        Nos cenários NTN-*, o modelo de canal do 5G-LENA exige posições
 *                                        geocêntricas: --gnbs passa a ser "lat,lon,alt_m" e o centro de cada
 *                                        grupo de UEs (cx, cy) passa a ser lat, lon; rmin/rmax seguem em
 *                                        metros e a velocidade é ignorada (terminais fixos).
 *   --txPowerDbm=43                       potência inicial de todos os gNBs
 *   --centralFreq, --bandwidth, --packetSize, --simTime, --seed, --run, --disableSrs
 *   --actionSchedule, --kpiPeriod         atuação e KPIs (rdl-nr-common.h)
 *   --powerAllocation=used|bw             alocação de potência do 5G-LENA (docs/17 §2.3). Padrão
 *                                        "used" (UniformPowerAllocUsed, como nas campanhas
 *                                        anteriores); "bw" = UniformPowerAllocBw (PSD constante)
 *
 * Saídas: rdl_kpi_timeseries.csv (vazão e atraso por célula com pacotes na janela),
 * rdl_cell_state.csv (ocupação, potência e estado de todas as células por janela, docs/17 §3.2)
 * e rdl_actuation_log.csv.
 *
 * Toda a pilha de rádio é NR (NrHelper), com EPC, attach ao gNB mais próximo, X2 entre gNBs
 * e handover; as ações do baseline (PRB_QUOTA, TX_POWER, HANDOVER, CELL_STATE) são aplicadas
 * na RAN durante a simulação por RdlActuation.
 * =========================================================================================
 */

#include "ns3/antenna-module.h"
#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"

#if __has_include("ns3/nr-module.h")
#include "ns3/nr-module.h"
#define HAS_NR_MODULE 1
#include "rdl-nr-common.h"
#else
#define HAS_NR_MODULE 0
#endif

#include <cmath>
#include <sstream>
#include <string>
#include <vector>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("ScenarioRdlMulticell");

static std::vector<std::vector<double>>
ParseTable(const std::string& text, size_t columns, const std::string& what)
{
    std::vector<std::vector<double>> rows;
    std::stringstream rowsStream(text);
    std::string row;
    while (std::getline(rowsStream, row, ';'))
    {
        if (row.empty())
        {
            continue;
        }
        std::vector<double> values;
        std::stringstream cols(row);
        std::string cell;
        while (std::getline(cols, cell, ','))
        {
            values.push_back(std::stod(cell));
        }
        if (values.size() != columns)
        {
            NS_FATAL_ERROR(what << ": esperado " << columns << " valores por item, recebido '" << row << "'");
        }
        rows.push_back(values);
    }
    if (rows.empty())
    {
        NS_FATAL_ERROR(what << " vazio");
    }
    return rows;
}

int
main(int argc, char* argv[])
{
    std::string gnbs = "0,0,25;200,0,25";
    std::string ueGroups = "20,0,0,10,80,10,0,0,1.5;20,200,0,10,80,10,0,0,1.5";
    std::string channel = "UMa";
    double txPowerDbm = 43.0;
    double simTime = 30.0;
    double centralFreq = 3.5e9;
    double bandwidth = 100e6;
    uint32_t packetSize = 1024;
    uint32_t randomSeed = 1001;
    uint32_t runIndex = 1;
    std::string actionSchedule = "";
    double kpiPeriod = 0.1;
    bool disableSrs = true;
    std::string powerAllocation = "used";

    CommandLine cmd(__FILE__);
    cmd.AddValue("gnbs", "Posicoes dos gNBs: x,y,z;x,y,z", gnbs);
    cmd.AddValue("ueGroups", "Grupos de UEs: n,cx,cy,rmin,rmax,intervalMs,vx,vy,z;...", ueGroups);
    cmd.AddValue("channel", "Cenario de canal 3GPP do 5G-LENA (UMa, RMa, NTN-Rural, ...)", channel);
    cmd.AddValue("txPowerDbm", "Potencia inicial dos gNBs (dBm)", txPowerDbm);
    cmd.AddValue("simTime", "Tempo de simulacao (s)", simTime);
    cmd.AddValue("centralFreq", "Frequencia central (Hz)", centralFreq);
    cmd.AddValue("bandwidth", "Largura de banda (Hz)", bandwidth);
    cmd.AddValue("packetSize", "Tamanho do pacote UDP (bytes)", packetSize);
    cmd.AddValue("seed", "Semente do gerador ns-3", randomSeed);
    cmd.AddValue("run", "Indice da repeticao", runIndex);
    cmd.AddValue("actionSchedule", "CSV de acoes aplicadas na RAN (baseline)", actionSchedule);
    cmd.AddValue("kpiPeriod", "Periodo da serie de KPIs (s)", kpiPeriod);
    cmd.AddValue("disableSrs", "Desativar SRS (contorno do 5G-LENA v5.1 em handover)", disableSrs);
    cmd.AddValue("powerAllocation", "Alocacao de potencia: used (padrao do 5G-LENA) ou bw (PSD constante)",
                 powerAllocation);
    cmd.Parse(argc, argv);

    if (disableSrs)
    {
        Config::SetDefault("ns3::NrMacSchedulerNs3::EnableSrsInUlSlots", BooleanValue(false));
        Config::SetDefault("ns3::NrMacSchedulerNs3::EnableSrsInFSlots", BooleanValue(false));
    }
    SeedManager::SetSeed(randomSeed);
    SeedManager::SetRun(runIndex);
    Time::SetResolution(Time::NS);

    auto gnbTable = ParseTable(gnbs, 3, "--gnbs");
    auto ueTable = ParseTable(ueGroups, 9, "--ueGroups");

    const bool ntn = channel.rfind("NTN", 0) == 0;
    NodeContainer gnbNodes;
    gnbNodes.Create(gnbTable.size());
    if (ntn)
    {
        // Satélite fixo na posição geográfica dada (instantâneo de um feixe LEO)
        for (uint32_t i = 0; i < gnbNodes.GetN(); ++i)
        {
            Ptr<GeocentricConstantPositionMobilityModel> m = CreateObject<GeocentricConstantPositionMobilityModel>();
            m->SetGeographicPosition(Vector(gnbTable[i][0], gnbTable[i][1], gnbTable[i][2]));
            gnbNodes.Get(i)->AggregateObject(m);
        }
    }
    else
    {
        Ptr<ListPositionAllocator> gnbPos = CreateObject<ListPositionAllocator>();
        for (const auto& g : gnbTable)
        {
            gnbPos->Add(Vector(g[0], g[1], g[2]));
        }
        MobilityHelper gnbMobility;
        gnbMobility.SetPositionAllocator(gnbPos);
        gnbMobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
        gnbMobility.Install(gnbNodes);
    }

    NodeContainer ueNodes;
    std::vector<double> ueInterval;
    Ptr<UniformRandomVariable> uni = CreateObject<UniformRandomVariable>();
    for (const auto& grp : ueTable)
    {
        uint32_t n = static_cast<uint32_t>(grp[0]);
        NodeContainer group;
        group.Create(n);
        if (ntn)
        {
            // Terminais em terra, num disco de raio [rmin, rmax] m ao redor de (lat, lon)
            const double kMetersPerDegLat = 111320.0;
            for (uint32_t i = 0; i < n; ++i)
            {
                double r = uni->GetValue(grp[3], grp[4]);
                double theta = uni->GetValue(0.0, 2 * M_PI);
                double lat = grp[1] + r * std::cos(theta) / kMetersPerDegLat;
                double lon = grp[2] + r * std::sin(theta) / (kMetersPerDegLat * std::cos(grp[1] * M_PI / 180.0));
                Ptr<GeocentricConstantPositionMobilityModel> m = CreateObject<GeocentricConstantPositionMobilityModel>();
                m->SetGeographicPosition(Vector(lat, lon, grp[8]));
                group.Get(i)->AggregateObject(m);
                ueInterval.push_back(grp[5]);
            }
            ueNodes.Add(group);
            continue;
        }
        MobilityHelper m;
        std::ostringstream rho;
        rho << "ns3::UniformRandomVariable[Min=" << grp[3] << "|Max=" << grp[4] << "]";
        std::ostringstream x, y, z;
        x << grp[1];
        y << grp[2];
        z << grp[8];
        m.SetPositionAllocator("ns3::RandomDiscPositionAllocator", "X", StringValue(x.str()), "Y",
                               StringValue(y.str()), "Z", StringValue(z.str()), "Rho", StringValue(rho.str()));
        bool moving = grp[6] != 0.0 || grp[7] != 0.0;
        m.SetMobilityModel(moving ? "ns3::ConstantVelocityMobilityModel" : "ns3::ConstantPositionMobilityModel");
        m.Install(group);
        if (moving)
        {
            for (uint32_t i = 0; i < group.GetN(); ++i)
            {
                group.Get(i)->GetObject<ConstantVelocityMobilityModel>()->SetVelocity(Vector(grp[6], grp[7], 0.0));
            }
        }
        for (uint32_t i = 0; i < n; ++i)
        {
            ueInterval.push_back(grp[5]);
        }
        ueNodes.Add(group);
    }
    std::cout << "[RDL-SCN] " << gnbNodes.GetN() << " gNB(s), " << ueNodes.GetN() << " UE(s), canal " << channel
              << ", " << txPowerDbm << " dBm" << std::endl;

#if HAS_NR_MODULE
    RdlSetPowerAllocation(powerAllocation); // antes de instalar os dispositivos
    RdlNrNetwork net = RdlBuildNrNetwork(gnbNodes, ueNodes, centralFreq, bandwidth, channel);
    for (uint32_t g = 0; g < net.gnbDevs.GetN(); ++g)
    {
        Ptr<NrGnbNetDevice> dev = DynamicCast<NrGnbNetDevice>(net.gnbDevs.Get(g));
        for (uint32_t b = 0; b < dev->GetCcMapSize(); ++b)
        {
            NrHelper::GetGnbPhy(dev, b)->SetTxPower(txPowerDbm);
        }
    }
    ApplicationContainer serverApps;
    ApplicationContainer clientApps;
    RdlInstallDownlinkUdp(net, ueNodes, serverApps, clientApps, 7001,
                          [&](uint32_t i) { return MilliSeconds(ueInterval[i]); }, packetSize);
    RdlActuation actuation(net.nrHelper, net.gnbDevs, net.ueDevs);
    actuation.Load(actionSchedule);
    RdlKpiSampler kpi(net.ueDevs, kpiPeriod, simTime);
    RdlCellEnergySampler cellState(net.gnbDevs, net.ueDevs, kpiPeriod, simTime);
#else
    NS_FATAL_ERROR("Este cenario requer o modulo 5G-LENA (nr).");
    ApplicationContainer serverApps;
    ApplicationContainer clientApps;
#endif

    serverApps.Start(Seconds(0.5));
    serverApps.Stop(Seconds(simTime));
    clientApps.Start(Seconds(1.0));
    clientApps.Stop(Seconds(simTime));

    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll();
    Simulator::Stop(Seconds(simTime));
    Simulator::Run();
    monitor->CheckForLostPackets();
    monitor->SerializeToXmlFile("flowmonitor_scenario_rdl_multicell.xml", true, true);
    Simulator::Destroy();
    return 0;
}
