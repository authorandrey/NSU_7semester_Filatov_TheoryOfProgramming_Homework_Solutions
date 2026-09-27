echo "Check if 1.5 with k=4 and base 2 is equivalent to 1.4 with k=4"
py .\1.5_generator.py 4 2 1.5.tur
java -jar .\turing-machine-emulator.jar --program 1.5.tur --test .\1.4.test

echo "Running tests for k=64 and base 10"
py .\1.5_generator.py 64 10 1.5.tur
java -jar .\turing-machine-emulator.jar --program 1.5.tur --test .\1.5.test