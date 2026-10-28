"""The five phases of the SIB-200 test.

A phase is a plain Python function. The engine calls it with `measurements`
and the plugs it asks for by name (the names come from `plugs:` in
procedure.yaml). The phase reads the instrument and stores a number. It never
decides pass or fail: the limits in procedure.yaml do that.

If you come from TestStand: a phase is a Step, `measurements.x = ...` fills a
Numeric Limit Test, and the limits sit in the YAML next to the step.
"""

import time  # to space out the temperature readings


def power_on(measurements, psu, log):
    psu.set_voltage(24.0)                           # the SIB-200 runs on 24 V
    psu.enable()
    measurements.idle_current = psu.read_current_ma()
    log.info(f"idle current {measurements.idle_current} mA")


def rail_3v3(measurements, dmm, log):
    measurements.rail_3v3 = dmm.read_volts()        # the engine compares it to 3.2 .. 3.4 V
    log.info(f"3.3 V rail {measurements.rail_3v3} V")


def flash_firmware(measurements, programmer, log):
    programmer.flash("sib200_v2.1.0.hex")
    measurements.firmware_version = programmer.read_version()
    log.info(f"firmware {measurements.firmware_version}")


def read_sensor(measurements, sensor, log):
    measurements.temp_c = sensor.read_temp_c(0x48)  # 0x48: the sensor's I2C address
    log.info(f"temperature {measurements.temp_c} °C")


def temperature_log(measurements, sensor, log, ui):
    # 100 readings, one every 20 ms: 2 seconds in total.
    times = []
    temps = []
    start = time.monotonic()
    for i in range(100):
        times.append(round(time.monotonic() - start, 3))
        temps.append(sensor.read_temp_c(0x48))
        ui.progress = i + 1                     # the progress bar on screen, 0 to 100
        next_reading = start + (i + 1) * 0.02   # when the next reading is due
        time.sleep(max(0, next_reading - time.monotonic()))

    # A curve: time on the x axis, temperature on the y axis.
    measurements.temperature_log.x_axis = times
    measurements.temperature_log.y_axis.temperature = temps

    # The limits in procedure.yaml check the lowest and highest values.
    measurements.temperature_log.y_axis.temperature.aggregations.min = min(temps)
    measurements.temperature_log.y_axis.temperature.aggregations.max = max(temps)
    log.info(f"temperature from {min(temps)} to {max(temps)} °C")
