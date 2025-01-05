class MIPSSimulator:
    def __init__(self):
        # 初始化記憶體與暫存器
        self.memory = [0] * 1024
        self.registers = [0] * 32
        self.registers[0] = 0  # $0 永遠為 0

        # 初始化流水線暫存器
        self.pipeline_registers = {
            "IF/ID": None,
            "ID/EX": None,
            "EX/MEM": None,
            "MEM/WB": None,
        }

        # 程式計數器與輸出日誌
        self.pc = 0
        self.instructions = []  # 指令列表
        self.running = True  # 控制執行流程
        self.clock_log = []  # 用於記錄每個 Clock Cycle 的狀態

    def load_instructions_from_file(self, input_file):
        """從檔案載入 MIPS 指令到記憶體"""
        with open(input_file, 'r') as file:
            self.instructions = [line.strip() for line in file.readlines() if line.strip() and not line.startswith("#")]

    def log_stage(self, clock_cycle, stage, details):
        """記錄流水線每階段的狀態"""
        self.clock_log.append(f"Clock Cycle {clock_cycle}:\n{stage} {details}")

    def fetch(self, clock_cycle):
        """IF 階段: 抓取指令"""
        if self.pc < len(self.instructions):
            instruction = self.instructions[self.pc]
            self.pipeline_registers["IF/ID"] = instruction
            self.log_stage(clock_cycle, instruction.split()[0].lower(), "IF")
            self.pc += 1
        else:
            self.pipeline_registers["IF/ID"] = None
            self.running = False

    def decode(self, clock_cycle):
        """ID 階段: 解碼指令並讀取操作數"""
        instruction = self.pipeline_registers["IF/ID"]
        if not instruction:
            return

        self.log_stage(clock_cycle, instruction.split()[0].lower(), "ID")
        self.pipeline_registers["ID/EX"] = instruction

    def execute(self, clock_cycle):
        """執行指令"""
        instruction = self.pipeline_registers["ID/EX"]
        if not instruction:
            return

        opcode = instruction.split()[0].lower()
        self.log_stage(clock_cycle, opcode, "EX RegDst=X ALUSrc=X Branch=X MemRead=X MemWrite=X RegWrite=X MemToReg=X")
        self.pipeline_registers["EX/MEM"] = instruction

    def memory_access(self, clock_cycle):
        """訪問記憶體"""
        instruction = self.pipeline_registers["EX/MEM"]
        if not instruction:
            return

        opcode = instruction.split()[0].lower()
        self.log_stage(clock_cycle, opcode, "MEM Branch=X MemRead=X MemWrite=X RegWrite=X MemToReg=X")
        self.pipeline_registers["MEM/WB"] = instruction

    def write_back(self, clock_cycle):
        """WB 階段: 寫回暫存器"""
        instruction = self.pipeline_registers["MEM/WB"]
        if not instruction:
            return

        opcode = instruction.split()[0].lower()
        self.log_stage(clock_cycle, opcode, "WB RegWrite=X MemToReg=X")

    def save_output(self, output_file):
        """將最終結果保存到檔案"""
        with open(output_file, 'w') as file:
            file.write("# Example 1 Case\n## Each clocks\n")
            file.write("\n".join(self.clock_log))
            file.write("\n\n## Final Result:\n")
            file.write(f"Total Cycles: {len(self.clock_log)}\n")
            file.write("Final Register Values:\n")
            file.write(" ".join(map(str, self.registers)) + "\n")
            file.write("Final Memory Values:\n")
            file.write(" ".join(map(str, self.memory[:32])) + "\n")

    def run(self):
        """主執行流程"""
        clock_cycle = 1
        while self.running:
            self.write_back(clock_cycle)
            self.memory_access(clock_cycle)
            self.execute(clock_cycle)
            self.decode(clock_cycle)
            self.fetch(clock_cycle)
            clock_cycle += 1

if __name__ == "__main__":
    simulator = MIPSSimulator()

    # 指定輸入與輸出檔案
    input_file = "C:\\Users\\user\\Documents\\GitHub\\MIPS\\inputs\\test1.txt"
    output_file = "C:\\Users\\user\\Documents\\GitHub\\MIPS\\outputs\\result.txt"

    # 載入指令並執行
    simulator.load_instructions_from_file(input_file)
    simulator.run()
    simulator.save_output(output_file)
