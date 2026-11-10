/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/**
 * =========================================================================================
 * Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
 * Arquivo: rdl-nr-common.h
 *
 * Infraestrutura comum dos cenários ns-3.48 + 5G-LENA v5.1:
 *   1. RdlBuildNrNetwork / RdlInstallDownlinkUdp: rede NR funcional (EPC, host remoto,
 *      IPs, attach ao gNB mais próximo, X2 entre gNBs) e tráfego UDP downlink.
 *   2. RdlActuation: aplica na RAN, durante a simulação, as ações de controle de um
 *      cronograma CSV (time_s,gnb,parameter,value,ue,xapp_id,action_id):
 *        PRB_QUOTA -> máscara de RBGs do escalonador (SetDlNotchedRbgMask)
 *        TX_POWER  -> potência de transmissão do gNB (NrGnbPhy::SetTxPower)
 *        HANDOVER  -> handover X2 dos UEs servidos pelo gNB de origem (NrHelper::HandoverRequest)
 *        CELL_STATE-> 0: célula "desligada", emulada com potência mínima (-30 dBm), porque o
 *                     5G-LENA v5.1 não desliga a célula nem dispara RLF; 1: restaura a potência
 *      Não há lógica de decisão nem de segurança aqui: o cronograma vem do baseline
 *      avaliado (B0..B3). Cada ação aplicada é registrada em rdl_actuation_log.csv.
 *   3. RdlKpiSampler: série temporal de vazão e atraso por célula, medida nos UdpServer
 *      dos UEs (rdl_kpi_timeseries.csv), com progresso impresso ao vivo.
 * Saídas em std::cout (NS_LOG é removido no perfil otimizado).
 * =========================================================================================
 */
#ifndef RDL_NR_COMMON_H
#define RDL_NR_COMMON_H

#include "ns3/antenna-module.h"
#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/nr-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/seq-ts-header.h"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

