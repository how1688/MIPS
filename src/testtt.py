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

    def load_instructions(self, instructions):
        """
        載入指令。
        """
        self.instructions = instructions

    def detect_hazard(self):
        """
        檢測資料冒險或條件。
        """
        # 如果 `add` 或 `sub` 尚未完成 MEM 階段，阻止 `beq` 进入 EX。
        if self.EX_MEM and self.EX_MEM.get("opcode") in ["add", "sub"]:
            dest = self.EX_MEM.get("destination")
            if self.IF_ID and self.IF_ID.get("opcode") == "beq":
                # 如果 beq 依赖 add 或 sub 的结果，返回 True 表示需要 stall
                if dest in [self.IF_ID.get("source1"), self.IF_ID.get("source2")]:
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

    def execute_cycle(self, cycle):
        """
        執行單個時鐘周期。
        """
        log_entry = [f"Clock Cycle {cycle}:"]

        # Write Back (WB)
        if self.MEM_WB:
            if self.MEM_WB["opcode"] == "add":
                self.registers[self.MEM_WB["destination"]] = self.MEM_WB["value"]
            elif self.MEM_WB["opcode"] == "sub":
                self.registers[self.MEM_WB["destination"]] = self.MEM_WB["value"]
            elif self.MEM_WB["opcode"] == "lw":
                self.registers[self.MEM_WB["destination"]] = self.MEM_WB["value"]

            log_entry.append(f"WB: {self.MEM_WB['opcode']} RegWrite={self.MEM_WB.get('control', {}).get('RegWrite', 'X')}")

        # Memory Access (MEM)
        if self.EX_MEM:
            if self.EX_MEM["opcode"] == "lw":
                address = self.EX_MEM["address"]
                value = self.memory[address // 4]
                self.EX_MEM["value"] = value
            elif self.EX_MEM["opcode"] == "sw":
                address = self.EX_MEM["address"]
                self.memory[address // 4] = self.registers[self.EX_MEM["destination"]]
            elif self.EX_MEM["opcode"] in ["add", "sub"]:
                # `add` 和 `sub` 不需要訪問記憶體，只更新 value
                pass

            log_entry.append(f"MEM: {self.EX_MEM['opcode']}")

        # Execute (EX)
        if self.ID_EX:
            if self.ID_EX["opcode"] == "add":
                source1 = self.registers[self.ID_EX["source1"]]
                source2 = self.registers[self.ID_EX["source2"]]
                self.ID_EX["value"] = source1 + source2
            elif self.ID_EX["opcode"] == "sub":
                source1 = self.registers[self.ID_EX["source1"]]
                source2 = self.registers[self.ID_EX["source2"]]
                self.ID_EX["value"] = source1 - source2
            elif self.ID_EX["opcode"] in ["lw", "sw"]:
                base = self.registers[self.ID_EX["base"]]
                offset = self.ID_EX["offset"]
                self.ID_EX["address"] = base + offset
            elif self.ID_EX["opcode"] == "beq":
                source1 = self.registers[self.ID_EX["source1"]]
                source2 = self.registers[self.ID_EX["source2"]]
                if source1 == source2:
                    # 設置分支目標地址
                    self.pc += self.ID_EX["offset"]
                    self.IF_ID = None  # 清空 IF/ID 暫存器，停止抓取新指令
            log_entry.append(f"EX: {self.ID_EX['opcode']}")

        # Instruction Decode (ID)
        if self.IF_ID:
            # 如果 `beq` 等待 `add` 或 `sub` 完成，則停止進入 EX 階段
            if self.IF_ID["opcode"] == "beq" and self.detect_hazard():
                log_entry.append("Stall: beq waiting for add/sub to finish")
            else:
                log_entry.append(f"ID: {self.IF_ID['opcode']}")

        # Instruction Fetch (IF)
        next_instr = None
        if not self.detect_hazard():
            next_instr = self.fetch_next_instruction()
            if next_instr:
                log_entry.append(f"IF: {next_instr['opcode']}")
        else:
            log_entry.append("Stall: Data Hazard Detected")

        self.pipeline_log.append("\n".join(log_entry))

        # 更新流水線寄存器
        self.MEM_WB = self.EX_MEM
        self.EX_MEM = self.ID_EX
        self.ID_EX = self.IF_ID
        self.IF_ID = next_instr

    def print_results(self, output_file):
        """
        輸出結果到檔案。
        """
        with open(output_file, "w") as f:
            f.write("# Execution Log\n")
            for log in self.pipeline_log:
                f.write(log + "\n\n")

            f.write("## Final Results:\n")
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

    # 指令檔案路徑
    input_file = "C:\\Users\\user\\Downloads\\SampleProject (1)\\SampleProject\\inputs\\test4.txt"
    output_file = "C:\\Users\\user\\Downloads\\SampleProject (1)\\SampleProject\\inputs\\test4_output.txt"
    # 讀取指令
    with open(input_file, "r") as f:
        instructions = [parse_instruction(line.strip()) for line in f if line.strip()]

    # 載入指令並執行
    cpu.load_instructions(instructions)
    cycle = 1
    while cpu.pc < len(cpu.instructions) or any([cpu.IF_ID, cpu.ID_EX, cpu.EX_MEM, cpu.MEM_WB]):
        cpu.execute_cycle(cycle)
        cycle += 1

    # 輸出結果
    cpu.print_results(output_file)
