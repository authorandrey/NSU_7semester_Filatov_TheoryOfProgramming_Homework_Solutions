package nsu.ram

/** A RASP machine stores its program and data in the same memory.
  *
  * Memory cells are numbered from 0. Cell 0 is the accumulator (R0), while the
  * compiled program starts at cell 1: opcode in M[1], argument in M[2], next
  * opcode in M[3], and so on. Consequently the RASP program counter is the
  * address of the opcode cell and advances by two after an ordinary command.
  * Jump arguments are absolute memory addresses, not instruction numbers.
  */
object RASPMachine {
  def programAsMemory(prog: Program, instrSet: InstructionSet): RAM = {
    val memory = new RAM()
    val coder = instrSet.asCommands()

    prog.cmds.zipWithIndex.foreach { case ((cmd, arg), index) =>
      val opcodeAddress = Register(2 * index + 1)
      memory.writeRegister(opcodeAddress, coder.encode(cmd))
      memory.writeRegister(opcodeAddress.plusOne(), arg)
    }

    memory
  }
}

final class RASPMachine private (
  memory: RAM,
  input: Input,
  instructionSet: InstructionSet,
  logger: Logger
) extends Executor(
  memory,
  memory,
  IOModule(input, new BufferedOutput()),
  instructionSet.asCommands(),
  logger
) with RASPControl with InspectableMachine {

  def this(instrSet: InstructionSet, prog: Program, input: Input, logger: Logger) =
    this(RASPMachine.programAsMemory(prog, instrSet), input, instrSet, logger)

  /** In RASP, code can be rewritten by normal Store/Read instructions. */
  override protected def jumpTo(target: Register): Unit = updatePC(target)

  def printState(): String = {
    val printer = new StringBuilder
    val pc = currentPC()
    val opcode = dataMemory.readRegister(pc)
    val argument = dataMemory.readRegister(pc.plusOne())
    val decoded = decodeCmd(opcode).map(_.toString).getOrElse(s"<invalid opcode ${opcode.value}>")

    printer.append("Input     :").append(io.in).append("\n")
      .append("Output    :").append(io.out).append("\n\n")
      .append("Registers :").append(dataMemory).append("\n\n")
      .append(s"PC             :  ${pc.value}\n")
      .append(s"Current command:  ${opcode.value} ${argument.value}\n")
      .append(s"               :  $decoded ${argument.value}\n")
      .toString
  }

  override def nextCommand(): Unit = updatePC(currentPC().plus(Register.TWO))
}

trait RASPControl extends Control {
  private var current: Register = Register.ONE

  override def currentPC(): Register = current
  override def updatePC0(newPC: Register): Unit = {
    current = newPC
  }
}