namespace ns3
{

// ---------------------------------------------------------------------------------------
// Rede NR funcional
// ---------------------------------------------------------------------------------------

struct RdlNrNetwork
{
    Ptr<NrHelper> nrHelper;
    Ptr<NrPointToPointEpcHelper> epcHelper;
    NetDeviceContainer gnbDevs;
    NetDeviceContainer ueDevs;
    Ptr<Node> remoteHost;
    Ipv4InterfaceContainer ueIp;
};

/**
 * Instala gNBs e UEs NR (banda única), EPC, host remoto ligado ao PGW, IPs dos UEs,
 * attach ao gNB mais próximo e, com mais de um gNB, interfaces X2 (necessárias ao handover).
 * A mobilidade dos nós deve estar instalada antes.
 */
inline RdlNrNetwork
RdlBuildNrNetwork(NodeContainer gnbNodes,
                  NodeContainer ueNodes,
                  double centralFreq,
                  double bandwidth,
                  const std::string& channelScenario = "")
{
    RdlNrNetwork net;
    net.epcHelper = CreateObject<NrPointToPointEpcHelper>();
    Ptr<IdealBeamformingHelper> beamforming = CreateObject<IdealBeamformingHelper>();
    beamforming->SetAttribute("BeamformingMethod", TypeIdValue(DirectPathBeamforming::GetTypeId()));
    net.nrHelper = CreateObject<NrHelper>();
    net.nrHelper->SetBeamformingHelper(beamforming);
    net.nrHelper->SetEpcHelper(net.epcHelper);

    net.nrHelper->SetUeAntennaAttribute("NumRows", UintegerValue(1));
    net.nrHelper->SetUeAntennaAttribute("NumColumns", UintegerValue(1));
    net.nrHelper->SetUeAntennaAttribute("AntennaElement", PointerValue(CreateObject<IsotropicAntennaModel>()));
    net.nrHelper->SetGnbAntennaAttribute("NumRows", UintegerValue(1));
    net.nrHelper->SetGnbAntennaAttribute("NumColumns", UintegerValue(1));
    net.nrHelper->SetGnbAntennaAttribute("AntennaElement", PointerValue(CreateObject<IsotropicAntennaModel>()));

    CcBwpCreator ccBwpCreator;
    CcBwpCreator::SimpleOperationBandConf bandConf(centralFreq, bandwidth, 1);
    OperationBandInfo band = ccBwpCreator.CreateOperationBandContiguousCc(bandConf);
    Ptr<NrChannelHelper> channelHelper = CreateObject<NrChannelHelper>();
    if (!channelScenario.empty())
    {
        // Cenário 3GPP do 5G-LENA (UMa, UMi-StreetCanyon, RMa, InH-*, NTN-Rural, NTN-Urban...).
        // Vazio: as fábricas padrão, como nos cenários S0–S7.
        channelHelper->ConfigureFactories(channelScenario, "Default", "ThreeGpp");
    }
    channelHelper->AssignChannelsToBands({band});
    BandwidthPartInfoPtrVector allBwps = CcBwpCreator::GetAllBwps({band});

    net.gnbDevs = net.nrHelper->InstallGnbDevice(gnbNodes, allBwps);
    net.ueDevs = net.nrHelper->InstallUeDevice(ueNodes, allBwps);

    InternetStackHelper internet;
    internet.Install(ueNodes);
    net.ueIp = net.epcHelper->AssignUeIpv4Address(NetDeviceContainer(net.ueDevs));

    if (gnbNodes.GetN() > 1)
    {
        net.nrHelper->AddX2Interface(gnbNodes);
    }
    net.nrHelper->AttachToClosestGnb(net.ueDevs, net.gnbDevs);

    Ptr<Node> pgw = net.epcHelper->GetPgwNode();
    NodeContainer remoteHostContainer;
    remoteHostContainer.Create(1);
    net.remoteHost = remoteHostContainer.Get(0);
    internet.Install(remoteHostContainer);

    PointToPointHelper p2ph;
    p2ph.SetDeviceAttribute("DataRate", DataRateValue(DataRate("100Gb/s")));
    p2ph.SetDeviceAttribute("Mtu", UintegerValue(2500));
    p2ph.SetChannelAttribute("Delay", TimeValue(MilliSeconds(1)));
    NetDeviceContainer internetDevices = p2ph.Install(pgw, net.remoteHost);

    Ipv4AddressHelper ipv4h;
    ipv4h.SetBase("1.0.0.0", "255.0.0.0");
    ipv4h.Assign(internetDevices);

    Ipv4StaticRoutingHelper routing;
    Ptr<Ipv4StaticRouting> remoteRouting = routing.GetStaticRouting(net.remoteHost->GetObject<Ipv4>());
    remoteRouting->AddNetworkRouteTo(Ipv4Address("7.0.0.0"), Ipv4Mask("255.0.0.0"), 1);
    for (uint32_t i = 0; i < ueNodes.GetN(); ++i)
    {
        Ptr<Ipv4StaticRouting> ueRouting = routing.GetStaticRouting(ueNodes.Get(i)->GetObject<Ipv4>());
        ueRouting->SetDefaultRoute(net.epcHelper->GetUeDefaultGatewayAddress(), 1);
    }
    return net;
}

/**
 * Tráfego UDP downlink: um UdpServer por UE e um UdpClient no host remoto.
 * intervalOf(i) define o intervalo entre pacotes do UE i.
 */
inline void
RdlInstallDownlinkUdp(const RdlNrNetwork& net,
                      NodeContainer ueNodes,
                      ApplicationContainer& serverApps,
                      ApplicationContainer& clientApps,
                      uint16_t basePort,
                      const std::function<Time(uint32_t)>& intervalOf,
                      uint32_t packetSize)
{
    for (uint32_t i = 0; i < ueNodes.GetN(); ++i)
    {
        uint16_t port = basePort + i;
        UdpServerHelper server(port);
        serverApps.Add(server.Install(ueNodes.Get(i)));
        UdpClientHelper client(net.ueIp.GetAddress(i), port);
        client.SetAttribute("MaxPackets", UintegerValue(0xFFFFFFFF));
        client.SetAttribute("Interval", TimeValue(intervalOf(i)));
        client.SetAttribute("PacketSize", UintegerValue(packetSize));
        clientApps.Add(client.Install(net.remoteHost));
    }
}

// ---------------------------------------------------------------------------------------
// Atuação na RAN a partir de um cronograma
// ---------------------------------------------------------------------------------------

class RdlActuation
{
  public:
    RdlActuation(Ptr<NrHelper> nrHelper, NetDeviceContainer gnbDevs, NetDeviceContainer ueDevs)
        : m_nrHelper(nrHelper),
          m_gnbDevs(gnbDevs),
          m_ueDevs(ueDevs)
    {
    }

