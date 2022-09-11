#!/usr/bin/python3

import ts3
import logging
from prometheus_client import CollectorRegistry, Gauge, write_to_textfile

METRICS_TO_READ = {
    # "METRIC": "description",
    "virtualserver_port": "port the server is running on",
    "virtualserver_id": "id of the virtual server",
    "virtualserver_status": "1 if server is online, 0 if server is offline",
    "virtualserver_voiceclientsonline": "online voice clients",
    "virtualserver_queryclientsonline": "online query clients",
    "virtualserver_maxclients": "clientslots of the virtual server",
    "virtualserver_channelsonline": "counter of the channels on the server",
    "virtualserver_reserved_slots": "reserved clientslots",
    "virtualserver_uptime": "uptime",
    "virtualserver_total_bytes_uploaded": "bytes uploaded",
    "virtualserver_total_bytes_downloaded": "bytes downloaded",
    "virtualserver_total_packetloss_control": "packetloss of control packages",
    "virtualserver_total_packetloss_speech": "packetloss of speech packages",
    "virtualserver_total_packetloss_keepalive": "packetloss of keepalive packages",
    "virtualserver_total_packetloss_total": "packetloss of all packages",
    "virtualserver_total_ping": "client average RTT",
    "connection_bytes_sent_total": "bytes sent",
    "connection_bytes_received_total": "bytes received",
    "connection_bytes_sent_speech": "speech bytes sent",
    "connection_bytes_received_speech": "speech bytes received",
    "connection_bytes_sent_control": "control bytes sent",
    "connection_bytes_received_control": "control bytes received",
    "connection_bytes_sent_keepalive": "keepalive bytes sent",
    "connection_bytes_received_keepalive": "keepalive bytes received",
    "connection_packets_sent_total": "packages sent",
    "connection_packets_received_total": "packages received",
    "connection_packets_sent_speech": "speech packages sent",
    "connection_packets_received_speech": "speech packages received",
    "connection_packets_sent_control": "control packages sent",
    "connection_packets_received_control": "control packages received",
    "connection_packets_sent_keepalive": "keepalive packages sent",
    "connection_packets_received_keepalive": "keepalive packages received",
    "connection_bandwidth_sent_last_second_total": "bytes sent last second",
    "connection_bandwidth_received_last_second_total": "bytes received last second"
}


class Teamspeak3MetricService:
    def __init__(self, metrics):
        self.host = 'localhost'
        self.port = '10011'
        self.username = 'serveradmin'
        self.password = 'PUTPASSWORDHERE'
        self.filepath = '/var/lib/prometheus/node-exporter/teamspeak.prom'

        self.metrics = metrics
        self.ts3conn = ts3.query.TS3ServerConnection(
            "telnet://" + self.username + ":" + self.password + "@" + self.host + ":" + self.port)

    def read(self):
        registry = CollectorRegistry()
        # get the serverlist of running virtual servers
        serverlist_response = self.ts3conn.exec_("serverlist")
        if not serverlist_response.error["id"] == "0":
            logging.critical("Error retrieving serverlist")
            exit(1)

        servers = serverlist_response.parsed

        # get metrics for all virtual servers
        for server in servers:
            virtualserver_id = server["virtualserver_id"]
            self.ts3conn.exec_("use", sid=virtualserver_id)

            # retrieve serverinfo for this specific server
            serverinfo_response = self.ts3conn.exec_("serverinfo")
            if not serverinfo_response.error["id"] == "0":
                logging.critical("Error retrieving serverinfo")
                exit(1)
            serverinfo_response = serverinfo_response[0]

            # Note, the TS3Response class and therefore the TS3QueryResponse
            # class too, can work as a rudimentary container. So, these two
            # commands are equal:
            for metricset in self.metrics:
                metric = metricset
                description = self.metrics[metricset]

                gauge = Gauge("teamspeak_" + metric, description, ["virtualserver_id"], registry=registry)

                if metric == 'virtualserver_voiceclientsonline':
                    gauge.labels(virtualserver_id).set(int(serverinfo_response['virtualserver_clientsonline']) - int(
                        serverinfo_response['virtualserver_queryclientsonline']))
                elif metric == 'virtualserver_status':
                    if serverinfo_response['virtualserver_status'] == "online":
                        gauge.labels(virtualserver_id).set(1)
                    else:
                        gauge.labels(virtualserver_id).set(0)
                else:
                    gauge.labels(virtualserver_id).set(serverinfo_response[metric])
        write_to_textfile(self.filepath, registry)


ts3Service = Teamspeak3MetricService(METRICS_TO_READ)
ts3Service.read()

