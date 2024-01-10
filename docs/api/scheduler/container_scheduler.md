The "ContainerScheduler" class is responsible for allocating suitable "vHost" instances to "vContainer" instances based on the available CPU and RAM resources. The scheduling process is implemented as an event that is triggered whenever a new "vContainer" is created or a "vContainer" is terminated. Only one scheduling process can exist at any time during the simulation.

The "ContainerScheduler" class includes an abstract member function called "findHost", which allows developers to customize the conditions for determining which "vHost" instances are eligible for hosting a specific "vContainer". By implementing the "findHost" function, different scheduling strategies can be employed based on specific requirements and constraints.

PyCloudSim provides several default schedulers that can be used with the "ContainerScheduler" class:

1. "Bestfit" scheduler: This scheduler finds the most utilized "vHost" instance that still has available resources to host the "vContainer" being scheduled.
2. "Worstfit" scheduler: This scheduler finds the most underutilized "vHost" instance that still has available resources to host the "vContainer" being scheduled.
3. "Random" scheduler: This scheduler allocates the "vContainer" to a random "vHost" instance that has sufficient resources.

Only one "ContainerScheduler" can be defined and used in the simulation. If multiple "ContainerScheduler" instances are initialized, the last one defined will be used during the simulation.

The general procedure followed by the "ContainerScheduler" involves evaluating the available resources of each "vHost" instance and selecting the most suitable "vHost" to host the "vContainer" based on the defined scheduling strategy. This process ensures efficient resource allocation and utilization in the simulated cloud environment.

:::PyCloudSim.scheduler.container_scheduler