    /** Lê o cronograma e agenda cada ação. Retorna o número de ações agendadas. */
    uint32_t Load(const std::string& path)
    {
        if (path.empty())
        {
            std::cout << "[RDL-ACT] sem cronograma de ações: execução sem atuação na RAN" << std::endl;
            return 0;
        }
        std::ifstream in(path);
        if (!in.is_open())
        {
            NS_FATAL_ERROR("Cronograma de ações não encontrado: " << path);
        }
        m_log.open("rdl_actuation_log.csv");
        m_log << "time_s,gnb,cell_id,parameter,value,ue,xapp_id,action_id,status,detail\n";
        std::string line;
        uint32_t count = 0;
        std::getline(in, line); // cabeçalho
        while (std::getline(in, line))
        {
            if (line.empty() || line[0] == '#')
            {
                continue;
            }
            std::vector<std::string> f = Split(line);
            if (f.size() < 7)
            {
                NS_FATAL_ERROR("Linha inválida no cronograma: " << line);
            }
            Action a{std::stod(f[0]), static_cast<uint32_t>(std::stoul(f[1])), f[2], std::stod(f[3]),
                     std::stoi(f[4]), f[5], f[6]};
            Simulator::Schedule(Seconds(a.time), &RdlActuation::Apply, this, a);
            ++count;
        }
        std::cout << "[RDL-ACT] " << count << " ações agendadas a partir de " << path << std::endl;
        return count;
    }

  private:
    struct Action
    {
        double time;
        uint32_t gnb;
        std::string parameter;
        double value;
        int ue;
        std::string xapp;
        std::string id;
    };

    static std::vector<std::string> Split(const std::string& s)
    {
        std::vector<std::string> out;
        std::stringstream ss(s);
        std::string item;
        while (std::getline(ss, item, ','))
        {
            out.push_back(item);
        }
        return out;
    }

    uint16_t CellIdOf(uint32_t gnb) const
    {
        return DynamicCast<NrGnbNetDevice>(m_gnbDevs.Get(gnb))->GetCellId();
    }

    void Record(const Action& a, const std::string& status, const std::string& detail)
    {
        double now = Simulator::Now().GetSeconds();
        uint16_t cell = a.gnb < m_gnbDevs.GetN() ? CellIdOf(a.gnb) : 0;
        std::cout << "[RDL-ACT] t=" << std::fixed << std::setprecision(3) << now << "s gnb=" << a.gnb
                  << " cell=" << cell << " " << a.parameter << "=" << a.value << " xapp=" << a.xapp
                  << " id=" << a.id << " -> " << status << " (" << detail << ")" << std::endl;
        m_log << now << "," << a.gnb << "," << cell << "," << a.parameter << "," << a.value << "," << a.ue
              << "," << a.xapp << "," << a.id << "," << status << "," << detail << "\n";
        m_log.flush();
    }

