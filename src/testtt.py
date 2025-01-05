class CPU:
    def __init__(self):
        # 初始化暫存器和記憶體
        self.registers = [1 for _ in range(32)]  # 所有暫存器初始值為 1
        self.registers[0] = 0  # $0 暫存器永遠為 0
        self.memory = [1 for _ in range(32)]  # 記憶體大小為 32 words，每個位置的初始值為 1
        self.pc = 0  # 程式計數器
        self.instructions = []  # 儲存解析後的指令
        self.result_log = []  # 執行過程記錄
        self.pipeline_log = []  # 每個時鐘週期的執行記錄

        # 流水線寄存器
        self.IF_ID = None
        self.ID_EX = None
        self.EX_MEM = None
        self.MEM_WB = None

        # 控制信號模板
        self.control_signals = {
            "RegDst": "X",
            "ALUSrc": "X",
            "Branch": "X",
            "MemRead": "X",
            "MemWrite": "X",
            "RegWrite": "X",
            "MemToReg": "X",
        }

    def load_instructions(self, instructions):
        self.instructions = instructions

    def detect_hazard(self):
        """
        檢測資料冒險，設置停滯信號。
        """
        if self.ID_EX and self.ID_EX.get("opcode") == "LW":
            dest = self.ID_EX.get("destination")
            if self.IF_ID and dest in [self.IF_ID.get("source1"), self.IF_ID.get("source2")]:
                return True
        return False

    def fetch_next_instruction(self):
        """
        抓取下一條指令。
        """
        if self.pc < len(self.instructions):
            instruction = self.instructions[self.pc]
            self.pc += 1
            return instruction
        return None

    def format_control_signals(self, signals):
        return " ".join([f"{key}={value}" for key, value in signals.items()])

    def execute_cycle(self, cycle):
        """
        執行單個時鐘周期。
        """
        log_entry = [f"Clock Cycle {cycle}:"]

        # Write Back (WB)
        if self.MEM_WB:
            if self.MEM_WB["opcode"] == "add":
                self.registers[self.MEM_WB["destination"]] = self.MEM_WB["value"]
            elif self.MEM_WB["opcode"] == "lw":
                self.registers[self.MEM_WB["destination"]] = self.MEM_WB["value"]

            log_entry.append(f"{self.MEM_WB['opcode']} WB RegWrite={self.MEM_WB['control'].get('RegWrite', 'X')} MemToReg={self.MEM_WB['control'].get('MemToReg', 'X')}")

        # Memory Access (MEM)
        if self.EX_MEM:
            if self.EX_MEM["opcode"] == "lw":
                address = self.EX_MEM["address"]
                value = self.memory[address]
                self.EX_MEM["value"] = value
            elif self.EX_MEM["opcode"] == "sw":
                address = self.EX_MEM["address"]
                address = int(address/4)
                print(address, self.registers[self.EX_MEM["destination"]])
                self.memory[address] = self.registers[self.EX_MEM["destination"]]

            log_entry.append(f"{self.EX_MEM['opcode']} MEM Branch={self.EX_MEM['control'].get('Branch', 'X')} MemRead={self.EX_MEM['control'].get('MemRead', 'X')} MemWrite={self.EX_MEM['control'].get('MemWrite', 'X')} RegWrite={self.EX_MEM['control'].get('RegWrite', 'X')} MemToReg={self.EX_MEM['control'].get('MemToReg', 'X')}")

        # Execute (EX)
        if self.ID_EX:
            if self.ID_EX["opcode"] == "add":
                source1 = self.registers[self.ID_EX["source1"]]
                source2 = self.registers[self.ID_EX["source2"]]
                self.ID_EX["value"] = source1 + source2
            elif self.ID_EX["opcode"] in ["lw", "sw"]:
                base = self.registers[self.ID_EX["base"]]
                offset = self.ID_EX["offset"]
                self.ID_EX["address"] = base + offset

            log_entry.append(f"{self.ID_EX['opcode']} EX RegDst={self.ID_EX['control'].get('RegDst', 'X')} ALUSrc={self.ID_EX['control'].get('ALUSrc', 'X')} Branch={self.ID_EX['control'].get('Branch', 'X')} MemRead={self.ID_EX['control'].get('MemRead', 'X')} MemWrite={self.ID_EX['control'].get('MemWrite', 'X')} RegWrite={self.ID_EX['control'].get('RegWrite', 'X')} MemToReg={self.ID_EX['control'].get('MemToReg', 'X')}")

        # Instruction Decode (ID)
        if self.IF_ID:
            log_entry.append(f"{self.IF_ID['opcode']} ID")

        # Instruction Fetch (IF)
        next_instr = None
        if not self.detect_hazard():
            next_instr = self.fetch_next_instruction()
            if next_instr:
                log_entry.append(f"{next_instr['opcode']} IF")

        self.pipeline_log.append("\n".join(log_entry))

        # 更新流水線寄存器
        self.MEM_WB = self.EX_MEM
        self.EX_MEM = self.ID_EX
        self.ID_EX = self.IF_ID
        self.IF_ID = next_instr

    def print_results(self):
        with open("C:\\Users\\user\\Downloads\\SampleProject (1)\\SampleProject\\inputs\\test2_output.txt", "w") as f:
            f.write("# Example 1 Case\n")
            f.write("\n## Each clocks\n")
            for log in self.pipeline_log:
                f.write(log + "\n\n")

            f.write("\n## Final Result:\n")
            f.write(f"Total Cycles: {len(self.pipeline_log)}\n")
            f.write("\nFinal Register Values:\n")
            f.write(" ".join(map(str, self.registers)) + "\n")
            f.write("\nFinal Memory Values:\n")
            f.write(" ".join(map(str, self.memory[:32])) + "\n")


