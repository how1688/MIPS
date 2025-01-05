class HazardHandler:
    def __init__(self):
        self.stall_detected = False
        self.hazard_forwarded = False

    def detect_hazard(self, current_stage, previous_stage, reg_dst):
        """Detect hazards between the current and previous pipeline stages."""
        hazard_detected = False
        if reg_dst in [current_stage['rs'], current_stage['rt']]:
            hazard_detected = True
        return hazard_detected

    def handle_stalling(self, current_stage, memory_read):
        """Handle stalling if the data is not ready from memory."""
        if memory_read and current_stage['rd'] in [current_stage['rs'], current_stage['rt']]:
            self.stall_detected = True
            return True
        self.stall_detected = False
        return False

    def handle_forwarding(self, current_stage, previous_stage, alu_result):
        """Handle forwarding data from previous stages to resolve hazards."""
        forwarded_values = {}
        if previous_stage['reg_write']:
            if previous_stage['rd'] == current_stage['rs']:
                forwarded_values['rs'] = alu_result
                self.hazard_forwarded = True
            if previous_stage['rd'] == current_stage['rt']:
                forwarded_values['rt'] = alu_result
                self.hazard_forwarded = True
        return forwarded_values


class PipelineRegister:
    def __init__(self):
        self.reg = {
            "rs": 0,
            "rt": 0,
            "rd": 0,
            "alu_result": 0,
            "reg_write": False,
            "mem_read": False,
            "mem_write": False,
        }

    def update(self, **kwargs):
        for key, value in kwargs.items():
            self.reg[key] = value


class ForwardingAndStallingUnit:
    def __init__(self):
        self.hazard_handler = HazardHandler()
        self.pipeline_stages = {
            "EX_MEM": PipelineRegister(),
            "MEM_WB": PipelineRegister(),
        }

    def process_pipeline(self, current_stage):
        """Check and resolve hazards, stalling, and forwarding in the pipeline."""
        forwarding_values = {}

        # Forwarding from MEM/WB to EX
        forwarding_values.update(
            self.hazard_handler.handle_forwarding(
                current_stage,
                self.pipeline_stages["MEM_WB"].reg,
                self.pipeline_stages["MEM_WB"].reg['alu_result'],
            )
        )

        # Forwarding from EX/MEM to EX
        forwarding_values.update(
            self.hazard_handler.handle_forwarding(
                current_stage,
                self.pipeline_stages["EX_MEM"].reg,
                self.pipeline_stages["EX_MEM"].reg['alu_result'],
            )
        )

        # Check for stalling
        stall = self.hazard_handler.handle_stalling(
            current_stage, self.pipeline_stages["EX_MEM"].reg['mem_read']
        )

        return stall, forwarding_values

    def update_pipeline_stage(self, stage_name, **kwargs):
        self.pipeline_stages[stage_name].update(**kwargs)


# Example usage in a MIPS simulator
if __name__ == "__main__":
    forwarding_unit = ForwardingAndStallingUnit()

    # Simulate pipeline stages
    current_instruction = {"rs": 1, "rt": 2, "rd": 3}

    # Update EX_MEM stage
    forwarding_unit.update_pipeline_stage("EX_MEM", rs=1, rt=2, rd=3, alu_result=10, reg_write=True, mem_read=True)

    # Update MEM_WB stage
    forwarding_unit.update_pipeline_stage("MEM_WB", rs=4, rt=5, rd=6, alu_result=20, reg_write=True)

    # Process hazards and forwarding
    stall, forwarding_values = forwarding_unit.process_pipeline(current_instruction)

    print("Stall Detected:", stall)
    print("Forwarding Values:", forwarding_values)