    void Apply(Action a)
    {
        if (a.gnb >= m_gnbDevs.GetN())
        {
            Record(a, "REJECTED_BY_TOPOLOGY", "gNB inexistente");
            return;
        }
        Ptr<NrGnbNetDevice> gnb = DynamicCast<NrGnbNetDevice>(m_gnbDevs.Get(a.gnb));
        uint32_t nBwp = gnb->GetCcMapSize();
        if (a.parameter == "TX_POWER")
        {
            for (uint32_t b = 0; b < nBwp; ++b)
            {
                NrHelper::GetGnbPhy(gnb, b)->SetTxPower(a.value);
            }
            std::ostringstream d;
            d << "TxPower=" << NrHelper::GetGnbPhy(gnb, 0)->GetTxPower() << " dBm";
            Record(a, "APPLIED", d.str());
        }
        else if (a.parameter == "PRB_QUOTA")
        {
            std::ostringstream d;
            for (uint32_t b = 0; b < nBwp; ++b)
            {
                Ptr<NrMacSchedulerNs3> sched = DynamicCast<NrMacSchedulerNs3>(NrHelper::GetScheduler(gnb, b));
                Ptr<NrGnbPhy> phy = NrHelper::GetGnbPhy(gnb, b);
                Ptr<NrGnbMac> mac = NrHelper::GetGnbMac(gnb, b);
                if (!sched)
                {
                    Record(a, "UNSUPPORTED", "escalonador sem máscara de RBG");
                    return;
                }
                uint32_t nRbg = phy->GetRbNum() / mac->GetNumRbPerRbg();
                double quota = std::min(100.0, std::max(0.0, a.value));
                uint32_t allowed = std::max<uint32_t>(1, static_cast<uint32_t>(std::lround(quota / 100.0 * nRbg)));
                std::vector<bool> mask(nRbg, false);
                std::fill(mask.begin(), mask.begin() + std::min(allowed, nRbg), true);
                sched->SetDlNotchedRbgMask(mask);
                d << "RBG " << allowed << "/" << nRbg << (a.value != quota ? " (fora de 0-100, limitado pela PHY)" : "");
            }
            Record(a, "APPLIED", d.str());
        }
        else if (a.parameter == "HANDOVER")
        {
            uint32_t target = static_cast<uint32_t>(a.value);
            if (target >= m_gnbDevs.GetN() || target == a.gnb)
            {
                Record(a, "REJECTED_BY_TOPOLOGY", "gNB de destino inválido");
                return;
            }
            uint16_t sourceCell = CellIdOf(a.gnb);
            uint16_t targetCell = CellIdOf(target);
            uint32_t moved = 0;
            for (uint32_t u = 0; u < m_ueDevs.GetN(); ++u)
            {
                if (a.ue >= 0 && static_cast<uint32_t>(a.ue) != u)
                {
                    continue;
                }
                Ptr<NrUeNetDevice> ue = DynamicCast<NrUeNetDevice>(m_ueDevs.Get(u));
                Ptr<NrUeRrc> rrc = ue->GetRrc();
                if (rrc->GetCellId() == sourceCell && rrc->GetState() == NrUeRrc::CONNECTED_NORMALLY)
                {
                    // Handovers escalonados (kHandoverSpacing por UE): disparar todos no mesmo
                    // instante leva o 5G-LENA v5.1 a abortar em NrSpectrumPhy::StartRxSrs
                    // ("Not allowed state for starting SRS reception").
                    m_nrHelper->HandoverRequest(kHandoverSpacing * moved, ue, gnb, targetCell);
                    ++moved;
                }
            }
            std::ostringstream d;
            d << moved << " UE(s) cell " << sourceCell << " -> " << targetCell << " (escalonados a cada "
              << kHandoverSpacing.GetMilliSeconds() << " ms)";
            Record(a, moved > 0 ? "APPLIED" : "NO_EFFECT", d.str());
        }
        else if (a.parameter == "CELL_STATE")
        {
            std::ostringstream d;
            if (a.value == 0.0)
            {
                if (m_savedTxPower.find(a.gnb) == m_savedTxPower.end())
                {
                    m_savedTxPower[a.gnb] = NrHelper::GetGnbPhy(gnb, 0)->GetTxPower();
                }
                for (uint32_t b = 0; b < nBwp; ++b)
                {
                    NrHelper::GetGnbPhy(gnb, b)->SetTxPower(kSleepTxPowerDbm);
                }
                d << "sleep emulado: TxPower=" << kSleepTxPowerDbm << " dBm";
                Record(a, "APPLIED", d.str());
            }
            else
            {
                auto it = m_savedTxPower.find(a.gnb);
                if (it == m_savedTxPower.end())
                {
                    Record(a, "NO_EFFECT", "célula já ativa");
                    return;
                }
                for (uint32_t b = 0; b < nBwp; ++b)
                {
                    NrHelper::GetGnbPhy(gnb, b)->SetTxPower(it->second);
                }
                d << "ativa: TxPower=" << it->second << " dBm";
                m_savedTxPower.erase(it);
                Record(a, "APPLIED", d.str());
            }
        }
        else
        {
            Record(a, "UNSUPPORTED", "parâmetro sem mapeamento na RAN simulada");
        }
    }