def parse_instruction(line):
    parts = line.split()
    opcode = parts[0]
    operands = parts[1:] if len(parts) > 1 else []
    operands = [op.replace(",", "") for op in operands]
    if opcode in ["lw", "sw"]:
        # 解析 LW/SW 的操作數，例如 "8($0)"
        # print(operands)
        offset, base = operands[1].split('(')
        offset = int(offset)
        base = int(base.replace("$", "").replace(")", ""))
        return {
            "opcode": opcode,
            "operands": operands,
            "control": {
                "RegDst": "X",
                "ALUSrc": "1",
                "Branch": "X",
                "MemRead": "1" if opcode == "LW" else "X",
                "MemWrite": "1" if opcode == "SW" else "X",
                "RegWrite": "1" if opcode == "LW" else "X",
                "MemToReg": "1" if opcode == "LW" else "X",
            },
            "source1": base,  # 基址寄存器
            "source2": None,
            "destination": int(operands[0].replace("$", "")),  # 目標寄存器
            "base": base,  # 基址寄存器
            "offset": offset,  # 偏移量
        }
    elif opcode in ["add", "sub"]:
        # 解析算術指令，例如 "ADD $1, $2, $3"
        rd = int(operands[0].replace("$", "").replace(",", ""))
        rs = int(operands[1].replace("$", "").replace(",", ""))
        rt = int(operands[2].replace("$", ""))
        return {
            "opcode": opcode,
            "operands": operands,
            "control": {
                "RegDst": "1",
                "ALUSrc": "0",
                "Branch": "X",
                "MemRead": "X",
                "MemWrite": "X",
                "RegWrite": "1",
                "MemToReg": "X",
            },
            "source1": rs,
            "source2": rt,
            "destination": rd,
        }
    elif opcode == "beq":
        # 解析分支指令，例如 "BEQ $1, $2, 10"
        rs = int(operands[0].replace("$", "").replace(",", ""))
        rt = int(operands[1].replace("$", "").replace(",", ""))
        offset = int(operands[2])
        return {
            "opcode": opcode,
            "operands": operands,
            "control": {
                "RegDst": "X",
                "ALUSrc": "0",
                "Branch": "1",
                "MemRead": "X",
                "MemWrite": "X",
                "RegWrite": "X",
                "MemToReg": "X",
            },
            "source1": rs,
            "source2": rt,
            "destination": None,
            "offset": offset,
        }
    else:
        # 其他不支持的指令
        raise ValueError(f"Unsupported opcode: {opcode}")



if __name__ == "__main__":
    cpu = CPU()

    # 從檔案讀取指令
    input_file = "C:\\Users\\user\\Downloads\\SampleProject (1)\\SampleProject\\inputs\\test2.txt"
    with open(input_file, "r") as f:
        instructions = [parse_instruction(line.strip()) for line in f if line.strip() and not line.startswith("#")]

    cpu.load_instructions(instructions)
    cycle = 1
    while cpu.pc < len(cpu.instructions) or any([cpu.IF_ID, cpu.ID_EX, cpu.EX_MEM, cpu.MEM_WB]):
        cpu.execute_cycle(cycle)
        cycle += 1
    cpu.print_results()
