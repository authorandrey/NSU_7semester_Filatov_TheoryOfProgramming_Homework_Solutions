package nsu.ram

import nsu.ram.Commands._
import nsu.ram.parsing.AsmParser
import org.scalatest.funsuite.AnyFunSuiteLike

class RASPSuite extends AnyFunSuiteLike {
  private val silentLogger: Logger = (_: String) => ()

  private def parse(source: String): Program = AsmParser.RASP.parse(source.linesIterator)._1

  private def executeRaspProgram(source: String, input: Seq[Int] = Seq.empty, maxSteps: Int = 100): (RASPMachine, ExecutionResult) = {
    val program = parse(source)
    val machine = new RASPMachine(
      InstructionSet.DEFAULT,
      program,
      RAMMachine.arrayInput(input.map(i => Register(i)).toArray),
      silentLogger
    )

    var steps = 0
    var result: ExecutionResult = Success
    while (steps < maxSteps && result == Success) {
      result = machine.step()
      steps += 1
    }
    if (result == Success) (machine, OutOfIterations) else (machine, result)
  }

  test("RASP quine prints its own compiled binary code") {
    val source = """Load =1
                    |Store 23
                    |LOOP: Load 23
                    |Sub =22
                    |JGTZ END
                    |Write *23
                    |Load 23
                    |Add =1
                    |Store 23
                    |Jump LOOP
                    |END: Halt 0""".stripMargin

    val (machine, result) = executeRaspProgram(source, maxSteps = 300)
    val expected = Seq(
      1, 1, 4, 23, 2, 23, 9, 22, 25, 21, 22, 23,
      2, 23, 6, 1, 4, 23, 23, 5, 0, 0
    ).map(BigInt(_))

    assert(result == HaltReached)
    assert(machine.io.out.current().map(_.value).toList == expected)
  }

  test("RASP starts at memory cell 1 and steps by two cells") {
    val (machine, result) = executeRaspProgram(
      """Write 1
        |Halt 0""".stripMargin
    )

    assert(result == HaltReached)
    assert(machine.io.out.current().map(_.value).toList == Seq(BigInt(21)))
    assert(machine.currentPC() == Register(3))
  }

  test("RASP jump labels resolve to opcode-cell addresses") {
    val (machine, result) = executeRaspProgram(
      """Load =5
        |Jump END
        |Write =99
        |END: Write =42
        |Halt 0""".stripMargin
    )

    assert(result == HaltReached)
    assert(machine.io.out.current().map(_.value).toList == Seq(BigInt(42)))
    val parsed = parse("""Jump END
                         |Halt 0
                         |END: Halt 0""".stripMargin)
    assert(parsed.cmds.head._2 == Register(5))
  }

  test("RASP instructions can overwrite future instructions") {
    val (machine, result) = executeRaspProgram(
      """Load =0
        |Store 5
        |Write =99
        |Halt 0""".stripMargin
    )

    assert(result == HaltReached)
    assert(machine.io.out.current().isEmpty)
    assert(machine.dataMemory.readRegister(Register(5)) == Register(0))
  }

  test("RASP Read consumes input and writes into shared memory") {
    val (machine, result) = executeRaspProgram(
      """Read 20
        |Write 20
        |Halt 0""".stripMargin,
      input = Seq(73)
    )

    assert(result == HaltReached)
    assert(machine.io.out.current().map(_.value).toList == Seq(BigInt(73)))
    assert(machine.dataMemory.readRegister(Register(20)) == Register(73))
  }

  test("RASP labels leave RAM label behavior unchanged") {
    val source = """Jump END
                   |Halt 0
                   |END: Halt 0""".stripMargin
    val ram = AsmParser.DEFAULT.parse(source.linesIterator)._1
    val rasp = AsmParser.RASP.parse(source.linesIterator)._1

    assert(ram.cmds.head._2 == Register(3))
    assert(rasp.cmds.head._2 == Register(5))
  }
}
