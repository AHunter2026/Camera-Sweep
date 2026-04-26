from machine import Pin, PWM
from time import sleep, sleep_ms
import sys

servo = PWM(Pin(0))
servo.freq(50)


def set_angle(angle):
    min_duty = 1638
    max_duty = 8192
    duty = int(min_duty + (max_duty - min_duty) * angle / 180)
    servo.duty_u16(duty)


wait_seconds = 30
cycle = 1

print()
print(">>> Sweep Program <<<")
print()

while True:
    print(f"--- Cycle {cycle} ---")

    # Sweep 20 times
    for i in range(1, 21):
        print(f"  Sweep {i} of 20")
        for pos in range(0, 181, 5):
            set_angle(pos)
            sleep_ms(10)
        for pos in range(180, -1, -5):
            set_angle(pos)
            sleep_ms(10)

    # Countdown
    for remaining in range(wait_seconds, 0, -1):
        sys.stdout.write(f"\r  Next cycle in {remaining} seconds...  ")
        sleep(1)
    print()

    cycle += 1