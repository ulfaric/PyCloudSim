The class "vMicroservice" is designed to resemble a deployment in Kubernetes, comprising one or more instances of the "vContainer" class. It encompasses the following important member functions and behaviours:

1. Recovery of Failed vContainers: When any "vContainer" crashes or encounters a failure, the "vMicroservice" includes a member function that facilitates the recovery of these failed containers. This recovery process is initiated immediately after a container failure or after a specific delay, as determined by the simulation.
2. Horizontal Scaling: The "vMicroservice" is responsible for horizontal scaling, which involves dynamically adjusting the number of "vContainer" instances based on certain conditions. If the overall CPU/RAM usage of all current "vContainer" instances exceeds a predetermined threshold, a new "vContainer" will be created to handle the increased workload. Conversely, if a "vContainer" is identified as being under-utilized, it may be forcibly terminated. Horizontal scaling is implemented as an event, and only one horizontal scaling event can occur per "vMicroservice" instance at any given time during the simulation.
3. Readiness of vMicroservice: The readiness of a "vMicroservice" is determined by the number of current "vContainer" instances reaching the minimum required number. This minimum requirement ensures that the "vMicroservice" is considered ready for operation.

In summary, the "vMicroservice" class emulates the behaviour of deployments in Kubernetes, facilitating the management of "vContainer" instances, recovery from failures, horizontal scaling, and readiness evaluation within the simulated cloud environment.

:::PyCloudSim.entity.v_microservice.vMicroservice

#Default vMicroservice
:::PyCloudSim.entity.v_microservice.vDefaultMicroservice