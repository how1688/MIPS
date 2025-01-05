class MIPS_Simulator:
    def __init__(self, instructions):
        self.instructions = instructions  # 输入的指令列表
        self.registers = [0] * 32  # 32个寄存器
        self.cycles = 0  # 记录周期数，从0开始
        self.stalls = 0  # 记录暂停周期数
        self.pipeline = [None] * 5  # 模拟五个流水线阶段：IF, ID, EX, MEM, WB

    def check_data_hazard(self, current, previous):
        """检查是否有数据冒险"""
        if current[1] == previous[1] or current[2] == previous[1]:
            return True
        return False

    def handle_stalling(self, current_index):
        """处理数据冒险时的暂停"""
        # 确保 current_index 不超出范围
        if current_index < len(self.instructions) and current_index > 0:
            if self.check_data_hazard(self.instructions[current_index], self.instructions[current_index - 1]):
                self.stalls += 1
                return True
        return False

    def handle_forwarding(self, current, previous):
        """处理转发机制"""
        if previous is not None:
            if previous[4] == current[1]:  # 如果前一个指令的WB阶段写入当前指令需要的寄存器
                current[1] = previous[1]  # 通过转发提供数据
                return True
        return False

    def run(self):
        """模拟MIPS机器运作"""
        instruction_queue = self.instructions.copy()  # 保留指令队列
        while instruction_queue or any(stage is not None for stage in self.pipeline):
            # 每个周期的开始
            self.cycles += 1  # 每次进入新的周期

            # 打印当前流水线状态
            self.print_pipeline_status()

            # 将新的指令推入流水线的IF阶段
            if instruction_queue:
                self.pipeline[0] = instruction_queue.pop(0)

            # 检查是否需要STALL
            if self.handle_stalling(self.cycles - 1):
                continue  # 如果发生了STALL，跳过当前指令的执行

            # 处理转发
            if self.cycles > 1:
                self.handle_forwarding(self.pipeline[1], self.pipeline[0])

            # 推进流水线
            for i in range(4, 0, -1):  # 从WB到IF，逐步推进
                self.pipeline[i] = self.pipeline[i - 1]
            self.pipeline[0] = None  # 清空IF阶段

            # 更新寄存器值
            if self.pipeline[4] is not None:
                self.registers[self.pipeline[4][1]] = self.pipeline[4][3]

    def print_pipeline_status(self):
        """打印当前流水线阶段和周期"""
        print(f"Cycles: {self.cycles}")
        stages = ["IF", "ID", "EX", "MEM", "WB"]
        for stage, instr in zip(stages, self.pipeline):
            if instr is None:
                print(f"  {stage}: No instruction")
            else:
                print(f"  {stage}: {instr[0]} {instr[1:]}")

    def print_summary(self):
        print(f"Total Cycles: {self.cycles}")  # 最后一个周期是结束时的周期
        print(f"Total Stalls: {self.stalls}")
        print(f"Final Registers: {self.registers}")


# 示例指令（格式：[opcode, rs, rt, rd, result]）
# 两个 lw 指令加载数据，最后 add 指令将它们的值相加
instructions = [
    ["lw", 1, 0, 0, None],  # lw $t0, 0($t1) => 将内存地址0 + $t1的值加载到$t0
    ["lw", 1, 4, 2, None],  # lw $t2, 4($t1) => 将内存地址4 + $t1的值加载到$t2
    ["add", 0, 2, 3, None],  # add $t3, $t0, $t2 => 将$t0和$t2相加，结果存入$t3
]

simulator = MIPS_Simulator(instructions)
simulator.run()
simulator.print_summary()
