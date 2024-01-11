# Enity

The `Enity` is a class from discrete event simulation library `Akatosh`. All PyCloudSim simulated entities are built based on it.

An entity could be considered as an actor/NPC which lives within the simulated envrionment. The `NPC` comes to life with `create()` function and dies with `terminate()` function. During its life-cycle, the `NPC` can engage instant event which are the event that happens once at a time point, or continous event that happens multiple times for a period of time. Any future event will be canceled upon the `temination` of the `NPC`.

Therefore, fundamentally the PyCloudSim is a series of `NPC` playing the roles of all things involed in cloud computing and networking, with a series of instant event and continous event.

For more information, you can visit the `Akatosh` documentation site: <https://ulfaric.github.io/Akatosh/>
