TrafPy Manager
==============
.. warning::
    The ``trafpy.manager`` package is still a working progress. The aim of it is
    to integrate easily with demand data generated by the ``trafpy.generator`` package to enable
    end-to-end network benchmarking, standardisation, learning-agent training etc. using only TrafPy.
    Most people will find the ``trafpy.generator`` module the only one they need
    in order to generate traffic and import it into their own simulations.


As this tutorial has shown, TrafPy can be used as a stand-alone tool for generating, 
replicating, and reproducing network traffic data using the ``trafpy.generator``
package and the interactive Jupyter Notebook tool. TrafPy also comes with another
package, ``trafpy.manager``, which uses generated network traffic data to simulate
networks. ``trafpy.manager`` can be used as a tool for e.g. benchmarking and comparing
different network managers (routers, schedulers, machine placers, etc.) and for e.g.
a reinforcement learning training environment.

``trafpy.manager`` works by initialising a network environment (e.g. a data centre network)
which itself is initialised with a TrafPy demand object, a scheduling agent, a routing agent,
and a network object. TrafPy comes with pre-built versions of each of these, but
has been designed such that users can write their own e.g. scheduler and benchmark
it with ``trafpy.manager`` and with network demands generated with ``trafpy.generator``.

Import the ``trafpy.generator`` package and the requried objects from the
``trafpy.manager`` package::

    import trafpy.generator as tpg
    from trafpy.manager import Demand, RWA, SRPT, DCN
    from imports import config

Where the ``config.py`` file might be defined as

.. literalinclude:: imports/config.py

Load your previously saved TrafPy demand data dictionary (see the TrafPy Generator
section above)::

    demand_data = tpg.unpickle_data(path_to_load='data/flow_centric_demand_data.pickle',zip_data=True)

Initialise the ``trafpy.manager`` objects::

    network = tpg.gen_simple_network(ep_label=config.ENDPOINT_LABEL,num_channels=config.NUM_CHANNELS)
    demand = Demand(demand_data=demand_data)
    rwa = RWA(tpg.gen_channel_names(config.NUM_CHANNELS), config.NUM_K_PATHS)
    scheduler = SRPT(network, rwa, slot_size=config.SLOT_SIZE)
    env = DCN(network, demand, scheduler, slot_size=config.SLOT_SIZE, max_flows=config.MAX_FLOWS, max_time=config.MAX_TIME)

And run your simulation using the standard OpenAI Gym reinforcement learning
framework::

    for episode in range(config.NUM_EPISODES):
    print('\nEpisode {}/{}'.format(episode+1,config.NUM_EPISODES))
    observation = env.reset(config.LOAD_DEMANDS)
    while True:
        print('Time: {}'.format(env.curr_time))
        action = scheduler.get_action(observation)
        print('Action:\n{}'.format(action))
        observation, reward, done, info = env.step(action)
        if done:
            print('Episode finished.')
            break

When completed, you can print TrafPy's summary of the scheduling session::

    >>> env.get_scheduling_session_summary(print_summary=True)
    -=-=-=-=-=-=-= Scheduling Session Ended -=-=-=-=-=-=-=
    SUMMARY:
    ~* General Info *~
    Total session duration: 80000.0 time units
    Total number of generated demands (jobs or flows): 10
    Total info arrived: 56623.0 info units
    Load: 0.7672975615099775 info unit demands arrived per unit time (from first to last flow arriving)
    Total info transported: 56623.0 info units
    Throughput: 0.7077875 info units transported per unit time

    ~* Flow Info *~
    Total number generated flows (src!=dst,dependency_type=='data_dep'): 10
    Time first flow arrived: 0.0 time units
    Time last flow arrived: 73795.36028834846 time units
    Time first flow completed: 10000.0 time units
    Time last flow completed: 80000.0 time units
    Total number of demands that arrived and became flows: 10
    Total number of flows that were completed: 10
    Total number of dropped flows + flows in queues at end of session: 0
    Average FCT: 7669.998225473775 time units
    99th percentile FCT: 18035.645744379803 time units

