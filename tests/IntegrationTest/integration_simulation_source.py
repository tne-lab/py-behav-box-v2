from pybehave.Sources.Source import Source
import time

class IntegrationSimulationSource(Source):

    def write_component(self, component_id: str, msg: bool) -> None:
        # only react when the task turns a light ON
        if "nose_poke_lights" in component_id and msg is True:
            time.sleep(0.5)  #sims animal noticing the light
            poke_id = component_id.replace("nose_poke_lights", "nose_pokes") 
            self.update_component(poke_id, True)            
            time.sleep(0.2)  # duration of the poke           
            self.update_component(poke_id, False)