    const double kSleepTxPowerDbm = -30.0;
    std::map<uint32_t, double> m_savedTxPower;
    const Time kHandoverSpacing = MilliSeconds(10);
    Ptr<NrHelper> m_nrHelper;
    NetDeviceContainer m_gnbDevs;
    NetDeviceContainer m_ueDevs;
    std::ofstream m_log;
};

// ---------------------------------------------------------------------------------------
// Série temporal de KPIs por célula
// ---------------------------------------------------------------------------------------

class RdlKpiSampler
{
  public:
    RdlKpiSampler(NetDeviceContainer ueDevs, double periodS, double simTime)
        : m_period(periodS),
          m_simTime(simTime)
    {
        for (uint32_t u = 0; u < ueDevs.GetN(); ++u)
        {
            m_ueByNode[ueDevs.Get(u)->GetNode()->GetId()] = DynamicCast<NrUeNetDevice>(ueDevs.Get(u));
        }
        m_out.open("rdl_kpi_timeseries.csv");
        m_out << "t_end_s,cell_id,rx_packets,rx_bytes,throughput_mbps,mean_delay_ms\n";
        // ns-3.48: UdpServer herda de SinkApplication; o trace sem endereço dispara antes
        // de o SeqTsHeader ser removido, o que permite medir o atraso fim a fim.
        Config::Connect("/NodeList/*/ApplicationList/*/$ns3::UdpServer/RxWithoutAddress",
                        MakeCallback(&RdlKpiSampler::OnRx, this));
        Simulator::Schedule(Seconds(m_period), &RdlKpiSampler::Flush, this);
    }

  private:
    struct Acc
    {
        uint64_t packets{0};
        uint64_t bytes{0};
        double delaySumMs{0.0};
    };

    void OnRx(std::string context, Ptr<const Packet> packet)
    {
        uint32_t nodeId = std::stoul(context.substr(10, context.find('/', 10) - 10)); // "/NodeList/<id>/"
        auto it = m_ueByNode.find(nodeId);
        uint16_t cell = it != m_ueByNode.end() ? it->second->GetRrc()->GetCellId() : 0;
        Acc& acc = m_window[cell];
        acc.packets++;
        acc.bytes += packet->GetSize();
        SeqTsHeader seqTs;
        Ptr<Packet> copy = packet->Copy();
        if (copy->GetSize() >= seqTs.GetSerializedSize() && copy->PeekHeader(seqTs))
        {
            acc.delaySumMs += (Simulator::Now() - seqTs.GetTs()).GetSeconds() * 1000.0;
        }
    }

    void Flush()
    {
        double now = Simulator::Now().GetSeconds();
        double totalMbps = 0.0;
        double delaySum = 0.0;
        uint64_t packets = 0;
        for (const auto& [cell, acc] : m_window)
        {
            double mbps = acc.bytes * 8.0 / (m_period * 1e6);
            double delay = acc.packets ? acc.delaySumMs / acc.packets : 0.0;
            m_out << std::fixed << std::setprecision(3) << now << "," << cell << "," << acc.packets << ","
                  << acc.bytes << "," << mbps << "," << delay << "\n";
            totalMbps += mbps;
            delaySum += acc.delaySumMs;
            packets += acc.packets;
        }
        m_out.flush();
        if (std::fmod(now + 1e-9, 1.0) < m_period - 1e-9)
        {
            std::cout << "[RDL-KPI] t=" << std::fixed << std::setprecision(1) << now
                      << "s vazao=" << std::setprecision(2) << totalMbps << " Mbps atraso="
                      << (packets ? delaySum / packets : 0.0) << " ms" << std::endl;
        }
        m_window.clear();
        if (now + m_period <= m_simTime + 1e-9)
        {
            Simulator::Schedule(Seconds(m_period), &RdlKpiSampler::Flush, this);
        }
    }

    double m_period;
    double m_simTime;
    std::map<uint32_t, Ptr<NrUeNetDevice>> m_ueByNode;
    std::map<uint16_t, Acc> m_window;
    std::ofstream m_out;
};

} // namespace ns3

#endif // RDL_NR_COMMON_H
