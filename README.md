# README #

The EnergyPlus agent is a VOLTTRON agent that enables co-simulation of EnergyPlus with VOLTTRON using EnergyPlus' built-in BCVTB interface. This README contains instructions for installing dependencies and running a simple co-simulation example.

## DEPENDENCIES ##

The following instructions assume you have already cloned this repository, and that you have already installed the [PubSub](https://github.com/VOLTTRON/volttron-pubsub) modules into the VOLTTRON environment's site-packages directory.

Make sure you have installed [VOLTTRON](https://github.com/VOLTTRON/volttron) and its dependencies.

You must have an installation of EnergyPlus, preferably version 8.4 or higher. The EnergyPlus model included is in version 8.4 format. 

EnergyPlus uses the [Building Control Virtual Test Bed](https://simulationresearch.lbl.gov/bcvtb) for socket communication. You do not need to install the BCVTB; the library is included in this repository. However, the BCVTB library does require Java.

## INSTALLATION ##

Enable the VOLTTRON virtual environment
~~~
$ . [VOLTTRON repository location]/env/bin/activate
~~~
Install the package.
~~~
$ cd [volttron-energyplus repository location]
$ python setup.py install
~~~

## AGENT CONFIGURATION FOR EXAMPLE ##

EnergyPlus needs to know where to find the model and weather files used for simulation. You will need to edit the 'energyplus' configuration file included in the [volttron-energyplus repository location]/config/ directory if you are running the agents from the command line. If running from your IDE, you may nor may not have to modify the paths depending on how the IDE is configured. Specifically, the following parameters need to be updated:
~~~
...
	"model" : "[volttron-energyplus repository location]/eplus/1ZoneUncontrolled.idf",
	"weather" : "[volttron-energyplus repository location]/eplus/WeatherData/USA_CO_Golden-NREL.724666_TMY3.epw",
	"bcvtb_home" : "[volttron-energyplus repository location]/bcvtb/",
...
~~~
If you do not have the USA_CO_Golden-NREL.724666_TMY3.epw weather file, simply substitute for another.

## PACKAGING AND RUNNING EXAMPLE ##

Navigate to VOLTTRON source directory
~~~
$ cd [VOLTTRON repository location]
~~~
Enable the VOLTTRON virtual environment (if not already enabled).
~~~
$ . env/bin/activate
~~~
Run VOLTTRON
~~~
$ volttron -vv -l [logfilepath.log] &
~~~
Export environment variables required for make-agent.sh
~~~
$ export SOURCE=[volttron-energyplus repository location]/pnnl/energyplusagent/
$ export CONFIG=[volttron-energyplus repository location]/config/energyplus
$ export TAG=energyplus
~~~
Run the VOLTTRON make-agent.sh script
~~~
$ . scripts/core/make-agent.sh
~~~
View the log. The agent will indicate that it has started an EnergyPlus simulation.
~~~
$ tail -f [logfilepath.log]
~~~
~~~
...
2016-04-25 10:42:29,308 (energyplus-0.1 6990) pnnl.pubsubagent.pubsub.agent INFO: subscribed to test/extLightSchedule
2016-04-25 10:42:29,308 (energyplus-0.1 6990) pnnl.pubsubagent.pubsub.agent INFO: subscribed to test/shadeSchedule
2016-04-25 10:42:29,309 (energyplus-0.1 6990) energyplus.agent DEBUG: Bound to 59636 on 'cdcorbin-VirtualBox'
2016-04-25 10:42:29,309 (energyplus-0.1 6990) energyplus.agent DEBUG: Working in '/home/cdcorbin/Documents/EnergyPlus'
2016-04-25 10:42:29,309 (energyplus-0.1 6990) energyplus.agent DEBUG: Running: cd /home/cdcorbin/Documents/EnergyPlus; export BCVTB_HOME=.; energyplus -w /usr/local/EnergyPlus-8-4-0/WeatherData/USA_CO_Golden-NREL.724666_TMY3.epw -r /home/cdcorbin/Documents/EnergyPlus/1ZoneUncontrolled.idf
2016-04-25 10:42:29,313 (energyplus-0.1 6990) energyplus.agent DEBUG: Starting socket server
2016-04-25 10:42:29,313 (energyplus-0.1 6990) energyplus.agent DEBUG: server now listening
2016-04-25 10:42:29,531 (energyplus-0.1 6990) energyplus.agent DEBUG: Connected with 127.0.0.1:33129
2016-04-25 10:42:29,768 (energyplus-0.1 6990) energyplus.agent INFO: Received message from EnergyPlus: 2 0 3 0 0 0.000000000000000e+00 1.000000000000000e+01 0.000000000000000e+00 0.000000000000000e+00
2016-04-25 10:42:29,768 (energyplus-0.1 6990) pnnl.pubsubagent.pubsub.agent INFO: Sending: test/outdoorDryBulb 10.0
2016-04-25 10:42:29,771 (energyplus-0.1 6990) pnnl.pubsubagent.pubsub.agent INFO: Sending: test/horizontalRadiation 0.0
2016-04-25 10:42:29,773 (energyplus-0.1 6990) pnnl.pubsubagent.pubsub.agent INFO: Sending: test/incidentRadiation 0.0
...
~~~

At this point, the agent will simply sit and wait for others to send it the inputs it needs to proceed to the next time step. To see the simulation in action, package and install the two example agents included in the repository.
Export the environment variables and install the agents
~~~
$ export SOURCE=[volttron-energyplus repository location]/pnnl/lightcontrolagent/
$ export CONFIG=[volttron-energyplus repository location]/config/lightcontrol
$ export TAG=lightcontrol
$ . scripts/core/make-agent.sh
$ export SOURCE=[volttron-energyplus repository location]/pnnl/shadecontrolagent/
$ export CONFIG=[volttron-energyplus repository location]/config/shadecontrol
$ export TAG=shadecontrol
$ . scripts/core/make-agent.sh
~~~
View the log. You will observe the agents log the messages sent back and forth during the EnergyPlus simulation.
~~~
$ tail -f [logfilepath.log]
~~~
~~~
...
2016-04-25 11:14:21,742 (energyplus-0.1 7468) pnnl.pubsubagent.pubsub.agent INFO: Sending: test/outdoorDryBulb 10.0
2016-04-25 11:14:21,748 (shadecontrol-0.1 7367) pnnl.pubsubagent.pubsub.agent INFO: Received: test/outdoorDryBulb 10.0
2016-04-25 11:14:21,755 (energyplus-0.1 7468) pnnl.pubsubagent.pubsub.agent INFO: Sending: test/horizontalRadiation 0.0
2016-04-25 11:14:21,760 (lightcontrol-0.1 7277) pnnl.pubsubagent.pubsub.agent INFO: Received: test/horizontalRadiation 0.0
2016-04-25 11:14:21,760 (lightcontrol-0.1 7277) pnnl.pubsubagent.pubsub.agent INFO: Sending: test/extLightSchedule 1
2016-04-25 11:14:21,762 (energyplus-0.1 7468) pnnl.pubsubagent.pubsub.agent INFO: Sending: test/incidentRadiation 0.0
2016-04-25 11:14:21,774 (energyplus-0.1 7468) pnnl.pubsubagent.pubsub.agent INFO: Received: test/extLightSchedule 1
2016-04-25 11:14:21,779 (shadecontrol-0.1 7367) pnnl.pubsubagent.pubsub.agent INFO: Received: test/incidentRadiation 0.0
2016-04-25 11:14:21,779 (shadecontrol-0.1 7367) pnnl.pubsubagent.pubsub.agent INFO: Sending: test/shadeSchedule 0
2016-04-25 11:14:21,789 (energyplus-0.1 7468) pnnl.pubsubagent.pubsub.agent INFO: Received: test/shadeSchedule 0
2016-04-25 11:14:21,789 (energyplus-0.1 7468) energyplus.agent INFO: Sending message to EnergyPlus: 2 0 2 0 0 86400.0 1 0
2016-04-25 11:14:21,789 (energyplus-0.1 7468) energyplus.agent INFO: Received message from EnergyPlus: 2 0 3 0 0 8.640000000000000e+04 1.000000000000000e+01 0.000000000000000e+00 0.000000000000000e+00
...
~~~

Once the simulation ends, the agents will stop sending messages. You may re-start the simulation by stopping and restarting the agents.