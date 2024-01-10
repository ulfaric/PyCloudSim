The class "vSwitch" and "vRouter" are the implementation of the switch and router in the simulated network topology. "vSwitch" and "vRouter" will create a scheduling process to schedule all "vPacket" in the queue to "vNIC" for transmission based on the priority of "vPacket" when a "vPacket" arrived or has been transmitted. The scheduling process is implemented as an "event and only one scheduling process for each "vSwitch" or "vRouter" can exist at any time. If a "vSwitch" or "vRouter" does not have enough RAM to accommodate a "vPacket" upon receiving it, the "vPacket" will be dropped. The difference between "vSwitch" and "vRouter" are:

1.  For a "vSwitch," the IP address attribute of its "vNIC" is set to none, and its "vNIC" can be connected to any entity.

2.  For a "vRouter," the IP address of each of its "vNIC" instances must belong to a unique network and its "vNIC" cannot be connected to a "vHost" entity.

:::PyCloudSim.entity.v_switch.vSwitch