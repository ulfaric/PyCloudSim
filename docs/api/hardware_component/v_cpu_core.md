# vCPUCore

The class "vCPUCore" serves as the implementation of CPU cores within the simulation. It includes two mandatory attributes: frequency and instructions-per-cycle, which determine the computational capacity of the core. The computational capacity is represented as a "Resource" object from the "Akatosh" library, enabling withdrawal or return of the available amount during the simulation. The "vCPUCore" is responsible for allocating the computational power to the assigned processes and reclaiming the distributed amount once the execution of the assigned process is complete. In the event that the "vCPUCore" is arbitrarily powered off during the simulation, all processes currently in execution will be considered as failed.

:::PyCloudSim.entity.v_cpu_core.vCPUCore

## Usage Example

```python
from PyCloudSim.entity import vCPUCore
core = vCPUCore(
        1, #IPC
        4000, #Frequency in Mhz
        "Core 0", # Label
        0, # Created at 0s
    )
# power on CPU core
core.power_on(at=0)
# power off CPU core
core.powere_off(at=10)
# terminate the CPU core
core.terminate(at=12)
```
