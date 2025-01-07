from pathlib import Path


class CPU:
    def __init__(self):
        # 初始化暫存器和記憶體
        self.registers = [1] * 32  # 所有暫存器初始值為 1
        self.registers[0] = 0  # $0 暫存器永遠為 0
        self.memory = [1] * 32  # 記憶體大小為 32 words
        self.pc = 0  # 程式計數器
        self.instructions = []  # 儲存解析後的指令
        self.pipeline_log = []  # 每個時鐘週期的執行記錄

        # 流水線寄存器
        self.IF_ID = None
        self.ID_EX = None
        self.EX_MEM = None
        self.MEM_WB = None

    def load_instructions(self, instructions):
        """載入指令"""
        self.instructions = instructions

    def detect_hazard(self):
        """
        檢測流水線中的資料冒險。
        Returns:
            bool: 如果需要暫停流水線返回 True，否則返回 False。
        """
        # 檢測 Load-Use Hazard
        if self.EX_MEM and self.EX_MEM.get("opcode") == "lw":
            # EX/MEM 的目標暫存器
            dest = self.EX_MEM.get("destination")
            print(dest, self.ID_EX)
            if self.ID_EX and self.ID_EX.get("opcode") in ["add", "sub"]:
                # IF/ID 的來源暫存器
                sources = [self.ID_EX.get("source1"), self.ID_EX.get("source2")]
                if dest in sources:
                    return True  # Load-Use Hazard 檢測到，需停頓

        # 檢測控制冒險（分支指令依賴）
        if self.ID_EX and self.ID_EX.get("opcode") in ["beq"]:
            source1 = self.ID_EX.get("source1")
            source2 = self.ID_EX.get("source2")
            if self.EX_MEM:
                if self.EX_MEM.get("destination") in [source1, source2]:
                    return True  # 分支條件依賴 EX/MEM 的目標暫存器，需停頓
            if self.MEM_WB:
                if self.MEM_WB.get("destination") in [source1, source2] and self.MEM_WB.get("opcode") in ["lw", "sw"]:
                    return True  # 分支條件依賴 MEM/WB 的目標暫存器，需停頓

        # 檢測多重相依性（多條指令同時相依的情況）
        # if self.MEM_WB and self.EX_MEM:
        #     dest_MEM = self.EX_MEM.get("destination")
        #     dest_WB = self.MEM_WB.get("destination")
        #     if self.IF_ID:
        #         sources = [self.IF_ID.get("source1"), self.IF_ID.get("source2")]
        #         if dest_MEM in sources or dest_WB in sources:
        #             return True  # 多條目標寄存器與當前指令的來源相依，需停頓

        return False  # 無資料冒險，流水線正常執行

    def fetch_next_instruction(self):
        """抓取下一條指令"""
        if self.pc < len(self.instructions):
            instruction = self.instructions[self.pc]
            self.pc += 1
            return instruction
        return None

    def execute_cycle(self, cycle):
        """執行單個時鐘周期"""
        log_entry = [f"Clock Cycle {cycle}:"]

        # 暫存每個指令的狀態，用於重新排列輸出順序
        instruction_status = []
        
        # Write Back (WB)
        if self.MEM_WB:
            regwrite = self.MEM_WB["control"].get("RegWrite", "X")
            memtoreg = self.MEM_WB["control"].get("MemToReg", "X")
            instruction_status.append(f"{self.MEM_WB['opcode']}: WB RegWrite={regwrite} MemToReg={memtoreg}")
            if self.MEM_WB["opcode"] in ["add", "sub", "lw"]:
                self.registers[self.MEM_WB["destination"]] = self.MEM_WB.get("value", self.registers[self.MEM_WB["destination"]])

        # Memory Access (MEM)
        if self.EX_MEM:
            Branch = self.EX_MEM["control"].get("Branch", "X")
            MemRead = self.EX_MEM["control"].get("MemRead", "X")
            MemWrite = self.EX_MEM["control"].get("MemWrite", "X")
            RegWrite = self.EX_MEM["control"].get("RegWrite", "X")
            MemToReg = self.EX_MEM["control"].get("MemToReg", "X")
            instruction_status.append(f"{self.EX_MEM['opcode']}: MEM Branch={Branch} MemRead={MemRead} MemWrite={MemWrite} RegWrite={RegWrite} MemToReg={MemToReg}")
            if self.EX_MEM["opcode"] == "lw":
                address = self.EX_MEM["address"]
                self.EX_MEM["value"] = self.memory[address // 4]
            elif self.EX_MEM["opcode"] == "sw":
                address = self.EX_MEM["address"]
                self.memory[address // 4] = self.registers[self.EX_MEM["destination"]]
            elif self.EX_MEM["opcode"] in ["add", "sub"]:
                self.registers[self.EX_MEM["destination"]] = self.EX_MEM.get("value", self.registers[self.EX_MEM["destination"]])

        # Execute (EX)
        if self.ID_EX:
            if not self.detect_hazard():
                RegDst = self.ID_EX["control"].get("RegDst", "X")
                ALUSrc = self.ID_EX["control"].get("ALUSrc", "X")
                Branch = self.ID_EX["control"].get("Branch", "X")
                MemRead = self.ID_EX["control"].get("MemRead", "X")
                MemWrite = self.ID_EX["control"].get("MemWrite", "X")
                RegWrite = self.ID_EX["control"].get("RegWrite", "X")
                MemToReg = self.ID_EX["control"].get("MemToReg", "X")
                instruction_status.append(f"{self.ID_EX['opcode']}: EX RegDst={RegDst} ALUSrc={ALUSrc} Branch={Branch} MemRead={MemRead} MemWrite={MemWrite} RegWrite={RegWrite} MemToReg={MemToReg}")
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
                        self.pc -= 1
                        print(self.pc, "Branch taken to", self.ID_EX["offset"])
                        self.pc += self.ID_EX["offset"]
                        self.IF_ID = None  # 清空 IF/ID 暫存器
            else:
                if self.ID_EX:
                    instruction_status.append(f"{self.ID_EX['opcode']}: ID")
                if self.IF_ID:
                    instruction_status.append(f"{self.IF_ID['opcode']}: IF")
                # 如果發生冒險，停止更新 IF/ID 和 PC
                self.pipeline_log.append("\n".join(log_entry + instruction_status))
                self.MEM_WB = self.EX_MEM
                self.EX_MEM = []
                # IF/ID 保持不變，不抓取新指令
                return
        # Instruction Decode (ID)
        if self.IF_ID:
            instruction_status.append(f"{self.IF_ID['opcode']}: ID")

        # Instruction Fetch (IF)
        next_instr = self.fetch_next_instruction()
        if next_instr:
            instruction_status.append(f"{next_instr['opcode']}: IF")

        # 排列日誌輸出
        log_entry.extend(instruction_status)
        self.pipeline_log.append("\n".join(log_entry))

        # 更新流水線寄存器
        self.MEM_WB = self.EX_MEM
        self.EX_MEM = self.ID_EX
        self.ID_EX = self.IF_ID
        self.IF_ID = next_instr


    def print_results(self, output_file):
        """輸出結果到檔案"""
        with open(output_file, "w") as f:
            f.write("# Execution Log\n")
            f.write("\n".join(self.pipeline_log) + "\n\n")
            f.write("## Final Results:\n")
            f.write(f"Total Cycles: {len(self.pipeline_log)}\n")
            f.write("\nFinal Register Values:\n")
            f.write(" ".join(map(str, self.registers)) + "\n")
            f.write("\nFinal Memory Values:\n")
            f.write(" ".join(map(str, self.memory)) + "\n")


def parse_instruction(line):
    """解析指令"""
    parts = line.split()
    opcode = parts[0].lower()  # 確保指令小寫
    operands = [op.strip(",") for op in parts[1:]]
    if opcode in ["lw", "sw"]:
        offset, base = operands[1].split('(')
        offset = int(offset)
        base = int(base.strip(")$").strip("$"))
        return {
            "opcode": opcode,
            "control": {
                "RegDst": "X" if opcode == "sw" else "0",
                "ALUSrc": "1",
                "Branch": "X",
                "MemRead": "1" if opcode == "lw" else "0",
                "MemWrite": "1" if opcode == "sw" else "0",
                "RegWrite": "1" if opcode == "lw" else "0",
                "MemToReg": "1" if opcode == "lw" else "X",
            },
            "destination": int(operands[0].strip("$")),
            "base": base,
            "offset": offset,
        }
    elif opcode in ["add", "sub"]:
        return {
            "opcode": opcode,
            "destination": int(operands[0].strip("$")),
            "control": {
                "RegDst": "1",
                "ALUSrc": "0",
                "Branch": "X",
                "MemRead": "0",
                "MemWrite": "0",
                "RegWrite": "1",
                "MemToReg": "0",
            },
            "source1": int(operands[1].strip("$")),
            "source2": int(operands[2].strip("$")),
        }
    elif opcode == "beq":
        return {
            "opcode": opcode,
            "source1": int(operands[0].strip("$")),
            "source2": int(operands[1].strip("$")),
            "offset": int(operands[2]),
            "control": {
                "RegDst": "X",
                "ALUSrc": "0",
                "Branch": "1",
                "MemRead": "0",
                "MemWrite": "0",
                "RegWrite": "0",
                "MemToReg": "X",
            },
        }
    else:
        raise ValueError(f"Unsupported opcode: {opcode}")


if __name__ == "__main__":
    cpu = CPU()

    # 檔案路徑
    input_file = Path("C:\\Users\\user\\Downloads\\SampleProject (1)\\SampleProject\\inputs\\test3.txt")
    output_file = Path("C:\\Users\\user\\Downloads\\SampleProject (1)\\SampleProject\\inputs\\test3_output.txt")

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
