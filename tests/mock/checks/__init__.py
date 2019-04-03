import logging


class AgentCheck:
    def __init__(self, name, init_config, agentConfig, instances):
        self.init_config = init_config
        self.instances = instances
        self.log = logging.getLogger("unittest")

    def increment(self, *args, **kwargs):
        pass

    def histogram(self, *args, **kwargs):
        pass

    def _roll_up_instance_metadata(self, *args, **kwargs):
        pass
