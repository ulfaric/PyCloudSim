# Welcome to PyCloudSim Docs

PyCloudSim is a simulation toolkit written in python to simulate cloud computing with incorporation of Network Service and Service Funtion Chain. It is based a light-weighted discrete event simulation library Akatosh. PyCloudSim is inspired by CloudSim and CloudSim Plus. However, PyCloudSim simulates the computation fundamentally differently. 

In CloudSim, a computing work is defined as a Cloudlet with a given length. Then, the Cloudlet is scheduled onto VM. The Cloudlet included two functions defined for CPU usage and RAM usage. Hence, the actual resource usages are just random numbers generated from a predefined function.

In PyCloudSim, a computing work is defined as vProcess which has a instruction length. Then a set of random bytes are generated as "instructons" to determine the RAM usage for this vProcess. Then, PyCloudSim simulates the CPU for scheduling process on multiple core for execution. Hence, vProcess could occupiy one or more vCPUCore at the same time. Each vCPUCore consumes the "insrtuctions" according to schedule from vCPU. While vCPUCore is executing "instructions", its computational power ( defined by frequency and instructions per cycle ) is considered as been used. After executing, the vCPUCore will regain the used computational power. When a vProcess has its "instructions" all been executed, then it is complete. Therefore, the CPU and RAM usage patterns simulated by PyCloudSim are not merely random numbers, they are more realistic to how a real computer should behave.

In addtion, PyCloudSim also simulates the network traffic. That is, vPackets will be created along vProcess. Then, vNIC will queue and transmit them! So you can simulate a API call between vContainers! The API call is simulated as vRequest and only when its associated vProcess is complete and all its associated vPackets have reached the destination, the vRequest is complete! This is impossible within CloudSim or CloudSim Plus.

