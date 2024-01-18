# Quick Start Guide

## Installation

PyCloudSIm can be easily installed via pip with:

    pip install -U PyCloudSim

Its dependencies will be automatically installed!

If you are using PyCloudSim for your research, please use the following refernece.

```bibtex
@INPROCEEDINGS{10329606,
  author={Ren, Yifei and Agrawal, Himanshu and Ferdosian, Nasim and Nejabati, Reza},
  booktitle={2023 IEEE Conference on Network Function Virtualization and Software Defined Networks (NFV-SDN)}, 
  title={PyCloudSim: Modernized Cloud Computing Simulation Framework with the Incorporation of SFC}, 
  year={2023},
  volume={},
  number={},
  pages={92-98},
  doi={10.1109/NFV-SDN59219.2023.10329606}}

```

## Basic Example

Let's sceipt a basic example of simulation that consists five vHost, one switch and two vMicroservice. To start, we firstly import the modules:

    from PyCloudSim.entity import vDefaultMicroservice, vHost, vSwitch

Then, we can create a core switch that connects all the simulated hosts:

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

Remeber you must call the power on function to actualy power on the simulated switch. Then, we create our hosts and link them with the switch:

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

Next, we create our microservices:

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

The "vDefaultMicroservice" is similar to a Kubernetes deployment that the number of container instances schedule up and down based on the utilization threshold. The default configuration is scale up whenever CPU or RAM reach 80% and scale down when they reach 20%.

Next, we create simulated API calls that engages with the microservice:

from Akatosh import instant_event

    @instant_event(at=0.11)
    def test():
        test = vAPICall(
            src=ms_1,
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

In this simple example, we simply one API call after another. You can create a SFC process with a group of API Calls chaining together. This example can be considered as an SFC with two microservices only.

Next, we set the container scheduler and use a built in container monitor:

    from PyCloudSim.monitor.container_monitor import LoggingContainerMonitor
    from PyCloudSim.scheduler import DefaultContainerScheduler

    DefaultContainerScheduler()

    LoggingContainerMonitor(label="Container Monitor", sample_period=0.01)

Finally, we start the simulation:

    simulation.debug(False)
    simulation.simulate(1.5)

# Change log

## 10.01.2024
1. Implemented Dataframe monitors for container and hosts. These monitors collect the telemetries as pandas dataframe.

## 12.12.2023
1. Updated with newest version of Akatosh to speed up the simulation.
2. Implemeted simulated user and it association with simulated gateway.
3. Default microservice is now able to recover failed container instances automatically.
