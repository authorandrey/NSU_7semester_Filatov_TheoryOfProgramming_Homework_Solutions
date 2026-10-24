package nsu.ram

import java.io.{BufferedWriter, File, FileWriter}
import nsu.ram.parsing.{AsmParser, BinaryParser, Parser, TestParser}

import scala.collection.mutable

object Main {

  // TODO: drop this ugly mess
  private var logger: String => Unit = defaultLogger()
  private def defaultLogger(): String => Unit = println
  def setLogger(l: (String) => Unit): Unit = {
    logger = l
  }

  // Use a platform-independent form in logs and golden-file tests.
  private def displayPath(file: File): String = file.getAbsolutePath.replace('\\', '/')

  private def runTest(t: Test, p: Program, maxIter: Int, rasp: Boolean = false): (ExecutionResult, Seq[String]) = {
    val buf = mutable.ArrayBuffer[String]()
    val log = Logger.toBuffer(buf)

    val machine = createMachine(p, RAMMachine.arrayInput(t.in), (_: String) => (), rasp)

    val result = runMachine(machine, maxIter, log) match {
      case (OutOfIterations, _) => OutOfIterations
      case (e: Error, _) => e
      case (HaltReached, its) =>
        val out = machine.io.out.current()
        val expected = t.out
        logger(s" ${its.get} iterations. ")
        if (out.length == expected.length &&
          out.zipWithIndex.forall { case (register, i) => expected(i).equals(register) }
        ) {
          Success
        } else {
          Error(s"Output differs from expected." +
            s"\n  Expected = ${expected map (_.value) mkString " "}" +
            s"\n  Real     = ${out map (_.value) mkString " "}")
        }
      case (Success, _) =>
        Error("Execution returned success without reaching HALT")
    }

    (result, buf.toList)
  }

  private def runMachine(ram: Executor with InspectableMachine, maxIters: Int, logger: Logger) : (ExecutionResult, Option[Int]) = {
    for (iteration <- 0 to maxIters) {
      logger.log(s"====================================================\n")
      logger.log(s"Iteration $iteration:\n")
      logger.log(ram.printState() + "\n")
      ram.step() match {
        case HaltReached =>
          logger.log("HALT executed, stopping\n")
          logger.log("Final output:" + ram.io.out + "\n")
          return (HaltReached, Some(iteration + 1))

        case Error(desc) =>
          logger.log("Execution stopped, reason = " + desc + "\n")
          return (Error(desc), Some(iteration + 1))

        case _ =>
      }
    }

    logger.log("OutOfIterations\n")
    logger.log("Final output:" + ram.io.out + "\n")
    (OutOfIterations, None)
  }

  private def compileToAsm(file: String, rasp: Boolean = false): Unit = {
    assert(file.endsWith(".asm"), s"$file is not *.asm")
    val parser: AsmParser = if (rasp) AsmParser.RASP else AsmParser.DEFAULT
    logger(s"Parsing ${displayPath(new File(file))}\n")

    val (prog, map) = parser.parse(file)

    def changeAsmExtToBinExt(s: String) = {
      assert(s.endsWith(".asm"))
      s.reverse.replaceFirst("msa.", "nib.").reverse
    }

    val outFile = (new File(changeAsmExtToBinExt(file)))

    if (outFile.exists) {
      logger(s"Overwriting ${displayPath(outFile)}\n")
    } else {
      logger(s"Writing to ${displayPath(outFile)}\n")
    }

    val bw = new BufferedWriter(new FileWriter(outFile))
    bw.write(parser.write(prog, map))
    bw.close()
  }

  def main(args: Array[String]): Unit = {
    if (args.isEmpty) {
      logger("run examples:\n")
      logger("  <file>.asm              -- convert sources to binary format\n")
      logger("  <file>.bin \"1 2 3\" 1000 -- start program with input <read_0=1 read_1=2 read_2=3>, at most 1000 iterations\n")
      logger("  --test <file1>.bin <file2>.test 1000 -- test RAM program with all inputs\n")
      logger("  --compile-rasp <file>.asm -- compile an assembly program with RASP label addresses\n")
      logger("  --rasp <file>.bin \"1 2 3\" 1000 -- run a RASP program\n")
      logger("  --rasp-test <file>.bin <file>.test 1000 -- test a RASP program\n")
      return
    }

    args match {
      case Array("--compile-rasp", file) => compileToAsm(file, rasp = true)
      case Array("--rasp", file, in, iter) => runProgram(file, in, iter, rasp = true)
      case Array("--rasp-test", f1, f2, i) => runTests(f1, f2, i, rasp = true)
      case Array(file) => compileToAsm(file)
      case Array(file, in, iter) => runProgram(file, in, iter)
      case Array("--test", f1, f2, i) => runTests(f1, f2, i)
      case _ =>
        logger("Invalid arguments. Run without arguments to see usage.\n")
    }
  }

  private def createMachine(p: Program, input: Input, logger: Logger, rasp: Boolean): Executor with InspectableMachine =
    if (rasp) new RASPMachine(InstructionSet.DEFAULT, p, input, logger)
    else new RAMMachine(InstructionSet.DEFAULT, p, input, logger)

  private def runProgram(file: String, in: String, iter: String, rasp: Boolean = false): Unit = {
    assert(file.endsWith(".bin"))
    val input = in.trim.split(" ")
      .flatMap(Parser.trim)
      .map(s => Register(BigInt(s)))

    val maxIters = Integer.parseInt(iter)

    logger(s"Reading program from ${displayPath(new File(file))}\n")
    val program = BinaryParser.DEFAULT.parse(file)
    logger("Program:\n")
    logger("============\n")
    val prettyParser = if (rasp) AsmParser.RASP else AsmParser.DEFAULT
    logger(prettyParser.write(program, Map.empty) + "\n")
    logger("============\n")

    logger(s"Running with\n")
    logger("  input : " + (if (input.isEmpty) "empty" else input mkString " ") + "\n")
    logger(s"  maxIterations = $maxIters\n")

    val machine = createMachine(program, RAMMachine.arrayInput(input), (_: String) => (), rasp)

    runMachine(machine, maxIters, (msg: String) => logger(msg))
  }

  private def runTests(f1: String, f2: String, i: String, rasp: Boolean = false): Unit = {
    logger("Testing\n")

    logger(s"Reading program from ${displayPath(new File(f1))}\n")
    val program = BinaryParser.DEFAULT.parse(f1)
    logger("Program:\n")
    logger("============\n")
    val prettyParser = if (rasp) AsmParser.RASP else AsmParser.DEFAULT
    logger(prettyParser.write(program, Map.empty))
    logger("============\n")

    val maxIters = Integer.parseInt(i)
    logger(s"Max iterations = $maxIters\n")

    logger(s"Reading tests from ${displayPath(new File(f2))}\n")
    val tests = TestParser.DEFAULT.parse(f2).toList
    logger(s"  tests = ${tests.length}\n")

    for ((t, i) <- tests.zipWithIndex) {
      logger(s"${i + 1} / ${tests.length} ${t.name} ...\n")
      val start = System.currentTimeMillis()
      runTest(t, program, maxIters, rasp) match {
        case (Success, _) =>
          val end = System.currentTimeMillis()
          logger(s"  Success\n") //  in ${end - start} ms

        case (OutOfIterations, _) =>
          logger("  Out of iterations\n")

        case (Error(desc), protocol) =>
          logger(s"  Failed: $desc \n")
          logger(protocol mkString "\n")

        case (HaltReached, protocol) =>
          logger("  Failed: unexpected HALT result from test runner\n")
          logger(protocol mkString "\n")
      }
    }
  }
}
