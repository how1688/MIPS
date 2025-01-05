class CPU:
    def __init__(self):
        # 記憶體與暫存器初始化
        self.memory = [0] * 256  # 指令記憶體
        self.registers = [1] * 32  # 暫存器檔 (32 registers)
        self.registers[0] = 0
        self.pipeline_registers = {
            "IF/ID": None  # 暫存器，用於傳遞 IF -> ID 資料
        }
        self.pc = 0  # 程式計數器 (PC)
        self.running = True

    def load_instructions(self, instructions):
        """
        將指令載入記憶體。
        """
        for i, instr in enumerate(instructions):
            self.memory[i] = instr

    def fetch(self):
        """
        IF 階段: 抓取指令
        """
        if self.pc < len(self.memory) and self.memory[self.pc]:
            instruction = self.memory[self.pc]
            self.pipeline_registers["IF/ID"] = instruction
            print(f"IF: Fetch instruction '{instruction}' at PC={self.pc}")
            self.pc += 1  # 更新程式計數器
        else:
            self.pipeline_registers["IF/ID"] = None
            print(f"IF: No instruction to fetch at PC={self.pc}")
            self.running = False  # 無新指令時結束執行

    def decode(self):
        """
        ID 階段: 解碼指令並讀取操作數
        """
        instruction = self.pipeline_registers["IF/ID"]
        if not instruction:
            print("ID: No instruction to decode")
            return

        parts = instruction.split()
        opcode = parts[0]
        decoded = {"opcode": opcode}

        if opcode in ["add", "sub"]:
            # R-format: add rd, rs, rt
            rd, rs, rt = parts[1], parts[2], parts[3]
            decoded.update({
                "rd": int(rd[1:]),  # 去掉 `$`，轉成整數
                "rs": int(rs[1:]),
                "rt": int(rt[1:])
            })
            print(f"ID: Decode {opcode} rd=${decoded['rd']}, rs=${decoded['rs']}, rt=${decoded['rt']}")

        elif opcode in ["lw", "sw"]:
            # I-format: lw/sw rt, offset(base)
            rt, offset_base = parts[1], parts[2]
            offset, base = offset_base.split("(")
            base = base.strip(")")  # 去掉括號
            decoded.update({
                "rt": int(rt[1:].strip(",")),
                "offset": int(offset),
                "base": int(base[1:])
            })
            print(f"ID: Decode {opcode} rt=${decoded['rt']}, offset={decoded['offset']}, base=${decoded['base']}")

        elif opcode == "beq":
            # Branch: beq rs, rt, offset
            rs, rt, offset = parts[1], parts[2], parts[3]
            decoded.update({
                "rs": int(rs[1:]),
                "rt": int(rt[1:]),
                "offset": int(offset)
            })
            print(f"ID: Decode {opcode} rs=${decoded['rs']}, rt=${decoded['rt']}, offset={decoded['offset']}")

        else:
            print(f"ID: Unsupported instruction '{instruction}'")
            return

        # 將解碼結果傳遞到下一階段 (目前僅解碼)
        self.pipeline_registers["ID/EX"] = decoded

    def run(self):
        """
        主執行邏輯。
        """
        while self.running:
            self.decode()
            self.fetch()


# 測試模擬器功能
if __name__ == "__main__":
    cpu = CPU()

    # 測試指令集
    instructions = [
        "add $1 $2 $3",  # $1 = $2 + $3
        "sub $4 $5 $6",  # $4 = $5 - $6
        "lw $7, 16($8)",  # $7 = MEM[$8 + 16]
        "sw $9, 32($10)",  # MEM[$10 + 32] = $9
        "beq $11 $12 -4"  # if ($11 == $12) branch to PC - 4 instructions
    ]

    # 載入指令並執行
    cpu.load_instructions(instructions)
    cpu.run()
