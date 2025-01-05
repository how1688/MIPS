class CPU:
    def __init__(self):
        # 初始化暫存器、記憶體和流水線寄存器
        self.registers = [0 for _ in range(32)]  # 暫存器初始值為 0
        self.memory = [0 for _ in range(1024)]  # 記憶體初始值為 0
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
            log_entry.append(f"{self.MEM_WB['opcode']} WB {self.format_control_signals(self.MEM_WB.get('control', {}))}")

        # Memory Access (MEM)
        if self.EX_MEM:
            log_entry.append(f"{self.EX_MEM['opcode']} MEM {self.format_control_signals(self.EX_MEM.get('control', {}))}")

        # Execute (EX)
        if self.ID_EX:
            log_entry.append(f"{self.ID_EX['opcode']} EX {self.format_control_signals(self.ID_EX.get('control', {}))}")

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
        with open("C:\\Users\\user\\Documents\\GitHub\\MIPS\\outputs\\test1_output.txt", "w") as f:
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
    return {
        "opcode": opcode,
        "operands": operands,
        "control": {
            "RegDst": "1" if opcode in ["ADD", "SUB"] else "X",
            "ALUSrc": "1" if opcode in ["LW", "SW"] else "X",
            "Branch": "1" if opcode == "BEQ" else "X",
            "MemRead": "1" if opcode == "LW" else "X",
            "MemWrite": "1" if opcode == "SW" else "X",
            "RegWrite": "1" if opcode in ["ADD", "SUB", "LW"] else "X",
            "MemToReg": "1" if opcode == "LW" else "X",
        },
        "source1": operands[1][1:-1] if opcode in ["LW", "SW"] else operands[1] if len(operands) > 1 else None,
        "source2": operands[2] if opcode in ["ADD", "SUB", "BEQ"] else None,
        "destination": operands[0] if opcode in ["ADD", "SUB", "LW"] else None,
    }


if __name__ == "__main__":
    cpu = CPU()

    # 從檔案讀取指令
    input_file = "C:\\Users\\user\\Documents\\GitHub\\MIPS\\inputs\\test1.txt"
    with open(input_file, "r") as f:
        instructions = [parse_instruction(line.strip()) for line in f if line.strip() and not line.startswith("#")]

    cpu.load_instructions(instructions)
    cycle = 1
    while cpu.pc < len(cpu.instructions) or any([cpu.IF_ID, cpu.ID_EX, cpu.EX_MEM, cpu.MEM_WB]):
        cpu.execute_cycle(cycle)
        cycle += 1
    cpu.print_results()
