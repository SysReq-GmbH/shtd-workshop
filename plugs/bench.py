"""Simulated instruments for the SIB-200 bench.

A plug is a plain Python class. The engine creates it once per run and hands
it to every phase that names it in procedure.yaml. Swap these for real
drivers (VISA, serial, a vendor SDK) and nothing else changes.

Everything here is simulated: no DMM, no power supply, no board needed.
The values are realistic, with a bit of noise. About one board in ten has
a weak 3.3 V regulator, so you will see a FAIL. That is on purpose.
"""

import random  # noise on the measurements
import time  # small delays, so the run feels like a real bench

# One board in ten fails on the 3.3 V rail. Drawn once per run, when the
# DMM is created, so every phase of that run sees the same board.
_FAIL_RATE = 1 / 10


class PowerSupply:
    """A bench power supply. 24 V output, reads back the current."""

    def __init__(self):
        self.output_on = False
        self.volts = 0.0

    def set_voltage(self, volts: float):
        self.volts = volts

    def enable(self):
        self.output_on = True
        time.sleep(0.3)  # a real supply needs a moment to settle

    def read_current_ma(self) -> float:
        if not self.output_on:
            return 0.0
        return round(random.gauss(62.0, 2.5), 1)  # idle current, around 62 mA


class DMM:
    """A digital multimeter on the 3.3 V test point."""

    def __init__(self):
        self.bad_board = random.random() < _FAIL_RATE

    def read_volts(self) -> float:
        time.sleep(0.2)
        if self.bad_board:
            return round(random.gauss(3.47, 0.01), 4)  # a weak regulator, out of limits
        return round(random.gauss(3.30, 0.015), 4)  # a good one


class Programmer:
    """An SWD programmer. Flashes the MCU and reads back the firmware version."""

    def flash(self, hex_file: str) -> bool:
        time.sleep(0.8)  # flashing takes a moment
        return True

    def read_version(self) -> str:
        return "2.1.0"


class I2CSensor:
    """The temperature sensor on the board, read over I2C at address 0x48."""

    def __init__(self):
        self.base_temp = random.uniform(20.5, 24.5)  # this board's temperature
        self.drift = 0.0                             # slow change, at most ±0.5 °C

    def read_temp_c(self, addr: int = 0x48) -> float:
        # Each reading moves a little, so the temperature log shows a real curve.
        self.drift += random.gauss(0, 0.05)
        self.drift = max(-0.5, min(0.5, self.drift))
        return round(self.base_temp + self.drift, 2)
