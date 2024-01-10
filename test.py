from ipaddress import IPv4Network
from typing import List

from Akatosh import instant_event

from PyCloudSim import simulation
from PyCloudSim.entity import vAPICall, vDefaultMicroservice, vHost, vSwitch, vGateway, vUser
from PyCloudSim.monitor.container_monitor import LoggingContainerMonitor
from PyCloudSim.scheduler import DefaultContainerScheduler

DefaultContainerScheduler()

LoggingContainerMonitor(label="Container Monitor", sample_period=0.01)

core_switch = vSwitch(
    ipc=1,
    frequency=5000,
    num_cores=4,
    cpu_tdps=150,
    cpu_mode=1,
    ram=8,
    rom=16,
    subnet=IPv4Network("192.168.0.0/24"),
    label="Core",
    create_at=0,
)
core_switch.power_on(0)

gateway = vGateway()
user = vUser(gateway)

simulation.network.add_link(core_switch, gateway, 1, 0)


hosts: List[vHost] = []
for i in range(5):
    host = vHost(
        ipc=1,
        frequency=5000,
        num_cores=4,
        cpu_tdps=150,
        cpu_mode=2,
        ram=2,
        rom=16,
        label=str(i),
        create_at=0,
    )

    host.power_on(0)
    simulation.network.add_link(host, core_switch, 1, 0)
    hosts.append(host)

ms_1 = vDefaultMicroservice(
    cpu=100,
    cpu_limit=500,
    ram=500,
    ram_limit=1000,
    label="test 1",
    image_size=100,
    create_at=0,
    deamon=True,
    min_num_instances=2,
    max_num_instances=4,
)

ms_2 = vDefaultMicroservice(
    cpu=100,
    cpu_limit=500,
    ram=500,
    ram_limit=1000,
    label="test 2",
    image_size=100,
    create_at=0,
    deamon=True,
    min_num_instances=3,
    max_num_instances=4,
)


@instant_event(at=0.11)
def test():
    test = vAPICall(
        src=user,
        dst=ms_2,
        src_process_length=10,
        dst_process_length=10,
        ack_process_length=10,
        num_src_packets=10,
        num_ret_packets=10,
        num_ack_packets=10,
        src_packet_size=100,
        ret_packet_size=100,
        ack_packet_size=100,
        priority=1,
        create_at=0.11,
        label="test",
    )
    
    post_test = vAPICall(
        src=ms_2,
        dst=ms_1,
        src_process_length=10,
        dst_process_length=10,
        ack_process_length=10,
        num_src_packets=10,
        num_ret_packets=10,
        num_ack_packets=10,
        src_packet_size=100,
        ret_packet_size=100,
        ack_packet_size=100,
        priority=1,
        create_at=0.11,
        label="Post test",
        precursor=test,
    )

@instant_event(at=0.12)
def test2():
    ms_1.containers[0].fail(0.12)

simulation.debug(False)
simulation.simulate(1.5)
simulation.network.plot("./output/topology.png")
